# Idempotency and locking

Production scripts are re-run constantly — by cron, by systemd, by CI
retries, by humans hitting up-arrow. A script that mutates state when re-run
is a footgun. This reference covers the three layers of idempotency: cheap
state checks (in `defensive-patterns.md` Pattern 7), single-instance locks
(`flock`), and persistent state-file checkpoints.

Declare the Bash version/source role and utility implementations first.
Examples are executed Bash with named utility dependencies, not universal
POSIX-2017 or native-Zsh library code. Existing example APIs are retained.

## Why idempotency matters

The cost of a re-run must approach zero. A deploy script that runs `npm
install` from scratch on every retry adds 90 seconds × N retries. A
config-management script that recreates a database user on every run
fails the second time. A test setup that fails partway leaves the next
attempt to clean up half-finished state.

The three indicators an operation is idempotent:

1. **Intended state is unchanged** on re-run (required content and metadata).
2. **Failures remain visible**; a retry must not bless a partially completed step.
3. **Revalidation follows the contract**; speed and identical logging are useful
   properties but are not the definition of idempotency.

## Pattern 1: `mkdir -p`, `ln -sfn`, `rsync -a`

The cheapest idempotency: use commands that already encode it.

```bash
# Wrong: fails on re-run
mkdir /var/cache/myapp

# Right: idempotent
mkdir -p -- /var/cache/myapp

# Wrong: fails if link exists
ln -s target link

# Right: idempotent (force, no-dereference)
ln -sfn -- target link

# Wrong: cp over a tree is non-idempotent (timestamps, perms drift)
cp -r src/ dst/

# Right: rsync's archive mode preserves timestamps + skips unchanged files
rsync -a --delete -- src/ dst/
```

`rsync -a` normally uses a size/mtime quick check, not per-file content
checksums. `--delete` is destructive and needs an exact authorized destination.
Neither a forced symlink replacement nor archive mode is a universal safe default.

## Pattern 2: State-file checkpoints

For workflows with multiple steps, write a sentinel file after each step
completes. On re-run, skip steps whose sentinel exists:

```bash
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/myscript"
mkdir -p -- "$state_dir"

step_done() {
  [[ -f "$state_dir/$1.done" ]]
}
mark_done() {
  : > "$state_dir/$1.done"
}

if ! step_done "fetch"; then
  fetch_data || exit "$?"
  mark_done "fetch" || exit "$?"
fi

if ! step_done "process"; then
  process_data || exit "$?"
  mark_done "process" || exit "$?"
fi

if ! step_done "publish"; then
  publish_data || exit "$?"
  mark_done "publish" || exit "$?"
fi
```

Two refinements:

- Embed a content hash in the sentinel name: `${state_dir}/fetch-$(sha256sum data.in | cut -d' ' -f1).done`. A re-run after the input changes invalidates the sentinel automatically.
- For destructive cleanup, use `--force` to allow re-running the cleanup
  itself: `step_done cleanup || (force_cleanup && mark_done cleanup)`.

## Pattern 3: `flock` for single-instance enforcement

`flock` ensures only one instance of a script runs at a time. The idiom:

```bash
exec 9>/var/lock/myscript.lock
flock -n 9 || { echo "already running" >&2; exit 1; }
# Critical section — lock held until exec'd FD 9 closes (script exits)
```

`exec 9>...` opens FD 9 for the duration of the script. `flock -n` is
non-blocking; without `-n` it waits. The lock is released when all references to the locked open file description
close; inherited descriptors in child processes can extend its lifetime.

Choose an owned lock location with actual permissions and lifetime.
`flock` is an explicit dependency, not a standard macOS or POSIX-2017 command.
Moving a pathname to /tmp does not supply the utility.

For finer-grained locks (multiple resources, reader-writer semantics), use
`flock -s` (shared) and `flock -x` (exclusive) on different FDs:

```bash
exec 8>/var/lock/myscript.lock
exec 9>/var/lock/myscript.lock
flock -s 8        # shared read lock
flock -nx 9 || exit 1   # conflicts with the held shared lock on the same object
```

## Pattern 4: Atomic writes

A re-run after a crashed previous run must not see half-written files.
Rename-based replacement requires same-filesystem staging, a complete successful
producer, destination-type checks and the required permissions/metadata policy.
Atomic visibility is not crash durability:

```bash
atomic_write() {
  local target="$1"
  local tmp
  local rc
  tmp=$(mktemp "${target}.XXXXXX") || return "$?"
  if cat >"$tmp"; then
    :
  else
    rc=$?
    rm -f -- "$tmp" || :
    return "$rc"
  fi
  if mv -- "$tmp" "$target"; then
    return 0
  else
    rc=$?
    rm -f -- "$tmp" || :
    return "$rc"
  fi
}

# Input is already complete and validated; do not publish a fallible pipeline.
atomic_write "/var/lib/myapp/data.json" < validated-data.json
```

A consumer may rename a failed producer's prefix before pipefail reports the
pipeline failure. Stage and validate the producer first. Handle abandoned
staging files using an owned-resource cleanup policy.

## Pattern 5: Cleanup is also idempotent

Don't write cleanup that fails on a missing file:

```bash
# Wrong: fails if file already gone
rm /tmp/myscript.lock

# Right: idempotent
rm -f -- /tmp/myscript.lock
```

The `-f` flag suppresses missing-file errors but NOT other errors (permission
denied, etc.). For cleanup whose failure matters, check its nonzero status. The following
suppresses failure and is suitable only for explicitly best-effort cleanup;
it does not establish successful cleanup:

```bash
rm -f -- "$tmp" 2>/dev/null || true
```

Do not unlink a held flock lock file: another process can recreate the pathname
with a different inode and acquire an unrelated lock. Close the owned descriptor.
Readers and writers must use the same lock object. The shared/exclusive example
above demonstrates the conflict; use separate processes in an actual protocol.

## Cron + systemd timer hygiene

When a script runs from cron/systemd timer:

- Set `MAILTO=ops@…` in cron so stderr emits a notification.
- `OnFailure=` in systemd unit triggers an alert handler.
- Lock with `flock` to guarantee no overlap between schedule runs.
- Write to `$LOGNAME`-owned state dirs (`$XDG_STATE_HOME` or `/var/lib/$USER`),
  not `/tmp` (which is wiped on reboot).

A complete systemd unit + timer pair:

```ini
# /etc/systemd/system/myscript.service
[Service]
Type=oneshot
ExecStart=/usr/local/bin/myscript.sh
Nice=10
IOSchedulingClass=best-effort
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/var/lib/myapp

# /etc/systemd/system/myscript.timer
[Timer]
OnCalendar=hourly
Persistent=true   # catches up after downtime

[Install]
WantedBy=timers.target
```

`Persistent=true` means a missed run (because the host was down) fires once
when the system comes back up — and the script's idempotency layer means that
catch-up run is safe.

## Sources

- Patterns synthesized from `docs/shell-skills-research.md` § 2 line 71
  (idempotency paragraph) + the FHS spec for lock file locations.
- Locally corrected on 2026-11-06: utility scope, status propagation, same-object
  locking, descriptor lifetime and staged-write failure boundaries.
- `flock` idiom (`exec 9>...; flock -n 9 || exit 1`) is the canonical form
  from `man flock(1)` examples.
- systemd `Persistent=true` semantics from `systemd.timer(5)`.
