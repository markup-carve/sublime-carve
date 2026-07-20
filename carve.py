"""Sublime Text commands for Carve documents.

Two things Carve's own constructs make possible and that plain highlighting
cannot do:

* Cross-references are first-class in Carve (`</#id>` fills its link text from
  the target heading), so they should be navigable like code symbols.
* `carve fmt` is a canonical formatter whose output is byte-identical across
  the three engines, so formatting a buffer is safe and deterministic.

Both are opt-in commands; nothing here runs on its own.
"""

import os
import re
import subprocess

import sublime
import sublime_plugin

SETTINGS_FILE = "Carve.sublime-settings"

# `{#id}` on a block-attribute line, and the id slug carve derives from a
# heading when none is given.
ATTR_ID_RE = re.compile(r"\{[^}\n]*#([^\s}]+)[^}\n]*\}")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CROSSREF_RE = re.compile(r"</#([^>\s]+)>")


def carve_binary():
    """The `carve` executable, overridable via Carve.sublime-settings."""
    settings = sublime.load_settings(SETTINGS_FILE)
    return settings.get("carve_binary", "carve")


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
            # Cross-references resolve case-insensitively.
            lowered = {k.lower(): v for k, v in heading_ids(self.view).items()}
            row = lowered.get(target.lower())
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
        binary = carve_binary()
        try:
            proc = subprocess.Popen(
                [binary, "fmt"],
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
                "\"carve_binary\" in Carve.sublime-settings." % binary
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
        if not sublime.load_settings(SETTINGS_FILE).get("carve_format_on_save", False):
            return
        view.run_command("carve_format")


def _startupinfo():
    """Keep a console window from flashing on Windows."""
    if os.name != "nt":
        return None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return info
