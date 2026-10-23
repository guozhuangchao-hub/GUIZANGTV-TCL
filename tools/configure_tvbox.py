#!/usr/bin/env python3
"""Configure bundled TVBox through its visible settings and official LAN input API.
No external backend, APK patching or private app-data writes. Existing source replacement is opt-in.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from tv_setup import Device, ROOT, write_private

TVBOX = 'com.github.tvbox.osc.jun'
DEST = '/sdcard/Download/GuiZangTV/tvbox'
URL = 'clan://localhost/Download/GuiZangTV/tvbox/tvbox.json'


def ui(device):
    path = '/sdcard/guizang-installer-ui.xml'
    device.shell('uiautomator', 'dump', path)
    raw = device.shell('cat', path)
    return ET.fromstring(raw)


def node(root, text=None, resource=None):
    matches = [n for n in root.iter('node') if n.get('package') == TVBOX
               and (n.get('text') == text if text is not None else n.get('resource-id') == resource)]
    if len(matches) != 1:
        raise RuntimeError('Expected one visible TVBox control; use the TV remote to open 设置 → 配置地址')
    return matches[0]


def tap(device, n):
    values = list(map(int, re.findall(r'\d+', n.get('bounds', ''))))
    if len(values) != 4 or values[2] <= values[0] or values[3] <= values[1]:
        raise RuntimeError('Control has no visible bounds')
    device.shell('input', 'tap', str((values[0]+values[2])//2), str((values[1]+values[3])//2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial', required=True); p.add_argument('--adb', default=shutil.which('adb') or 'adb')
    p.add_argument('--apply', action='store_true'); p.add_argument('--replace-source', action='store_true')
    p.add_argument('--backup', type=Path)
    a = p.parse_args()
    catalog = json.loads((ROOT/'packages/catalog.json').read_text())
    resources = catalog['tvbox_config']['files']
    for item in resources:
        path = ROOT/item['file']
        if path.is_symlink() or ROOT not in path.resolve().parents:
            raise ValueError('Configuration escaped repository')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Configuration hash mismatch: '+path.name)
    if not a.apply:
        print(json.dumps({'action':'copy verified local config/plugins, open TVBox settings, input via forwarded LAN API',
                          'source':URL,'replace_existing_source':a.replace_source,
                          'sites':catalog['tvbox_config']['sites'],'playback_status':'Not all third-party sites/channels are usable'},ensure_ascii=False,indent=2))
        return
    if not a.backup or ROOT in a.backup.expanduser().resolve().parents:
        p.error('--apply requires a new private --backup outside the repository')
    d = Device(a.adb, a.serial)
    d.shell('am','start','-n',TVBOX+'/com.github.tvbox.osc.ui.activity.HomeActivity')
    root = ui(d)
    if not any(n.get('resource-id') == TVBOX+':id/input' for n in root.iter('node')):
        if any(n.get('text') == '设置' for n in root.iter('node')):
            tap(d,node(root,text='设置')); root=ui(d)
        tap(d,node(root,text='配置地址')); root=ui(d)
    old = node(root,resource=TVBOX+':id/input').get('text','')
    old_live = node(root,resource=TVBOX+':id/inputLive').get('text','')
    existing = [s for s in [old,old_live] if s and s not in ['请输入配置地址','请输入直播地址',URL]]
    if existing and not a.replace_source:
        raise RuntimeError('Existing source retained. Explicit --replace-source is needed to replace it')
    write_private(a.backup,{'serial':a.serial,'package':TVBOX,'old_source':old,'old_live_source':old_live,'new_source':URL})
    d.shell('pm','grant',TVBOX,'android.permission.READ_EXTERNAL_STORAGE')
    d.shell('mkdir','-p',DEST)
    d.run('push',str(ROOT/'packages/tvbox-config/tvbox.json'),DEST+'/tvbox.json',timeout=60)
    d.run('push',str(ROOT/'packages/tvbox-config/lib'),DEST+'/lib',timeout=60)
    port = d.run('forward','tcp:0','tcp:9978')
    if not port.isdigit():
        raise RuntimeError('ADB did not return a local forwarding port')
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        payload = urllib.parse.urlencode({'do':'api','url':URL}).encode()
        with op.open('http://127.0.0.1:'+port+'/action',payload,timeout=10) as r:
            if r.status != 200 or r.read().strip() != b'ok':
                raise RuntimeError('TVBox configuration input API failed')
        root=ui(d)
        if node(root,resource=TVBOX+':id/input').get('text') != URL:
            raise RuntimeError('TVBox did not display the expected source URL; settings not confirmed')
        tap(d,node(root,resource=TVBOX+':id/inputConfirm'))
        print('Local config saved. Verify home/categories and actual playback; no computer backend is needed.')
    finally:
        d.run('forward','--remove','tcp:'+port)


if __name__ == '__main__':
    try:
        main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError,ET.ParseError) as e:
        raise SystemExit('Configuration stopped: '+str(e))
