#!/usr/bin/env python3
"""Verify bundled payload digests without contacting a TV or executing APK code."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    catalog=json.loads((ROOT/'packages/catalog.json').read_text())
    items=list(catalog['artifacts'].values())+catalog['tvbox_config']['files']+catalog['source_archives']
    for item in items:
        p=ROOT/item['file']
        if p.is_symlink() or ROOT not in p.resolve().parents:raise SystemExit('Invalid artifact path')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Hash mismatch: '+item['file'])
    print('Verified',len(items),'payloads; APK hashes, matching TVBox source archive and local configuration intact.')

if __name__=='__main__':main()
