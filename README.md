# checkdigit

Check digits catch typos, not fraud. Every ISBN and every retail barcode
carries one extra digit that's a weighted checksum of the rest of the
number, so a single mistyped or transposed digit almost always turns a valid
code into an invalid one. This library computes and validates those digits
for the formats you actually run into:

- ISBN-10 and ISBN-13 (mod 11 and mod 10 respectively; ISBN-10 can end in `X`)
- ISSN (mod 11, same shape as ISBN-10 but 7 digits wide, can also end in `X`)
- ISMN, the old 10-character `M-...` form (mod 10, reuses the GS1 algorithm
  by treating the leading `M` as the digit 3)
- EAN-13, UPC-A, and EAN-8 (all the same mod-10 GS1 algorithm, just different
  lengths)

It also converts an ISBN-10 to its ISBN-13 form, since that's the same
computation with a `978` prefix stapled on.

## Why this isn't three copies of the same loop

EAN-13, UPC-A, and EAN-8 look like different formats but they use one
algorithm: reverse the digits before the check digit, multiply by weights
alternating 3 and 1 starting from the one closest to the check digit, sum,
and take `(10 - sum % 10) % 10`. The only thing that changes is how many
digits come before the check digit. `gs1_check_digit()` implements that once;
`ean13_check_digit()`, `upca_check_digit()`, and `ean8_check_digit()` are thin
wrappers that just enforce the expected payload length before calling it.
ISBN-10 is genuinely different (mod 11, letter check digit) and gets its own
function.

## Library usage

```python
from checkdigit import core

core.is_valid_isbn10("0-306-40615-2")     # True
core.is_valid_isbn13("978-0-306-40615-7") # True
core.isbn10_to_isbn13("0-306-40615-2")    # "9780306406157"

core.is_valid_ean13("4006381333931")      # True
core.upca_check_digit("03600029145")      # "2"
```

Functions that validate a full code (`is_valid_*`) return `False` for
malformed input instead of raising. Functions that compute a check digit from
a payload (`*_check_digit`) raise `ValueError` if the payload is the wrong
length, since that's a programming error rather than bad user input.

## Command line

```
$ python -m checkdigit.cli isbn10 0-306-40615-2
valid

$ python -m checkdigit.cli isbn13 030640615
7

$ python -m checkdigit.cli ean13 4006381333930
invalid: expected check digit 1, got 0

$ python -m checkdigit.cli convert 0-306-40615-2
9780306406157
```

Give a subcommand a payload (missing its check digit) and it computes the
check digit. Give it a full code and it validates. Subcommands: `isbn10`,
`isbn13`, `issn`, `ismn`, `ean13`, `upca`, `ean8`, `convert`.

Installing the package (`pip install -e .`) also gives you a `checkdigit`
console script that does the same thing without the `-m` invocation.

## Running the tests

```
python -m unittest discover -v
```

No third-party dependencies anywhere, so this runs against a stock Python
3.9+ install.
