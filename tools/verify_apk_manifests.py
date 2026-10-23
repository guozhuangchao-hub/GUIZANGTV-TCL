#!/usr/bin/env python3
"""Check final APK manifest capabilities and signing identity with an existing SDK."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-tools',type=Path,required=True);a=p.parse_args();out=[]
    for variant in ('tcl','standard'):
        apk=ROOT/'packages'/('guizang-tv-'+variant+'-0.4.0.apk')
        tree=subprocess.check_output([str(a.build_tools/'aapt2'),'dump','xmltree',str(apk),'--file','AndroidManifest.xml'],text=True)
        # queries/intent categories only control package visibility, not launcher declarations.
        application=tree.split('E: application',1)[1]
        home='android.intent.category.HOME' in application
        if home!=(variant=='standard'):raise SystemExit('Wrong HOME declaration: '+variant)
        if 'android.permission.INTERNET' in tree:raise SystemExit('Launcher unexpectedly gained network permission')
        cert=subprocess.check_output([str(a.build_tools/'apksigner'),'verify','--print-certs',str(apk)],text=True)
        digest=re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)',cert).group(1)
        out.append({'variant':variant,'declares_home':home,'certificate_sha256':digest,'internet_permission':False})
    if out[0]['certificate_sha256']!=out[1]['certificate_sha256']:raise SystemExit('Variant signatures differ')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
