"""Tests for checkdigit.cli.

main() only ever communicates through its return code and stdout/stderr, so
these tests drive it exactly the way a shell would: build argv, capture the
streams, check the exit code.
"""

import contextlib
import io
import unittest

from checkdigit import cli


def run(argv):
    """Run cli.main(argv) and return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue().strip(), err.getvalue().strip()


class ComputeTests(unittest.TestCase):
    def test_isbn10_payload_prints_check_digit(self):
        code, out, err = run(["isbn10", "030640615"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "2")
        self.assertEqual(err, "")

    def test_isbn13_payload_prints_check_digit(self):
        code, out, _ = run(["isbn13", "978030640615"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "7")

    def test_ismn_payload_prints_check_digit(self):
        code, out, _ = run(["ismn", "M26000043"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "8")

    def test_upca_payload_prints_check_digit(self):
        code, out, _ = run(["upca", "03600029145"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "2")

    def test_hyphenated_payload_is_accepted(self):
        code, out, _ = run(["isbn10", "0-306-40615"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "2")


class ValidateTests(unittest.TestCase):
    def test_valid_full_code_prints_valid(self):
        code, out, err = run(["isbn10", "0-306-40615-2"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "valid")
        self.assertEqual(err, "")

    def test_invalid_full_code_reports_expected_digit_on_stderr(self):
        code, out, err = run(["ean13", "4006381333930"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(err, "invalid: expected check digit 1, got 0")

    def test_invalid_full_code_reports_expected_letter_check_digit(self):
        # payload "080442957" checks to X, so a "7" in the last slot is wrong
        code, out, err = run(["isbn10", "0804429577"])
        self.assertEqual(code, 1)
        self.assertIn("expected check digit X, got 7", err)


class SuggestTests(unittest.TestCase):
    def test_single_candidate_is_labelled_suggestion(self):
        code, out, err = run(["isbn10", "0306406157", "--suggest"])
        self.assertEqual(code, 1)
        self.assertIn("invalid:", err)
        self.assertIn("suggestion: 0306406152", err)

    def test_suggest_line_is_present_for_an_invalid_code(self):
        # whether it resolves to one fix, several, or none, --suggest always
        # adds a line starting with "suggestion" (singular) or "suggestions".
        code, out, err = run(["ean8", "40170720", "--suggest"])
        self.assertEqual(code, 1)
        self.assertIn("suggestion", err)

    def test_without_suggest_flag_no_suggestion_is_printed(self):
        code, out, err = run(["isbn10", "0306406157"])
        self.assertEqual(code, 1)
        self.assertNotIn("suggestion", err)


class LengthErrorTests(unittest.TestCase):
    def test_wrong_length_reports_both_accepted_lengths(self):
        code, out, err = run(["isbn10", "123"])
        self.assertEqual(code, 2)
        self.assertIn("needs 9 digits", err)
        self.assertIn("10", err)


class ConvertTests(unittest.TestCase):
    def test_convert_isbn10_to_isbn13(self):
        code, out, err = run(["convert", "0-306-40615-2"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "9780306406157")

    def test_convert_rejects_wrong_length(self):
        code, out, err = run(["convert", "12345"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertNotEqual(err, "")


class ParserTests(unittest.TestCase):
    def test_every_format_has_a_subcommand(self):
        parser = cli.build_parser()
        subparsers_action = next(
            action for action in parser._actions if action.dest == "command"
        )
        self.assertEqual(
            set(subparsers_action.choices),
            {"isbn10", "isbn13", "issn", "ismn", "ean13", "upca", "ean8", "convert"},
        )

    def test_missing_command_exits_nonzero(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cli.build_parser().parse_args([])
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
