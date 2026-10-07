#!/usr/bin/env python3
"""Command-line access to the same Windows adapter and offline OUI engine."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from macspoofer.oui import Catalog
from macspoofer.engine import WindowsAdapters

def main():
    p=argparse.ArgumentParser(description='MAC // Spoofer - Windows adapters and offline OUI intelligence')
    p.add_argument('-l','--list',action='store_true',help='Read adapters')
    p.add_argument('-r','--random',action='store_true',help='Generate a private MAC; does not apply without --interface')
    p.add_argument('--lookup',help='Inspect a MAC offline')
    p.add_argument('--search',help='Search registered prefixes offline')
    p.add_argument('-i','--interface',help='Exact Windows interface GUID')
    p.add_argument('-m','--mac',help='Address to apply')
    p.add_argument('--restore',action='store_true',help='Remove the selected adapter override')
    p.add_argument('--yes',action='store_true',help='Confirm adapter restart and brief disconnection')
    a=p.parse_args()
    c=Catalog()
    try:
        if a.list: result=WindowsAdapters().list()
        elif a.lookup: result=c.inspect(a.lookup)
        elif a.search is not None: result=c.search(a.search)
        elif a.interface:
            if not a.yes: p.error('Applying requires --yes to acknowledge the adapter restart.')
            if a.restore and (a.mac or a.random): p.error('--restore cannot be combined with --mac or --random.')
            if not (a.restore or a.mac or a.random): p.error('Choose --mac, --random or --restore.')
            address=None if a.restore else a.mac or c.generate()['mac']
            from macspoofer.paths import DATA
            def journal(record):
                with (DATA/'changes.jsonl').open('a',encoding='utf-8') as f:
                    f.write(json.dumps(record)+'\n')
                    f.flush()
                    import os
                    os.fsync(f.fileno())
            result=WindowsAdapters().change(a.interface,address,journal,lambda m:print(m,file=sys.stderr))
        elif a.random: result=c.generate()
        else: p.print_help();return 0
        print(json.dumps(result,indent=2))
        return 0
    except Exception as exc:
        print(str(exc),file=sys.stderr)
        return 1
if __name__=='__main__': raise SystemExit(main())
