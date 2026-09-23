#!/usr/bin/env python3
"""Derive the list-item fence contexts from `code-blocks`.

A fence inside a list item needs the same per-language embeds as a fence at
document level, but a different opener (a marker line or an indent) and a
different closer (the item's boundary). `code-blocks` stays the hand-edited
source of truth; this script copies its language table into the two container
contexts, and `--check` fails when they drift.

Run with no arguments to rewrite the generated block in place.
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SYNTAX = ROOT / "Carve.sublime-syntax"

BEGIN = "  # --- BEGIN GENERATED CONTAINER FENCES (tools/generate-container-fences.py) ---"
END = "  # --- END GENERATED CONTAINER FENCES ---"

LANGUAGE = re.compile(r"^\^\(\(`\|~\)\\2\{2,\}\)\[ \\t\]\*\(([^()]+)\)\\b\(\.\*\)\$$")

# Groups 1-6 (indent, bullet, ordered, definition, glued attribute block,
# task) come first, so the fence is group 7 and its character group 8. The
# attribute block is spelled as `lists` spells it: a quoted value may hold `}`.
MARKER_LINE = (
    r"^([ \t]*)(?:([-*])|([0-9]+[.)]|[A-Za-z][.)]|[ivxlcdm]+[.)]|[IVXLCDM]+[.)]|\.)|(:))"
    r"""(\{(?:"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|[^}"'\n])*\})?"""
    r" +(\[[ xX\-_>?]\] +)?((`|~)\8{2,})[ \t]*"
)
MARKER_CAPTURES = [
    "2: markup.list.unnumbered.carve punctuation.definition.list.begin.carve",
    "3: markup.list.numbered.carve punctuation.definition.list.begin.carve",
    "4: markup.list.definition.carve punctuation.definition.list.begin.carve",
    "5: meta.attributes.carve",
    "6: constant.language.task-list.carve",
    "7: punctuation.definition.raw.begin.carve",
]
# The closer is indented; a non-blank line that does not reach past the
# marker's own indent is the item's boundary and ends an unclosed fence.
MARKER_ESCAPE = r"^[ \t]+(\7\8*)\s*$|^(?![ \t]*$)(?!\1[ \t])"

BODY = r"^([ \t]+)((`|~)\3{2,})[ \t]*"
# The body sits AT the opener's indent, so the boundary is a line that does
# not reach it.
BODY_ESCAPE = r"^[ \t]+(\2\3*)\s*$|^(?![ \t]*$)(?!\1)"


def languages():
    data = yaml.safe_load(SYNTAX.read_text(encoding="utf-8"))
    out = []
    for rule in data["contexts"]["code-blocks"]:
        if "embed" not in rule:
            continue
        match = LANGUAGE.match(rule["match"])
        if not match:
            raise SystemExit(f"code-blocks rule not in the expected shape: {rule['match']}")
        out.append((match.group(1), rule["embed"]))
    return out


def quote(regex):
    return "'" + regex.replace("'", "''") + "'"


def emit(lines, opener, captures, lang_group, header_group, escape):
    for names, embed in languages():
        match = quote(opener + "(" + names + r")\b(.*)$")
        lines += [
            f"    - match: {match}",
            "      captures:",
            *(f"        {c}" for c in captures),
            f"        {lang_group}: entity.name.type.language.carve",
            f"        {header_group}: meta.code-fence.header.carve",
            f"      embed: {embed}",
            "      embed_scope: markup.raw.block.fenced.code.carve",
            f"      escape: {quote(escape)}",
            "      escape_captures:",
            "        1: punctuation.definition.raw.end.carve",
        ]
    # No language: a `=FORMAT` info string is a raw block, not a code fence.
    closer, boundary = escape.split("|", 1)
    match = quote(opener + r"(?!=)([^`~\s]+)?(.*)$")
    lines += [
        f"    - match: {match}",
        "      captures:",
        *(f"        {c}" for c in captures),
        f"        {lang_group}: entity.name.type.language.carve",
        f"        {header_group}: meta.code-fence.header.carve",
        "      push:",
        "        - meta_scope: markup.raw.block.fenced.code.carve",
        f"        - match: {quote(closer)}",
        "          captures:",
        "            1: punctuation.definition.raw.end.carve",
        "          pop: true",
        f"        - match: {quote(boundary)}",
        "          pop: true",
    ]


def render():
    lines = [
        BEGIN,
        "  # Do not edit by hand: change `code-blocks` and run the script.",
        "  code-blocks-on-a-marker-line:",
    ]
    emit(lines, MARKER_LINE, MARKER_CAPTURES, 9, 10, MARKER_ESCAPE)
    lines += ["", "  code-blocks-at-a-body-column:"]
    emit(
        lines,
        BODY,
        ["2: punctuation.definition.raw.begin.carve"],
        4,
        5,
        BODY_ESCAPE,
    )
    lines.append(END)
    return "\n".join(lines) + "\n"


def main():
    text = SYNTAX.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n", re.S)
    if not pattern.search(text):
        raise SystemExit("No generated container-fence block in Carve.sublime-syntax")
    block = render()
    updated = pattern.sub(lambda _: block, text)
    if "--check" in sys.argv:
        if updated != text:
            print(
                "Carve.sublime-syntax container fences are out of sync with code-blocks.\n"
                "Run tools/generate-container-fences.py and commit the result.",
                file=sys.stderr,
            )
            return 1
        print(f"generate-container-fences: {len(languages())} language(s) in sync.")
        return 0
    SYNTAX.write_text(updated, encoding="utf-8")
    print(f"generate-container-fences: wrote {len(languages())} language(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
