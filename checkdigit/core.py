"""Checksum math for ISBN-10, ISBN-13, and GS1 retail barcodes (EAN-13, UPC-A, EAN-8).

ISBN-10 uses a mod-11 weighted sum (weights 10..1, check digit can be the
letter X). ISBN-13 and every GS1 retail barcode share a mod-10 weighted sum
that alternates weights of 1 and 3. The only thing that differs between
EAN-13, UPC-A, and EAN-8 is how many digits come before the check digit, so
they all go through the same gs1_check_digit() rather than three near-copies
of the same loop.
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
