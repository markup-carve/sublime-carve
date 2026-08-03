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

# `# <- selector` or `#   ^^^ selector`, capturing what follows the arrow.
ASSERTION = re.compile(r"^\s*#\s*(?:<-|\^+)\s+(?P<selector>.*)$")


def problems(path):
    found = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        match = ASSERTION.match(line)
        if not match:
            continue
        selector = match.group("selector").strip()
        if re.match(r"^-\s", selector):
            wanted = "-" + selector[1:].strip()
            found.append(
                "{}:{}: negative marker followed by a space - Sublime accepts "
                "this and checks nothing. Write `{}`.".format(path.name, number, wanted)
            )
    return found


def main():
    root = Path(__file__).resolve().parent.parent
    tests = sorted(root.glob("syntax_test_*"))
    if not tests:
        print("No syntax_test_* files found; nothing to lint.", file=sys.stderr)
        return 1
    found = [p for test in tests for p in problems(test)]
    for line in found:
        print(line, file=sys.stderr)
    if found:
        print("\n{} assertion(s) cannot fail.".format(len(found)), file=sys.stderr)
        return 1
    total = sum(
        len([l for l in t.read_text().splitlines() if ASSERTION.match(l)]) for t in tests
    )
    print(
        "lint-syntax-tests: {} assertion(s) across {} file(s), none dead.".format(
            total, len(tests)
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
