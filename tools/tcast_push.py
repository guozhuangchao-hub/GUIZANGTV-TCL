#!/usr/bin/env python3
"""TCL 多屏互动推送。Protocol from Tigris/Aerial (MIT); see NOTICE.md.
Only the selected APK is served, only to the selected TV; no directory serving.
"""
import argparse
import hashlib
import http.server
import ipaddress
import math
from pathlib import Path
import secrets
import socket
import struct
import threading
import time

MAX_FRAME = 2 * 1024 * 1024


def frames(buffer):
    messages = []
    while len(buffer) >= 4:
        size = struct.unpack('>i', buffer[:4])[0]
        if size < 0 or size > MAX_FRAME:
            raise ValueError('Invalid T-Cast frame length')
        if len(buffer) < 4 + size:
            break
        messages.append(buffer[4:4 + size].decode('utf-8', 'replace'))
        buffer = buffer[4 + size:]
    return messages, buffer


def send(sock, message):
    data = message.encode('utf-8')
    sock.sendall(struct.pack('>i', len(data)) + data)


def apk_handler(apk, tv_ip, route):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.client_address[0] != tv_ip or self.path != route:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.android.package-archive')
            self.send_header('Content-Length', str(apk.stat().st_size))
            self.end_headers()
            with apk.open('rb') as source:
                while chunk := source.read(1024 * 1024):
                    self.wfile.write(chunk)

        def log_message(self, *args):
            pass
    return Handler


def push(tv_ip, apk, package, label, version, timeout=180, port=6553):
    address = ipaddress.ip_address(tv_ip)
    if address.version != 4 or not address.is_private or address.is_unspecified or address.is_multicast:
        raise ValueError('T-Cast needs the TV private IPv4 address')
    apk = Path(apk).resolve(strict=True)
    for value in (package, label, str(version)):
        if '>>' in value or '\n' in value or '\r' in value:
            raise ValueError('Invalid T-Cast metadata')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as route_socket:
        route_socket.connect((tv_ip, port))
        local_ip = route_socket.getsockname()[0]
    route = '/' + secrets.token_hex(16) + '.apk'
    server = http.server.ThreadingHTTPServer((local_ip, 0), apk_handler(apk, tv_ip, route))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        url = f'http://{local_ip}:{server.server_port}{route}'
        with socket.create_connection((tv_ip, port), timeout=5) as sock:
            sock.settimeout(1)
            send(sock, '159>>1>>0')
            # MD5 is a protocol URL correlation field, not the package authenticity check.
            token = hashlib.md5(url.encode()).hexdigest()
            send(sock, '>>'.join(['223', 'INSTALL', package, label, url, '2', str(version),
                                  str(math.ceil(apk.stat().st_size / 1024**2)), '', '', '', token]))
            print('电视即将显示多屏互动安装提示，请在电视选择“同意”。', flush=True)
            buffer = b''
            deadline, beat = time.monotonic() + timeout, time.monotonic()
            while time.monotonic() < deadline:
                try:
                    chunk = sock.recv(65536)
                    if not chunk:
                        raise RuntimeError('T-Cast connection closed before installation confirmation')
                    buffer += chunk
                except socket.timeout:
                    pass
                messages, buffer = frames(buffer)
                for message in messages:
                    parts = message.split('>>')
                    if len(parts) < 5 or parts[0] != '223' or parts[2] != package:
                        continue
                    if parts[1] == 'INSTALL' and parts[4] == 'denied':
                        raise RuntimeError('TV user declined installation')
                    if parts[1] == 'PROGRESS':
                        if parts[4] == '5':
                            return
                        if parts[4] == '2':
                            raise RuntimeError('TV reported download or installation failure')
                if time.monotonic() - beat >= 5:
                    send(sock, '150>>')
                    beat = time.monotonic()
            raise TimeoutError('Timed out waiting for the TV installation prompt')
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('tv_ip'); p.add_argument('apk', type=Path)
    p.add_argument('--package', required=True); p.add_argument('--label', required=True)
    p.add_argument('--version', required=True); p.add_argument('--timeout', type=int, default=180)
    a = p.parse_args()
    push(a.tv_ip, a.apk, a.package, a.label, a.version, a.timeout)


if __name__ == '__main__':
    main()
