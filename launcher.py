"""Start Spool Maker, but only talk to the NFC reader (ACR122U) and ignore other smart card readers.

Replaces NFCSpool.request before the GUI starts, so the original files stay untouched.
Everything the app prints, and any crash, is written to %LOCALAPPDATA%\\SpoolMaker\\spoolmaker.log
and errors are shown in a message box instead of silently closing the app.
"""
import os
import sys
import time
import traceback

_base = os.getenv('LOCALAPPDATA') or os.path.expanduser('~')
_logdir = os.path.join(_base, 'SpoolMaker')
os.makedirs(_logdir, exist_ok=True)
LOGFILE = os.path.join(_logdir, 'spoolmaker.log')
_log = open(LOGFILE, 'a', buffering=1, encoding='utf-8', errors='replace')
sys.stdout = _log
sys.stderr = _log
print('\n===== Spool Maker start =====')


def _hook(exc_type, exc, tb):
    text = ''.join(traceback.format_exception(exc_type, exc, tb))
    print('UNCAUGHT ERROR:\n' + text)
    try:
        from PyQt5 import QtWidgets
        QtWidgets.QMessageBox.critical(None, 'Spool Maker error',
                                       text[-1500:] + '\n\nLog: ' + LOGFILE)
    except Exception:
        pass


sys.excepthook = _hook

import NFCSpool as s
import reader_select
from smartcard.Exceptions import CardConnectionException, NoCardException

# --- Protocol selection + resilient reads ----------------------------------
# The log showed the first read command failing with "protocol T1" and error
# 0x80100017 / 0x80100069. The app now opens the tag with T=0 first, then T=1,
# then the Windows default, and logs which one works. A failed command is
# retried with the next protocol.
from smartcard.CardConnection import CardConnection

PROTOCOLS = [('T0', CardConnection.T0_protocol),
             ('T1', CardConnection.T1_protocol),
             ('default', None)]
RETRIES = 6
PAUSE = 0.4


def _wrap_connection(conn):
    if getattr(conn, '_resilient', False):
        return conn
    orig_connect = conn.connect
    orig_reconnect = conn.reconnect
    orig_transmit = conn.transmit
    state = {'i': 0, 'ok': False}

    def _name():
        return PROTOCOLS[state['i']][0]

    def _proto():
        return PROTOCOLS[state['i']][1]

    def connect(*a, **k):
        print('connect with protocol', _name())
        if _proto() is None:
            return orig_connect()
        return orig_connect(_proto())

    def reconnect(*a, **k):
        print('reconnect with protocol', _name())
        if _proto() is None:
            return orig_reconnect()
        return orig_reconnect(_proto())

    def transmit(cmd, *a, **k):
        last = None
        for attempt in range(RETRIES):
            try:
                result = orig_transmit(cmd, *a, **k)
                if not state['ok']:
                    state['ok'] = True
                    print('transmit OK with protocol', _name())
                return result
            except (CardConnectionException, NoCardException) as e:
                last = e
                print('transmit failed (attempt %d/%d, protocol %s): %s' % (attempt + 1, RETRIES, _name(), e))
                time.sleep(PAUSE * (attempt + 1))
                if attempt % 2 == 1:
                    state['i'] = (state['i'] + 1) % len(PROTOCOLS)
                try:
                    reconnect()
                except Exception as e2:
                    try:
                        connect()
                    except Exception as e3:
                        print('reconnect failed:', e2, '/', e3)
        raise last

    conn.connect = connect
    conn.reconnect = reconnect
    conn.transmit = transmit
    conn._resilient = True
    return conn


class _NFCRequest:
    def waitforcard(self):
        service = reader_select.make_request(s.TIMEOUT, s.card_type).waitforcard()
        try:
            _wrap_connection(service.connection)
        except Exception as e:
            print('Could not wrap connection:', e)
        return service


s.request = _NFCRequest()

import SpoolMaker

if __name__ == '__main__':
    SpoolMaker.main()
