"""Start Spool Maker, but only talk to the NFC reader (ACR122U) and ignore other smart card readers.

Replaces NFCSpool.request before the GUI starts, so the original files stay untouched.
Everything the app prints, and any crash, is written to %LOCALAPPDATA%\\SpoolMaker\\spoolmaker.log
and errors are shown in a message box instead of silently closing the app.
"""
import os
import sys
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


class _NFCRequest:
    def waitforcard(self):
        return reader_select.make_request(s.TIMEOUT, s.card_type).waitforcard()


s.request = _NFCRequest()

import SpoolMaker

if __name__ == '__main__':
    SpoolMaker.main()
