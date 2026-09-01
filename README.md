# Beacon

A small status light for your coding agents — [Claude Code](https://claude.com/claude-code)
and Codex, side by side. One graphite pilot light per top-level session, docked
in the corner of your screen and coloured by what that session is actually
doing. Click a light to land back in it.

**[Download for macOS →](https://cpektas.github.io/beacon/)**

Requires macOS 14 or later. Apple silicon and Intel.

The status hooks (step 2 below) are Python, so Beacon needs `python3` on your
Mac — macOS ships it with the Xcode Command Line Tools, which most people
working with Claude Code already have.

## What it does

- **The whole board at a glance.** Every session you have running, in one row of
  dots across both agents, grouped by the project each belongs to. Dots stay
  put unless you deliberately rearrange them; hover shows the session and its
  context use, while the capacity rim keeps account limits one glance away.
- **A nudge when you're the one holding it up, and a way back in.** A blocked
  session keeps pulsing until it is resolved; a completed turn announces itself
  once. After the first pulse, Beacon quiets repetition while you are actively
  working in an agent host, and lets you snooze a flash for three to ten
  minutes. Click the light, or use a compact keyboard switcher for waiting and
  pinned work, and Beacon raises that terminal window or opens that tab.
- **Your priority set, kept close.** Pin the sessions that matter, drag them
  into your order, collapse everything else, hide noise, and add optional glass
  identity marks. Choose a global shortcut in Settings, repeat it to cycle the
  waiting-and-pinned set, then press Return to jump.
- **Parallel work without a wall of lights.** Delegated agents stay grouped
  under the session that started them. A small neutral number shows live
  background work; hover or open the session list for the agent and command
  breakdown. The count never changes the session's status colour.

## What the colours mean

| | | |
|---|---|---|
| 🟠 | **Needs you** | Blocked on a person — a question, or a permission it can't grant itself. |
| 🟢 | **Your move** | The turn finished. Not stuck; waiting to hear what's next. |
| 🟡 | **Working** | Busy, and the only dot that moves. Nothing is being asked of you. |
| ⚪ | **Idle** | Open, quiet, nothing pending. |

A finished session turns **blue** when work landed this turn and the whole tree
is clean. Blue isn't a fifth state; it's the deterministic ready-to-close form
of "your move."

## Setting it up

1. Open the disk image and drag Beacon to your Applications folder, then launch
   it. There's no Dock icon — the first-run guide opens as a normal window and
   the pill lives in the corner of your screen.
2. Open its settings and press **Install them** when it offers to install the
   status hooks for Claude Code. They're what lets a session say when a turn
   starts and finishes; without them those sessions all read as idle. Codex
   needs no setup — Beacon reads what it already writes.
3. Grant Accessibility access when asked. This is only needed so clicking a dot
   can bring you to that session; Beacon works without it.

Beacon updates itself. It checks every half hour, and a persistent yellow
sparkle beside the corner pill says when a new version is waiting — installing
is still your click.

## Privacy

Beacon reads files your agents already write on your Mac, and never modifies
them. It shares anonymous usage statistics so it can be improved — clicks,
alerts, status changes, counts and durations, tied to a random install id.
What you're building never leaves the Mac: session names, folder names, file
paths, prompts and window titles are stripped before anything is sent, project
names appear only as salted hashes, and every field a shared copy can ever
contain is listed in Settings → Privacy & Data. One switch there turns sharing
off entirely; the full log always stays on your Mac either way.

## Reporting a problem

Open an issue here. Settings → Privacy & Data → **Create diagnostics folder**
writes a redacted bundle with an inventory of what's in it — attaching that
makes almost any report actionable.

## Source

Beacon is not open source; this repository carries its releases, and the
download above is a notarized build. If you'd like to work on it, get in touch.
