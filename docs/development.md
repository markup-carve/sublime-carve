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
