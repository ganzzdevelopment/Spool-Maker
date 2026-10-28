"""Start Spool Maker, but only talk to the NFC reader (ACR122U) and ignore other smart card readers.

Replaces NFCSpool.request before the GUI starts, so the original files stay untouched.
"""
import NFCSpool as s
import reader_select


class _NFCRequest:
    def waitforcard(self):
        return reader_select.make_request(s.TIMEOUT, s.card_type).waitforcard()


s.request = _NFCRequest()

import SpoolMaker

if __name__ == '__main__':
    SpoolMaker.main()
