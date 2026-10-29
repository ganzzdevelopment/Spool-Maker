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

# --- Resilient reads -------------------------------------------------------
# The reader can drop out for a moment during the ~75 read commands of one scan
# (Windows error 0x80100017, "reader unavailable"). Instead of crashing, wait
# briefly, reconnect to the tag and retry the same command.
RETRIES = 6
PAUSE = 0.4


def _wrap_connection(conn):
    if getattr(conn, '_resilient', False):
        return conn
    original = conn.transmit

    def transmit(cmd, *a, **k):
        last = None
        for attempt in range(RETRIES):
            try:
                return original(cmd, *a, **k)
            except (CardConnectionException, NoCardException) as e:
                last = e
                print('transmit failed (attempt %d/%d): %s' % (attempt + 1, RETRIES, e))
                time.sleep(PAUSE * (attempt + 1))
                try:
                    conn.reconnect()
                except Exception as e2:
                    try:
                        conn.connect()
                    except Exception as e3:
                        print('reconnect failed:', e2, '/', e3)
        raise last

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
