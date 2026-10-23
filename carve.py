"""Sublime Text commands for Carve documents.

Two things Carve's own constructs make possible and that plain highlighting
cannot do:

* Cross-references are first-class in Carve (`</#id>` fills its link text from
  the target heading), so they should be navigable like code symbols.
* `carve fmt` is a canonical formatter whose output is byte-identical across
  the three engines, so formatting a buffer is safe and deterministic.

All commands are opt-in; nothing here runs on its own.
"""

import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys

import sublime
import sublime_plugin
from Default.exec import ExecCommand

SETTINGS_FILE = "Carve.sublime-settings"

# `{#id}` on a block-attribute line, and the id slug carve derives from a
# heading when none is given.
ATTR_ID_RE = re.compile(r"\{[^}\n]*#([^\s}]+)[^}\n]*\}")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CROSSREF_RE = re.compile(r"</#([^>\s]+)>")

IMPORT_FORMATS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
}


def setting(view, key, default):
    """Read a setting, letting a view or project override the package default.

    Sublime merges project settings into view settings, so checking the view
    first is what lets a project pin its own carve build (a repo checkout, a
    pinned version) without changing the user's global preference.
    """
    if view is not None:
        value = view.settings().get(key)
        if value is not None:
            return value
    return sublime.load_settings(SETTINGS_FILE).get(key, default)


def carve_binary(view=None):
    """The `carve` executable: view/project setting, else package setting."""
    return setting(view, "carve_binary", "carve")


def carve_command(binary):
    """`carve_binary` as an argv prefix; a list allows e.g. ["node", ".../cli.js"]."""
    return list(binary) if isinstance(binary, list) else [binary]


def slugify(text):
    """Carve's heading-id slug: case-preserving, GitHub-style."""
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip()
    return re.sub(r"\s+", "-", text)


def heading_ids(view):
    """Map every reachable heading id in the view to its row.

    An explicit `{#id}` attribute line binds to the heading on the NEXT line;
    a heading with no attribute line binds to its slug.
    """
    ids = {}
    lines = view.substr(sublime.Region(0, view.size())).split("\n")
    pending_id = None
    for row, line in enumerate(lines):
        heading = HEADING_RE.match(line)
        if heading:
            if pending_id is not None:
                ids.setdefault(pending_id, row)
                pending_id = None
            ids.setdefault(slugify(heading.group(2)), row)
            continue
        attr = ATTR_ID_RE.match(line.strip())
        pending_id = attr.group(1) if attr else None
    return ids


class CarveGotoCrossrefCommand(sublime_plugin.TextCommand):
    """Jump from `</#id>` to the heading it points at."""

    def run(self, edit):
        target = self.crossref_under_cursor()
        if not target:
            sublime.status_message("Carve: no cross-reference under the cursor")
            return

        row = heading_ids(self.view).get(target)
        if row is None:
            sublime.status_message("Carve: no heading with id '%s'" % target)
            return

        point = self.view.text_point(row, 0)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(point))
        self.view.show_at_center(point)

    def crossref_under_cursor(self):
        for region in self.view.sel():
            line = self.view.line(region.begin())
            text = self.view.substr(line)
            offset = region.begin() - line.begin()
            for match in CROSSREF_RE.finditer(text):
                if match.start() <= offset <= match.end():
                    return match.group(1)
        return None

    def is_enabled(self):
        return self.view.match_selector(0, "text.carve")


class CarveFormatCommand(sublime_plugin.TextCommand):
    """Run `carve fmt` over the buffer and replace it with the result.

    Formats the buffer contents (not the file on disk), so it works on unsaved
    changes and leaves the undo history intact.
    """

    def run(self, edit):
        source = self.view.substr(sublime.Region(0, self.view.size()))
        binary = carve_binary(self.view)
        try:
            proc = subprocess.Popen(
                carve_command(binary) + ["fmt"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(self.view.file_name() or "") or None,
                startupinfo=_startupinfo(),
            )
            out, err = proc.communicate(source.encode("utf-8"), timeout=15)
        except FileNotFoundError:
            sublime.error_message(
                "Carve: '%s' not found on PATH.\n\n"
                "Install it (npm install -g @markup-carve/carve) or set "
                "\"carve_binary\" in settings (package, project, or view)." % carve_command(binary)[0]
            )
            return
        except subprocess.TimeoutExpired:
            proc.kill()
            sublime.error_message("Carve: 'carve fmt' timed out")
            return

        if proc.returncode != 0:
            sublime.error_message(
                "Carve: 'carve fmt' failed\n\n%s" % err.decode("utf-8", "replace").strip()
            )
            return

        formatted = out.decode("utf-8")
        if formatted == source:
            sublime.status_message("Carve: already formatted")
            return

        self.view.replace(edit, sublime.Region(0, self.view.size()), formatted)
        sublime.status_message("Carve: formatted")

    def is_enabled(self):
        return self.view.match_selector(0, "text.carve")


class CarveFormatOnSave(sublime_plugin.EventListener):
    """Optional format-on-save, off unless "carve_format_on_save" is true."""

    def on_pre_save(self, view):
        if not view.match_selector(0, "text.carve"):
            return
        if not setting(view, "carve_format_on_save", False):
            return
        view.run_command("carve_format")


def import_format(path):
    """The `carve migrate --from` format for a path, or None."""
    if not path:
        return None
    return IMPORT_FORMATS.get(os.path.splitext(path)[1].lower())


class CarveImportCommand(sublime_plugin.WindowCommand):
    """Convert a Markdown or HTML file to a sibling .crv via `carve migrate`.

    Reads the file on disk, so unsaved edits in an open buffer are not included.
    """

    def run(self, paths=None):
        source = self.source_path(paths)
        fmt = import_format(source)
        if fmt is None:
            sublime.status_message("Carve: import needs a .md or .html file")
            return

        target = os.path.splitext(source)[0] + ".crv"
        if os.path.exists(target) and not sublime.ok_cancel_dialog(
            "Carve: %s already exists.\n\nOverwrite it?" % os.path.basename(target),
            "Overwrite",
        ):
            return

        binary = carve_binary(self.window.active_view())
        sublime.set_timeout_async(lambda: self.convert(binary, fmt, source, target), 0)

    def convert(self, binary, fmt, source, target):
        try:
            proc = subprocess.Popen(
                carve_command(binary) + ["migrate", "--from", fmt, source],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(source) or None,
                startupinfo=_startupinfo(),
            )
            out, err = proc.communicate(timeout=30)
        except FileNotFoundError:
            sublime.error_message(
                "Carve: '%s' not found on PATH.\n\n"
                "Install it (npm install -g @markup-carve/carve) or set "
                "\"carve_binary\" in settings (package, project, or view)." % carve_command(binary)[0]
            )
            return
        except subprocess.TimeoutExpired:
            proc.kill()
            sublime.error_message("Carve: 'carve migrate' timed out")
            return

        if proc.returncode != 0:
            sublime.error_message(
                "Carve: 'carve migrate' failed\n\n%s" % err.decode("utf-8", "replace").strip()
            )
            return
        if not out.strip():
            sublime.error_message("Carve: 'carve migrate' produced no output")
            return

        with open(target, "wb") as handle:
            handle.write(out)
        sublime.set_timeout(lambda: self.window.open_file(target), 0)
        sublime.status_message("Carve: imported %s" % os.path.basename(target))

    def source_path(self, paths):
        if paths:
            return paths[0] if len(paths) == 1 else None
        view = self.window.active_view()
        return view.file_name() if view else None

    def is_enabled(self, paths=None):
        return import_format(self.source_path(paths)) is not None

    def is_visible(self, paths=None):
        return self.is_enabled(paths)


# Lint reports `file:line:col rule - message`. A finding in an included file
# names that file relative to the include root and ends with its include chain.
LINT_FILE_REGEX = r"^(.+?):([0-9]+):([0-9]+) (.*)$"
INCLUDE_ROOT_NOTICE = (
    "Carve: this carve CLI has no `lint --include-root`, so includes are not "
    "followed (carve-js 0.1.13 or carve-rs 0.1.11 and later have it).\n"
)

_include_root_support = {}


def _inside(path, folder):
    # No os.path.commonpath: plugins without .python-version run on Python 3.3.
    path = os.path.normcase(os.path.normpath(path))
    folder = os.path.normcase(os.path.normpath(folder)).rstrip(os.sep)
    return path.startswith(folder + os.sep)


def resolve_include_root(value, file_path, folders):
    """The `--include-root` for a lint run, or None to pass no flag.

    Returns (root, notice); notice is a line for the build panel or None.
    """
    file_dir = os.path.dirname(file_path)
    if value is False or value is None:
        return None, None
    if value == "file_dir":
        return file_dir, None
    if value is True or value == "project":
        containing = [f for f in folders if _inside(file_path, f)]
        return (max(containing, key=len) if containing else file_dir), None
    if isinstance(value, str):
        root = os.path.expanduser(value)
        if os.path.isabs(root) and os.path.isdir(root):
            return root, None
    notice = (
        "Carve: carve_lint_include_root %s is not \"project\", \"file_dir\", "
        "false or an existing absolute directory; using \"project\".\n"
        % json.dumps(value)
    )
    return resolve_include_root("project", file_path, folders)[0], notice


def shell_join(argv, windows=os.name == "nt"):
    if not windows:
        return " ".join(shlex.quote(arg) for arg in argv)
    # cmd.exe splits on an unquoted & or |, so quote every argument. A path
    # cannot hold `"`; a trailing backslash would escape the closing quote.
    return " ".join('"%s"' % (arg + "." if arg.endswith("\\") else arg) for arg in argv)


def shell_argv(shell_cmd):
    """Run a command line the way Sublime's exec runs a build's shell_cmd.

    On macOS that is a login shell, so the PATH a GUI-launched Sublime lacks
    (npm or cargo globals) is the same for the probe as for the build.
    """
    if sys.platform == "darwin":
        return ["/usr/bin/env", "bash", "-l", "-c", shell_cmd], False
    if os.name == "nt":
        return shell_cmd, True
    return ["/usr/bin/env", "bash", "-c", shell_cmd], False


def build_env(env=None, path="", view_env=None):
    """The environment Sublime's exec gives a build, so the probe sees it too."""
    merged = os.environ.copy()
    if path:
        merged["PATH"] = os.path.expandvars(path)
    merged.update(env or {})
    merged.update(view_env or {})
    return {key: os.path.expandvars(value) for key, value in merged.items()}


def supports_include_root(command, root, env=None):
    """Whether `carve lint` accepts `--include-root`.

    Probed by running it on empty input: carve-js lists `--include-root` under
    render in its help before lint took it, so the help text cannot tell.
    """
    env = env if env is not None else os.environ.copy()
    exe = shutil.which(command[0], path=env.get("PATH"))
    try:
        stamp = os.path.getmtime(exe) if exe else None
    except OSError:
        stamp = None
    key = (tuple(command), stamp, env.get("PATH"))
    if key not in _include_root_support:
        argv, shell = shell_argv(shell_join(command + ["lint", "--include-root", root]))
        try:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                env=env,
                startupinfo=_startupinfo(),
                start_new_session=os.name != "nt",
            )
        except OSError:
            return None
        try:
            proc.communicate(b"", timeout=15)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            try:
                proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            return None
        supported = proc.returncode == 0
        _include_root_support[key] = supported
    return _include_root_support[key]


def lint_command(command, file_path, root, supported):
    """The lint shell command and its working directory.

    An included file is reported relative to the include root, so the root is
    the working directory the result regex resolves paths against.
    """
    if root is not None and supported:
        return shell_join(command + ["lint", "--include-root", root, file_path]), root
    return shell_join(command + ["lint", file_path]), os.path.dirname(file_path)


class CarveLintCommand(ExecCommand):
    """The Lint build: `carve lint`, following includes within a root."""

    # Build options passed on to exec; shell_cmd, cmd and working_dir are ours.
    FORWARDED = ("env", "path", "encoding", "quiet", "word_wrap", "syntax")

    pending = 0

    def run(self, kill=False, file_regex=LINT_FILE_REGEX, **kwargs):
        # A cancel, or a newer build, drops a launch still waiting on its probe.
        self.pending += 1
        if kill:
            return super().run(kill=True)

        view = self.window.active_view()
        file_path = view.file_name() if view else None
        if not file_path:
            sublime.status_message("Carve: save the file before linting it")
            return

        command = carve_command(carve_binary(view))
        value = setting(view, "carve_lint_include_root", "project")
        root, notice = resolve_include_root(value, file_path, self.window.folders())
        options = {key: kwargs[key] for key in self.FORWARDED if key in kwargs}
        options["file_regex"] = file_regex
        if root is None:
            self.launch(self.pending, command, file_path, None, False, notice, options)
            return

        env = build_env(kwargs.get("env"), kwargs.get("path", ""), view.settings().get("build_env"))

        # The first probe of a CLI starts a process, so keep it off the UI thread.
        ticket = self.pending

        def probe():
            supported = supports_include_root(command, root, env)
            sublime.set_timeout(
                lambda: self.launch(ticket, command, file_path, root, supported, notice, options), 0
            )

        sublime.set_timeout_async(probe, 0)

    def launch(self, ticket, command, file_path, root, supported, notice, options):
        if ticket != self.pending:
            return
        if root is not None and supported is False:
            notice = (notice or "") + INCLUDE_ROOT_NOTICE
        shell_cmd, working_dir = lint_command(command, file_path, root, supported)
        super().run(shell_cmd=shell_cmd, working_dir=working_dir, **options)
        if notice and self.output_view is not None:
            self.output_view.run_command("append", {"characters": notice, "force": True})


def _kill_tree(proc):
    """Kill a probe and the carve it started, not only the shell around it."""
    try:
        if os.name == "nt":
            subprocess.call(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=_startupinfo(),
            )
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
        proc.kill()


def _startupinfo():
    """Keep a console window from flashing on Windows."""
    if os.name != "nt":
        return None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return info
