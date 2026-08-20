"""Command-line front end for the checkdigit library.

Each format has a payload length (digits before the check digit) and a full
length (payload plus check digit). Feed a payload and it computes the check
digit; feed a full code and it tells you whether the check digit is right.
"""

import argparse
import sys

from . import core

_SPECS = {
    "isbn10": (core.is_valid_isbn10, core.isbn10_check_digit, 9, 10),
    "isbn13": (core.is_valid_isbn13, core.isbn13_check_digit, 12, 13),
    "ean13": (core.is_valid_ean13, core.ean13_check_digit, 12, 13),
    "upca": (core.is_valid_upca, core.upca_check_digit, 11, 12),
    "ean8": (core.is_valid_ean8, core.ean8_check_digit, 7, 8),
}


def _handle_format(kind, code):
    validate, compute, payload_len, full_len = _SPECS[kind]
    cleaned = code.strip().replace("-", "").replace(" ", "")
    if len(cleaned) == payload_len:
        print(compute(cleaned))
        return 0
    if len(cleaned) == full_len:
        if validate(cleaned):
            print("valid")
            return 0
        payload, given = cleaned[:-1], cleaned[-1].upper()
        expected = compute(payload)
        print(f"invalid: expected check digit {expected}, got {given}", file=sys.stderr)
        return 1
    print(
        f"{kind} needs {payload_len} digits (to compute) or {full_len} "
        f"(to validate), got {len(cleaned)}",
        file=sys.stderr,
    )
    return 2


def _handle_convert(code):
    cleaned = code.strip().replace("-", "").replace(" ", "")
    try:
        print(core.isbn10_to_isbn13(cleaned))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="checkdigit",
        description="Compute or validate check digits for ISBN and barcode formats.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for kind in _SPECS:
        sub = subparsers.add_parser(kind, help=f"compute or validate a {kind} code")
        sub.add_argument("code", help="payload (to compute) or full code (to validate)")

    convert = subparsers.add_parser("convert", help="convert an ISBN-10 to ISBN-13")
    convert.add_argument("code", help="a 10-character ISBN-10")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "convert":
        return _handle_convert(args.code)
    return _handle_format(args.command, args.code)


if __name__ == "__main__":
    sys.exit(main())
