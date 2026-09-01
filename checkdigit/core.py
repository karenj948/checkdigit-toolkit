"""Checksum math for ISBN-10/13, ISSN, ISMN, and GS1 retail barcodes (EAN-13, UPC-A, EAN-8).

ISBN-10 and ISSN both use a mod-11 weighted sum (descending weights, check
digit can be the letter X); they differ only in payload length and starting
weight, so they're two short functions rather than a shared one -- sharing
would cost more in indirection than it'd save in lines. ISBN-13, ISMN, and
every GS1 retail barcode share a mod-10 weighted sum that alternates weights
of 1 and 3. The only thing that differs between EAN-13, UPC-A, and EAN-8 is
how many digits come before the check digit, so they all go through the same
gs1_check_digit() rather than three near-copies of the same loop. The old
10-character ISMN goes through it too, once its leading M is swapped for the
digit value (3) that ISMN assigns it.
"""

import itertools


def _clean(code):
    return code.strip().replace("-", "").replace(" ", "").upper()


def _require_digits(payload, label):
    if not payload.isdigit():
        raise ValueError(f"{label} must contain only digits, got {payload!r}")


def isbn10_check_digit(payload):
    payload = _clean(payload)
    if len(payload) != 9:
        raise ValueError(f"ISBN-10 payload must be exactly 9 digits, got {payload!r}")
    _require_digits(payload, "ISBN-10 payload")
    total = sum(int(d) * w for d, w in zip(payload, range(10, 1, -1)))
    check = (11 - total % 11) % 11
    return "X" if check == 10 else str(check)


def is_valid_isbn10(isbn):
    code = _clean(isbn)
    if len(code) != 10:
        return False
    payload, check = code[:9], code[9]
    if not payload.isdigit() or not (check.isdigit() or check == "X"):
        return False
    return isbn10_check_digit(payload) == check


def isbn13_check_digit(payload):
    payload = _clean(payload)
    if len(payload) != 12:
        raise ValueError(f"ISBN-13 payload must be exactly 12 digits, got {payload!r}")
    _require_digits(payload, "ISBN-13 payload")
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(payload))
    return str((10 - total % 10) % 10)


def is_valid_isbn13(isbn):
    code = _clean(isbn)
    if len(code) != 13 or not code.isdigit():
        return False
    return isbn13_check_digit(code[:12]) == code[12]


def isbn10_to_isbn13(isbn10):
    code = _clean(isbn10)
    if len(code) != 10:
        raise ValueError(f"ISBN-10 must be exactly 10 characters, got {code!r}")
    payload = "978" + code[:9]
    return payload + isbn13_check_digit(payload)


def gs1_check_digit(payload):
    payload = _clean(payload)
    if not payload:
        raise ValueError("barcode payload must not be empty")
    _require_digits(payload, "barcode payload")
    weights = itertools.cycle((3, 1))
    total = sum(int(d) * w for d, w in zip(reversed(payload), weights))
    return str((10 - total % 10) % 10)


def is_valid_gs1(code):
    code = _clean(code)
    if len(code) < 2 or not code.isdigit():
        return False
    payload, check = code[:-1], code[-1]
    return gs1_check_digit(payload) == check


def ean13_check_digit(payload):
    payload = _clean(payload)
    if len(payload) != 12:
        raise ValueError(f"EAN-13 payload must be exactly 12 digits, got {payload!r}")
    return gs1_check_digit(payload)


def is_valid_ean13(code):
    code = _clean(code)
    return len(code) == 13 and is_valid_gs1(code)


def upca_check_digit(payload):
    payload = _clean(payload)
    if len(payload) != 11:
        raise ValueError(f"UPC-A payload must be exactly 11 digits, got {payload!r}")
    return gs1_check_digit(payload)


def is_valid_upca(code):
    code = _clean(code)
    return len(code) == 12 and is_valid_gs1(code)


def ean8_check_digit(payload):
    payload = _clean(payload)
    if len(payload) != 7:
        raise ValueError(f"EAN-8 payload must be exactly 7 digits, got {payload!r}")
    return gs1_check_digit(payload)


def is_valid_ean8(code):
    code = _clean(code)
    return len(code) == 8 and is_valid_gs1(code)


def issn_check_digit(payload):
    payload = _clean(payload)
    if len(payload) != 7:
        raise ValueError(f"ISSN payload must be exactly 7 digits, got {payload!r}")
    _require_digits(payload, "ISSN payload")
    total = sum(int(d) * w for d, w in zip(payload, range(8, 1, -1)))
    check = (11 - total % 11) % 11
    return "X" if check == 10 else str(check)


def is_valid_issn(issn):
    code = _clean(issn)
    if len(code) != 8:
        return False
    payload, check = code[:7], code[7]
    if not payload.isdigit() or not (check.isdigit() or check == "X"):
        return False
    return issn_check_digit(payload) == check


def ismn_check_digit(payload):
    """payload is 'M' followed by the 8-digit body, e.g. 'M26000043'.

    The old 10-character ISMN reuses the GS1 mod-10 algorithm: the leading
    M is worth 3 (the value ISMN assigns it), the rest is the digit body,
    and gs1_check_digit does the same reversed-weights sum it does for
    EAN/UPC. That's also why the 13-digit ISMN (979-0-...) matches
    isbn13_check_digit exactly -- it's the same 12 digits with 9790 as the
    prefix instead of M.
    """
    payload = _clean(payload)
    if len(payload) != 9 or payload[0] != "M":
        raise ValueError(f"ISMN payload must be 'M' followed by 8 digits, got {payload!r}")
    body = payload[1:]
    _require_digits(body, "ISMN payload")
    return gs1_check_digit("3" + body)


def is_valid_ismn(ismn):
    code = _clean(ismn)
    if len(code) != 10 or code[0] != "M":
        return False
    payload, check = code[:9], code[9]
    if not payload[1:].isdigit() or not check.isdigit():
        return False
    return ismn_check_digit(payload) == check


def nearby_valid_codes(code, validate, check_symbols=""):
    """Every code that's one character away from `code` and passes `validate`.

    Meant for guessing what an invalid code was supposed to be when exactly
    one digit was mistyped -- try every other symbol in every position and
    keep the ones that pass. `check_symbols` are extra characters (e.g. "X"
    for ISBN-10/ISSN) that are only tried in the last position, since that's
    the only place those formats allow a non-digit.
    """
    code = _clean(code)
    results = []
    for i in range(len(code)):
        alphabet = "0123456789"
        if i == len(code) - 1:
            alphabet += check_symbols
        for symbol in alphabet:
            if symbol == code[i]:
                continue
            candidate = code[:i] + symbol + code[i + 1:]
            if validate(candidate):
                results.append(candidate)
    return results
