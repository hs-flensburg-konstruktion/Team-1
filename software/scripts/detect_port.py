#!/usr/bin/env python3
"""Only select a unique identified XIAO or a unique USB modem; never pick arbitrarily."""
import glob
import json
import sys

def choose_port(data, fallback):
    ports = data.get('detected_ports', []) if isinstance(data, dict) else data
    exact, usb = set(), set(fallback)
    for item in ports:
        port = item.get('port', {})
        address = port.get('address', '')
        if port.get('protocol') != 'serial':
            continue
        if address.startswith('/dev/cu.usbmodem'):
            usb.add(address)
        props = {k.lower(): str(v).lower().removeprefix('0x')
                 for k, v in port.get('properties', {}).items()}
        known_board = any(b.get('fqbn') == 'esp32:esp32:XIAO_ESP32S3'
                          for b in item.get('matching_boards', []))
        known_id = props.get('vid') == '2886' and props.get('pid') in ('0056', '8056')
        if known_board or known_id:
            exact.add(address)
    candidates = exact or usb
    if len(candidates) == 1:
        return next(iter(candidates))
    if not candidates:
        raise ValueError('Kein ESP32-USB-Port gefunden. Datenkabel anschließen; ggf. BOOT halten, RESET drücken, BOOT loslassen. Alternativ: ./scripts/upload.sh --port /dev/cu.usbmodem…')
    raise ValueError('Mehrere mögliche Boards: ' + ', '.join(sorted(candidates)) + '. Bitte --port angeben.')

if __name__ == '__main__':
    try:
        print(choose_port(json.load(sys.stdin), glob.glob('/dev/cu.usbmodem*')))
    except (ValueError, KeyError) as error:
        sys.exit(str(error))
