#!/bin/sh
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=${AMAZON_AGENT_REPO:-$(CDPATH= cd -- "$source_dir/../../.." && pwd)}
export AMAZON_AGENT_REPO="$repo"
# Generate desktop quoting and keep retirement receipts without shell interpolation.
python3 - "$source_dir" "$@" <<'PY'
import argparse
import datetime
import os
from pathlib import Path
import shutil
import shlex
import sys

source = Path(sys.argv[1])
parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
dry_run = parser.parse_args(sys.argv[2:]).dry_run
repo = Path(os.environ['AMAZON_AGENT_REPO']).resolve()
if not (repo / 'tools/browserctl/browserctl.mjs').is_file():
    sys.exit(f'No browserctl in {repo}')
home = Path.home()
autostart = home / '.config/autostart'
bin_dir = home / '.local/bin'
retired = home / '.amazon-agent' / ('retired-autostart-' + datetime.date.today().isoformat())

def retire(path):
    if not path.exists() and not path.is_symlink():
        return
    destination = retired / path.relative_to(home)
    if dry_run:
        print(f'Would retire {path} -> {destination}')
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = 0
    while destination.exists() or destination.is_symlink():
        suffix += 1
        destination = destination.with_name(path.name + f'.{suffix}')
    shutil.move(str(path), str(destination))
    print(f'Retired {path} -> {destination}')

managed = {'amazon-operator-9222.desktop', 'wizards-ai-9223.desktop'}
retired_names = {'chrome-amazon-operator.desktop', 'chrome-wizards-readonly.desktop'}
retired_wrappers = {str(bin_dir / name) for name in ('chrome-amazon-operator', 'chrome-wizards-readonly')}

def uses_retired_wrapper(text):
    for line in text.splitlines():
        if line.startswith('Exec='):
            try:
                command = shlex.split(line[5:])
            except ValueError:
                continue
            if command and command[0] in retired_wrappers:
                return True
    return False

# Retire duplicate browser startup entries, including older managed names.
for path in sorted(autostart.glob('*.desktop')):
    text = path.read_text()
    if path.name not in managed and (path.name in retired_names or uses_retired_wrapper(text)):
        retire(path)
for name in sorted(retired_names):
    path = home / '.local/share/applications' / name
    if path.is_file() and uses_retired_wrapper(path.read_text()):
        retire(path)
for name in ('chrome-amazon-operator', 'chrome-wizards-readonly'):
    retire(bin_dir / name)

def install(path, content, mode):
    if path.is_file() and not path.is_symlink() and path.read_text() == content:
        if not dry_run:
            path.chmod(mode)
        print(f'Unchanged {path}')
        return
    retire(path)
    if dry_run:
        print(f'Would install {path}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(mode)
    print(f'Installed {path}')

def desktop_quote(value):
    # Exec quoting has both desktop-string and command-line escaping layers.
    value = str(value).replace('%', '%%')
    value = ''.join('\\' + c if c in '\\"`$' else c for c in value)
    return '"' + value.replace('\\', '\\\\') + '"'

for wrapper, desktop in (('operator-9222', 'amazon-operator-9222.desktop'),
                         ('grimoire-9223', 'wizards-ai-9223.desktop')):
    target = bin_dir / wrapper
    install(target, (source / wrapper).read_text(), 0o755)
    command = 'env ' + desktop_quote('AMAZON_AGENT_REPO=' + str(repo)) + ' ' + desktop_quote(target)
    install(autostart / desktop, (source / desktop).read_text().replace('@EXEC@', command), 0o644)
print('Managed application-menu launchers and systemd units were not changed.')
PY
