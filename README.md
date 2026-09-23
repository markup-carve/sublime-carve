# Carve for Sublime Text

Syntax highlighting for the [Carve](https://github.com/markup-carve/carve)
markup language in Sublime Text 3 and 4.

Files with a `.crv` extension are highlighted automatically.

This package is authored from the maintained Carve TextMate grammar
(scope `text.carve`) so its scope names line up with existing color schemes.

## Features

- Headings (`#` ... `######`)
- Inline mnemonics: `/italic/`, `*bold*`, `_underline_`, `~strike~`,
  `=highlight=` (single `=`), `{^sup^}`, `{,sub,}`, `` `code` ``
- Links, autolinks (`<https://...>`, `<a@b.com>`), reference and
  cross-reference links, inline spans
- Images in all three forms: `![alt](src)`, `![alt][ref]` and `![alt][]`
- Lists, task lists (`- [ ]` / `- [x]`), ordered lists, definition lists (`:`)
- Block quotes (`>`)
- Fenced code with language plus the fence header `"header"` / `[label]` -
  and the code inside is highlighted with Sublime's own syntax for that
  language (python, js/ts, rust, go, php, ruby, sql, shell, yaml, json,
  html, css and ~35 more)
- Raw passthrough fences (```` ```=html ````), kept verbatim and never
  highlighted as code
- Divs (`:::`) with `"title"` / `[label]`; the eight Tier-1 admonition types
  get a scope of their own, distinct from a custom container, and so do the
  bare `::: figure` composite-figure opener, the `::: |` line block and the
  `::: \` local hard-break block
- Block and inline attributes (`{#id .class key="val"}`)
- Tables with `|`, `|=` header rows, `^` rowspan, `<` colspan, and GFM
  `|---|` delimiter rows
- Footnotes: references (`[^id]`), inline notes (`^[text]`) and definitions
  (`[^id]: body`), whose body is inline content rather than a destination
- Hard line breaks (a trailing `\`)
- Math: inline `$`..`` `` ` ``, display `$$`..`` `` ` ``, and ```` ```math ```` fences
- Frontmatter (`---`, `---toml`, `---json`), highlighted with the declared
  format's own syntax
- Mentions (`@name`), tags (`#tag`), symbols (`:smile:`)
- Critic markup (`{+ins+}`, `{-del-}`, `{~a~>b~}`, `{#comment#}`)
- Line comments (`%%`), trailing comments, block comments (`%%%`) and
  delimited inline comments (`{% ... %}`)
- Every verbatim payload stays verbatim: nothing inside a code block, raw
  block, code span, inline literal, math span or comment is coloured as markup
- A bare delimiter never pairs across a link destination, an image source or
  an autolink (PART 9 §9 E2a), so `/see [x](http://a.b/c/) now/` is one italic
  run. One limit: a code span holding `]` inside a link label is not
  recognized, so that link does not shield its destination

## Install

### Package Control

1. Open the command palette (`Ctrl/Cmd+Shift+P`).
2. Run **Package Control: Install Package**.
3. Search for **Carve** and install it.

### Manual

1. Find your packages directory via **Preferences > Browse Packages...**.
2. Create a folder named `Carve` inside it.
3. Copy the contents of this repository into that folder.

## Recommended view settings

The package does not override any editor settings. Since Carve is
prose-oriented markup, settings like these tend to work well - open a `.crv`
file and pick **Preferences > Settings - Syntax Specific** to apply them for
Carve files only:

```json
{
    "tab_size": 2,
    "translate_tabs_to_spaces": true,
    "word_wrap": true,
    "spell_check": true,
    // Spell-check prose only: skip code spans, code blocks, raw passthrough,
    // math, links, and attribute values.
    "spelling_selector": "text.carve - markup.raw - meta.math - markup.underline.link - meta.attributes",
    "trim_trailing_white_space_on_save": false
}
```

`trim_trailing_white_space_on_save` matters more here than in most languages:
trailing spaces inside a Carve code block are content and render inside `<pre>`.

## Commands

Available from the command palette:

| Command | What it does |
|---|---|
| **Carve: Go to Cross-Reference Target** | Jumps from a `</#id>` under the cursor to the heading it points at (explicit `{#id}` attributes and derived heading slugs both resolve, case-insensitively, like Carve itself). |
| **Carve: Format Buffer (carve fmt)** | Runs `carve fmt` over the buffer. Formats unsaved content and keeps undo history. |
| **Carve: Import Markdown/HTML as .crv (carve migrate)** | Converts the current `.md` or `.html` file to a `.crv` next to it with `carve migrate --from markdown` or `--from html`, then opens the result. Asks before overwriting an existing `.crv`. Reads the file on disk, so save first. |

The import command is also in the sidebar context menu (**Carve: Import as .crv**)
when you right-click a single `.md`, `.markdown`, `.html` or `.htm` file.

Formatting and import need the `carve` CLI on PATH (`npm install -g @markup-carve/carve`
or `cargo install carve-lang`). The npm `carve` 0.1.7 currently exits without
output when started through its installed symlink, so import reports "produced
no output"; use the cargo build, or set `carve_binary` to a command list such as
`["node", "/path/to/@markup-carve/carve/dist/cli.js"]`. Configure in
**Preferences > Package Settings**:

```json
{
    "carve_binary": "carve",
    "carve_format_on_save": false
}
```

## Export to Markdown or HTML

Exporting goes the other way and comes from the language server, not this
package. Install [sublime-carve-lsp](https://github.com/markup-carve/sublime-carve-lsp)
and the **Export as Markdown** and **Export as HTML** code actions write
`notes.md` or `notes.html` next to `notes.crv`. They need a carve-lsp release
newer than 0.1.7.

## Build system

With a `.crv` file open, **Tools > Build** (`ctrl+b`) runs `carve lint` and the
reported problems are clickable, because carve prints `file:line:column`.
**Tools > Build With...** offers the other variants: lint the whole project,
`carve fmt --check`, `carve fmt -w`, render HTML to stdout or to a file, and an
ANSI terminal preview.

## Snippets

Tab triggers for the constructs that are tedious to type by hand: `note`
(admonition), `table`, `codegroup`, `listtable`, `figure` (image + caption),
`deflist`, `fn` (footnote + definition), `xref`, `code`, `fm` (frontmatter),
`math`, `spoiler`. Typing an admonition or extension name (`warning`, `tabs`,
`toc`, `mermaid`, ...) also offers a completion that expands the whole fence.

## Running the syntax tests

See the [development guide](docs/development.md) for running the syntax suite
locally and maintaining the package.
