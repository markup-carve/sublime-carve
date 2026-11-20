# Carve 0.2 in Sublime Text

Open a `.crv` file to use the `Carve` syntax. The package highlights Carve 0.2 block and inline forms, plus the fence languages listed in `tools/fence-languages.json`.

The command palette provides linting, formatting, importing, navigation, and PDF export. Set `carve_binary` in `Carve.sublime-settings` when the `carve` executable is outside `PATH`. The lint commands can follow includes from the project folder when `carve_lint_include_root` is enabled.

The syntax tests in `syntax_test_carve.crv` check the 0.2 grammar. Use the headless Sublime syntax test runner or CI to run them.
