# Beacon for Claude Code

This plugin lets the [Beacon macOS app](https://cpektas.github.io/beacon/) see
when a Claude Code session is working, waiting for you, ready, or closed. It
does not install the app itself.

## Install

```text
/plugin marketplace add cpektas/beacon
/plugin install beacon@beacon
```

Restart existing Claude Code sessions after installation. Claude loads hooks
when a session starts, so a session that was already open will not report until
you reopen it.

If Beacon previously installed its older manual hook, open Beacon Settings and
use its duplicate-hook cleanup after installing this plugin. Running both is
safe, but makes every lifecycle event do the same local write twice.

## What runs

The plugin runs one small status hook when Claude Code emits
`UserPromptSubmit`, `Stop`, `Notification`, `PermissionRequest`, or
`SessionEnd`. It deliberately does not run on every tool call.

The hook reads Claude's event JSON from standard input and writes one status
file per session under:

```text
~/.claude/beacon/status/
```

It may also read the session transcript and local Git metadata to identify
unfinished background work, group the session with its project, and determine
whether a completed coding turn is clean. The plugin makes no network requests
and uploads nothing. Beacon's separate, optional usage sharing is controlled
inside the macOS app.

The hook needs Python 3. It recognizes Homebrew and python.org installations,
or the Python supplied by Apple's Command Line Tools. If none is available, it
exits silently and Beacon's setup check explains what is missing.

## Disable or uninstall

```text
/plugin disable beacon@beacon
/plugin uninstall beacon@beacon
```

Uninstalling removes only the plugin. Session status files and Beacon's own
settings remain yours; the macOS app's **Remove Beacon…** flow can remove those
separately.
