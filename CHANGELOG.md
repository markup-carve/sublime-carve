# Changelog

All notable changes to the Carve package for Sublime Text are documented in
this file. The per-release notes Package Control shows live in `messages/`.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Releases before 0.1.8 are described on the
[releases page](https://github.com/markup-carve/sublime-carve/releases).

## [Unreleased]

## [0.1.8] - 2026-10-08

### Fixed

- **Carve: Go to Cross-Reference Target** jumps to a heading only when its id
  matches the reference's own case. Its lowercased fallback sent `</#plan>` to
  a heading written `{#Plan}`; names compare case exactly from Carve 0.1.8, so
  the command reports that there is no heading with that id instead. The README
  row that described case-insensitive resolution is updated to match (#62).
