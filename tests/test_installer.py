import hashlib
import http.client
import http.server
import json
from pathlib import Path
import struct
import socket
import urllib.request
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import tv_setup as setup
import tcast_push
import configure_tvbox


class FakeDevice:
    serial = 'FAKE-TV:5555'
    def __init__(self): self.calls=[]
    def shell(self,*args):
        self.calls.append(args)
        if args[:3] == ('pm','path','io.github.op7418.guizangtv'): return 'package:/data/app/base.apk'
        if args[:2] == ('dumpsys','package'): return 'versionCode=10'
        if args[:4] == ('settings','get','secure','enabled_accessibility_services'):
            return 'assistant/.Voice:'+setup.GUARD+':new.app/.Service'
        if args[:2] == ('am','broadcast'): return 'Broadcast completed: result=0, data=enabled=false guard_mode=false'
        return ''
    def run(self,*args,**kw): self.calls.append(args); return 'Success'


class InstallerTest(unittest.TestCase):
    def test_explicit_serial_and_no_host_shell(self):
        with patch.object(setup.subprocess,'run') as run:
            run.return_value.returncode=0;run.return_value.stdout='ok'
            setup.Device('/adb','TV-A:5555').shell('cmd','notification','allow_listener',setup.LISTENER)
        argv=run.call_args.args[0]
        self.assertEqual(argv[:4],['/adb','-s','TV-A:5555','shell'])
        self.assertIn("'"+setup.LISTENER+"'",argv[4])
        self.assertNotIn('shell',run.call_args.kwargs)

    def test_plan_routes_tcl_and_unknown_brand_without_guessing(self):
        catalog={'artifacts':{k:{'file':k,'package':k,'sha256':'test'} for k in ['launcher-tcl','launcher-standard','xinmiao','tvbox']}}
        tcl={'model':'tcl_mt5879_cn','brand':'TCL','manufacturer':'TCL','abis':'armeabi-v7a'}
        sony={'model':'TV','brand':'Sony','manufacturer':'Sony','abis':'arm64-v8a,armeabi-v7a'}
        self.assertEqual(setup.choose_artifacts(tcl,catalog,True)[0][0],'launcher-tcl')
        plan=setup.make_plan(sony,setup.choose_artifacts(sony,catalog),False)
        self.assertEqual(plan['transport'],'adb');self.assertFalse(plan['default_home_changed'])
        self.assertFalse(plan['guard'])

    def test_arm64_only_media_is_not_mistaken_for_v7a(self):
        with self.assertRaisesRegex(RuntimeError,'armeabi-v7a'):
            setup.choose_artifacts({'model':'TV','brand':'Other','manufacturer':'Other','abis':'arm64-v8a'},
                                   {'artifacts':{'launcher-standard':{}}},True)

    def test_tampered_payload_stops_before_device_mutation(self):
        fake=FakeDevice()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'app.apk').write_bytes(b'bad')
            with patch.object(setup,'ROOT',p),patch.object(setup,'verify_artifact',side_effect=ValueError('hash mismatch')):
                with self.assertRaises(ValueError):
                    setup.apply_install(fake,{},[('launcher-tcl',{})],True,p/'backup')
            self.assertEqual(fake.calls,[])

    def test_no_home_variant_can_be_selected_for_other_restricted_firmware(self):
        catalog={'artifacts':{'launcher-standard':{'file':'s'},'launcher-tcl':{'file':'t'}}}
        unknown={'model':'TV','brand':'Other','manufacturer':'Other','abis':'armeabi-v7a'}
        self.assertEqual(setup.choose_artifacts(unknown,catalog,variant='tcl')[0][0],'launcher-tcl')

    def test_configuration_requires_receiver_acknowledgement(self):
        fake=FakeDevice()
        with patch.object(fake,'shell',return_value='Broadcast completed: result=0'):
            with self.assertRaises(RuntimeError):setup.broadcast(fake,'--ez','enabled','true')

    def test_payload_path_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'repo';root.mkdir();outside=Path(d)/'secret';outside.write_bytes(b'x')
            (root/'alias.apk').symlink_to(outside)
            for f in ['../secret','alias.apk']:
                with self.assertRaises(ValueError):setup.verify_artifact({'file':f,'sha256':hashlib.sha256(b'x').hexdigest()},root)

    def test_backup_is_exclusive_and_private(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'backup.json';setup.write_private(p,{'old':'keep'})
            self.assertEqual(p.stat().st_mode&0o777,0o600)
            with self.assertRaises(FileExistsError):setup.write_private(p,{'old':'overwrite'})
            self.assertEqual(json.loads(p.read_text()),{'old':'keep'})

    def test_restore_preserves_other_services_and_revokes_new_permission(self):
        fake=FakeDevice()
        data={'serial':fake.serial,'guard_was_enabled':False,'listener_was_enabled':False,
              'secure_settings_was_granted':False,'appops':'SYSTEM_ALERT_WINDOW: ignore'}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'backup';p.write_text(json.dumps(data));setup.restore(fake,p)
        writes=[a for a in fake.calls if a[:4]==('settings','put','secure','enabled_accessibility_services')]
        self.assertEqual(writes[0][4],'assistant/.Voice:new.app/.Service')
        self.assertIn(('pm','revoke',setup.PACKAGE,'android.permission.WRITE_SECURE_SETTINGS'),fake.calls)
        self.assertNotIn(('pm','uninstall',setup.PACKAGE),fake.calls)

    def test_restore_existing_guard_refuses_before_mutating(self):
        fake=FakeDevice()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'backup';p.write_text(json.dumps({'serial':fake.serial,'guard_was_enabled':True}))
            with self.assertRaises(RuntimeError):setup.restore(fake,p)
        self.assertEqual(fake.calls,[])

    def test_ui_does_not_click_other_apps_or_ambiguous_buttons(self):
        import xml.etree.ElementTree as ET
        root=ET.fromstring('<hierarchy><node package="other.app" text="确定" bounds="[1,1][2,2]"/></hierarchy>')
        with self.assertRaises(RuntimeError):configure_tvbox.node(root,text='确定')


class TCastTest(unittest.TestCase):
    def test_fragmented_and_combined_messages(self):
        a=b'223>>INSTALL>>pkg>>label>>confirm_pending';b=b'223>>PROGRESS>>pkg>>label>>5'
        data=struct.pack('>i',len(a))+a+struct.pack('>i',len(b))+b
        msgs,left=tcast_push.frames(data[:11]);self.assertEqual(msgs,[])
        msgs,left=tcast_push.frames(left+data[11:]);self.assertEqual(msgs,[a.decode(),b.decode()]);self.assertEqual(left,b'')

    def test_loopback_fake_tv_download_and_install_protocol(self):
        # A fake TV on loopback downloads dummy bytes; no LAN or adb is used.
        with tempfile.TemporaryDirectory() as d:
            apk=Path(d)/'fixture.apk';apk.write_bytes(b'fake-apk-for-protocol-test')
            listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1)
            port=listener.getsockname()[1];errors=[];requests=[]
            def tv():
                try:
                    with listener.accept()[0] as conn:
                        conn.settimeout(5)
                        def read_frame():
                            header=b''
                            while len(header)<4:header+=conn.recv(4-len(header))
                            n=struct.unpack('>i',header)[0];data=b''
                            while len(data)<n:data+=conn.recv(n-len(data))
                            return data.decode()
                        self.assertEqual(read_frame(),'159>>1>>0')
                        parts=read_frame().split('>>');requests.append(parts)
                        self.assertEqual(parts[:4],['223','INSTALL','example.fixture','Fixture'])
                        op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                        with op.open(parts[4],timeout=5) as response:self.assertEqual(response.read(),apk.read_bytes())
                        tcast_push.send(conn,'223>>INSTALL>>example.fixture>>Fixture>>confirm_pending')
                        tcast_push.send(conn,'223>>PROGRESS>>example.fixture>>Fixture>>5>>100>>'+parts[-1])
                except BaseException as e:errors.append(e)
                finally:listener.close()
            worker=threading.Thread(target=tv,daemon=True);worker.start()
            tcast_push.push('127.0.0.1',apk,'example.fixture','Fixture','7',timeout=5,port=port)
            worker.join(timeout=6);self.assertFalse(worker.is_alive());self.assertEqual(errors,[]);self.assertEqual(len(requests),1)

    def test_invalid_length_fails_without_unbounded_buffer(self):
        for n in [-1,tcast_push.MAX_FRAME+1]:
            with self.assertRaises(ValueError):tcast_push.frames(struct.pack('>i',n))

    def test_http_serves_only_selected_payload_and_tv(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'app.apk';p.write_bytes(b'APK test fixture');(Path(d)/'secret.key').write_text('secret')
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),tcast_push.apk_handler(p,'127.0.0.1','/nonce.apk'))
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                for path,status,body in [('/nonce.apk',200,b'APK test fixture'),('/secret.key',404,None),('/',404,None),('/../secret.key',404,None)]:
                    c=http.client.HTTPConnection('127.0.0.1',server.server_port);c.request('GET',path);r=c.getresponse();data=r.read();c.close();self.assertEqual(r.status,status)
                    if body:self.assertEqual(data,body)
            finally:server.shutdown();server.server_close();worker.join()


if __name__=='__main__':unittest.main()
