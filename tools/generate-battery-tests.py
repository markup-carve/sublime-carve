#!/usr/bin/env python3
"""Compile the shared block battery into syntax-test assertions.

Every other Carve grammar runs `tests/lib/block-battery.json` directly. This one
cannot: Sublime's syntax tests only execute inside the editor, via the CI
action, so the battery has to be expressed in the assertion language of
`syntax_test_carve.crv`.

So it is generated, and `--check` verifies the committed block still matches
what this script produces. Without that, the generated block would be a copy
nothing compares - the exact failure the battery exists to catch, one level up.

Run with no arguments to rewrite the block in place.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATTERY = ROOT / "tests" / "lib" / "block-battery.json"
TESTS = ROOT / "syntax_test_carve.crv"

BEGIN = "# --- BEGIN GENERATED BLOCK BATTERY (tools/generate-battery-tests.py) ---"
END = "# --- END GENERATED BLOCK BATTERY ---"

SCOPE = {
    "heading": "punctuation.definition.heading.carve",
    "list": "punctuation.definition.list.begin.carve",
    "deflist": "punctuation.definition.list.begin.carve",
    "caption": "punctuation.definition.caption.carve",
    "quote": "punctuation.definition.quote.carve",
}

# A `none` shape asserts the absence of every block marker scope, so a marker
# that starts being recognised anywhere shows up rather than only in the family
# someone thought to check.
NEGATIVE = " ".join(
    "-" + scope
    for scope in (
        "punctuation.definition.heading.carve",
        "punctuation.definition.list.begin.carve",
        "punctuation.definition.caption.carve",
        "punctuation.definition.quote.carve",
    )
)


def render():
    shapes = json.loads(BATTERY.read_text())["shapes"]
    out = [
        BEGIN,
        "#",
        "# Generated from tests/lib/block-battery.json, the table every Carve",
        "# grammar is checked against. Do not edit by hand: run",
        "# tools/generate-battery-tests.py and commit the result.",
        "#",
        "# `want` is what carve-rs renders.",
        "#",
    ]
    skipped = []
    covered = 0
    for shape in shapes:
        src = shape["src"]
        # A source line starting with `#` is indistinguishable from this file's
        # own comment and assertion prefix, and a literal tab does not survive
        # review. Those shapes are NAMED below rather than dropped, so the block
        # states what it does not cover.
        if src.startswith("#") or "\t" in src:
            skipped.append(src)
            continue
        if shape.get("why"):
            out.append("# " + shape["why"])
        out.append(src)
        out.append("# <- " + (NEGATIVE if shape["want"] == "none" else SCOPE[shape["want"]]))
        covered += 1

    if skipped:
        out += [
            "#",
            "# NOT covered here, because this file cannot express them:",
        ]
        for src in skipped:
            why = (
                "a line starting with `#` is this file's own comment prefix"
                if src.startswith("#")
                else "contains a literal tab"
            )
            out.append(f"#   {src!r} - {why}")
        out += [
            "# They are covered by the grammars that run the table directly:",
            "# carve-grammars, vscode-carve, intellij-carve, vim-carve, emacs-carve.",
        ]
    out.append(END)
    return "\n".join(out) + "\n", covered, len(skipped)


def main():
    text = TESTS.read_text()
    block, covered, skipped = render()
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n", re.S)
    updated = (
        pattern.sub(lambda _: block, text)
        if pattern.search(text)
        else text.rstrip("\n") + "\n\n" + block
    )

    if "--check" in sys.argv:
        if updated != text:
            print(
                "syntax_test_carve.crv is out of sync with the block battery.\n"
                "Run tools/generate-battery-tests.py and commit the result.",
                file=sys.stderr,
            )
            return 1
        print(
            f"generate-battery-tests: {covered} shape(s) asserted, "
            f"{skipped} not expressible here."
        )
        return 0

    TESTS.write_text(updated)
    print(
        f"generate-battery-tests: wrote {covered} shape(s), "
        f"{skipped} not expressible here."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
