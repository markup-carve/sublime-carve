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
- Links, autolinks (`<https://...>`, `<a@b.com>`), images, reference and
  cross-reference links, inline spans
- Lists, task lists (`- [ ]` / `- [x]`), ordered lists, definition lists (`:`)
- Block quotes (`>`)
- Fenced code with language plus the fence header `"header"` / `[label]` -
  and the code inside is highlighted with Sublime's own syntax for that
  language (python, js/ts, rust, go, php, ruby, sql, shell, yaml, json,
  html, css and ~35 more)
- Raw passthrough fences (```` ```=html ````), kept verbatim and never
  highlighted as code
- Divs (`:::`) with admonition types and `"title"` / `[label]`
- Block and inline attributes (`{#id .class key="val"}`)
- Tables with `|`, `|=` header rows, `^` rowspan, `<` colspan, and GFM
  `|---|` delimiter rows
- Footnotes (`[^id]`)
- Math: inline `$`..`` `` ` ``, display `$$`..`` `` ` ``, and ```` ```math ```` fences
- Frontmatter (`---`, `---toml`, `---json`), highlighted with the declared
  format's own syntax
- Mentions (`@name`), tags (`#tag`), symbols (`:smile:`)
- Critic markup (`{+ins+}`, `{-del-}`, `{~a~>b~}`, `{#comment#}`)
- Line comments (`%%`) and block comments (`%%%`)

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

Both need the `carve` CLI on PATH for formatting (`npm install -g @markup-carve/carve`
or `cargo install carve-lang`). Configure in **Preferences > Package Settings**:

```json
{
    "carve_binary": "carve",
    "carve_format_on_save": false
}
```

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

`syntax_test_carve.crv` uses Sublime's syntax-test format, and CI runs it on
every push via [SublimeText/syntax-test-action](https://github.com/SublimeText/syntax-test-action).

To run it locally **without a GUI**, use Sublime's headless test runner:

```bash
# match <BUILD> to your Sublime build (Help > About)
curl -sSLO https://download.sublimetext.com/st_syntax_tests_build_4200_x64.tar.xz
tar xf st_syntax_tests_build_4200_x64.tar.xz
cd st_syntax_tests
mkdir -p Data/Packages/Carve && cp -r /path/to/sublime-carve/* Data/Packages/Carve/
./syntax_tests
```

Fenced code embeds Sublime's bundled language syntaxes, so to exercise those
assertions the runner also needs the default packages: download
`https://github.com/sublimehq/Packages/archive/v<BUILD>.tar.gz` and copy its
folders into `Data/Packages/` (this is what CI's `default_packages: binary`
does). Inside Sublime itself, the tests also run from **Build With... > Syntax
Tests**.

## License

MIT. See [LICENSE](LICENSE).
