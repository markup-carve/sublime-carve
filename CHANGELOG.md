# Changelog

All notable changes to the Carve package for Sublime Text are documented in
this file. The per-release notes Package Control shows live in `messages/`.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Releases before 0.1.8 are described on the
[releases page](https://github.com/markup-carve/sublime-carve/releases).

## [Unreleased]

## [0.1.12] - 2026-10-23

### Improvements

- The Lint build follows `{{ path }}` includes: it passes `--include-root`
  (the deepest project folder holding the file, else the file's directory),
  and findings in included files are clickable and show their include chain.
  The new `carve_lint_include_root` setting picks the root or turns this off.
  Needs carve-js 0.1.13 or carve-rs 0.1.11; an older `carve` lints as before
  with a one-line notice (#87).
- The Lint build runs the CLI set in `carve_binary`, like the format and
  import commands (#87).
- The Lint Project build follows includes too, with the folder being linted
  as the include root, and also runs `carve_binary`.

## [0.1.11] - 2026-10-23

### Breaking

- Sublime Text 4, build 4050 or later, is required. The continuation-marker
  rule reads the line below a lone `+`, which needs `branch_point`/`fail`
  from build 4050. On Sublime Text 3, keep Carve 0.1.10 (#77).

### Fixed

- A lone `+` is a continuation marker only when the next line attaches at the
  open item's, description's, footnote's or quote's column. Before a blank
  line, a sibling item or at the item's content column it is text (#77).
- Glued quote prefixes `>+`, `>>+`, `> >+` and `>> +` are text, not quote
  lines or markers; `> +` and `> > +` stay markers (#77, #78).
- A colon line with no term above it is text, in a quote or out of it (#77).
- A quoted item's `+` is scoped after blank quote lines and two or three
  quotes deep (#80).
- A quote's first-line `+` followed by an indented quote line stays text (#83).
- An indented `> +` outside a list item is text, since that line opens no
  quote (#84).
- A first-block `+` after a quoted chain such as `> - > +` is text when a list
  or a blank line follows, and a `+` at column 0 below an item's indented
  quote is read at the item's column, so a list next leaves it text (#85).
- A top-level indented `>` line is paragraph text, and so is a `+` below it.
  Under a footnote, an indented `> +` is a marker when a block follows at the
  quote's column (#86).
- The **Lint Project** build works on Windows (#79, #81).

### Added

- `csv` and `tsv` fence bodies are highlighted: separators, quoted and
  unquoted fields, doubled quotes and the header row (#75, #76).

## [0.1.10] - 2026-10-15

### Fixed

- Front matter with no closing `---` ends at the first line no YAML mapping
  starts, instead of the rest of the document turning into YAML (#73).
- An inline note ends at the end of its paragraph, so an unclosed `^[` no
  longer runs to the next `]` anywhere in the document (#73).
- A stray `{` mid-line opens no attribute block without its `}` on the line (#73).
- A list marker or `^ ` line after a paragraph is prose, a marker after a list
  item's lazy continuation still opens the next item, and a `^ ` line after a
  heading or after a paragraph and a blank line is no caption (#73).
- Headings, list markers, definitions, tables and container fences are scoped
  inside `> ` quotes, and a quoted fence keeps its body as code until its
  closer or the end of the quote (#73).
- A colon container's closer ends a fence or other block left open inside it (#73).
- Bold and strikethrough need a word boundary outside their delimiters
  (`2*3*4`, `a~b~c` stay text) (#73).
- Every ASCII punctuation character escapes (`\$`, `\"`, `\&`, `\:`, `\;`,
  `\?` were missing), `==x==` is no longer highlighted, `-->` and `==>` are
  typography and `=>` is not (#73).
- A `|` line needs its closing pipe to be a table row (#73).
- An unpartnered backtick run is code to the end of its paragraph, and a span
  may close on a later line of it (#73).
- A line of unclosed brackets is no longer quadratic: link labels nest three
  deep instead of recursing, and a label stops at a bare `[` (#73).

## [0.1.9] - 2026-10-14

### Fixed

- A `^ text` line before the first block remains prose (#70).
- A ```` ```c++ ```` fence is highlighted as C++, and ```` ```c# ```` as C#.
  Both were highlighted as C, with `++` or `#` shown as the fence header (#67).
- A language word only matches as a whole info-string token: ```` ```python-x ````
  is no longer highlighted as Python (#67).

### Added

- More fence languages are highlighted: `bibtex`/`bib`, `d`, `erb`, `haml`,
  `objcpp`/`objective-cpp`, and new aliases for existing languages (`c#`,
  `objective-c`, `h`, `hpp`, `mjs`, `cjs`, `mts`, `cts`, `py3`, `jsonc`,
  `json5`, `htm`, `xhtml`, `svg`, `xsd`, `xsl`, `xslt`, `cljs`, `edn`,
  `gradle`, `cmd`). The list now comes from the fence-language table shared
  by every Carve editor grammar (#67).
- A fence's language word matches in any case, so ```` ```Python ```` embeds
  Python (#67).

## [0.1.8] - 2026-10-08

### Fixed

- **Carve: Go to Cross-Reference Target** jumps to a heading only when its id
  matches the reference's own case. Its lowercased fallback sent `</#plan>` to
  a heading written `{#Plan}`; names compare case exactly from Carve 0.1.8, so
  the command reports that there is no heading with that id instead. The README
  row that described case-insensitive resolution is updated to match (#62).
