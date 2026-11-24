# Secret handling for shell workflows

Declare the interpreter, source/execute role, credential consumer and platform.
Use the consumer's supported credential channel. Do not include real secrets in
examples, tests, prompts, argv, diffs or logs. This reference does not authorize
credential retrieval, installation or external writes.

## Credential transport

Reading a token from the environment and then expanding it into
`curl --header "Authorization: Bearer $TOKEN"` still puts the token in argv.
That recipe does not solve process-list or command-audit exposure.
Environment variables can also be exposed through inherited processes,
diagnostics or same-user inspection; do not describe them as universally private.

Prefer the consumer's documented stdin/file-descriptor, protected credential
file, keyring, agent or short-lived identity integration. Verify the current
consumer API before implementing a transport. A shell wrapper cannot make an
argv-based credential private by renaming the variable.

Disable xtrace around secret processing and restore the caller's trace policy
deliberately. Sourced libraries must not silently change global options.
Avoid command substitutions that print credentials into captured debug logs.
Do not evaluate dotenv content as shell.

## Temporary secret material

Use an approved private storage location with actual ownership, permission,
mount, persistence and cleanup properties checked. `XDG_RUNTIME_DIR` is not
universally set and its name alone does not prove tmpfs or no swap. Do not
assume macOS and Linux provide the same storage.

Create a private owned resource with restrictive permissions, check all
creation/decryption/consumption statuses, and clean up only that resource.
Preserve the original failing status when cleanup also fails. Use the consuming
tool's supported protected-file interface; do not assume `ssh -i /dev/stdin`
is a universal portable key transport.

## Logging

Redact the entire value. Prefixes can disclose credential structure or identify
a secret across logs; do not print the first four characters.

```bash
log_credential_use() {
  local operation="$1"
  printf 'credential=[REDACTED] operation=%s\n' "$operation" >&2
}
```

Pass a non-secret operation label, not a credential value. ShellCheck does not
establish absence of credential leaks. Keep secret-bearing environment/config
fields out of tool outputs and review artifacts.

## Deletion and repository hygiene

Unlinking and `shred` cannot guarantee erasure across SSD remapping, COW,
snapshots, journals, backups or network filesystems. Minimize persistence and use
the platform's approved secret-storage design. Do not claim temporary storage
or overwritten bytes establish secure deletion.

Use reviewed ignore rules and the repository's existing secret-scanning process
for relevant changes. A .gitignore entry does not remove a tracked secret, and
a scanner pass is not proof that every secret channel is safe.

## Sources

Locally corrected from `docs/shell-skills-research.md` §2 and §6.
[GNU shred documentation](https://www.gnu.org/software/coreutils/manual/html_node/shred-invocation.html)
and [XDG Base Directory specification](https://specifications.freedesktop.org/basedir/latest/).
Credential transport must be verified against the actual consumer's current
documentation before implementation.
