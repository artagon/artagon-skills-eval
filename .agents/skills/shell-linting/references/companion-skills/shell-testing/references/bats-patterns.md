# bats-core patterns — full catalog

This reference was absorbed from the original `bats-testing-patterns` skill
(`wshobson/agents@c15b108`, MIT; 2026-05-17 consolidation) and corrected
locally on 2026-11-06. It is active guidance, not a verbatim snapshot.

Bats 1.14.0 uses Bash 3.2+ for the harness and can explicitly execute any UNIX
program. Declare the target dialect/edition/version, source/execute role and
utility implementations independently. Native-Zsh and POSIX-target libraries
must be sourced inside their actual target shell, not the Bash test process.
ShellSpec is optional for same-shell inclusion/mocking, not required for every
non-Bash program. Written cases and missing interpreter lanes are not test passes.

## Table of contents

- [Bats fundamentals](#bats-fundamentals)
- [File structure](#file-structure)
- [Basic test structure](#basic-test-structure)
- [Assertion patterns](#assertion-patterns)
  - [Exit-code assertions](#exit-code-assertions)
  - [Output assertions](#output-assertions)
  - [File assertions](#file-assertions)
- [Setup and teardown](#setup-and-teardown)
- [Mocking and stubbing](#mocking-and-stubbing)
- [Fixtures](#fixtures)
- [Error-condition testing](#error-condition-testing)
- [Dependency and skip-if](#dependency-and-skip-if)
- [Shell-compatibility testing](#shell-compatibility-testing)
- [Parallel execution](#parallel-execution)
- [test_helper.sh pattern](#test_helpersh-pattern)
- [CI integration](#ci-integration)

## Bats fundamentals

Bats (Bash Automated Testing System) is a TAP-compliant testing framework
for shell scripts. It provides:

- Simple natural test syntax (`@test "name" { … }`)
- TAP output format compatible with CI systems
- Fixtures + `setup`/`teardown` (per-test) and `setup_file`/`teardown_file` (per-file)
- Assertion helpers (the standard `bats-assert`, `bats-support` libraries)
- Parallel test execution (`--jobs N`)

Install:

```bash
brew install bats-core           # macOS
apt install bats                 # Debian/Ubuntu
npm install -g bats              # cross-platform
git clone https://github.com/bats-core/bats-core.git  # from source
./bats-core/install.sh /usr/local
bats --version                   # verify
```

## File structure

```
project/
├── bin/
│   ├── script.sh
│   └── helper.sh
├── tests/
│   ├── test_script.bats
│   ├── test_helper.sh
│   ├── fixtures/
│   │   ├── input.txt
│   │   └── expected_output.txt
│   └── helpers/
│       └── mocks.bash
└── README.md
```

## Basic test structure

```bash
#!/usr/bin/env bats

# Load test helper if present
load test_helper

# Setup runs before EACH test
setup() {
    export TMPDIR
    TMPDIR=$(mktemp -d)
}

# Teardown runs after EACH test
teardown() {
    rm -rf -- "$TMPDIR"
}

@test "Function returns 0 on success" {
    run my_function "input"
    [ "$status" -eq 0 ]
}

@test "Function outputs correct result" {
    run my_function "test"
    [ "$output" = "expected output" ]
}

@test "Function returns 1 on missing argument" {
    run my_function
    [ "$status" -eq 1 ]
}
```

`run` captures `$status` (exit code) and `$output` (combined stdout+stderr).

## Assertion patterns

### Exit-code assertions

```bash
@test "Command succeeds" {
    run true
    [ "$status" -eq 0 ]
}

@test "Command fails as expected" {
    run false
    [ "$status" -ne 0 ]
}

@test "Command returns specific exit code" {
    run my_function --invalid
    [ "$status" -eq 127 ]
}

@test "Can capture command result" {
    run echo "hello"
    [ "$status" -eq 0 ]
    [ "$output" = "hello" ]
}
```

### Output assertions

```bash
@test "Output matches string" {
    result=$(echo "hello world")
    [ "$result" = "hello world" ]
}

@test "Output contains substring" {
    result=$(echo "hello world")
    [[ "$result" == *"world"* ]]
}

@test "Output matches regex pattern" {
    result=$(date +%Y)
    [[ "$result" =~ ^[0-9]{4}$ ]]
}

@test "Multi-line output" {
    run printf "line1\nline2\nline3"
    [ "$output" = "line1
line2
line3" ]
}

@test "Lines variable contains output" {
    run printf "line1\nline2\nline3"
    [ "${lines[0]}" = "line1" ]
    [ "${lines[1]}" = "line2" ]
    [ "${lines[2]}" = "line3" ]
}
```

`${lines[@]}` is auto-populated by `run` from `$output` split on newlines.

### File assertions

```bash
@test "File is created" {
    [ ! -f "$TMPDIR/output.txt" ]
    my_function > "$TMPDIR/output.txt"
    [ -f "$TMPDIR/output.txt" ]
}

@test "File contents match expected" {
    my_function > "$TMPDIR/output.txt"
    [ "$(cat "$TMPDIR/output.txt")" = "expected content" ]
}

@test "File is readable" {
    touch "$TMPDIR/test.txt"
    [ -r "$TMPDIR/test.txt" ]
}

@test "File has correct permissions" {
    touch "$TMPDIR/test.txt"
    chmod 644 "$TMPDIR/test.txt"
    # BSD stat (macOS): %OLp; GNU stat (Linux): %a
    if [[ "$(uname)" == "Darwin" ]]; then
      [ "$(stat -f %OLp "$TMPDIR/test.txt")" = "644" ]
    else
      [ "$(stat -c %a "$TMPDIR/test.txt")" = "644" ]
    fi
}

@test "File size is correct" {
    echo -n "12345" > "$TMPDIR/test.txt"
    [ "$(wc -c < "$TMPDIR/test.txt")" -eq 5 ]
}
```

For cross-platform `stat`, see
`../../shell-defensive/references/cross-platform.md`.

## Setup and teardown

### Per-test setup/teardown

```bash
#!/usr/bin/env bats

setup() {
    TEST_DIR=$(mktemp -d)
    export TEST_DIR

    # Source script under test
    source "${BATS_TEST_DIRNAME}/../bin/script.sh"
}

teardown() {
    rm -rf -- "$TEST_DIR"
}

@test "Test using TEST_DIR" {
    touch "$TEST_DIR/file.txt"
    [ -f "$TEST_DIR/file.txt" ]
}
```

### Per-file setup_file/teardown_file (expensive shared resources)

```bash
#!/usr/bin/env bats

load test_helper

# setup_file runs ONCE before all tests in this file
setup_file() {
    SHARED_RESOURCE=$(mktemp -d)
    export SHARED_RESOURCE
    echo "Expensive setup" > "$SHARED_RESOURCE/data.txt"
}

# teardown_file runs ONCE after all tests
teardown_file() {
    rm -rf -- "$SHARED_RESOURCE"
}

@test "First test uses shared resource" {
    [ -f "$SHARED_RESOURCE/data.txt" ]
}

@test "Second test uses shared resource" {
    [ -d "$SHARED_RESOURCE" ]
}
```

`$BATS_TEST_TMPDIR` is auto-created per-test and auto-cleaned — prefer
it over manually-managed `mktemp -d` when per-file scope is unnecessary.

### Setup with structured fixtures

```bash
setup() {
    mkdir -p "$TMPDIR/data/input"
    mkdir -p "$TMPDIR/data/output"

    echo "line1" > "$TMPDIR/data/input/file1.txt"
    echo "line2" > "$TMPDIR/data/input/file2.txt"

    export DATA_DIR="$TMPDIR/data"
    export INPUT_DIR="$DATA_DIR/input"
    export OUTPUT_DIR="$DATA_DIR/output"
}

teardown() {
    rm -rf -- "$TMPDIR/data"
}

@test "Processes input files" {
    run my_process_script "$INPUT_DIR" "$OUTPUT_DIR"
    [ "$status" -eq 0 ]
    [ -f "$OUTPUT_DIR/file1.txt" ]
}
```

## Mocking and stubbing

### Function mocking (in-process)

```bash
#!/usr/bin/env bats

# Mock an external command by redefining it
my_external_tool() {
    echo "mocked output"
    return 0
}

@test "Function uses mocked tool" {
    export -f my_external_tool
    run my_function
    [[ "$output" == *"mocked output"* ]]
}
```

`export -f` is required so the mock is inherited by subshells `run` spawns.

### Command stubbing (PATH-based)

Useful for mocking *external* commands the script-under-test invokes via
its `$PATH`:

```bash
#!/usr/bin/env bats

setup() {
    STUBS_DIR="$TMPDIR/stubs"
    mkdir -p "$STUBS_DIR"
    export PATH="$STUBS_DIR:$PATH"
}

create_stub() {
    local cmd="$1"
    local output="$2"
    local code="${3:-0}"

    cat > "$STUBS_DIR/$cmd" <<EOF
#!/usr/bin/env bash
echo "$output"
exit $code
EOF
    chmod +x "$STUBS_DIR/$cmd"
}

@test "Function works with stubbed curl" {
    create_stub curl '{"status":"ok"}' 0
    run my_api_function
    [ "$status" -eq 0 ]
}
```

For richer mocking (call assertions, argument matching), use the
[bats-mock](https://github.com/jasonkarns/bats-mock) helper library and
its `stub`/`unstub` idiom.

### Environment-variable stubbing

```bash
@test "Function handles environment override" {
    export MY_SETTING="override_value"
    run my_function
    [ "$status" -eq 0 ]
    [[ "$output" == *"override_value"* ]]
}

@test "Function uses default when var unset" {
    unset MY_SETTING
    run my_function
    [ "$status" -eq 0 ]
    [[ "$output" == *"default"* ]]
}
```

## Fixtures

### Static fixture files

```bash
setup() {
    FIXTURES_DIR="${BATS_TEST_DIRNAME}/fixtures"
    WORK_DIR=$(mktemp -d)
    export WORK_DIR
}

teardown() {
    rm -rf -- "$WORK_DIR"
}

@test "Process fixture file" {
    cp "$FIXTURES_DIR/input.txt" "$WORK_DIR/input.txt"
    run my_process_function "$WORK_DIR/input.txt"
    diff "$WORK_DIR/output.txt" "$FIXTURES_DIR/expected_output.txt"
}
```

### Dynamic fixture generation

```bash
generate_fixture() {
    local lines="$1"
    local file="$2"

    for i in $(seq 1 "$lines"); do
        echo "Line $i content" >> "$file"
    done
}

@test "Handle large input file" {
    generate_fixture 1000 "$TMPDIR/large.txt"
    run my_function "$TMPDIR/large.txt"
    [ "$status" -eq 0 ]
    [ "$(wc -l < "$TMPDIR/large.txt")" -eq 1000 ]
}
```

For deterministic random fixtures, seed `$RANDOM` or use `shuf
--random-source` with a fixed-content file.

## Error-condition testing

```bash
@test "Function fails with missing file" {
    run my_function "/nonexistent/file.txt"
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "Function fails with invalid input" {
    run my_function ""
    [ "$status" -ne 0 ]
}

@test "Function fails with permission denied" {
    touch "$TMPDIR/readonly.txt"
    chmod 000 "$TMPDIR/readonly.txt"
    run my_function "$TMPDIR/readonly.txt"
    [ "$status" -ne 0 ]
    chmod 644 "$TMPDIR/readonly.txt"  # Cleanup
}

@test "Function provides helpful error message" {
    run my_function --invalid-option
    [ "$status" -ne 0 ]
    [[ "$output" == *"Usage:"* ]]
}
```

The "permission denied" test must restore perms (or use `$BATS_TEST_TMPDIR`
which is auto-cleaned) — bats does not guarantee unrestricted teardown.

## Dependency and skip-if

```bash
setup() {
    if ! command -v jq &>/dev/null; then
        skip "jq is not installed"
    fi
    export SCRIPT="${BATS_TEST_DIRNAME}/../bin/script.sh"
}

@test "JSON parsing works" {
    command -v jq >/dev/null 2>&1 || skip "jq is not installed"
    run my_json_parser '{"key":"value"}'
    [ "$status" -eq 0 ]
}
```

Use Bats `skip` for an unavailable optional dependency. In setup it skips
each affected test, not one file-wide success. Do not assume a `skip_if` helper
exists unless the repository explicitly loads one. Required compatibility
lanes must remain visible as unverified/blocked rather than becoming silent skips.

## Shell-compatibility testing

```bash
@test "Script works in bash" {
    bash "${BATS_TEST_DIRNAME}/../bin/script.sh" arg1
}

@test "Script works in sh (POSIX)" {
    sh "${BATS_TEST_DIRNAME}/../bin/script.sh" arg1
}

@test "Script works in dash" {
    if command -v dash &>/dev/null; then
        dash "${BATS_TEST_DIRNAME}/../bin/script.sh" arg1
    else
        skip "dash not installed"
    fi
}
```

Run only combinations in the declared target matrix, using actual minimum and
current interpreter paths. Record what generic `sh` resolves to. A Bash-only
program need not run under dash; a Bash-hosted Bats suite can test a POSIX
program under dash or native Zsh explicitly. ShellSpec is an optional alternate,
especially for same-shell library inclusion. Neither Bash POSIX mode nor Zsh
sh-emulation establishes compatibility with every POSIX deployment shell.

## Parallel execution

```bash
@test "Multiple independent operations" {
    run bash -c 'for i in {1..10}; do
        my_operation "$i" &
    done
    wait'
    [ "$status" -eq 0 ]
}

@test "Concurrent file operations" {
    for i in {1..5}; do
        my_function "$TMPDIR/file$i" &
    done
    wait
    [ -f "$TMPDIR/file1" ]
    [ -f "$TMPDIR/file5" ]
}
```

For test-suite-level parallelism, run `bats --jobs 4 tests/` — bats
parallelizes BETWEEN tests, not within. Each test gets its own
`$BATS_TEST_TMPDIR` so per-test isolation is automatic.

## test_helper.sh pattern

```bash
#!/usr/bin/env bash

# Source script under test
export SCRIPT_DIR="${BATS_TEST_DIRNAME%/*}/bin"

# Common test utilities
assert_file_exists() {
    if [ ! -f "$1" ]; then
        echo "Expected file to exist: $1"
        return 1
    fi
}

assert_file_equals() {
    local file="$1"
    local expected="$2"

    if [ ! -f "$file" ]; then
        echo "File does not exist: $file"
        return 1
    fi

    local actual
    actual=$(cat -- "$file")
    if [ "$actual" != "$expected" ]; then
        echo "File contents do not match"
        echo "Expected: $expected"
        echo "Actual: $actual"
        return 1
    fi
}

# Create / cleanup test directories
setup_test_dir() {
    TEST_DIR=$(mktemp -d)
    export TEST_DIR
}

cleanup_test_dir() {
    rm -rf -- "$TEST_DIR"
}
```

Load with `load test_helper` at the top of any `.bats` file in the same
directory. For cross-directory helpers, use
`load ../../helpers/setup` (path resolution is relative to the test file).

## CI integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install bats
        uses: bats-core/bats-action@3.0.0

      - name: Run tests
        run: bats --report-formatter junit tests/*.bats

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: bats-report
          path: tests/report.xml
```

### Makefile target

```makefile
.PHONY: test test-verbose test-tap test-parallel coverage

test:
	bats tests/*.bats

test-verbose:
	bats tests/*.bats --verbose

test-tap:
	bats tests/*.bats --tap

test-parallel:
	bats tests/*.bats --jobs 4

coverage: test
	# Optional: integrate kcov or similar for shell-script coverage
```

`bats --tap` produces TAP-13 output that CI tools (Jenkins, GitLab, Buildkite)
parse natively. `--report-formatter junit` produces JUnit XML for GitHub
Actions and Bitbucket.

## Best practices

1. **Test one thing per test** — single responsibility.
2. **Use descriptive test names** — `@test "name"` should read like a sentence.
3. **Clean up after tests** — always remove temporary files in teardown (or use `$BATS_TEST_TMPDIR`).
4. **Test both success and failure paths** — don't just test the happy path.
5. **Mock external dependencies** — isolate the unit under test.
6. **Use fixtures for complex data** — makes tests more readable.
7. **Run tests in CI/CD** — catch regressions early.
8. **Test across shell dialects** — ensure portability.
9. **Keep tests fast** — run in parallel when possible (`--jobs 4`).
10. **Document complex test setup** — explain unusual patterns inline.

## Source

Originally `bats-testing-patterns/SKILL.md` from `wshobson/agents@c15b108`,
MIT licensed. Absorbed verbatim into `shell-testing/references/` during
Phase 4 consolidation, 2026-05-17. See
`plugins/artagon-shell/UPSTREAM-wshobson-shell-scripting.md` for full
attribution.
