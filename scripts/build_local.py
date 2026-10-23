#!/usr/bin/env python3
"""Offline Android build with installed SDK/JDK. No Gradle downloads or TV access.
Use an external keystore/password environment for an upgrade-compatible release.
"""
import argparse, os, shutil, subprocess, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk', type=Path, default=Path(os.environ.get('ANDROID_HOME', str(Path.home() / 'Library/Android/sdk'))))
    p.add_argument('--java-home', type=Path, default=Path(os.environ.get('JAVA_HOME', '/usr/lib/jvm/default-java')))
    p.add_argument('--variant', choices=['tcl','standard'], required=True)
    p.add_argument('--keystore', type=Path, required=True)
    p.add_argument('--alias', default='guizang-tv')
    p.add_argument('--password-env', default='GUIZANG_STORE_PASSWORD')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if not os.environ.get(a.password_env): p.error('Signing password must be supplied in the named environment variable')
    sdk = a.sdk; tools = sdk / 'build-tools' / sorted([d.name for d in (sdk/'build-tools').iterdir()], key=lambda x:tuple(int(n) for n in x.split('.')))[-1]
    android = sdk / 'platforms' / sorted([d.name for d in (sdk/'platforms').iterdir()], key=lambda x:int(x.split('-')[-1]))[-1] / 'android.jar'
    build = ROOT / 'app/build/local' / a.variant
    if build.exists(): shutil.rmtree(build)
    for name in ('gen','classes','dex'): (build/name).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, JAVA_HOME=str(a.java_home)); env['PATH'] = str(a.java_home/'bin') + os.pathsep + env['PATH']
    def run(cmd): subprocess.run([str(x) for x in cmd], check=True, env=env, timeout=120)
    ns = '{http://schemas.android.com/apk/res/android}'; ET.register_namespace('android',ns[1:-1])
    tree=ET.parse(ROOT/'app/src/main/AndroidManifest.xml'); tree.getroot().set('package','io.github.op7418.guizangtv')
    if a.variant=='tcl': tree.getroot().find('application').set(ns+'label','归藏电视 TCL版')
    if a.variant=='standard':
        activity = next(x for x in tree.getroot().find('application').findall('activity') if x.get(ns+'name')=='.FrameHomeActivity')
        filt=ET.SubElement(activity,'intent-filter'); ET.SubElement(filt,'action',{ns+'name':'android.intent.action.MAIN'})
        for value in ('android.intent.category.HOME','android.intent.category.DEFAULT'): ET.SubElement(filt,'category',{ns+'name':value})
    tree.write(build/'AndroidManifest.xml',encoding='unicode')
    run([tools/'aapt2','compile','--dir',ROOT/'app/src/main/res','-o',build/'resources.zip'])
    run([tools/'aapt2','link','-o',build/'base.apk','--manifest',build/'AndroidManifest.xml','-I',android,
        '--min-sdk-version','26','--target-sdk-version','34','--version-code','10','--version-name','0.4.0-'+a.variant,
        '--java',build/'gen','-A',ROOT/'app/src/main/assets',build/'resources.zip'])
    run([a.java_home/'bin/javac','-encoding','UTF-8','-source','17','-target','17','-classpath',android,'-d',build/'classes',
        *list((ROOT/'app/src/main/java').rglob('*.java')),*list((build/'gen').rglob('*.java'))])
    run([tools/'d8','--release','--min-api','26','--lib',android,'--output',build/'dex',*list((build/'classes').rglob('*.class'))])
    with zipfile.ZipFile(build/'base.apk','a') as z:
        for dex in (build/'dex').glob('*.dex'): z.write(dex,dex.name)
    run([tools/'zipalign','-f','4',build/'base.apk',build/'aligned.apk'])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    run([tools/'apksigner','sign','--ks',a.keystore,'--ks-key-alias',a.alias,'--ks-pass','env:'+a.password_env,'--key-pass','env:'+a.password_env,'--out',a.output,build/'aligned.apk'])
    run([tools/'apksigner','verify','--verbose',a.output])
    print('BUILT',a.variant,a.output)

if __name__=='__main__': main()
