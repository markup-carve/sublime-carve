# Changelog

All notable changes to the Carve package for Sublime Text are documented in
this file. The per-release notes Package Control shows live in `messages/`.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Releases before 0.1.8 are described on the
[releases page](https://github.com/markup-carve/sublime-carve/releases).

## [Unreleased]

### Added

- More fence languages are highlighted: `bibtex`/`bib`, `d`, `erb`, `haml`,
  `objcpp`/`objective-cpp`, and new aliases for existing languages (`c#`,
  `objective-c`, `h`, `hpp`, `mjs`, `cjs`, `mts`, `cts`, `py3`, `jsonc`,
  `json5`, `htm`, `xhtml`, `svg`, `xsd`, `xsl`, `xslt`, `cljs`, `edn`,
  `gradle`, `cmd`). The list now comes from the fence-language table shared
  by every Carve editor grammar.
- A fence's language word matches in any case, so ```` ```Python ```` embeds
  Python.

### Fixed

- A ```` ```c++ ```` fence is highlighted as C++, and ```` ```c# ```` as C#.
  Both were highlighted as C, with `++` or `#` shown as the fence header.
- A language word only matches as a whole info-string token: ```` ```python-x ````
  is no longer highlighted as Python.

## [0.1.8] - 2026-10-08

### Fixed

- **Carve: Go to Cross-Reference Target** jumps to a heading only when its id
  matches the reference's own case. Its lowercased fallback sent `</#plan>` to
  a heading written `{#Plan}`; names compare case exactly from Carve 0.1.8, so
  the command reports that there is no heading with that id instead. The README
  row that described case-insensitive resolution is updated to match (#62).
