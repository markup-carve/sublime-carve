"""Tests for the Lint build's include root (carve.py, outside Sublime).

The integration cases run a real carve CLI when CARVE_LINT_NEW (a CLI with
`lint --include-root`) or CARVE_LINT_OLD (one without) names its command line.
"""

import os
import re
import shlex
import subprocess
import sys
import tempfile
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeExec:
    def __init__(self, window):
        self.window = window
        self.output_view = None
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)


def load_carve():
    sublime = types.ModuleType("sublime")
    sublime_plugin = types.ModuleType("sublime_plugin")
    for name in ("TextCommand", "WindowCommand", "EventListener"):
        setattr(sublime_plugin, name, type(name, (), {}))
    default = types.ModuleType("Default")
    default_exec = types.ModuleType("Default.exec")
    default_exec.ExecCommand = FakeExec
    default.exec = default_exec
    sys.modules.update({
        "sublime": sublime,
        "sublime_plugin": sublime_plugin,
        "Default": default,
        "Default.exec": default_exec,
    })
    sys.path.insert(0, ROOT)
    import carve
    return carve


carve = load_carve()
SUPPORTS = carve.supports_include_root


class ResolveIncludeRoot(unittest.TestCase):
    file = os.path.join(os.sep, "w", "docs", "guide", "main.crv")

    def resolve(self, value, folders=()):
        return carve.resolve_include_root(value, self.file, list(folders))

    def test_project_picks_the_deepest_folder_holding_the_file(self):
        folders = [os.path.join(os.sep, "w"), os.path.join(os.sep, "w", "docs")]
        self.assertEqual(self.resolve("project", folders), (folders[1], None))
        self.assertEqual(self.resolve("project", folders[::-1]), (folders[1], None))

    def test_project_ignores_a_sibling_folder_sharing_a_prefix(self):
        folders = [os.path.join(os.sep, "w", "doc"), os.path.join(os.sep, "w")]
        self.assertEqual(self.resolve("project", folders), (folders[1], None))

    def test_project_without_a_containing_folder_uses_the_file_dir(self):
        file_dir = os.path.dirname(self.file)
        self.assertEqual(self.resolve("project"), (file_dir, None))
        self.assertEqual(self.resolve("project", [os.path.join(os.sep, "other")]), (file_dir, None))

    def test_file_dir(self):
        folders = [os.path.join(os.sep, "w")]
        self.assertEqual(self.resolve("file_dir", folders), (os.path.dirname(self.file), None))

    def test_false_passes_no_root(self):
        self.assertEqual(self.resolve(False, [os.path.join(os.sep, "w")]), (None, None))

    def test_an_explicit_absolute_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.resolve(tmp), (tmp, None))

    def test_an_invalid_value_falls_back_to_project_with_a_notice(self):
        folders = [os.path.join(os.sep, "w")]
        for value in ("relative/dir", os.path.join(os.sep, "no", "such", "dir"), 3):
            root, notice = self.resolve(value, folders)
            self.assertEqual(root, folders[0])
            self.assertIn("carve_lint_include_root", notice)


class LintCommand(unittest.TestCase):
    def test_supported_passes_the_root_and_runs_in_it(self):
        cmd, cwd = carve.lint_command(["carve"], "/w/docs/main.crv", "/w", True)
        self.assertEqual(shlex.split(cmd), ["carve", "lint", "--include-root", "/w", "/w/docs/main.crv"])
        self.assertEqual(cwd, "/w")

    def test_unsupported_or_disabled_lints_the_file_alone(self):
        for root, supported in (("/w", False), ("/w", None), (None, True)):
            cmd, cwd = carve.lint_command(["carve"], "/w/docs/main.crv", root, supported)
            self.assertEqual(shlex.split(cmd), ["carve", "lint", "/w/docs/main.crv"])
            self.assertEqual(cwd, "/w/docs")

    def test_a_command_list_and_spaces_are_quoted(self):
        cmd, _ = carve.lint_command(["node", "/a b/cli.js"], "/w/my doc.crv", "/w", True)
        self.assertEqual(shlex.split(cmd), ["node", "/a b/cli.js", "lint", "--include-root", "/w", "/w/my doc.crv"])


class FakeSettings(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class FakeView:
    def __init__(self, path, settings):
        self.path = path
        self._settings = FakeSettings(settings)

    def file_name(self):
        return self.path

    def settings(self):
        return self._settings


class FakeWindow:
    def __init__(self, view, folders):
        self.view = view
        self._folders = folders

    def active_view(self):
        return self.view

    def folders(self):
        return self._folders


class Cancel(unittest.TestCase):
    def setUp(self):
        self.queued = []
        carve.sublime.set_timeout_async = lambda fn, delay=0: self.queued.append(fn)
        carve.sublime.set_timeout = lambda fn, delay=0: fn()
        carve.sublime.load_settings = lambda name: FakeSettings()
        carve.supports_include_root = lambda command, root, env=None: True
        view = FakeView("/w/docs/main.crv", {"carve_binary": "carve"})
        self.command = carve.CarveLintCommand(FakeWindow(view, ["/w"]))

    def tearDown(self):
        carve.supports_include_root = SUPPORTS

    def test_a_probe_finishing_after_cancel_starts_nothing(self):
        self.command.run()
        self.command.run(kill=True)
        self.queued.pop(0)()
        self.assertEqual(self.command.calls, [{"kill": True}])

    def test_a_probe_finishing_uncancelled_starts_the_lint(self):
        self.command.run(env={"A": "1"})
        self.queued.pop(0)()
        call = self.command.calls[0]
        self.assertEqual(call["working_dir"], "/w")
        self.assertEqual(call["env"], {"A": "1"})
        self.assertIn("--include-root", call["shell_cmd"])


class ShellJoin(unittest.TestCase):
    def test_windows_quotes_every_argument(self):
        self.assertEqual(
            carve.shell_join(["carve", "lint", "--include-root", "C:\\", "C:\\a&b\\x.crv"], windows=True),
            '"carve" "lint" "--include-root" "C:\\." "C:\\a&b\\x.crv"',
        )

    def test_posix_quotes_metacharacters(self):
        self.assertEqual(shlex.split(carve.shell_join(["carve", "/a&b/x;y.crv"], windows=False)), ["carve", "/a&b/x;y.crv"])


@unittest.skipIf(os.name == "nt", "uses a POSIX shell script")
class ProbeTimeout(unittest.TestCase):
    def test_a_hung_cli_is_killed_with_its_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = os.path.join(tmp, "child.pid")
            cli = os.path.join(tmp, "carve")
            with open(cli, "w", encoding="utf-8") as handle:
                handle.write("#!/bin/sh\nsleep 60 &\necho $! > %s\nwait\n" % marker)
            os.chmod(cli, 0o755)
            real = subprocess.Popen.communicate

            def short(self, input=None, timeout=None):
                return real(self, input, timeout=1 if timeout else None)

            subprocess.Popen.communicate = short
            try:
                self.assertIsNone(carve.supports_include_root([cli], tmp, dict(os.environ)))
            finally:
                subprocess.Popen.communicate = real
            with open(marker, encoding="utf-8") as handle:
                child = int(handle.read())
            with self.assertRaises(OSError):
                for _ in range(50):
                    os.kill(child, 0)
                    __import__("time").sleep(0.05)


class BuildEnv(unittest.TestCase):
    def test_path_then_env_then_view_build_env(self):
        os.environ["CARVE_TEST_BASE"] = "/base"
        env = carve.build_env(
            env={"A": "env", "B": "env"},
            path="/x:$CARVE_TEST_BASE",
            view_env={"B": "view"},
        )
        self.assertEqual(env["PATH"], "/x:/base")
        self.assertEqual((env["A"], env["B"]), ("env", "view"))


def make_project(tmp):
    def write(rel, text):
        with open(os.path.join(tmp, rel), "w", encoding="utf-8") as handle:
            handle.write(text)

    os.makedirs(os.path.join(tmp, "docs", "parts"))
    os.makedirs(os.path.join(tmp, "shared"))
    write("docs/main.crv", "# Main\n\n{{ parts/a.crv }}\n\n{{ ../shared/s.crv }}\n")
    write("docs/parts/a.crv", "Bad **bold** here.\n\n{{ b.crv }}\n")
    write("docs/parts/b.crv", "Nested </#nope>.\n")
    write("shared/s.crv", "Shared ~~strike~~.\n")
    return os.path.join(tmp, "docs", "main.crv")


def run_lint(command, folders, main):
    root, _ = carve.resolve_include_root("project", main, folders)
    supported = carve.supports_include_root(command, root)
    shell_cmd, cwd = carve.lint_command(command, main, root, supported)
    argv, shell = carve.shell_argv(shell_cmd)
    out = subprocess.run(argv, shell=shell, cwd=cwd, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT).stdout.decode("utf-8")
    regex = re.compile(carve.LINT_FILE_REGEX)
    hits = [regex.match(line) for line in out.splitlines()]
    return supported, cwd, out, [m for m in hits if m]


@unittest.skipUnless(os.environ.get("CARVE_LINT_NEW"), "CARVE_LINT_NEW not set")
class WithIncludeRoot(unittest.TestCase):
    def test_findings_in_included_files_resolve_from_the_build_dir(self):
        command = shlex.split(os.environ["CARVE_LINT_NEW"])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            main = make_project(tmp)
            supported, cwd, out, hits = run_lint(command, [tmp], main)
            self.assertIs(supported, True)
            self.assertEqual(cwd, tmp)
            files = {os.path.normpath(os.path.join(cwd, m.group(1))) for m in hits}
            expected = {os.path.join(tmp, p) for p in ("docs/parts/a.crv", "docs/parts/b.crv", "shared/s.crv")}
            self.assertEqual(files, expected, out)
            nested = [m for m in hits if m.group(1).endswith("b.crv")]
            self.assertRegex(nested[0].group(4), r"\(included from .*main\.crv:3:1 > .*a\.crv:3:1\)$")


    def test_the_probe_finds_the_cli_on_the_build_path(self):
        bindir = os.path.dirname(os.path.abspath(shlex.split(os.environ["CARVE_LINT_NEW"])[0]))
        env = carve.build_env(path=bindir + os.pathsep + os.environ["PATH"])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIs(carve.supports_include_root(["carve"], tmp, env), True)


@unittest.skipUnless(os.environ.get("CARVE_LINT_OLD"), "CARVE_LINT_OLD not set")
class WithoutIncludeRoot(unittest.TestCase):
    def test_an_older_cli_lints_without_the_flag(self):
        command = shlex.split(os.environ["CARVE_LINT_OLD"])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            main = make_project(tmp)
            supported, cwd, out, hits = run_lint(command, [tmp], main)
            self.assertIs(supported, False)
            self.assertEqual(cwd, os.path.dirname(main))
            self.assertNotIn("nknown option", out)
            self.assertEqual(hits, [], out)


if __name__ == "__main__":
    unittest.main()
