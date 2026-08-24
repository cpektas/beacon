#!/usr/bin/env python3
"""Beacon status hook — invoked by Claude Code lifecycle hooks.

Reads the hook event JSON from stdin and writes a per-session status file to
~/.claude/beacon/status/<session_id>.json, which the Beacon menu-bar app watches.

Event mapping (turn-level only; deliberately no per-tool-call events, which
would add subprocess latency to every tool call):
  UserPromptSubmit  -> working      (you sent a message; Claude is on it)
  Stop              -> ready        (turn finished; your move)
  Notification      -> needs_input  (mid-turn only: in-chat question or
                                     permission prompt. The same event is also
                                     Claude Code's idle nudge ~60s after a turn
                                     ends, so after Stop it is ignored —
                                     see `main`.)
  PermissionRequest -> needs_input  (permission dialog shown)
  SessionEnd        -> (removes the status file)

Every write records which checkout the session works in (branch, worktree, and
the repo/worktree roots a dot is grouped under — see `git_identity`). That is
identity, and it has to hold for the whole session: keyed on a fact only Stop
recorded, a worktree session left its repo's dot cluster the moment somebody
sent a prompt.

On Stop the hook also snapshots git facts for the session's cwd (clean tree,
fresh commit this turn, branch merged) so Beacon can derive "ready to close".
Cleanliness comes in two strengths: "clean" is the whole tree (the guarantee),
"sessionClean" ignores dirty files this session never edited (the judgment —
several sessions share one checkout, and a sibling's in-progress work should
not block this session's mint). Which files the session edited comes from its
own transcript (Edit/Write tool calls). Each git command is timeout-bounded;
a non-repo cwd just omits the facts.

Stop also counts background work Beacon has no hook for. A `run_in_background`
Bash call or a background Agent (subagent) call keeps running after Stop fires
— Claude Code has no hook event for "a background task started" or "finished",
so without this the dot reads "ready" the instant the visible reply ends, even
with shells or subagents still going. See `pending_background_work`.

Must be fast and silent: always exit 0, never write to stdout/stderr.
"""

import json
import os
import re
import subprocess
import sys
import time

EVENT_STATUS = {
    "UserPromptSubmit": "working",
    "Stop": "ready",
    "Notification": "needs_input",
    "PermissionRequest": "needs_input",
    "SessionEnd": None,
}

# The fields in the `git` block that describe WHERE a session works rather than
# how its turn went. Every event carries them (see `git_identity`); only Stop
# adds the evidence beside them.
IDENTITY_KEYS = ("branch", "worktree", "repoRoot", "worktreeRoot")


# Tools whose input names a file the session changed directly. Files touched
# as a side-effect of Bash commands are invisible here — a known blind spot;
# sessionClean is a judgment, "clean" remains the guarantee.
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def session_edited_files(transcript_path):
    """Absolute paths of every file this session edited (any turn, subagents
    included). None on any failure so the caller omits the judgment facts."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return None
    try:
        if os.path.getsize(transcript_path) > 50 * 1024 * 1024:
            return None
        edited = set()
        with open(transcript_path) as f:
            for line in f:
                # Cheap substring pre-filter; full JSON parse only on hits.
                if '"tool_use"' not in line or '_path"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                message = obj.get("message") or {}
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue
                    if block.get("name") not in EDIT_TOOLS:
                        continue
                    inp = block.get("input") or {}
                    path = inp.get("file_path") or inp.get("notebook_path")
                    if isinstance(path, str) and path:
                        edited.add(os.path.realpath(path))
        return edited
    except Exception:
        return None


# Tool calls that keep running after their own tool_use returns: a
# `run_in_background` Bash command, or a subagent dispatched via the Agent
# tool (background by default). Both get a <task-notification> appended to
# the transcript later, tagged with the ORIGINAL tool_use id, when they
# actually finish — nothing else in the transcript says so.
BACKGROUND_SPAWN_TOOLS = {"Bash", "Agent"}
NOTIFICATION_ID_RE = re.compile(r"<tool-use-id>([^<]+)</tool-use-id>")


def _result_text_head(block, limit=200):
    """The first characters of a tool_result's text — where the harness puts
    its own notices. Content is either a string or a list of typed blocks."""
    content = block.get("content")
    if isinstance(content, str):
        return content[:limit]
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                return (part.get("text") or "")[:limit]
    return ""


def pending_background_work(transcript_path):
    """Count of this session's background Bash/Agent calls with no matching
    <task-notification> yet, i.e. presumed still running. A tool_use with no
    notification is the false-safe direction: the alternative (assuming it
    finished) is exactly what showed a session as safe to close while
    background shells were still going. None on any failure, so the caller
    omits the fact rather than guessing at a number."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return None
    try:
        if os.path.getsize(transcript_path) > 50 * 1024 * 1024:
            return None
        launched = set()
        notified = set()
        bash_ids = set()
        echo_ids = set()
        with open(transcript_path) as f:
            for line in f:
                if '"tool_use"' in line and ('"Bash"' in line or '"Agent"' in line):
                    try:
                        obj = json.loads(line)
                    except Exception:
                        obj = None
                    content = ((obj or {}).get("message") or {}).get("content")
                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict) or block.get("type") != "tool_use":
                                continue
                            name = block.get("name")
                            tool_id = block.get("id")
                            if name not in BACKGROUND_SPAWN_TOOLS or not tool_id:
                                continue
                            # Every Bash call, foreground included: the
                            # auto-background fallback below may only claim an
                            # id that was actually a Bash call. A session that
                            # merely TALKS about backgrounding (an issue
                            # description, this very file's source printed by
                            # a command) echoes the phrases through other
                            # tools' results, and each phantom it minted was
                            # permanent — no notification ever resolves a task
                            # that never ran. Seen live 2026-08-11: two
                            # phantoms held a session at working-"?" over a
                            # true "your move".
                            inp = block.get("input") or {}
                            if name == "Bash":
                                bash_ids.add(tool_id)
                                # A command that itself CONTAINS the notice
                                # phrases (a grep of this file, a heredoc
                                # printing its source) echoes them into its
                                # result at any position, including the head.
                                # Its result is testimony about text, not
                                # about backgrounding — never fallback-count
                                # it.
                                cmd = str(inp.get("command") or "")
                                if (
                                    "moved to the background" in cmd
                                    or "running in background with ID" in cmd
                                ):
                                    echo_ids.add(tool_id)
                            # Agent calls run in background unless told not to;
                            # Bash only counts here when explicitly requested —
                            # the auto-backgrounded-after-timeout case (below)
                            # is caught from its tool_result instead, since the
                            # original input never asked for it.
                            if name == "Agent" and inp.get("run_in_background") is False:
                                continue
                            if name == "Bash" and not inp.get("run_in_background"):
                                continue
                            launched.add(tool_id)
                if "moved to the background" in line or "running in background with ID" in line:
                    try:
                        obj = json.loads(line)
                    except Exception:
                        obj = None
                    content = ((obj or {}).get("message") or {}).get("content")
                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict) or block.get("type") != "tool_result":
                                continue
                            tool_id = block.get("tool_use_id")
                            # Two guards, both load-bearing (see bash_ids
                            # above): the result must belong to a real Bash
                            # call, and the harness's notice sits at the HEAD
                            # of the result — a phrase buried deep in output
                            # is quoted text, not a notice.
                            if not tool_id or tool_id not in bash_ids:
                                continue
                            if tool_id in echo_ids:
                                continue
                            head = _result_text_head(block)
                            if (
                                "moved to the background" in head
                                or "running in background with ID" in head
                            ):
                                launched.add(tool_id)
                if "task-notification" in line and "tool-use-id" in line:
                    notified.update(NOTIFICATION_ID_RE.findall(line))
        return len(launched - notified)
    except Exception:
        return None


def porcelain_paths(porcelain):
    """Repo-relative paths out of `git status --porcelain` output."""
    paths = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:  # rename: "R  old -> new"
            path = path.split(" -> ", 1)[1]
        paths.append(path.strip('"'))
    return paths


def _git_runner(cwd):
    """A timeout-bounded `git -C cwd` caller. This runs inside the user's
    turn, so every call is bounded and every failure is None."""
    def run(args, timeout, strip=True):
        try:
            out = subprocess.run(
                ["git", "-C", cwd] + args,
                capture_output=True, text=True, timeout=timeout,
            )
            if out.returncode != 0:
                return None
            # strip=False keeps leading spaces — porcelain lines start with
            # a significant status column that stripping would corrupt.
            return out.stdout.strip() if strip else out.stdout
        except Exception:
            return None
    return run


def git_identity(cwd, run=None):
    """Which checkout this session works in — branch, worktree, and the two
    roots a dot can be grouped under. Identity, never evidence: nothing about a
    status or a close verdict may be derived from any of it.

    Split out of `git_facts` because it is written on EVERY event, not just
    Stop. Keyed on it, a session's group has to survive the whole turn: while
    this lived in the Stop-only block, a worktree session's `repoRoot` vanished
    the instant somebody sent a prompt, its dot fell back to grouping by cwd
    and left its repo's cluster for one named after the worktree — a dot moving
    because its session started working, which is the one thing grouping must
    never do.

    Returns {} for a repository that answered nothing, None when the cwd is not
    a work tree at all. The caller tells those apart: the first is an answer,
    the second is a reason to keep the last one.
    """
    if not cwd or not os.path.isdir(cwd):
        return None
    run = run or _git_runner(cwd)
    if run(["rev-parse", "--is-inside-work-tree"], 1) != "true":
        return None

    identity = {}

    # THIS checkout's root. Two jobs, and they want different roots in a
    # linked worktree: dirty-path attribution in `git_facts` needs the
    # worktree's own toplevel (porcelain paths are relative to it), and so does
    # anyone grouping worktrees apart — while the identity a session groups
    # under by default wants the MAIN checkout's root. See repoRoot below.
    toplevel = run(["rev-parse", "--show-toplevel"], 1)
    worktree_root = os.path.realpath(toplevel) if toplevel else None
    repo_root = worktree_root

    branch = run(["branch", "--show-current"], 1) or None  # None on detached HEAD
    if branch:
        identity["branch"] = branch

    # Which worktree this is, when it is a linked one. In a linked worktree
    # --git-dir points inside the main checkout's .git/worktrees/<name> while
    # --git-common-dir points at the .git itself; in an ordinary checkout the
    # two are the same path and there is nothing to say. Both come back from a
    # single rev-parse, one line each, so this costs one git call rather than
    # two. Several Beacon sessions routinely share one repo through worktrees,
    # which is exactly when "which checkout is this dot" stops being obvious.
    dirs = run(["rev-parse", "--git-dir", "--git-common-dir"], 1)
    if dirs:
        lines = dirs.splitlines()
        if len(lines) == 2:
            git_dir = os.path.realpath(os.path.join(cwd, lines[0]))
            common = os.path.realpath(os.path.join(cwd, lines[1]))
            if git_dir != common:
                identity["worktree"] = os.path.basename(git_dir)
                # A linked worktree's --show-toplevel is the worktree itself —
                # the very path the default grouping must NOT key on. The
                # shared .git names the main checkout, and its parent is the
                # repo every worktree of this repo agrees on. Guarded on the
                # basename because a submodule's common dir lives in
                # .git/modules/<name>, where the parent is nothing at all.
                if os.path.basename(common) == ".git":
                    repo_root = os.path.dirname(common)

    # The two roots, and the pair is the point: `repoRoot` is what every
    # worktree of one repository agrees on (the default — a session belongs to
    # its repo before it belongs to its checkout), `worktreeRoot` is this
    # checkout alone, for anyone who wants each worktree as its own cluster.
    # Equal in an ordinary checkout, which is why one field could not carry
    # both answers. See `SessionGrouping`.
    if repo_root:
        identity["repoRoot"] = repo_root
    if worktree_root:
        identity["worktreeRoot"] = worktree_root

    return identity


def git_facts(cwd, turn_started_ms, transcript_path=None):
    if not cwd or not os.path.isdir(cwd):
        return None

    run = _git_runner(cwd)
    identity = git_identity(cwd, run=run)
    if identity is None:
        return None

    # Identity rides in the same block as the evidence because that is where
    # the git calls already are; the two are separated again on Beacon's side
    # (`WorkspaceIdentity` vs `CompletionFacts`).
    facts = dict(identity)
    toplevel = identity.get("worktreeRoot")
    branch = identity.get("branch")

    porcelain = run(["status", "--porcelain"], 2, strip=False)
    if porcelain is not None:
        facts["clean"] = porcelain.strip() == ""
        if porcelain.strip():
            # Judgment scope: which of the dirty files are actually ours?
            edited = session_edited_files(transcript_path)
            if toplevel and edited is not None:
                dirty = porcelain_paths(porcelain)
                mine, others = [], []
                for rel in dirty:
                    absolute = os.path.realpath(os.path.join(toplevel, rel))
                    (mine if absolute in edited else others).append(rel)
                facts["sessionClean"] = not mine
                facts["dirtySessionFiles"] = sorted(mine)[:10]
                facts["dirtyOtherFiles"] = sorted(others)[:10]

    commit_ct = run(["log", "-1", "--format=%ct"], 1)
    if commit_ct and commit_ct.isdigit():
        commit_ms = int(commit_ct) * 1000
        facts["lastCommitAt"] = commit_ms
        if turn_started_ms:
            # 5s slop: the commit's second-resolution timestamp vs our ms clock.
            facts["committedThisTurn"] = commit_ms >= int(turn_started_ms) - 5000

    default_ref = run(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], 1)
    if default_ref:
        default_branch = default_ref.split("/", 1)[-1]
        facts["defaultBranch"] = default_branch
        if branch and branch != default_branch:
            facts["merged"] = run(
                ["merge-base", "--is-ancestor", "HEAD", default_ref], 1
            ) is not None

    return facts


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    session_id = data.get("session_id")
    event = data.get("hook_event_name", "")
    if not session_id or event not in EVENT_STATUS:
        return

    status_dir = os.path.expanduser("~/.claude/beacon/status")
    path = os.path.join(status_dir, f"{session_id}.json")

    status = EVENT_STATUS[event]
    if status is None:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        return

    prev = {}
    try:
        with open(path) as f:
            prev = json.load(f)
    except Exception:
        pass

    # One event, two meanings: Claude Code fires Notification for a real block
    # (an in-chat question, a permission dialog — neither of which fires any
    # other hook) and again as an idle nudge roughly a minute after a turn
    # ended. Mid-turn it is the only signal we get, so it still counts; once
    # Stop has fired the turn is over and the nudge is a fact about the human,
    # not about the session. Honouring it there escalated a finished session to
    # needs_input, which breaks through every indefinite suppression by design
    # — one false orange flashed 101 times in an hour. Leave the file alone.
    if event == "Notification" and prev.get("event") == "Stop":
        return

    now_ms = int(time.time() * 1000)
    payload = {
        "status": status,
        "event": event,
        "updatedAt": now_ms,
        "cwd": data.get("cwd"),
        "message": str(data.get("message") or "")[:200],
        "transcriptPath": data.get("transcript_path"),
    }

    # Turn start survives intermediate writes (Notification etc.) so that at
    # Stop time we can tell whether a commit landed during this turn.
    if event == "UserPromptSubmit":
        payload["turnStartedAt"] = now_ms
    elif prev.get("turnStartedAt"):
        payload["turnStartedAt"] = prev["turnStartedAt"]

    # What the last write knew about this checkout, when it was the same one.
    # Identity does not change while the cwd doesn't, so this is both the cache
    # that keeps mid-turn events free and the fallback that keeps a git read
    # failing (git missing, a timeout, a checkout mid-rebuild) from dropping a
    # dot out of its group.
    carried = (
        {k: v for k, v in (prev.get("git") or {}).items() if k in IDENTITY_KEYS}
        if prev.get("cwd") == payload["cwd"] else {}
    )

    if event == "Stop":
        git = git_facts(
            data.get("cwd"), payload.get("turnStartedAt"), data.get("transcript_path")
        )
        pending = pending_background_work(data.get("transcript_path"))
        if pending is not None:
            payload["pendingBackground"] = pending
    elif carried.get("repoRoot"):
        # Already answered, and the answer cannot have changed: reuse it rather
        # than spend four git calls in the middle of somebody's turn. Stop
        # re-reads regardless — it needs the block anyway, and that is where a
        # branch switched mid-turn lands.
        git = carried
    else:
        git = git_identity(data.get("cwd"))

    # A read that could not answer keeps the last answer. Only a read that
    # produced no root at all is topped up: a successful read reporting no
    # branch is a detached HEAD, not a gap, and must not resurrect a stale one.
    if carried:
        if not git:
            git = carried
        elif "repoRoot" not in git:
            merged = dict(carried)
            merged.update(git)
            git = merged
    if git:
        payload["git"] = git

    os.makedirs(status_dir, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f)
    os.replace(tmp, path)  # atomic rename → triggers Beacon's directory watcher


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit(0)
