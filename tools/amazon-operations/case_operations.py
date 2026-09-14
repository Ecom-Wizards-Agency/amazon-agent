"""Case preparation and correspondence verification inside the operations journal.

The caller authenticates requests through case_service. This module binds that
service's revision to immutable outgoing content; it never maintains a second
send journal or infers success from a submit-button response.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path


class CaseOperationError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, code, message):
    if not condition:
        raise CaseOperationError(code, message)


def timestamp(value):
    try:
        result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.tzinfo is not None, 'invalid_time', 'Case timestamps require timezone')
        return result
    except (ValueError, TypeError, AttributeError) as exc:
        raise CaseOperationError('invalid_time', 'Expected case timestamp with timezone') from exc


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize_body(value):
    # HTML rendering and textarea values normalize line endings. No whitespace
    # collapse, signature stripping, substring, or approximate message matching.
    return value.replace('\r\n', '\n').replace('\r', '\n').strip('\n')


def validate_targets(operation, targets):
    key = 'issue_key' if operation == 'case.create' else 'case_id'
    require(operation in {'case.create', 'case.reply'} and isinstance(targets, list) and len(targets) == 1, 'invalid_targets', 'Cases require exactly one typed target')
    target = targets[0]
    require(isinstance(target, dict) and set(target) == {key} and isinstance(target[key], str) and target[key].strip(), 'invalid_targets', f'Case target must contain only {key}')
    if key == 'case_id':
        require(bool(re.fullmatch(r'[0-9]{5,30}', target[key])), 'invalid_targets', 'Amazon case ID must be numeric')
    return targets


def prepare(request, directory):
    inputs = request['inputs']
    validate_targets(request['operation'], request['targets'])
    body = inputs.get('signed_body')
    require(isinstance(body, str) and body.strip(), 'missing_message', 'Exact signed message is required')
    owner, mandate, binding = inputs.get('owner', {}), inputs.get('mandate', {}), inputs.get('case_binding', {})
    require(isinstance(owner, dict) and owner.get('member_id') and owner.get('signature_name') and isinstance(owner.get('revision'), int) and owner['revision'] > 0, 'missing_owner', 'Verified owner name and revision are required')
    require(normalize_body(body).endswith(owner.get('signature', owner['signature_name'])), 'signature_mismatch', 'Message must end with the saved owner signature')
    require(mandate.get('id') and isinstance(mandate.get('revision'), int) and mandate['revision'] > 0, 'missing_mandate', 'Case mandate ID and revision required')
    require(binding.get('registry_id') and binding.get('owner_revision') == owner['revision'] and binding.get('mandate_id') == mandate['id'] and binding.get('mandate_revision') == mandate['revision'] and isinstance(binding.get('authorization_revision'), int), 'binding_mismatch', 'Case binding must match the owner and mandate revision')
    baseline = inputs.get('baseline', {})
    observed = timestamp(baseline.get('observed_at'))
    require(observed <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5), 'invalid_time', 'Case baseline cannot be future dated')
    for key in ('contact_ids', 'case_ids'):
        require(isinstance(baseline.get(key, []), list) and all(isinstance(v, str) for v in baseline.get(key, [])), 'invalid_baseline', f'{key} must be a list of IDs')
    subject = inputs.get('subject', '')
    duplicate_query = None
    if request['operation'] == 'case.create':
        require(isinstance(subject, str) and subject.strip() and '\n' not in subject, 'missing_subject', 'New case requires an exact one-line subject')
        identity = re.search(r'\bFBA[A-Z0-9]{8,12}\b|\bB0[A-Z0-9]{8}\b', subject + ' ' + str(inputs.get('issue_key', '')), re.I)
        duplicate_query = identity.group(0).upper() if identity else subject.strip()
        require(baseline.get('duplicate_query') == duplicate_query, 'duplicate_query_mismatch', 'New case baseline must come from the same scoped issue/subject search')
    attachments = inputs.get('attachments', [])
    require(isinstance(attachments, list), 'invalid_attachments', 'Attachments must be a list')
    copied, names = [], set()
    for index, artifact in enumerate(attachments):
        require(isinstance(artifact, dict), 'invalid_attachment', 'Attachment must contain path, sha256 and name')
        name = artifact.get('name')
        require(isinstance(name, str) and name == Path(name).name and name not in {'', '.', '..'} and name not in names, 'invalid_attachment', 'Attachment names must be unique plain filenames')
        names.add(name)
        path = Path(artifact.get('path', '')).expanduser().resolve()
        require(path.is_file() and sha(path) == artifact.get('sha256'), 'artifact_changed', 'Attachment source checksum mismatch')
        target_dir = directory / 'attachments' / str(index)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / name
        shutil.copyfile(path, target)
        require(sha(target) == artifact['sha256'], 'artifact_changed', 'Attachment changed while copying')
        copied.append({'name': name, 'path': str(target), 'sha256': artifact['sha256'], 'size': target.stat().st_size})
    return {**inputs, 'status': 'prepared', 'adapter': 'cases.cdp', 'requires_live_canary': True, 'signed_body': normalize_body(body), 'attachments': copied,
            'duplicate_query': duplicate_query, 'message_sha256': hashlib.sha256(normalize_body(body).encode()).hexdigest()}


def case_service():
    path = Path(__file__).with_name('case_service.py')
    spec = importlib.util.spec_from_file_location('amazon_case_service', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_execution(plan, grant, *, case_state_dir=None, case_policy_path=None):
    require(grant.get('case_binding') == plan['body']['case_binding'], 'binding_mismatch', 'Execution grant must bind the exact case ownership and mandate')
    case_service().validate_send_binding(plan['body']['case_binding'], plan['body'], account=plan['account'], operation=plan['operation'], targets=plan['targets'], operation_id=plan['operation_id'], request_hash=plan['request_hash'], state_dir=case_state_dir, config_path=case_policy_path)
    if grant.get('allow_live_canary') is not True:
        validate_adapter_readiness(plan['account'], plan['operation'], policy_path=case_policy_path, cases_root=case_state_dir)


def validate_adapter_readiness(account, operation, *, policy_path=None, cases_root=None):
    """Enable a profile only from its independently verified canary journal."""
    policy_path = Path(policy_path or Path.home() / '.amazon-agent/case-policy.json')
    cases_root = Path(cases_root or Path.home() / '.amazon-agent/cases').resolve()
    require(policy_path.is_file(), 'canary_required', 'No trusted case rollout policy exists')
    policy = json.loads(policy_path.read_text())
    readiness = policy.get('profile_readiness', {}).get(account['profile_key'], {})
    require(readiness.get('account') == account, 'canary_required', 'Readiness must bind the exact target account')
    access = 'create_access' if operation == 'case.create' else 'reply_access'
    require(readiness.get(access) is True, 'case_access_unverified', 'Case access has not been verified for this profile')
    canary = readiness.get('canaries', {}).get(operation, {})
    operation_id = canary.get('operation_id', '')
    require(isinstance(operation_id, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', operation_id), 'canary_required', 'A verified case canary is required')
    journal_path = (cases_root / 'operations' / operation_id / 'journal.json').resolve()
    require(journal_path.is_relative_to(cases_root / 'operations') and journal_path.is_file(), 'canary_required', 'Canary journal is missing or outside the canonical operation directory')
    journal = json.loads(journal_path.read_text())
    require(journal.get('verified') is True and journal.get('status') == 'verified' and journal.get('account') == account and journal.get('operation') == operation and journal.get('plan_hash') == canary.get('plan_hash'), 'canary_required', 'Canary journal does not verify this account and operation')
    evidence = Path(journal.get('evidence_path', '')).resolve()
    require(str(evidence) == str(Path(canary.get('evidence_path', '')).resolve()) and evidence.is_relative_to(journal_path.parent) and evidence.is_file(), 'canary_required', 'Canary requires its persisted independent correspondence evidence')
    proof = json.loads(evidence.read_text())
    require(proof.get('account') == account and proof.get('plan_hash') == journal['plan_hash'] and proof.get('history_complete') is True, 'canary_required', 'Canary readback is not bound to the verified journal')
    timestamp(canary.get('verified_at'))
    return readiness


def collect(service, directory, state, plan):
    response = service.run_collector(directory, 'cases.mjs', {
        'schema_version': 1, 'mode': 'observe', 'operation_id': plan['operation_id'],
        'operation': plan['operation'], 'account': plan['account'], 'plan_hash': state['plan_hash'],
        'targets': plan['targets'], 'inputs': plan['body'],
        'case_id': state.get('submission_id'),
    })
    state['last_collection'] = response
    return response if response.get('status') == 'collected' else None


def reconcile(service, directory, state, plan, request):
    if state['status'] == 'verified':
        return state
    require(state.get('execution_started_at'), 'missing_submission', 'Case reconciliation requires a recorded execution attempt')
    # Case evidence always comes from a fresh read-only collector. The sender's
    # response, staged form and caller-provided evidence cannot prove delivery.
    require(not request.get('evidence'), 'untrusted_case_evidence', 'Case reconciliation collects fresh correspondence directly')
    evidence = collect(service, directory, state, plan)
    if evidence is None:
        return service.persist(directory, state, 'uncertain', reason='case_readback_unavailable', next_action='reconcile')
    require(evidence.get('account') == plan['account'] and evidence.get('plan_hash') == state['plan_hash'], 'identity_mismatch', 'Case evidence account/plan mismatch')
    observed = timestamp(evidence.get('observed_at'))
    started = timestamp(state['execution_started_at'])
    require(started <= observed <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5), 'stale_evidence', 'Case observation is stale or future dated')
    require(evidence.get('history_complete') is True, 'incomplete_history', 'Readback must include complete correspondence')
    body = plan['body']
    wanted_id = plan['targets'][0].get('case_id') or state.get('submission_id')
    matches = []
    for case in evidence.get('cases', [evidence]):
        if wanted_id and case.get('case_id') != wanted_id:
            continue
        if plan['operation'] == 'case.create' and (case.get('case_id') in body['baseline'].get('case_ids', []) or case.get('subject') != body['subject']):
            continue
        for contact in case.get('contacts', []):
            if contact.get('is_amazon') is not False or contact.get('id') in body['baseline'].get('contact_ids', []):
                continue
            if normalize_body(str(contact.get('message', ''))) != body['signed_body']:
                continue
            sent_at = timestamp(contact.get('timestamp'))
            if sent_at < started.replace(microsecond=0) or sent_at > observed:
                continue
            actual = contact.get('attachments')
            if not isinstance(actual, list) or len(actual) != len(body['attachments']):
                continue
            expected = {(x['name'], x['sha256']) for x in body['attachments']}
            if {(x.get('name'), x.get('sha256')) for x in actual} != expected:
                continue
            matches.append((case['case_id'], contact['id'], contact['timestamp']))
    path = directory / 'case-readback.json'
    # Operations.persist uses the existing atomic journal writer. Evidence is
    # immutable per digest and never treated as authorization.
    content = json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()
    path = directory / ('case-readback-' + hashlib.sha256(content).hexdigest() + '.json')
    path.write_bytes(content)
    if len(matches) != 1:
        return service.persist(directory, state, 'uncertain', reason='case_readback_ambiguous' if matches else 'case_message_not_observed', evidence_path=str(path), next_action='reconcile')
    case_id, contact_id, sent_at = matches[0]
    return service.persist(directory, state, 'verified', submission_id=case_id, case_id=case_id, contact_id=contact_id, sent_at=sent_at, owner=body['owner'], login_identity=evidence.get('login_identity'), evidence_path=str(path), reason='case_correspondence_verified', next_action=None)
