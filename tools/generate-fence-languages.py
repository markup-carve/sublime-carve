#!/usr/bin/env python3
"""Generate the fenced-code language rules from tools/fence-languages.json.

The table is carve-grammars' `fence-languages/fence-languages.json`, vendored
byte for byte (tools/check-fence-languages-drift.sh compares it). Every row
with a `sublime` embed becomes one rule in each fence position:

- `code-blocks`, a fence at document level;
- `code-blocks-on-a-marker-line`, a fence on a list item's marker line;
- `code-blocks-at-a-body-column`, a fence at a list item's body column.

The two container contexts need a different opener (a marker line or an
indent) and a different closer (the item's boundary), so they are generated
whole; `code-blocks` keeps its hand-written no-language fallback after the
generated rules.

Run with no arguments to rewrite the generated blocks in place; `--check`
exits 1 when they are stale.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYNTAX = ROOT / "Carve.sublime-syntax"
TABLE = ROOT / "tools" / "fence-languages.json"

DOC_BEGIN = "    # --- BEGIN GENERATED FENCE LANGUAGES (tools/generate-fence-languages.py) ---"
DOC_END = "    # --- END GENERATED FENCE LANGUAGES ---"
BEGIN = "  # --- BEGIN GENERATED CONTAINER FENCES (tools/generate-fence-languages.py) ---"
END = "  # --- END GENERATED CONTAINER FENCES ---"

# The language token ends where grammar.ebnf's `language_info` class ends, not
# at `\b`: `c\+\+\b` can never match, and `c\b` claimed `c++` and `c#`.
BOUNDARY = r"(?![\w+#./-])"

DOC_OPENER = r"^((`|~)\2{2,})[ \t]*"
DOC_CAPTURES = ["1: punctuation.definition.raw.begin.carve"]
DOC_ESCAPE = r"^(\1\2*)\s*$"

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

SPECIALS = set("\\.^$|?*+()[]{}")


def languages():
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    out = []
    for row in table["languages"]:
        embed = row["sublime"]
        if embed is None:
            continue
        words = "|".join("".join("\\" + c if c in SPECIALS else c for c in w) for w in row["words"])
        out.append((f"(?i:{words})", embed))
    return out


def quote(regex):
    return "'" + regex.replace("'", "''") + "'"


def emit(lines, indent, opener, captures, lang_group, header_group, escape, note=False):
    pad = " " * indent
    for names, embed in languages():
        lines += [
            f"{pad}- match: {quote(opener + '(' + names + ')' + BOUNDARY + '(.*)$')}",
            f"{pad}  captures:",
            *(f"{pad}    {c}" for c in captures),
            f"{pad}    {lang_group}: entity.name.type.language.carve",
            f"{pad}    {header_group}: meta.code-fence.header.carve",
        ]
        if note and embed == "document":
            lines += [
                f"{pad}  # Not `main`: main's `set` swaps out the embed's base and the outer",
                f"{pad}  # fence then closes on an inner one.",
            ]
        lines += [
            f"{pad}  embed: {embed}",
            f"{pad}  embed_scope: markup.raw.block.fenced.code.carve",
            f"{pad}  escape: {quote(escape)}",
            f"{pad}  escape_captures:",
            f"{pad}    1: punctuation.definition.raw.end.carve",
        ]


def emit_container(lines, opener, captures, lang_group, header_group, escape):
    emit(lines, 4, opener, captures, lang_group, header_group, escape)
    # No language: a `=FORMAT` info string is a raw block, not a code fence.
    closer, boundary = escape.split("|", 1)
    lines += [
        f"    - match: {quote(opener + r'(?!=)([^`~\s]+)?(.*)$')}",
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


def render_document():
    lines = [DOC_BEGIN, "    # Do not edit by hand: change tools/fence-languages.json and run the script."]
    emit(lines, 4, DOC_OPENER, DOC_CAPTURES, 3, 4, DOC_ESCAPE, note=True)
    lines.append(DOC_END)
    return "\n".join(lines) + "\n"


def render_containers():
    lines = [
        BEGIN,
        "  # Do not edit by hand: change tools/fence-languages.json and run the script.",
        "  code-blocks-on-a-marker-line:",
    ]
    emit_container(lines, MARKER_LINE, MARKER_CAPTURES, 9, 10, MARKER_ESCAPE)
    lines += ["", "  code-blocks-at-a-body-column:"]
    emit_container(lines, BODY, ["2: punctuation.definition.raw.begin.carve"], 4, 5, BODY_ESCAPE)
    lines.append(END)
    return "\n".join(lines) + "\n"


def splice(text, begin, end, block):
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end) + r"\n", re.S)
    if len(pattern.findall(text)) != 1:
        raise SystemExit(f"Expected exactly one block starting {begin.strip()!r} in {SYNTAX.name}")
    return pattern.sub(lambda _: block, text)


def main():
    text = SYNTAX.read_text(encoding="utf-8")
    updated = splice(text, DOC_BEGIN, DOC_END, render_document())
    updated = splice(updated, BEGIN, END, render_containers())
    count = len(languages())
    if "--check" in sys.argv:
        if updated != text:
            print(
                "Carve.sublime-syntax fence languages are out of sync with tools/fence-languages.json.\n"
                "Run tools/generate-fence-languages.py and commit the result.",
                file=sys.stderr,
            )
            return 1
        print(f"generate-fence-languages: {count} language row(s) in sync.")
        return 0
    SYNTAX.write_text(updated, encoding="utf-8")
    print(f"generate-fence-languages: wrote {count} language row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
