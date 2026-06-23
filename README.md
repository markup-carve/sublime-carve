# Carve for Sublime Text

Syntax highlighting for the [Carve](https://en.wikipedia.org/wiki/Lightweight_markup_language)
markup language in Sublime Text 3 and 4.

Files with a `.crv` or `.carve` extension are highlighted automatically.

This package is authored from the maintained Carve TextMate grammar
(scope `text.carve`) so its scope names line up with existing color schemes.

## Features

- Headings (`#` ... `######`)
- Inline mnemonics: `/italic/`, `*bold*`, `_underline_`, `~strike~`,
  `=highlight=` (single `=`), `^sup^`, `,,sub,,`, `` `code` ``
- Links, autolinks (`<https://...>`, `<a@b.com>`), images, reference and
  cross-reference links, inline spans
- Lists, task lists (`- [ ]` / `- [x]`), ordered lists, definition lists (`:`)
- Block quotes (`>`)
- Fenced code with language plus the `#201` fence header `"header"` / `[label]`,
  and raw `=FORMAT` (`%%%`) fences
- Divs (`:::`) with admonition types and `"title"` / `[label]`
- Block and inline attributes (`{#id .class key="val"}`)
- Tables with `|`, `|=` header rows, `^` rowspan, `<` colspan, and GFM
  `|---|` delimiter rows
- Footnotes (`[^id]`)
- Math: inline `$`..`` `` ` ``, display `$$`..`` `` ` ``, and ```` ```math ```` fences
- Frontmatter (`---`, `---toml`, `---json`)
- Mentions (`@name`), tags (`#tag`), emoji (`:smile:`)
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

## Running the syntax tests

`syntax_test_carve.crv` uses Sublime's syntax-test format. Open it in Sublime
Text and run the build (**Tools > Build**, or **Build With... > Syntax Tests**
on ST4). The results appear in the build output panel.

## License

MIT. See [LICENSE](LICENSE).
