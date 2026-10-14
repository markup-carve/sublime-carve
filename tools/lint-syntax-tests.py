#!/usr/bin/env python3
"""Reject syntax-test assertions that cannot fail.

Sublime binds a negative assertion's marker to the scope selector with NO space:
`-scope`, not `- scope`. Written with the space it is accepted and checks
nothing, so the assertion sits in the file looking like coverage while guarding
nothing at all.

That is not hypothetical. Every negative assertion in syntax_test_carve.crv was
written with the space when it landed, and stayed dead until the syntax was
reverted and CI came back green anyway.

The syntax-test runner cannot tell us - it has no way to know the space was not
intended - so this runs alongside it.
"""
import re
import sys
from pathlib import Path

# Read the comment token from each file's syntax-test header.
def assertion_pattern(path):
    lines = path.read_text().splitlines()
    header = re.match(r"^(.*?)\s+SYNTAX TEST(?:\s|$)", lines[0]) if lines else None
    if not header:
        return None, lines
    comment = header.group(1)
    return (
        re.compile(rf"^\s*{re.escape(comment)}\s*(?:<-|\^+)\s+(?P<selector>.*)$"),
        lines,
    )


def problems(path):
    found = []
    assertion, lines = assertion_pattern(path)
    if assertion is None:
        return [f"{path.name}:1: missing syntax-test marker"], 0
    total = 0
    for number, line in enumerate(lines, start=1):
        match = assertion.match(line)
        if not match:
            continue
        total += 1
        selector = match.group("selector").strip()
        if re.match(r"^-\s", selector):
            wanted = "-" + selector[1:].strip()
            found.append(
                "{}:{}: negative marker followed by a space - Sublime accepts "
                "this and checks nothing. Write `{}`.".format(path.name, number, wanted)
            )
    if total == 0:
        found.append(f"{path.name}: no assertions use its syntax-test comment token")
    return found, total


def main():
    root = Path(__file__).resolve().parent.parent
    tests = sorted(root.glob("syntax_test_*"))
    if not tests:
        print("No syntax_test_* files found; nothing to lint.", file=sys.stderr)
        return 1
    results = [problems(test) for test in tests]
    found = [p for errors, _ in results for p in errors]
    for line in found:
        print(line, file=sys.stderr)
    if found:
        print("\n{} assertion(s) cannot fail.".format(len(found)), file=sys.stderr)
        return 1
    total = sum(count for _, count in results)
    print(
        "lint-syntax-tests: {} assertion(s) across {} file(s), none dead.".format(
            total, len(tests)
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
