"""Table-driven tests for checkdigit.core.

The tables lean on real, published codes where possible (the Nivea EAN-13,
the Wrigley's UPC-A from the Wikipedia UPC article) plus a few hand-computed
ones for cases that are hard to find in the wild, like an ISBN-10 with an X
check digit or an all-zero payload.
"""

import unittest

from checkdigit import core


class Isbn10Tests(unittest.TestCase):
    VALID = [
        ("plain", "0306406152"),
        ("hyphenated", "0-306-40615-2"),
        ("spaced", "0 306 40615 2"),
        ("check digit is X", "0-8044-2957-X"),
        ("lowercase x", "0-8044-2957-x"),
        ("all zeros", "0000000000"),
    ]

    INVALID = [
        ("wrong final digit", "0-306-40615-1"),
        ("too short", "030640615"),
        ("too long", "03064061523"),
        ("letter in payload", "0-30A-40615-2"),
        ("empty string", ""),
    ]

    def test_valid_codes(self):
        for label, code in self.VALID:
            with self.subTest(label):
                self.assertTrue(core.is_valid_isbn10(code))

    def test_invalid_codes(self):
        for label, code in self.INVALID:
            with self.subTest(label):
                self.assertFalse(core.is_valid_isbn10(code))

    def test_check_digit_examples(self):
        self.assertEqual(core.isbn10_check_digit("030640615"), "2")
        self.assertEqual(core.isbn10_check_digit("080442957"), "X")

    def test_check_digit_rejects_wrong_length(self):
        with self.assertRaises(ValueError):
            core.isbn10_check_digit("12345")


class Isbn13Tests(unittest.TestCase):
    VALID = [
        ("plain", "9780306406157"),
        ("hyphenated", "978-0-306-40615-7"),
        ("979 prefix, all-zero-ish payload", "9790000000001"),
        ("all zeros", "0000000000000"),
    ]

    INVALID = [
        ("wrong final digit", "9780306406158"),
        ("too short", "978030640615"),
        ("non-digit", "978030640615X"),
    ]

    def test_valid_codes(self):
        for label, code in self.VALID:
            with self.subTest(label):
                self.assertTrue(core.is_valid_isbn13(code))

    def test_invalid_codes(self):
        for label, code in self.INVALID:
            with self.subTest(label):
                self.assertFalse(core.is_valid_isbn13(code))

    def test_isbn10_to_isbn13(self):
        self.assertEqual(core.isbn10_to_isbn13("0-306-40615-2"), "9780306406157")
        self.assertEqual(core.isbn10_to_isbn13("0-8044-2957-X"), "9780804429573")


class IssnTests(unittest.TestCase):
    VALID = [
        ("Mathematical Reviews", "0378-5955"),
        ("plain", "03785955"),
        ("check digit is 0", "2049-3630"),
        ("check digit is X", "1000-002X"),
        ("all zeros", "00000000"),
    ]

    INVALID = [
        ("wrong final digit", "0378-5954"),
        ("too short", "037859"),
        ("too long", "037859551"),
        ("letter in payload", "037A5955"),
        ("empty string", ""),
    ]

    def test_valid_codes(self):
        for label, code in self.VALID:
            with self.subTest(label):
                self.assertTrue(core.is_valid_issn(code))

    def test_invalid_codes(self):
        for label, code in self.INVALID:
            with self.subTest(label):
                self.assertFalse(core.is_valid_issn(code))

    def test_check_digit_examples(self):
        self.assertEqual(core.issn_check_digit("0378595"), "5")
        self.assertEqual(core.issn_check_digit("2049363"), "0")

    def test_check_digit_rejects_wrong_length(self):
        with self.assertRaises(ValueError):
            core.issn_check_digit("12345")


class IsmnTests(unittest.TestCase):
    VALID = [
        ("plain", "M260000438"),
        ("hyphenated", "M-2600-0043-8"),
        ("lowercase m", "m-2600-0043-8"),
        ("all zeros", "M000000001"),
    ]

    INVALID = [
        ("wrong final digit", "M-2600-0043-7"),
        ("too short", "M-2600-004"),
        ("too long", "M-2600-0043-80"),
        ("missing M", "2-2600-0043-8"),
        ("empty string", ""),
    ]

    def test_valid_codes(self):
        for label, code in self.VALID:
            with self.subTest(label):
                self.assertTrue(core.is_valid_ismn(code))

    def test_invalid_codes(self):
        for label, code in self.INVALID:
            with self.subTest(label):
                self.assertFalse(core.is_valid_ismn(code))

    def test_check_digit_example(self):
        self.assertEqual(core.ismn_check_digit("M26000043"), "8")

    def test_matches_isbn13_style_prefix(self):
        # the 13-digit ISMN form (979-0-...) is the same 12 digits run
        # through isbn13_check_digit as the M-form is through gs1_check_digit.
        self.assertEqual(core.isbn13_check_digit("979026000043"), "8")

    def test_check_digit_rejects_wrong_length(self):
        with self.assertRaises(ValueError):
            core.ismn_check_digit("M123")

    def test_check_digit_rejects_missing_m(self):
        with self.assertRaises(ValueError):
            core.ismn_check_digit("226000043")


class Gs1Tests(unittest.TestCase):
    # (label, full code, expected check digit function, validator)
    CASES = [
        ("EAN-13, Nivea creme tin", "4006381333931", core.is_valid_ean13),
        ("UPC-A, Wrigley's gum", "036000291452", core.is_valid_upca),
        ("EAN-8", "40170725", core.is_valid_ean8),
        ("EAN-13, all zeros", "0000000000000", core.is_valid_ean13),
        ("UPC-A, all zeros", "000000000000", core.is_valid_upca),
    ]

    def test_valid_codes(self):
        for label, code, validator in self.CASES:
            with self.subTest(label):
                self.assertTrue(validator(code))

    def test_flipped_check_digit_is_invalid(self):
        for label, code, validator in self.CASES:
            with self.subTest(label):
                bad = code[:-1] + str((int(code[-1]) + 1) % 10)
                self.assertFalse(validator(bad))

    def test_wrong_length_is_invalid_not_an_exception(self):
        self.assertFalse(core.is_valid_ean13("123"))
        self.assertFalse(core.is_valid_upca("4006381333931"))

    def test_generic_gs1_matches_named_wrappers(self):
        self.assertEqual(core.gs1_check_digit("400638133393"), core.ean13_check_digit("400638133393"))
        self.assertEqual(core.gs1_check_digit("03600029145"), core.upca_check_digit("03600029145"))
        self.assertEqual(core.gs1_check_digit("4017072"), core.ean8_check_digit("4017072"))

    def test_named_wrappers_reject_wrong_payload_length(self):
        with self.assertRaises(ValueError):
            core.ean13_check_digit("123")
        with self.assertRaises(ValueError):
            core.upca_check_digit("123")
        with self.assertRaises(ValueError):
            core.ean8_check_digit("123")


if __name__ == "__main__":
    unittest.main()
