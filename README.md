# Beacon

A small status light for your coding agents — [Claude Code](https://claude.com/claude-code)
and Codex, side by side. One dot per session, docked in the corner of your
screen, coloured by what that session is actually doing. Click a dot to land
back in it.

**[Download for macOS →](https://cpektas.github.io/beacon/)**

Requires macOS 14 or later. Apple silicon and Intel.

The status hooks (step 2 below) are Python, so Beacon needs `python3` on your
Mac — macOS ships it with the Xcode Command Line Tools, which most people
working with Claude Code already have.

## What it does

- **The whole board at a glance.** Every session you have running, in one row of
  dots across both agents, grouped by the project each belongs to. Dots only
  change colour, never move, so the third dot is the same work every time.
- **A nudge when you're the one holding it up, and a way back in.** A brief
  pulse when something blocks on you — quiet if you're already in that session,
  and it gives up rather than nags. Click the dot and Beacon raises that
  terminal window or opens that tab.
- **Being caught up before you switch back** is the third job, and it isn't
  built yet. The first attempt was removed rather than shipped; it's being
  redone.

## What the colours mean

| | | |
|---|---|---|
| 🟠 | **Needs you** | Blocked on a person — a question, or a permission it can't grant itself. |
| 🟢 | **Your move** | The turn finished. Not stuck; waiting to hear what's next. |
| 🟡 | **Working** | Busy, and the only dot that moves. Nothing is being asked of you. |
| ⚪ | **Idle** | Open, quiet, nothing pending. |

A finished session turns **blue** when it's also safe to close — a checkmark
when the work landed and the whole tree is clean, a question mark when that's a
judgment rather than a guarantee. Blue isn't a fifth state; it's what "your
move" looks like when something actually shipped.

A mark wearing a **"?"** means Beacon isn't certain. Some sessions report their
status outright; others have to be read from the files they leave behind. A
guess is drawn as its best colour plus a "?", never as a plain colour pretending
to be a fact.

## Setting it up

1. Open the disk image and drag Beacon to your Applications folder, then launch
   it. There's no Dock icon — look for the pill in the corner of your screen.
2. Open its settings and press **Install them** when it offers to install the
   status hooks for Claude Code. They're what lets a session say when a turn
   starts and finishes; without them those sessions all read as idle. Codex
   needs no setup — Beacon reads what it already writes.
3. Grant Accessibility access when asked. This is only needed so clicking a dot
   can bring you to that session; Beacon works without it.

Beacon updates itself. New versions arrive within a day, or immediately from
Settings → Updates.

## Privacy

Beacon reads files your agents already write on your Mac, and never modifies
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
