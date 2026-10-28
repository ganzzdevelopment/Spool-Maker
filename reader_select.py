"""Pick the NFC reader (ACR122U) and ignore other smart card readers."""
from smartcard.CardRequest import CardRequest
from smartcard.System import readers

READER_KEYWORDS = ('acr122', 'acs acr', 'picc')       # ACR122U with the ACS driver
GENERIC_KEYWORDS = ('usbccid', 'ccid')                 # ACR122U on the generic Windows driver
EXCLUDE_KEYWORDS = ('alcorlink', 'contact', 'sim', 'windows hello', 'virtual')  # other smart card readers


def find_nfc_reader():
    """ACS name first, then a generic CCID reader that is not a known other reader."""
    try:
        found = readers()
    except Exception as e:
        print('Could not list smart card readers:', e)
        return None
    print('Smart card readers found:', [str(r) for r in found])
    for r in found:
        if any(k in str(r).lower() for k in READER_KEYWORDS):
            print('Using NFC reader (ACS name):', r)
            return r
    for r in found:
        n = str(r).lower()
        if any(k in n for k in GENERIC_KEYWORDS) and not any(k in n for k in EXCLUDE_KEYWORDS):
            print('Using NFC reader (generic driver):', r)
            return r
    return None


def make_request(timeout, card_type):
    r = find_nfc_reader()
    if r is not None:
        return CardRequest(timeout=timeout, cardType=card_type, readers=[r])
    print('No NFC reader recognised, listening on all readers')
    return CardRequest(timeout=timeout, cardType=card_type)
