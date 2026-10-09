# Development

## Syntax tests

`syntax_test_carve.crv` uses Sublime's syntax-test format. CI runs it on every
push through
[SublimeText/syntax-test-action](https://github.com/SublimeText/syntax-test-action).

To run the suite locally without a GUI, use Sublime's headless test runner:

```bash
# Match <BUILD> to your Sublime build (Help > About).
curl -sSLO https://download.sublimetext.com/st_syntax_tests_build_<BUILD>_x64.tar.xz
tar xf st_syntax_tests_build_<BUILD>_x64.tar.xz
cd st_syntax_tests
mkdir -p Data/Packages/Carve
cp -r /path/to/sublime-carve/* Data/Packages/Carve/
./syntax_tests
```

Fenced code embeds Sublime's bundled language syntaxes. To exercise those
assertions, download
`https://github.com/sublimehq/Packages/archive/v<BUILD>.tar.gz` and copy its
folders into `Data/Packages/`; CI's `default_packages: binary` performs the
equivalent setup.

Inside Sublime, run the tests through **Build With... > Syntax Tests**.

## Fence languages

Which syntax a fenced code block embeds is not written by hand. The rules come
from `tools/fence-languages.json`, a byte-for-byte copy of carve-grammars'
`fence-languages/fence-languages.json`, the shared table every Carve editor
grammar embeds from. Each row whose `sublime` column is set becomes one rule in
each fence position: `code-blocks` (document level),
`code-blocks-on-a-marker-line` and `code-blocks-at-a-body-column` (inside list
items). Everything between the `BEGIN GENERATED` and `END GENERATED` comments in
`Carve.sublime-syntax` is overwritten.

To add or change a language, change the table in carve-grammars first, then
re-copy it here and regenerate:

```bash
cp ../carve-grammars/fence-languages/fence-languages.json tools/
python3 tools/generate-fence-languages.py
```

CI runs `tools/generate-fence-languages.py --check`, which fails when the
syntax is stale against the table, and `tools/check-fence-languages-drift.sh`,
which fails when the copy differs from carve-grammars `main` (set
`CARVE_GRAMMARS_DIR` to compare against a local checkout instead).
