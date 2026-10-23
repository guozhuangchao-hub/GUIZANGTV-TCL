#!/usr/bin/env python3
"""GuiZang TV installer. Python 3.9+, official adb. No device selected implicitly.
Doctor/plan are read-only. Mutations require --apply; guard grants require --guard.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time

from tcast_push import push

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'io.github.op7418.guizangtv'
GUARD = PACKAGE + '/' + PACKAGE + '.TclHomeGuard'
LISTENER = PACKAGE + '/' + PACKAGE + '.TclHomeGuard$Revival'
CONFIG = PACKAGE + '/.InstallConfigReceiver'


def shell_text(args):
    # adb shell reparses arguments: preserve nested class '$' and all user values.
    return ' '.join(shlex.quote(str(a)) for a in args)


class Device:
    def __init__(self, adb, serial):
        if not serial or serial.startswith('-'):
            raise ValueError('Invalid adb target')
        self.adb, self.serial = adb, serial

    def run(self, *args, timeout=30):
        r = subprocess.run([self.adb, '-s', self.serial, *args], capture_output=True,
                           text=True, errors='replace', timeout=timeout)
        if r.returncode:
            raise RuntimeError(f'adb failed ({r.returncode}): {r.stderr.strip() or r.stdout.strip()}')
        return r.stdout.strip()

    def shell(self, *args):
        return self.run('shell', shell_text(args))


def inspect(device):
    state = device.run('get-state')
    if state != 'device':
        raise RuntimeError('TV is not authorized; accept the ADB prompt on that TV')
    facts = {key: device.shell('getprop', prop) for key, prop in {
        'manufacturer': 'ro.product.manufacturer', 'brand': 'ro.product.brand',
        'model': 'ro.product.model', 'sdk': 'ro.build.version.sdk',
        'firmware': 'ro.build.display.id', 'abis': 'ro.product.cpu.abilist'}.items()}
    if not facts['sdk'].isdigit() or int(facts['sdk']) < 26:
        raise RuntimeError('GuiZang requires Android 8 / API 26 or newer')
    facts['current_home'] = device.shell('cmd', 'package', 'resolve-activity', '--brief',
                                        '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME')
    return facts


def is_tcl(facts):
    return facts['model'].startswith('tcl_') or any(
        facts.get(k, '').casefold() in {'tcl', 'ffalcon'} for k in ('brand', 'manufacturer'))


def choose_artifacts(facts, catalog, media=False, variant="auto"):
    keys = ['launcher-tcl' if is_tcl(facts) else 'launcher-standard']
    if variant != 'auto':
        keys = ['launcher-' + variant]
    if media:
        abis = facts['abis'].split(',')
        # Both bundled media APKs contain v7a. arm64-only TVs cannot run these APKs.
        if 'armeabi-v7a' not in abis:
            raise RuntimeError('Bundled media APKs require armeabi-v7a; get a matching build for this TV')
        keys += ['xinmiao', 'tvbox']
    return [(key, catalog['artifacts'][key]) for key in keys]


def verify_artifact(item, root=ROOT):
    original = root / item['file']
    if original.is_symlink():
        raise ValueError('Artifact must not be a symlink')
    path = original.resolve(strict=True)
    if root.resolve() not in path.parents:
        raise ValueError('Artifact path escaped repository')
    if path.is_symlink():
        raise ValueError('Artifact must be a local regular file')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != item['sha256']:
        raise ValueError(f'APK SHA256 mismatch: {path.name}')
    return path


def make_plan(facts, selected, guard=False):
    return {'facts': facts, 'transport': 'tcast' if is_tcl(facts) else 'adb',
            'artifacts': [{'id': k, 'file': a['file'], 'package': a['package'], 'sha256': a['sha256']}
                          for k, a in selected],
            'guard': guard, 'default_home_changed': False,
            'note': 'APK installation only; no reboot, root, system-package disable, verifier changes or data deletion.'}


def write_private(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def snapshot(device, facts):
    try:
        appops = device.shell('appops', 'get', PACKAGE)
    except RuntimeError:
        appops = 'NOT_INSTALLED'
    try:
        details = device.shell('dumpsys', 'package', PACKAGE)
    except RuntimeError:
        details = ''
    return {'facts': facts, 'serial': device.serial,
            'secure_settings_was_granted': bool(re.search(r'android\.permission\.WRITE_SECURE_SETTINGS: granted=true', details)),
            'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'secure': {key: device.shell('settings', 'get', 'secure', key) for key in
                       ('enabled_accessibility_services', 'accessibility_enabled', 'enabled_notification_listeners')},
            'startup_target': device.shell('settings', 'get', 'system', 'start_3rd_app'),
            'appops': appops,
            'guard_was_enabled': GUARD in device.shell('settings', 'get', 'secure', 'enabled_accessibility_services'),
            'listener_was_enabled': LISTENER in device.shell('settings', 'get', 'secure', 'enabled_notification_listeners')}


def configure_guard(device):
    commands = [('pm', 'grant', PACKAGE, 'android.permission.WRITE_SECURE_SETTINGS'),
                ('cmd', 'notification', 'allow_listener', LISTENER),
                ('appops', 'set', PACKAGE, 'SYSTEM_ALERT_WINDOW', 'allow')]
    for args in commands:
        output = device.shell(*args)
        if re.search(r'(?i)exception|error:|denied|not allowed', output):
            raise RuntimeError('Guard grant failed: ' + output)
    results = []
    for op in ('APP_AUTO_START', 'APP_ASSOC_START'):
        try:
            output = device.shell('appops', 'set', PACKAGE, op, 'allow')
            results.append({'op': op, 'output': output})
        except RuntimeError as error:
            results.append({'op': op, 'unsupported': str(error)})  # TCL-specific ops are absent elsewhere.
    try:
        device.shell('appops', 'write-settings')
    except RuntimeError:
        pass
    return results


def broadcast(device, *extras):
    result = device.shell('am', 'broadcast', '-a', PACKAGE + '.CONFIG', '-n', CONFIG, *extras)
    if 'result=1' in result or not re.search(r'enabled=(true|false) guard_mode=(true|false)', result):
        raise RuntimeError('GuiZang configuration was not saved')
    return result


def apply_install(device, facts, selected, guard, backup_path, tv_ip=None):
    # Verify every package before making any device mutation.
    payloads = [(key, item, verify_artifact(item)) for key, item in selected]
    for _, item, _ in payloads:
        if item['min_sdk'] > int(facts['sdk']):
            raise RuntimeError('APK requires newer Android: ' + item['label'])
    write_private(backup_path, snapshot(device, facts))
    results = []
    for key, item, apk in payloads:
        if is_tcl(facts):
            if not tv_ip:
                raise ValueError('--tv-ip is required for TCL T-Cast push')
            push(tv_ip, apk, item['package'], item['label'], item['version_code'])
        else:
            output = device.run('install', '-r', str(apk), timeout=180)
            if 'Success' not in output:
                raise RuntimeError('ADB install did not succeed: ' + output)
        installed = device.shell('pm', 'path', item['package'])
        if not installed.startswith('package:'):
            raise RuntimeError('TV did not register the installed package: ' + item['package'])
        details = device.shell('dumpsys', 'package', item['package'])
        if not re.search(r'versionCode=' + str(item['version_code']) + r'\b', details):
            raise RuntimeError('Installed version does not match the selected APK: ' + item['package'])
        results.append({'id': key, 'installed': True, 'package': item['package']})
    # Open once via explicit activity, avoiding Xiaomi's CATEGORY_INFO boot gate.
    device.shell('am', 'start', '-n', PACKAGE + '/.FrameHomeActivity')
    if guard:
        grants = configure_guard(device)
        results.append({'guard_grants': grants})
        results.append({'configuration': broadcast(device, '--ez', 'guard', 'true', '--ez', 'enabled', 'true')})
    if any(key == 'tvbox' for key, _ in selected):
        results.append({'media_pin': broadcast(device, '--ez', 'pin_media', 'true')})
    return {'installed': results, 'backup': str(backup_path),
            'validation': 'Packages/version registered; remote control, playback, boot and wake still need observation.'}


def restore(device, path):
    data = json.loads(Path(path).read_text())
    if data['serial'] != device.serial:
        raise ValueError('Backup is for a different adb target')
    if data['guard_was_enabled']:
        raise RuntimeError('Guard existed before install; restore its previous preferences manually without overwriting them')
    # Do not overwrite the entire accessibility list: other services may have changed since install.
    broadcast(device, '--ez', 'enabled', 'false', '--ez', 'guard', 'false')
    key = 'enabled_accessibility_services'
    current = device.shell('settings', 'get', 'secure', key)
    entries = [x for x in current.split(':') if x and x != 'null' and x != GUARD]
    device.shell('settings', 'put', 'secure', key, ':'.join(entries))
    if not data['listener_was_enabled']:
        device.shell('cmd', 'notification', 'disallow_listener', LISTENER)
    for op in ('SYSTEM_ALERT_WINDOW', 'APP_AUTO_START', 'APP_ASSOC_START'):
        match = re.search(r'^' + op + r':\s*(\w+)', data['appops'], re.MULTILINE)
        try:
            device.shell('appops', 'set', PACKAGE, op, match.group(1) if match else 'default')
        except RuntimeError:
            pass
    if not data.get('secure_settings_was_granted', True):
        device.shell('pm', 'revoke', PACKAGE, 'android.permission.WRITE_SECURE_SETTINGS')
    return {'restored': 'Disabled new guard, removed only own service/listener additions, restored saved appops.',
            'preserved': 'Apps, data, stock Home and other accessibility services. No uninstall or reboot.',
            'note': 'Previously granted secure-settings permission is retained; a grant added by this installer is revoked.'}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['doctor', 'install', 'restore'])
    p.add_argument('--serial', required=True, help='Exact adb serial / IP:port from adb devices')
    p.add_argument('--adb', default=shutil.which('adb') or 'adb')
    p.add_argument('--variant', choices=['auto','tcl','standard'], default='auto', help='Override package variant after checking firmware capabilities')
    p.add_argument('--tv-ip', help='Private TV IPv4 for T-Cast; do not use computer IP')
    p.add_argument('--with-media', action='store_true', help='Install and pin both bundled media APKs')
    p.add_argument('--guard', action='store_true', help='Explicit opt-in to persistent guard grants and Home key handling')
    p.add_argument('--apply', action='store_true', help='Without this flag, only inspect and print the plan')
    p.add_argument('--backup', type=Path, help='Private JSON outside repo; new file on install, existing on restore')
    a = p.parse_args(argv)
    if not a.serial or a.serial.startswith('-'):
        p.error('Invalid adb target')
    device = Device(a.adb, a.serial)
    facts = inspect(device)
    if a.action == 'doctor':
        result = facts
    elif a.action == 'restore':
        if not a.backup:
            p.error('restore requires --backup')
        result = restore(device, a.backup) if a.apply else {'plan': 'Restore own additions only', 'backup': str(a.backup)}
    else:
        catalog = json.loads((ROOT / 'packages/catalog.json').read_text())
        selected = choose_artifacts(facts, catalog, a.with_media, a.variant)
        result = make_plan(facts, selected, a.guard)
        for _, item in selected:
            verify_artifact(item)
        if a.apply:
            if not a.backup or ROOT in a.backup.expanduser().resolve().parents:
                p.error('--apply install requires --backup outside the repository')
            if is_tcl(facts) and not a.tv_ip:
                p.error('TCL installation requires --tv-ip')
            result = apply_install(device, facts, selected, a.guard, a.backup, a.tv_ip)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as e:
        print(f'Installation stopped: {e}', file=sys.stderr)
        sys.exit(1)
