# Beacon

A small status light for [Claude Code](https://claude.com/claude-code) sessions.
One dot per session, docked in the corner of your screen, coloured by what that
session is actually doing. Click a dot to jump straight into it.

**[Download for macOS →](https://cpektas.github.io/beacon/)**

Requires macOS 14 or later. Apple silicon and Intel.

The status hooks (step 2 below) are Python, so Beacon needs `python3` on your
Mac — macOS ships it with the Xcode Command Line Tools, which most people
working with Claude Code already have.

## What the colours mean

| | | |
|---|---|---|
| 🟠 | **Needs you** | Blocked on a person — a question, or a permission it can't grant itself. |
| 🟢 | **Your move** | The turn finished. Not stuck; waiting to hear what's next. |
| 🟡 | **Working** | Busy, and the only dot that moves. Nothing is being asked of you. |
| ⚪ | **Idle** | Open, quiet, nothing pending. |

A finished session turns blue when it's also safe to close — a checkmark when
the work landed and the whole tree is clean, a question mark when that's a
judgment rather than a guarantee.

## Setting it up

1. Open the disk image and drag Beacon to your Applications folder, then launch
   it. There's no Dock icon — look for the pill in the corner of your screen.
2. Open its settings and press **Install them** when it offers to install the
   status hooks. Without them every session reads as idle, because the hooks are
   what tell Beacon when a turn starts and finishes.
3. Grant Accessibility access when asked. This is only needed so clicking a dot
   can bring you to that session; Beacon works without it.

Beacon updates itself. New versions arrive within a day, or immediately from
Settings → Updates.

## Privacy

Beacon reads files Claude Code already writes on your Mac, and never modifies
them. Nothing is sent anywhere by default: the usage log stays local, and the
setting that would share an anonymised copy is off unless you turn it on.
Settings → Privacy & Data lists every field that copy could ever contain.

## Reporting a problem

Open an issue here. Settings → Privacy & Data → **Create diagnostics folder**
writes a redacted bundle with an inventory of what's in it — attaching that
makes almost any report actionable.

## Source

Beacon is not open source; this repository carries its releases, and the
download above is a notarized build. If you'd like to work on it, get in touch.
