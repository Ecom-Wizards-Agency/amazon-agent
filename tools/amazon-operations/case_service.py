#!/usr/bin/env python3
"""Shared case ownership and daily lifecycle; amazon-operations owns every send.

This is a trusted local-process API, like operations.py. Slack callers authenticate
the original message; attended callers bind the configured local operator. Neither
may supply a signature. Private member policy is read afresh for each authorization.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from zoneinfo import ZoneInfo

DEFAULT_STATE = Path.home() / '.amazon-agent/cases'
DEFAULT_CONFIG = Path.home() / '.amazon-agent/case-policy.json'
ZONE = ZoneInfo('Asia/Bangkok')
ROUTINE_CATEGORIES = frozenset({'factual_evidence', 'clarification', 'status_check'})


class CaseError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def require(condition, code, message):
    if not condition:
        raise CaseError(code, message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def timestamp(value):
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        require(parsed.tzinfo is not None, 'invalid_time', 'Timestamp requires a timezone')
        return parsed
    except (ValueError, TypeError) as exc:
        raise CaseError('invalid_time', 'Expected an ISO timestamp with timezone') from exc


def business_due(value, days=3):
    day = timestamp(value).astimezone(ZONE).date()
    while days:
        day += dt.timedelta(days=1)
        if day.weekday() < 5:
            days -= 1
    return dt.datetime.combine(day, dt.time(9), ZONE).isoformat()


class CaseService:
    def __init__(self, state_dir=None, config_path=None, *, clock=None):
        self.root = Path(state_dir or DEFAULT_STATE).expanduser().resolve()
        self.config_path = Path(config_path or DEFAULT_CONFIG).expanduser().resolve()
        self.clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self._transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, account_key TEXT NOT NULL, issue_key TEXT NOT NULL, remote_id TEXT, data TEXT NOT NULL, UNIQUE(account_key, issue_key), UNIQUE(account_key, remote_id))')
            db.execute('CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, case_id TEXT NOT NULL)')
        os.chmod(self.root / 'registry.sqlite3', 0o600)

    @contextlib.contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.root / 'registry.sqlite3', timeout=30)
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _now(self):
        value = self.clock()
        require(value.tzinfo is not None, 'invalid_time', 'Clock requires a timezone')
        return value

    def _policy(self):
        try:
            policy = json.loads(self.config_path.read_text())
        except (OSError, ValueError) as exc:
            raise CaseError('policy_unavailable', 'Trusted local case member policy is unavailable') from exc
        require(isinstance(policy.get('members'), dict), 'invalid_policy', 'Case policy requires members')
        return policy

    def _member(self, member_id):
        value = self._policy()['members'].get(member_id, {})
        require(value.get('approved') is True and value.get('signature_name') and value.get('signature'), 'unknown_owner', 'Case owner needs an approved signature in local policy')
        return {'member_id': member_id, 'signature_name': value['signature_name'], 'signature': value['signature']}

    def _authorization(self, value):
        require(isinstance(value, dict), 'missing_authorization', 'A trusted team or attended request is required')
        member = self._member(value.get('requester_id'))
        source = value.get('source')
        require(isinstance(source, dict) and source, 'missing_source', 'Record the original user instruction and source')
        if value.get('kind') == 'slack':
            require(all(source.get(k) for k in ('channel', 'message_ts', 'message_digest')), 'missing_source', 'Slack authorization requires exact message provenance')
            if source.get('requester_id'):
                require(source['requester_id'] == member['member_id'], 'requester_mismatch', 'Slack author differs from the authenticated requester')
        elif value.get('kind') == 'attended':
            require(member['member_id'] == self._policy().get('attended_operator_id'), 'operator_mismatch', 'Attended authorization must use the configured operator')
            require(source.get('instruction') and source.get('session_id'), 'missing_source', 'Attended requests require instruction text and session ID')
        else:
            raise CaseError('invalid_authorization', 'Only trusted Slack and attended requests are supported')
        return json.loads(canonical(value)), member

    def _account(self, value):
        require(isinstance(value, dict) and all(isinstance(value.get(k), str) and value[k].strip() for k in ('profile_key', 'client_slug', 'marketplace', 'seller_id', 'marketplace_id')), 'invalid_account', 'Exact account profile, client, marketplace, seller ID and marketplace ID are required')
        return dict(value)

    def _account_key(self, value):
        return digest({k: value[k] for k in ('seller_id', 'marketplace_id')})

    def _load(self, db, registry_id):
        row = db.execute('SELECT data FROM cases WHERE id=?', (registry_id,)).fetchone()
        require(row is not None, 'unknown_case', 'Case is absent from the shared registry')
        case = json.loads(row[0])
        return self._load(db, case['superseded_by']) if case.get('superseded_by') else case

    def _save(self, db, case):
        case['updated_at'] = self._now().isoformat()
        db.execute('INSERT INTO cases VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET remote_id=excluded.remote_id,data=excluded.data', (case['registry_id'], self._account_key(case['account']), case['issue_key'], case.get('case_id'), canonical(case)))

    def _source_id(self, authorization):
        source = authorization['source']
        if authorization['kind'] == 'slack':
            return digest(['slack', source['channel'], source['message_ts']])
        return digest(['attended', source['session_id'], source.get('request_id') or source['instruction']])

    def _new(self, account, issue_key, subject):
        require(isinstance(issue_key, str) and issue_key.strip(), 'invalid_issue', 'A stable issue key is required')
        require(isinstance(subject, str) and subject.strip(), 'invalid_subject', 'A case subject is required')
        return {'schema_version': 1, 'registry_id': digest([self._account_key(account), issue_key]), 'account': account, 'issue_key': issue_key, 'subject': subject, 'case_id': None, 'requester_id': None, 'owner': None, 'mandate': None, 'authorization_revision': 1, 'revision': 1, 'created_at': self._now().isoformat(), 'lifecycle': 'pending_creation', 'contact_ids': [], 'last_remote_contact': None, 'last_sent_at': None, 'next_due_at': None, 'unanswered_chasers': 0, 'daily': {}, 'actions': [], 'owner_issue_reported': False}

    def start(self, request):
        authorization, member = self._authorization(request.get('authorization'))
        assigned = request.get('assigned_owner')
        if assigned:
            require(authorization['source'].get('assigned_owner') == assigned, 'unverified_assignment', 'Explicit ownership assignment must be recorded in the verified source')
            assigned_member = self._member(assigned)
        else:
            assigned_member = member
        account = self._account(request.get('account'))
        candidate = self._new(account, request.get('issue_key'), request.get('subject'))
        with self._transaction() as db:
            row = db.execute('SELECT data FROM cases WHERE account_key=? AND issue_key=?', (self._account_key(account), candidate['issue_key'])).fetchone()
            case = self._load(db, json.loads(row[0])['registry_id']) if row else candidate
            require(case['account'] == account, 'account_changed', 'Resolve the existing account identity before continuing this issue')
            source_id = self._source_id(authorization)
            old_source = db.execute('SELECT case_id FROM sources WHERE id=?', (source_id,)).fetchone()
            require(not old_source or old_source[0] == case['registry_id'], 'source_reused', 'One source request cannot authorize a different issue')
            if not row:
                case['requester_id'] = member['member_id']
                case['owner'] = {**assigned_member, 'revision': 1}
                if assigned:
                    case['owner_evidence'] = {'kind': 'team_assignment', 'member_id': assigned, 'source': authorization}
            if not case['owner']:
                report = not case['owner_issue_reported']
                case['owner_issue_reported'] = True
                self._save(db, case)
                return {'status': 'needs_owner', 'case': case, 'report_owner_issue': report}
            require(not case.get('mandate', {}).get('revoked_at') if case.get('mandate') else True, 'mandate_revoked', 'A revoked case requires an explicit new authorization after review')
            if not case['mandate']:
                case['mandate'] = {'id': digest([case['registry_id'], source_id]), 'revision': 1, 'authorization': authorization, 'objective': request.get('objective') or case['subject'], 'permitted_actions': ['create', 'reply', 'chaser'], 'revoked_at': None}
            db.execute('INSERT OR IGNORE INTO sources VALUES (?,?)', (source_id, case['registry_id']))
            self._save(db, case)
            return {'status': 'existing' if row else 'ready', 'case': case}

    def _import_owner(self, request, *, observed_case=None, revision=1):
        if not request.get('owner_member_id'):
            return None
        evidence = request.get('owner_evidence')
        require(isinstance(evidence, dict) and evidence.get('member_id') == request['owner_member_id'] and evidence.get('kind') in {'seller_signature', 'team_assignment'} and evidence.get('source_id') and evidence.get('excerpt'), 'missing_owner_evidence', 'Historical ownership requires a seller signature or explicit team assignment with source evidence')
        member = self._member(request['owner_member_id'])
        if observed_case is not None and evidence['kind'] == 'seller_signature':
            matches = [c for c in observed_case.get('contacts', []) if c.get('id') == evidence['source_id'] and c.get('is_amazon') is False and evidence['excerpt'] in c.get('message', '')]
            require(len(matches) == 1 and member['signature_name'] in evidence['excerpt'], 'owner_evidence_mismatch', 'Original owner must be supported by the observed seller signature')
        return {**member, 'revision': revision}

    def _pending_adoption(self, pending, request):
        require(not pending.get('case_id') and pending.get('lifecycle') == 'pending_creation', 'issue_conflict', 'Only an unsent pending creation may become an existing case')
        for action in pending['actions']:
            directory = self.root / 'operations' / action['operation_id']
            require(not action.get('applied'), 'creation_attempted', 'An applied creation must reconcile before case adoption')
            for filename in ('journal.json', 'adapter-receipt.json'):
                path = directory / filename
                if not path.exists():
                    continue
                try:
                    receipt = json.loads(path.read_text())
                except (OSError, ValueError) as exc:
                    raise CaseError('creation_attempted', 'Creation journal cannot establish that no send occurred') from exc
                if filename == 'adapter-receipt.json':
                    require(receipt.get('attempted') is False, 'creation_attempted', 'A case submission may have occurred; reconcile it before adoption')
                else:
                    no_attempt = receipt.get('effects_started') is False and (receipt.get('adapter_result') or {}).get('attempted') is False
                    require(not receipt.get('verified') and not receipt.get('submission_id') and (not receipt.get('execution_started_at') or no_attempt) and receipt.get('status') not in {'uncertain', 'processing', 'partial'}, 'creation_attempted', 'Creation may have been submitted; reconcile it before adopting another case')
            require(not (directory / 'adapter-input.json').exists() or (directory / 'journal.json').exists(), 'creation_attempted', 'Missing execution journal cannot establish that no send occurred')
        proof = request.get('candidate_evidence')
        require(isinstance(proof, dict) and proof.get('matched_case_id') == request['case_id'] and isinstance(proof.get('match_reason'), str) and proof['match_reason'].strip(), 'missing_candidate_evidence', 'Reusing a found case requires a reviewed issue match and its observed evidence')
        observation = proof.get('observation')
        require(isinstance(observation, dict) and observation.get('account') == pending['account'] and observation.get('history_complete') is True, 'candidate_evidence_mismatch', 'Candidate observation must verify the exact account and complete case history')
        observed_at = timestamp(observation.get('observed_at'))
        require(timestamp(pending['created_at']) <= observed_at <= self._now() + dt.timedelta(minutes=5), 'stale_candidate_evidence', 'Candidate evidence must be collected after the pending request')
        matches = [c for c in observation.get('cases', [observation]) if c.get('case_id') == request['case_id']]
        require(len(matches) == 1 and matches[0].get('history_complete') is True and isinstance(matches[0].get('contacts'), list), 'candidate_evidence_mismatch', 'The matched case must have exactly one complete observed transcript')
        return matches[0]

    def adopt(self, request):
        account = self._account(request.get('account'))
        case = self._new(account, request.get('issue_key'), request.get('subject'))
        require(isinstance(request.get('case_id'), str) and request['case_id'].isdigit(), 'invalid_case_id', 'Amazon case ID must be numeric')
        with self._transaction() as db:
            row = db.execute('SELECT data FROM cases WHERE account_key=? AND issue_key=?', (self._account_key(account), case['issue_key'])).fetchone()
            remote = db.execute('SELECT data FROM cases WHERE account_key=? AND remote_id=?', (self._account_key(account), request['case_id'])).fetchone()
            if row and not json.loads(row[0]).get('case_id') and not json.loads(row[0]).get('superseded_by'):
                pending = json.loads(row[0])
                require(pending['account'] == account, 'account_changed', 'Pending account identity changed before adoption')
                observed_case = self._pending_adoption(pending, request)
                for action in pending['actions']:
                    action['invalidated'] = True
                pending['authorization_revision'] += 1
                pending['revision'] += 1
                owner_revision = (pending.get('owner') or {}).get('revision', 0) + 1
                target = json.loads(remote[0]) if remote else pending
                if remote:
                    require(target['account'] == account, 'account_changed', 'Existing case account identity differs')
                    pending.update(lifecycle='superseded', superseded_by=target['registry_id'])
                    self._save(db, pending)
                    db.execute('UPDATE sources SET case_id=? WHERE case_id=?', (target['registry_id'], pending['registry_id']))
                else:
                    target['owner'] = None  # The requester is not evidence of historical ownership.
                    target.pop('owner_evidence', None)
                if not target.get('owner'):
                    owner = self._import_owner(request, observed_case=observed_case, revision=owner_revision)
                    if owner:
                        target['owner'] = owner
                        target['owner_evidence'] = request['owner_evidence']
                elif request.get('owner_member_id'):
                    require(target['owner']['member_id'] == request['owner_member_id'], 'owner_conflict', 'Existing registered ownership requires explicit reassignment')
                attach_mandate = not target.get('mandate') and target.get('lifecycle') != 'resolved'
                if attach_mandate:
                    target['mandate'] = pending.get('mandate')
                if target.get('mandate') and (not remote or attach_mandate):
                    target['mandate']['permitted_actions'] = ['reply', 'chaser']
                    target['mandate']['revision'] += 1
                target.update(case_id=request['case_id'], lifecycle=target['lifecycle'] if remote else 'adopted', adoption_evidence=request['candidate_evidence'], remote_status=observed_case.get('case_status'), owner_issue_reported=False)
                target['remote_subject'] = observed_case.get('subject')
                seller_times = [timestamp(c['timestamp']) for c in observed_case['contacts'] if c.get('is_amazon') is False and c.get('timestamp')]
                if seller_times:
                    sent_at = max(seller_times).isoformat()
                    if not target.get('last_sent_at') or timestamp(sent_at) > timestamp(target['last_sent_at']):
                        target.update(last_sent_at=sent_at, next_due_at=business_due(sent_at))
                self._save(db, target)
                return {'status': 'adopted', 'case': target, 'send_authorized': bool(target['owner'] and target['mandate'] and not target['mandate'].get('revoked_at') and target['lifecycle'] != 'resolved')}
            if row or remote:
                existing = self._load(db, json.loads((row or remote)[0])['registry_id'])
                require(existing['case_id'] == request['case_id'], 'issue_conflict', 'Issue already belongs to a different case')
                return {'status': 'existing', 'case': existing}
            case.update(case_id=request['case_id'], lifecycle='imported')
            if request.get('owner_member_id'):
                case['owner'] = self._import_owner(request)
                case['owner_evidence'] = request['owner_evidence']
            historical = request.get('historical') or {}
            case['historical'] = historical
            case['contact_ids'] = list(dict.fromkeys(historical.get('contact_ids', [])))
            case['remote_status'] = historical.get('status')
            if historical.get('last_sent_at'):
                case['last_sent_at'] = timestamp(historical['last_sent_at']).isoformat()
                case['next_due_at'] = business_due(case['last_sent_at'])
            self._save(db, case)
            return {'status': 'imported', 'case': case}

    def list(self):
        with self._transaction() as db:
            records = [json.loads(row[0]) for row in db.execute('SELECT data FROM cases ORDER BY id')]
            return {'cases': [case for case in records if not case.get('superseded_by')], 'superseded': [case for case in records if case.get('superseded_by')]}

    def _active(self, case):
        require(case.get('lifecycle') != 'resolved', 'case_resolved', 'Resolved business issues require an explicit new request')
        require(case.get('owner'), 'unknown_owner', 'Assign an evidenced owner before sending')
        member = self._member(case['owner']['member_id'])
        require(all(case['owner'][key] == member[key] for key in member), 'signature_changed', 'Approved signature changed; explicitly refresh case ownership')
        require(case.get('mandate') and not case['mandate'].get('revoked_at'), 'mandate_revoked', 'Case has no active team-request mandate')
        self._authorization(case['mandate']['authorization'])

    def _binding(self, case):
        return {'registry_id': case['registry_id'], 'owner_revision': case['owner']['revision'], 'mandate_id': case['mandate']['id'], 'mandate_revision': case['mandate']['revision'], 'authorization_revision': case['authorization_revision']}

    def _daily(self, case, key):
        current = self._now().astimezone(ZONE)
        require(current.hour >= 9, 'daily_not_due', 'Automated correspondence runs after 09:00 Asia/Bangkok')
        day = current.date().isoformat()
        expected = f'{day}:{case["registry_id"]}'
        require(key == expected and case['daily'].get(day, {}).get('observed_at'), 'daily_not_observed', 'Reply requires the current daily observation')
        return case['daily'][day]

    def _uncertain_action(self, action):
        path = self.root / 'operations' / action['operation_id'] / 'journal.json'
        if not path.exists():
            return False
        try:
            journal = json.loads(path.read_text())
        except (OSError, ValueError):
            return True
        return journal.get('status') in {'uncertain', 'processing', 'partial'} or journal.get('effects_started') is True

    def _scope_assessment(self, value, *, body=None, contact_ids=()):
        """Require an explicit review; text matching cannot establish safe scope."""
        require(isinstance(value, dict), 'missing_scope_assessment', 'Every outgoing case message requires an evidence-backed scope assessment')
        require(value.get('decision') == 'routine' and value.get('category') in ROUTINE_CATEGORIES, 'scope_requires_human', 'Only factual evidence, clarification and status checks belong to the routine case mandate')
        require(isinstance(value.get('reason'), str) and value['reason'].strip(), 'missing_scope_assessment', 'Record why the exact outgoing message is routine')
        evidence = value.get('evidence')
        require(isinstance(evidence, list) and evidence and all(isinstance(item, dict) and item.get('kind') in {'case_contact', 'artifact', 'request'} and isinstance(item.get('source_id'), str) and item['source_id'].strip() for item in evidence), 'missing_scope_evidence', 'Scope assessment requires identified source evidence')
        require(all(item['source_id'] in contact_ids for item in evidence if item['kind'] == 'case_contact'), 'scope_evidence_mismatch', 'Cited case contacts must occur in the message baseline')
        require(isinstance(value.get('body_sha256'), str) and len(value['body_sha256']) == 64, 'scope_body_mismatch', 'Scope assessment must bind the exact unsigned message body')
        if body is not None:
            require(value['body_sha256'] == hashlib.sha256(body.encode()).hexdigest(), 'scope_body_mismatch', 'Scope assessment was written for different outgoing content')
        return json.loads(canonical(value))

    def prepare_send(self, request):
        with self._transaction() as db:
            case = self._load(db, request.get('registry_id'))
            self._active(case)
            purpose = request.get('purpose')
            require(purpose in case['mandate']['permitted_actions'], 'outside_mandate', 'Requested correspondence is outside the case mandate')
            if purpose == 'create':
                require(not case['case_id'], 'already_created', 'Reply in the existing case instead of creating another')
                trigger = 'create'
            else:
                require(case['case_id'], 'case_not_created', 'Case creation has not been confirmed')
                daily = self._daily(case, request.get('daily_key'))
                require(daily.get('next_action') == purpose and not daily.get('sent_operation_id'), 'daily_action_blocked', 'Daily action is absent, already delivered, or requires a human')
                trigger = request['daily_key']
            require(isinstance(request.get('body'), str) and request['body'].strip(), 'missing_body', 'Exact evidence-backed correspondence is required')
            baseline = request.get('baseline')
            require(isinstance(baseline, dict), 'missing_baseline', 'Current case/correspondence baseline is required')
            timestamp(baseline.get('observed_at'))
            scope = self._scope_assessment(request.get('assessment'), body=request['body'], contact_ids=baseline.get('contact_ids', []))
            duplicate_review = request.get('duplicate_review', [])
            if purpose == 'create':
                candidates = baseline.get('case_ids', [])
                require(isinstance(candidates, list) and len(candidates) == len(set(candidates)), 'invalid_baseline', 'Scoped duplicate baseline must contain unique case IDs')
                require(isinstance(duplicate_review, list) and all(isinstance(item, dict) and isinstance(item.get('case_id'), str) and isinstance(item.get('reason'), str) and item['reason'].strip() for item in duplicate_review), 'missing_duplicate_review', 'Every existing candidate needs an explicit reason it is a different issue')
                reviewed = [item['case_id'] for item in duplicate_review]
                require(len(reviewed) == len(set(reviewed)) and set(reviewed) == set(candidates), 'missing_duplicate_review', 'Duplicate review must cover exactly the observed scoped candidate case IDs')
            binding = self._binding(case)
            operation_id = 'case-' + digest([case['registry_id'], trigger, binding])[:48]
            # An unresolved earlier operation must reconcile in its existing journal.
            unresolved = [a for a in case['actions'] if not a.get('applied') and a['operation_id'] != operation_id and (not a.get('invalidated') or self._uncertain_action(a))]
            require(not unresolved, 'reconciliation_required', 'Resolve the previous operation journal before preparing another send')
            signed_body = (request['body'].rstrip() + '\n\n' + case['owner']['signature']).replace('\r\n', '\n').replace('\r', '\n').strip('\n')
            inputs = {'signed_body': signed_body, 'subject': case['subject'], 'attachments': request.get('attachments', []), 'owner': case['owner'], 'mandate': {'id': case['mandate']['id'], 'revision': case['mandate']['revision']}, 'case_binding': binding, 'baseline': baseline, 'issue_key': case['issue_key'], 'scope_assessment': scope, 'duplicate_review': duplicate_review}
            operation = {'schema_version': 1, 'operation_id': operation_id, 'operation': 'case.create' if purpose == 'create' else 'case.reply', 'account': case['account'], 'targets': [{'issue_key': case['issue_key']}] if purpose == 'create' else [{'case_id': case['case_id']}], 'inputs': inputs}
            previous = next((a for a in case['actions'] if a['operation_id'] == operation_id), None)
            require(not previous or previous['request_hash'] == digest(operation), 'immutable_action', 'Pending case content changed; reconcile or explicitly revise it first')
            if not previous:
                case['actions'].append({'operation_id': operation_id, 'request_hash': digest(operation), 'purpose': purpose, 'daily_key': request.get('daily_key'), 'binding': binding, 'signed_body_hash': digest(inputs['signed_body']), 'scope_hash': digest(scope), 'applied': False})
                self._save(db, case)
            return {'status': 'ready', 'operation_request': operation, 'operations_state_dir': str(self.root / 'operations')}

    def validate_binding(self, binding, inputs=None, *, account=None, operation=None, targets=None, operation_id=None, request_hash=None):
        require(isinstance(binding, dict), 'missing_case_binding', 'Case authorization binding is required')
        with self._transaction() as db:
            case = self._load(db, binding.get('registry_id'))
            self._active(case)
            require(binding == self._binding(case), 'stale_case_binding', 'Case ownership or mandate changed after preparation')
            if account is not None:
                require(account == case['account'], 'account_mismatch', 'Operation account differs from the registered case')
            if operation is not None or targets is not None:
                expected = [{'issue_key': case['issue_key']}] if operation == 'case.create' else [{'case_id': case['case_id']}]
                require(operation in {'case.create', 'case.reply'} and targets == expected, 'target_mismatch', 'Operation target differs from the registered case')
            if inputs is not None:
                require(inputs.get('owner') == case['owner'], 'owner_mismatch', 'Message owner differs from the persisted case owner')
                require(inputs.get('mandate') == {'id': case['mandate']['id'], 'revision': case['mandate']['revision']}, 'mandate_mismatch', 'Message mandate differs from the persisted case mandate')
                require(inputs.get('issue_key') == case['issue_key'], 'issue_mismatch', 'Message belongs to a different issue')
                scope = self._scope_assessment(inputs.get('scope_assessment'), contact_ids=(inputs.get('baseline') or {}).get('contact_ids', []))
                refs = [a for a in case['actions'] if a['binding'] == binding and not a.get('invalidated') and a['signed_body_hash'] == digest(inputs.get('signed_body')) and a.get('scope_hash') == digest(scope)]
                if operation_id is not None:
                    refs = [a for a in refs if a['operation_id'] == operation_id and not a.get('applied')]
                if request_hash is not None:
                    refs = [a for a in refs if a['request_hash'] == request_hash]
                require(refs, 'unprepared_message', 'Exact signed message is absent from the case registry')
                ref = refs[-1]
                if ref['purpose'] != 'create':
                    daily = self._daily(case, ref['daily_key'])
                    require(not daily.get('sent_operation_id') or daily['sent_operation_id'] == ref['operation_id'], 'daily_action_blocked', 'Another daily message was delivered')
            return {'status': 'valid', 'case_binding': binding, 'authorization': case['mandate']['authorization']}

    def _admin_replay(self, case, operation, authorization, payload):
        """One authenticated administrative instruction changes revisions once."""
        key = digest([operation, self._source_id(authorization)])
        fingerprint = digest({'authorization': authorization, 'payload': payload})
        previous = case.setdefault('administration', {}).get(key)
        require(not previous or previous['request_hash'] == fingerprint, 'admin_source_changed', 'The administrative request changed; use a new explicit instruction')
        if previous:
            return True
        case['administration'][key] = {'operation': operation, 'request_hash': fingerprint, 'at': self._now().isoformat()}
        return False

    def reassign(self, request):
        authorization, _ = self._authorization(request.get('authorization'))
        member = self._member(request.get('owner_member_id'))
        with self._transaction() as db:
            case = self._load(db, request.get('registry_id'))
            if self._admin_replay(case, 'reassign', authorization, {'owner_member_id': member['member_id']}):
                return {'status': 'already_reassigned', 'case': case}
            case['owner'] = {**member, 'revision': (case.get('owner') or {}).get('revision', 0) + 1}
            case['authorization_revision'] += 1
            case['revision'] += 1
            case['owner_issue_reported'] = False
            case.setdefault('ownership_history', []).append({'at': self._now().isoformat(), 'owner': case['owner'], 'authorization': authorization})
            for action in case['actions']:
                if not action.get('applied'):
                    action['invalidated'] = True
            self._save(db, case)
            return {'status': 'reassigned', 'case': case}

    def revoke(self, request):
        authorization, _ = self._authorization(request.get('authorization'))
        with self._transaction() as db:
            case = self._load(db, request.get('registry_id'))
            if self._admin_replay(case, 'revoke', authorization, {}):
                return {'status': 'already_revoked', 'case': case}
            if case.get('mandate'):
                case['mandate'].update(revoked_at=self._now().isoformat(), revocation=authorization, revision=case['mandate']['revision'] + 1)
            case['authorization_revision'] += 1
            self._save(db, case)
            return {'status': 'revoked', 'case': case}

    def resolve(self, request):
        authorization, _ = self._authorization(request.get('authorization'))
        evidence = request.get('evidence')
        require(isinstance(evidence, dict) and evidence.get('source_id') and evidence.get('summary'), 'missing_resolution_evidence', 'Business resolution requires an evidenced outcome, not Amazon case status alone')
        with self._transaction() as db:
            case = self._load(db, request.get('registry_id'))
            if self._admin_replay(case, 'resolve', authorization, {'evidence': evidence}):
                return {'status': 'already_resolved', 'case': case}
            case['lifecycle'] = 'resolved'
            case['resolution'] = {'authorization': authorization, 'evidence': evidence, 'at': self._now().isoformat()}
            case['authorization_revision'] += 1
            self._save(db, case)
            return {'status': 'resolved', 'case': case}

    def daily_due(self):
        current = self._now().astimezone(ZONE)
        date = current.date().isoformat()
        result = {'date': date, 'run_key': f'cases:{date}', 'timezone': 'Asia/Bangkok', 'cases': []}
        if current.hour < 9:
            return {**result, 'status': 'not_due'}
        with self._transaction() as db:
            for row in db.execute('SELECT data FROM cases ORDER BY id').fetchall():
                case = json.loads(row[0])
                if not case.get('case_id') or case['lifecycle'] == 'resolved':
                    continue
                daily = case['daily'].setdefault(date, {})
                if daily.get('observed_at'):
                    if daily.get('next_action') in {'reply', 'chaser'} and not daily.get('sent_operation_id'):
                        result['cases'].append({'registry_id': case['registry_id'], 'daily_key': f'{date}:{case["registry_id"]}', 'next_action': daily['next_action'], 'case': case})
                    continue
                item = {'registry_id': case['registry_id'], 'daily_key': f'{date}:{case["registry_id"]}', 'next_action': 'observe', 'case': case, 'send_authorized': True}
                if not case['owner'] or not case['mandate'] or case['mandate'].get('revoked_at'):
                    item['send_authorized'] = False
                    item['owner_issue_new'] = not case['owner_issue_reported']
                    case['owner_issue_reported'] = True
                result['cases'].append(item)
                self._save(db, case)
        return {**result, 'status': 'due'}

    def observe(self, request):
        observation = request.get('observation')
        require(isinstance(observation, dict), 'invalid_observation', 'Current observed case state is required')
        observed = timestamp(observation.get('observed_at'))
        current = self._now().astimezone(ZONE)
        require(current.hour >= 9 and observed.astimezone(ZONE).date() == current.date() and observed <= self._now() + dt.timedelta(minutes=5), 'daily_not_due', 'Observation must belong to the current daily check')
        with self._transaction() as db:
            case = self._load(db, request.get('registry_id'))
            date = current.date().isoformat()
            require(request.get('daily_key') == f'{date}:{case["registry_id"]}', 'invalid_daily_key', 'Daily key does not match case and date')
            daily = case['daily'].setdefault(date, {})
            if daily.get('observed_at'):
                return {'status': 'already_observed', 'case': case, 'next_action': daily['next_action'], 'daily_key': request['daily_key']}
            contacts = observation.get('contacts')
            require(observation.get('account') == case['account'] and observation.get('case_id') == case['case_id'], 'observation_mismatch', 'Observed account and Amazon case ID must match the registry')
            require(observation.get('history_complete') is True, 'incomplete_history', 'Daily decisions require the complete visible case history')
            require(isinstance(contacts, list) and all(isinstance(c, dict) and c.get('id') and isinstance(c.get('is_amazon'), bool) for c in contacts), 'invalid_contacts', 'Contacts require stable IDs and an evidenced sender classification')
            seen = set(case['contact_ids'])
            def contact_time(contact):
                return timestamp(contact['timestamp']) if contact.get('timestamp') else observed
            new_amazon = sorted([c for c in contacts if c['is_amazon'] and c['id'] not in seen], key=contact_time)
            seller_contacts = sorted([c for c in contacts if not c['is_amazon'] and c.get('timestamp')], key=contact_time)
            last_known_send = timestamp(case['last_sent_at']) if case['last_sent_at'] else None
            latest_seller = contact_time(seller_contacts[-1]) if seller_contacts else last_known_send
            if latest_seller and (not last_known_send or latest_seller > last_known_send):
                case['last_sent_at'] = latest_seller.isoformat()
                case['next_due_at'] = business_due(case['last_sent_at'])
            actionable_amazon = [c for c in new_amazon if not latest_seller or contact_time(c) > latest_seller]
            case['contact_ids'] = list(dict.fromkeys(case['contact_ids'] + [c['id'] for c in contacts]))
            if new_amazon:
                case['last_remote_contact'] = new_amazon[-1]['id']
                case['last_remote_contact_at'] = new_amazon[-1].get('timestamp') or observed.isoformat()
                if actionable_amazon:
                    case['unanswered_chasers'] = 0
            assessment = observation.get('assessment') or {}
            if isinstance(assessment, str):
                assessment = {'decision': assessment, 'reason': observation.get('reason'), 'evidence_contact_ids': observation.get('evidence_contact_ids', [])}
            require(isinstance(assessment, dict), 'invalid_assessment', 'Assessment must be an evidence-backed decision')
            decision = assessment.get('decision', 'human')
            require(decision in {'routine', 'human', 'wait'}, 'invalid_assessment', 'Assessment must be routine, human, or wait')
            evidence_ids = assessment.get('evidence_contact_ids', [])
            require(isinstance(evidence_ids, list) and set(evidence_ids) <= {c['id'] for c in contacts}, 'invalid_assessment', 'Assessment evidence must reference observed case contacts')
            if decision == 'routine':
                require(assessment.get('reason'), 'invalid_assessment', 'Routine correspondence requires an explicit scope assessment')
                if actionable_amazon:
                    require(set(evidence_ids) & {c['id'] for c in actionable_amazon}, 'invalid_assessment', 'Routine reply assessment must cite the new Amazon message')
            if observation.get('promised_deadline'):
                require(set(evidence_ids) & {c['id'] for c in contacts if c['is_amazon']}, 'unproven_deadline', 'Amazon promised deadline requires cited Amazon correspondence')
                case['next_due_at'] = timestamp(observation['promised_deadline']).isoformat()
            remote_status = observation.get('case_status') or observation.get('status')
            case['remote_status'] = remote_status
            case['last_observation'] = observation
            if str(remote_status or '').lower() in {'resolved', 'closed', 'completed'}:
                case['lifecycle'] = 'awaiting_resolution_review'
                action = 'human'
            elif not case['owner'] or not case['mandate'] or case['mandate'].get('revoked_at'):
                action = 'human'
            elif observation.get('can_edit') is False:
                action = 'human'
            elif decision == 'human':
                action = 'human'
            elif decision == 'wait':
                action = 'wait'
            elif actionable_amazon:
                action = 'reply'
            elif case['next_due_at'] and timestamp(case['next_due_at']) <= self._now():
                action = 'human' if case['unanswered_chasers'] >= 2 else 'chaser'
            else:
                action = 'wait'
            daily.update(observed_at=observed.isoformat(), next_action=action)
            self._save(db, case)
            return {'status': 'observed', 'case': case, 'next_action': action, 'daily_key': request['daily_key']}

    def record_receipt(self, request):
        operation_id = request.get('operation_id')
        require(isinstance(operation_id, str) and operation_id.startswith('case-') and '/' not in operation_id and '..' not in operation_id, 'invalid_operation_id', 'Expected a canonical case operation ID')
        expected = (self.root / 'operations' / operation_id / 'journal.json').resolve()
        require(expected.is_relative_to(self.root / 'operations') and Path(request.get('receipt_path') or expected).resolve() == expected, 'invalid_receipt', 'Receipt must be the existing operations journal')
        try:
            receipt = json.loads(expected.read_text())
        except (OSError, ValueError) as exc:
            raise CaseError('receipt_unavailable', 'Existing operations journal is unavailable') from exc
        with self._transaction() as db:
            case = self._load(db, request.get('registry_id'))
            action = next((a for a in case['actions'] if a['operation_id'] == operation_id), None)
            require(action and receipt.get('operation_id') == operation_id and receipt.get('account') == case['account'], 'receipt_mismatch', 'Operations journal does not match this case action')
            if action.get('applied'):
                return {'status': 'already_recorded', 'case': case}
            if receipt.get('status') != 'verified' or receipt.get('verified') is not True:
                return {'status': 'reconciliation_required', 'operation_id': operation_id, 'case': case}
            remote_id = receipt.get('case_id') or (receipt.get('result') or {}).get('case_id')
            if action['purpose'] == 'create':
                require(isinstance(remote_id, str) and remote_id.isdigit(), 'missing_case_id', 'Confirmed creation requires the verified Amazon case ID')
                require(not case['case_id'] or case['case_id'] == remote_id, 'case_mismatch', 'Verified creation differs from the registered Amazon case')
                case['case_id'] = remote_id
            elif remote_id:
                require(remote_id == case['case_id'], 'case_mismatch', 'Reply receipt belongs to a different Amazon case')
            sent_at = receipt.get('sent_at') or receipt.get('verified_at') or receipt.get('updated_at')
            timestamp(sent_at)
            action.update(applied=True, receipt_path=str(expected))
            promised = (case.get('last_observation') or {}).get('promised_deadline')
            due = promised if promised and timestamp(promised) > timestamp(sent_at) else business_due(sent_at)
            case.update(last_sent_at=sent_at, next_due_at=due, lifecycle='awaiting_amazon')
            if action['purpose'] == 'chaser' and (not case.get('last_remote_contact_at') or timestamp(case['last_remote_contact_at']) < timestamp(sent_at)):
                case['unanswered_chasers'] += 1
            if action.get('daily_key'):
                day = action['daily_key'].split(':', 1)[0]
                case['daily'][day]['sent_operation_id'] = operation_id
            self._save(db, case)
            return {'status': 'recorded', 'case': case}


def validate_send_binding(binding, inputs=None, *, state_dir=None, config_path=None, account=None, operation=None, targets=None, operation_id=None, request_hash=None):
    return CaseService(state_dir, config_path).validate_binding(binding, inputs, account=account, operation=operation, targets=targets, operation_id=operation_id, request_hash=request_hash)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['start', 'adopt', 'prepare-send', 'validate-binding', 'record-receipt', 'observe', 'reassign', 'revoke', 'resolve', 'list', 'daily-due'])
    parser.add_argument('--request')
    parser.add_argument('--state-dir')
    parser.add_argument('--config')
    args = parser.parse_args(argv)
    try:
        service = CaseService(args.state_dir, args.config)
        request = json.loads(Path(args.request).read_text()) if args.request else {}
        if args.command == 'validate-binding':
            result = service.validate_binding(request.get('binding'), request.get('inputs'), account=request.get('account'), operation=request.get('operation'), targets=request.get('targets'), operation_id=request.get('operation_id'), request_hash=request.get('request_hash'))
        else:
            method = getattr(service, args.command.replace('-', '_'))
            result = method() if args.command in {'list', 'daily-due'} else method(request)
        print(canonical(result))
        return 0
    except (CaseError, OSError, ValueError, sqlite3.Error) as exc:
        print(canonical({'status': 'blocked', 'reason': getattr(exc, 'code', 'invalid_request'), 'message': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
