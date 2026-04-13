# Shell & Bash Standards

Rules for writing production-grade shell scripts. Applies to all `.sh` files,
CI pipeline scripts, setup scripts, and automation glue.

Composable with: `code_writing/STANDARDS.md` · `cicd/STANDARDS.md` · `security/STANDARDS.md`

---

## Table of Contents

1. [Script Header](#1-script-header)
2. [Error Handling](#2-error-handling)
3. [Variable Rules](#3-variable-rules)
4. [Functions](#4-functions)
5. [Input Validation](#5-input-validation)
6. [Output Formatting](#6-output-formatting)
7. [Portability](#7-portability)
8. [File Operations](#8-file-operations)
9. [Security](#9-security)
10. [Testing](#10-testing)
11. [Script Structure](#11-script-structure)
12. [Common Patterns](#12-common-patterns)
13. [Anti-Patterns](#13-anti-patterns)
14. [Checklist](#14-checklist)

---

## 1. Script Header

Every script starts with exactly three elements: shebang, strict mode, description.

```bash
#!/usr/bin/env bash
set -euo pipefail

# deploy.sh — Deploy application to staging/production
# Usage: deploy.sh <environment> [--force]
```

### Shebang Rules

| Rule | Correct | Wrong |
|---|---|---|
| Bash scripts | `#!/usr/bin/env bash` | `#!/bin/bash` |
| POSIX scripts | `#!/usr/bin/env sh` | `#!/bin/sh` |
| ✗ hardcode interpreter path | `#!/usr/bin/env bash` | `#!/usr/local/bin/bash` |

`env` lookup handles NixOS, Homebrew, custom installs. Hardcoded paths break on non-standard layouts.

### Strict Mode — `set -euo pipefail`

| Flag | Effect |
|---|---|
| `-e` | Exit on non-zero return |
| `-u` | Error on unset variable reference |
| `-o pipefail` | Pipe returns rightmost non-zero exit code |

Place `set -euo pipefail` on line 2, immediately after shebang. ✗ place it inside functions · ✗ place it after sourcing other files.

Optional: `set -E` — propagate traps to functions. Add when using `trap ERR`.

### Script Description Block

```bash
# script_name.sh — One-line purpose
# Usage: script_name.sh <required_arg> [optional_arg] [--flag]
# Dependencies: jq, curl, aws-cli
# Environment: AWS_PROFILE, AWS_REGION
```

Every script declares: purpose · usage · external dependencies · required env vars.

---

## 2. Error Handling

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General error |
| `2` | Usage/argument error |
| `3` | Missing dependency |
| `4` | Permission denied |
| `5` | Resource not found |
| `126` | Command not executable (reserved) |
| `127` | Command not found (reserved) |
| `128+N` | Fatal signal N (reserved) |

Define project exit codes at script top:

```bash
readonly EX_OK=0
readonly EX_ERR=1
readonly EX_USAGE=2
readonly EX_NODEP=3
```

### Error Functions

```bash
die() {
  printf '%s: error: %s\n' "${0##*/}" "$1" >&2
  exit "${2:-1}"
}

warn() {
  printf '%s: warning: %s\n' "${0##*/}" "$1" >&2
}
```

`die` prints to stderr, exits with code. `warn` prints to stderr, continues.

### Trap for Cleanup

```bash
cleanup() {
  rm -f "${TMPFILE:-}"
  # restore terminal, release locks, etc.
}
trap cleanup EXIT
```

| Rule | Detail |
|---|---|
| Register `trap EXIT` early | Before creating any temp files |
| ✗ trap EXIT inside functions | Overrides script-level trap |
| Use `trap cleanup EXIT` not `trap 'rm -f ...' EXIT` | Named function = testable + readable |
| Stack traps when needed | `trap 'cleanup; original_trap' EXIT` |

### ERR Trap (Bash-specific)

```bash
on_error() {
  printf 'ERROR: %s failed at line %d\n' "${BASH_SOURCE[0]}" "${BASH_LINENO[0]}" >&2
}
trap on_error ERR
```

Combine with `set -E` to propagate ERR trap into functions.

### Handling Expected Failures

```bash
# Correct — disable set -e for expected failure
if ! grep -q "pattern" file.txt; then
  echo "Pattern not found"
fi

# Correct — explicit || handling
command_that_might_fail || status=$?

# Wrong — suppresses all errors in block
set +e
some_commands
set -e
```

✗ `set +e` / `set -e` blocks. Use `|| true`, `|| status=$?`, or `if !` constructs.

---

## 3. Variable Rules

### Naming Conventions

| Scope | Convention | Example |
|---|---|---|
| Environment / exported | `UPPER_SNAKE` | `DATABASE_URL`, `LOG_LEVEL` |
| Script-level constants | `UPPER_SNAKE` + `readonly` | `readonly CONFIG_DIR="/etc/myapp"` |
| Local to function | `lower_snake` | `local file_count=0` |
| Loop iterators | `lower_snake` | `for item in "${list[@]}"` |
| Boolean flags | `lower_snake` | `local dry_run=false` |

### Quoting — Always

```bash
# Correct
echo "${filename}"
cp "${src}" "${dest}"
if [[ -f "${config_path}" ]]; then

# Wrong — word splitting + glob expansion
echo $filename
cp $src $dest
if [ -f $config_path ]; then
```

**Rule: every variable expansion requires double quotes.** Only exceptions:

| Exception | Reason |
|---|---|
| Inside `[[ ]]` on left side | No word splitting in `[[ ]]` (but quote anyway for consistency) |
| Arithmetic `$(( ))` | Variables auto-expanded as integers |
| Assignment `var=$other` | Right side of simple assignment not split |

When in doubt, quote. Unquoted variables = bugs waiting for filenames with spaces.

### Declaration Rules

```bash
# Correct — declare constants with readonly
readonly VERSION="1.2.3"
readonly -a REQUIRED_TOOLS=(jq curl aws)

# Correct — local in functions
my_func() {
  local input="$1"
  local -i count=0
  local -a items=()
}

# Wrong — global variable inside function
my_func() {
  result="something"   # pollutes global scope
}
```

| Rule | Detail |
|---|---|
| `readonly` for constants | Prevents accidental mutation |
| `local` for every function variable | ✗ implicit globals inside functions |
| `local -i` for integers | Bash enforces integer context |
| `local -a` for arrays | Documents type, prevents errors |
| `local -A` for assoc arrays | Bash 4+ only — note in portability |
| Declare at function top | ✗ declare mid-function after logic |

### Default Values

```bash
# Provide default — ${var:-default}
log_level="${LOG_LEVEL:-info}"

# Error if unset — ${var:?message}
db_url="${DATABASE_URL:?DATABASE_URL must be set}"

# Assign default if unset — ${var:=default}
: "${TMPDIR:=/tmp}"
```

✗ test with `[ -z "$var" ]` then assign. Use parameter expansion.

### Arrays

```bash
# Declare
local -a files=()

# Append
files+=("new_file.txt")

# Iterate — always quote "${array[@]}"
for file in "${files[@]}"; do
  process "$file"
done

# Length
echo "${#files[@]}"
```

✗ use `$array` (returns first element only). Always use `"${array[@]}"`.

---

## 4. Functions

### Declaration

```bash
# Correct — name() { without 'function' keyword
do_deploy() {
  local env="$1"
  # ...
}

# Wrong — 'function' keyword is bashism with no benefit
function do_deploy() {
  # ...
}
```

| Rule | Detail |
|---|---|
| `name() {` syntax | POSIX-compatible, consistent |
| ✗ `function` keyword | Bash-only, zero benefit |
| Declare all functions before `main` | ✗ call before definition |
| One function = one task | See `architecture/STANDARDS.md` §1 |

### Arguments and Local Variables

```bash
process_file() {
  local file="$1"
  local -i line_count=0
  local output=""

  [[ -f "${file}" ]] || die "File not found: ${file}"

  line_count=$(wc -l < "${file}")
  output="Processed ${line_count} lines"
  printf '%s\n' "${output}"
}
```

Name positional args immediately: `local arg_name="$1"`. ✗ use `$1` throughout function body.

### Return Values

```bash
# Correct — print to stdout, caller captures
get_version() {
  local ver
  ver=$(cat VERSION)
  printf '%s' "${ver}"
}
version=$(get_version)

# Correct — return code for boolean
is_installed() {
  command -v "$1" &>/dev/null
}
if is_installed jq; then ...

# Wrong — set global variable
get_version() {
  VERSION=$(cat VERSION)   # global side-effect
}
```

| Pattern | When |
|---|---|
| `printf` to stdout + capture | String/data return |
| `return 0` / `return 1` | Boolean success/failure |
| ✗ global variable assignment | Creates hidden coupling |
| ✗ subshell for variable return | Variables set in subshell are lost |

### Function Size

Max 40 lines per function. Functions > 40 lines → decompose. Same rule as `code_writing/STANDARDS.md`.

---

## 5. Input Validation

### Argument Count Check

```bash
main() {
  if [[ $# -lt 1 ]]; then
    usage
    exit "${EX_USAGE}"
  fi
  # ...
}
```

Every script validates argument count before any work.

### Usage Function

```bash
usage() {
  cat <<EOF
Usage: ${0##*/} <environment> [options]

Arguments:
  environment    Target environment (staging|production)

Options:
  -f, --force    Skip confirmation prompt
  -n, --dry-run  Show what would happen without executing
  -v, --verbose  Enable verbose output
  -h, --help     Show this help message

Environment:
  AWS_PROFILE    AWS credential profile (required)
  LOG_LEVEL      Log verbosity [default: info]
EOF
}
```

`usage` prints to stdout (not stderr) and does ✗ call `exit`. Caller decides exit code.

### Argument Parsing — getopts (simple)

```bash
parse_args() {
  local OPTIND=1
  while getopts ":fvnh" opt; do
    case "${opt}" in
      f) FORCE=true ;;
      v) VERBOSE=true ;;
      n) DRY_RUN=true ;;
      h) usage; exit 0 ;;
      :) die "Option -${OPTARG} requires argument" "${EX_USAGE}" ;;
      *) die "Unknown option: -${OPTARG}" "${EX_USAGE}" ;;
    esac
  done
  shift $((OPTIND - 1))
}
```

### Argument Parsing — Long Options (manual)

```bash
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -f|--force)   FORCE=true; shift ;;
      -n|--dry-run) DRY_RUN=true; shift ;;
      -v|--verbose) VERBOSE=true; shift ;;
      -h|--help)    usage; exit 0 ;;
      --)           shift; break ;;
      -*)           die "Unknown option: $1" "${EX_USAGE}" ;;
      *)            ARGS+=("$1"); shift ;;
    esac
  done
}
```

| Approach | Use when |
|---|---|
| `getopts` | Short opts only, POSIX-compatible scripts |
| Manual `while/case` | Long opts needed, Bash-only acceptable |
| ✗ `getopt` (external) | Inconsistent across GNU/BSD, avoid |

### Dependency Checking

```bash
require_commands() {
  local -a missing=()
  for cmd in "$@"; do
    command -v "${cmd}" &>/dev/null || missing+=("${cmd}")
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    die "Missing required commands: ${missing[*]}" "${EX_NODEP}"
  fi
}

# Call early
require_commands jq curl aws
```

Check dependencies before work, not at point of use. `command -v` over `which` — POSIX, no aliases.

---

## 6. Output Formatting

### Channel Discipline

| Channel | Content |
|---|---|
| `stdout` | Data — parseable output, results, return values |
| `stderr` | Messages — progress, warnings, errors, debug info |

```bash
# Data → stdout
printf '%s\n' "${result}"

# Messages → stderr
printf 'Processing %d files...\n' "${count}" >&2
```

✗ mix data and messages on same channel. Breaks piping.

### Structured Logging

```bash
log() {
  local level="$1"; shift
  printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${level}" "$*" >&2
}

log INFO "Deploying to ${env}"
log ERROR "Connection failed after ${retries} retries"
```

### Color Output

```bash
if [[ -t 2 ]]; then
  readonly RED=$'\033[0;31m'
  readonly GREEN=$'\033[0;32m'
  readonly YELLOW=$'\033[0;33m'
  readonly BOLD=$'\033[1m'
  readonly RESET=$'\033[0m'
else
  readonly RED="" GREEN="" YELLOW="" BOLD="" RESET=""
fi

log_error() { printf '%s%s%s\n' "${RED}" "$*" "${RESET}" >&2; }
log_ok()    { printf '%s%s%s\n' "${GREEN}" "$*" "${RESET}" >&2; }
log_warn()  { printf '%s%s%s\n' "${YELLOW}" "$*" "${RESET}" >&2; }
```

| Rule | Detail |
|---|---|
| Check `[[ -t FD ]]` before colors | ✗ color codes in piped/redirected output |
| Define color vars as `readonly` | Constants, set once |
| Empty string fallback for non-tty | Zero-cost no-op when piped |
| ✗ `echo -e` for colors | Non-portable, use `$'...'` or `printf` |

### Progress Indicators

```bash
# Simple counter for stderr
progress() {
  printf '\r[%d/%d] %s' "$1" "$2" "$3" >&2
}

for i in $(seq 1 "${total}"); do
  progress "${i}" "${total}" "Processing..."
  do_work "${i}"
done
printf '\n' >&2  # final newline after \r
```

✗ spinner animations in non-interactive scripts. ✗ progress on stdout.

---

## 7. Portability

### POSIX vs Bash

| Feature | POSIX `sh` | Bash |
|---|---|---|
| `[[ ]]` | ✗ | Yes |
| Arrays | ✗ | Yes |
| `local` | Widely supported but not POSIX | Yes |
| `$(( ))` | Yes | Yes |
| `$( )` | Yes | Yes |
| Backticks `` ` ` `` | Yes (avoid) | Yes (avoid) |
| `set -o pipefail` | ✗ | Yes |
| `${var,,}` lowercase | ✗ | Bash 4+ |
| `=~` regex | ✗ | Bash 3+ |
| `&>` redirect | ✗ | Yes |
| Process substitution `<()` | ✗ | Yes |

### When to Use Which

| Script type | Target |
|---|---|
| CI pipeline scripts | Bash — `pipefail` mandatory |
| Docker entrypoints | `sh` — Alpine has no bash by default |
| Install scripts (public) | `sh` — maximum portability |
| Project automation | Bash — arrays + strict mode |
| Cron jobs | Bash — error handling required |

### Bashisms to Avoid in POSIX Scripts

```bash
# Bash-only          → POSIX equivalent
[[ "$a" == "$b" ]]   → [ "$a" = "$b" ]
[[ -n $var ]]         → [ -n "$var" ]
echo "${var,,}"       → echo "$var" | tr '[:upper:]' '[:lower:]'
array+=("item")       → no equivalent (use positional params or files)
read -r -a arr        → no equivalent
local var="x"         → var="x" (function scope varies)
(( count++ ))         → count=$((count + 1))
```

### Platform Differences

| Command | GNU (Linux) | BSD (macOS) |
|---|---|---|
| `sed -i` | `sed -i ''` needs no arg | `sed -i ''` requires empty string |
| `readlink -f` | Works | ✗ — use `realpath` or `python -c` |
| `date -d` | Works | ✗ — use `date -j` |
| `grep -P` | PCRE support | ✗ — use `grep -E` |
| `mktemp` | `mktemp` (auto) | `mktemp -t prefix` |
| `stat` format | `stat -c '%s'` | `stat -f '%z'` |

Handle with detection:

```bash
if sed --version 2>/dev/null | grep -q GNU; then
  SED_INPLACE=(sed -i)
else
  SED_INPLACE=(sed -i '')
fi
"${SED_INPLACE[@]}" 's/old/new/' file.txt
```

---

## 8. File Operations

### Temp Files

```bash
readonly TMPDIR_SCRIPT=$(mktemp -d)
trap 'rm -rf "${TMPDIR_SCRIPT}"' EXIT

# Single temp file
tmpfile=$(mktemp "${TMPDIR_SCRIPT}/data.XXXXXX")
```

| Rule | Detail |
|---|---|
| `mktemp` for all temp files | ✗ hardcode `/tmp/myfile` — race condition + predictable name |
| Create temp dir, clean in trap | Single cleanup point |
| `XXXXXX` suffix | mktemp replaces with random |
| Trap cleanup before creating temps | Ensures cleanup on early exit |

### Atomic File Writes

```bash
# Write to temp, move atomically
write_config() {
  local dest="$1"
  local tmp
  tmp=$(mktemp "${dest}.XXXXXX")

  generate_config > "${tmp}"
  chmod 644 "${tmp}"
  mv -f "${tmp}" "${dest}"
}
```

`mv` on same filesystem = atomic rename. ✗ redirect directly to target file — partial writes on failure. See `architecture/STANDARDS.md` §1 (rule 17 — copy-on-write).

### File Existence Checks

```bash
[[ -f "${path}" ]] || die "File not found: ${path}"
[[ -d "${dir}" ]]  || die "Directory not found: ${dir}"
[[ -r "${file}" ]] || die "File not readable: ${file}"
[[ -w "${dir}" ]]  || die "Directory not writable: ${dir}"
[[ -x "${bin}" ]]  || die "Not executable: ${bin}"
[[ -s "${file}" ]] || die "File is empty: ${file}"
```

Check before use. Specific test per need — ✗ generic `-e` when you need `-f`.

### Safe Directory Traversal

```bash
# Correct — null-delimited, handles spaces/newlines in names
while IFS= read -r -d '' file; do
  process "${file}"
done < <(find "${dir}" -type f -name '*.log' -print0)

# Wrong — breaks on whitespace in filenames
for file in $(find "${dir}" -name '*.log'); do
  process "${file}"
done
```

`find -print0` + `read -d ''` = safe for all filenames. ✗ for-loop over `find` output.

---

## 9. Security

### Command Injection

```bash
# CRITICAL: Never eval user input
eval "$user_input"            # ✗ arbitrary code execution
bash -c "$user_input"         # ✗ same risk
"${user_input}"               # ✗ command from variable

# Safe — validate against allowlist
case "${action}" in
  start|stop|restart) systemctl "${action}" myservice ;;
  *) die "Invalid action: ${action}" ;;
esac
```

| Rule | Detail |
|---|---|
| ✗ `eval` | No exceptions. Redesign if you think you need it |
| ✗ unquoted variables in commands | Injection via word splitting |
| ✗ `bash -c "$var"` | Same as eval |
| Allowlist over denylist | Validate against known-good values |

### Path Validation

```bash
# Validate path is under expected directory
validate_path() {
  local path="$1"
  local base_dir="$2"
  local resolved

  resolved=$(realpath -m "${path}")
  [[ "${resolved}" == "${base_dir}"/* ]] || die "Path traversal: ${path}"
}

validate_path "${user_file}" "/var/data"
```

✗ trust paths from user input, arguments, or environment without validation.

### Secrets

```bash
# ✗ secrets in command arguments — visible in ps output
mysql -p"${DB_PASS}" ...           # ✗ visible in process list

# Correct — use environment or stdin
export MYSQL_PWD="${DB_PASS}"
mysql ...

# Correct — file descriptor
echo "${SECRET}" | command --password-stdin
```

| Rule | Detail |
|---|---|
| ✗ secrets in CLI args | Visible in `ps aux`, `/proc/*/cmdline` |
| ✗ secrets in `export` at script top | Visible in `/proc/*/environ` |
| Use env vars or stdin piping | Per-command scope |
| `umask 077` for temp files with secrets | Restrict read access |
| Unset secret vars after use | `unset DB_PASS` |

### Permissions

```bash
# Set restrictive umask for sensitive files
umask 077
echo "${token}" > "${TMPDIR_SCRIPT}/auth_token"

# Verify ownership before sourcing
[[ "$(stat -c '%u' "${config}")" == "$(id -u)" ]] || die "Config not owned by current user"
```

✗ source files not owned by current user. ✗ execute files from world-writable directories.

See `security/STANDARDS.md` for comprehensive input validation and access control rules.

---

## 10. Testing

### ShellCheck — Mandatory

Every `.sh` file passes [ShellCheck](https://github.com/koalaman/shellcheck) with zero warnings.

```bash
# Run on all scripts
shellcheck -x -s bash scripts/*.sh

# In CI
shellcheck --format=gcc scripts/*.sh
```

| Flag | Purpose |
|---|---|
| `-x` | Follow sourced files |
| `-s bash` | Specify shell dialect |
| `--format=gcc` | CI-friendly output |
| `-e SC1091` | Exclude specific warnings (sparingly, with justification) |

Disable per-line only when justified:

```bash
# shellcheck disable=SC2059  # format string intentionally from variable
printf "${format}" "${args[@]}"
```

✗ blanket `# shellcheck disable=` at file top. Per-line only with comment explaining why.

### BATS Framework

[BATS](https://github.com/bats-core/bats-core) (Bash Automated Testing System) for all test scripts.

```bash
#!/usr/bin/env bats

setup() {
  TEST_TMPDIR=$(mktemp -d)
  export TEST_TMPDIR
}

teardown() {
  rm -rf "${TEST_TMPDIR}"
}

@test "deploy exits 2 on missing arguments" {
  run ./deploy.sh
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"Usage"* ]]
}

@test "deploy validates environment name" {
  run ./deploy.sh invalid_env
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"Invalid environment"* ]]
}

@test "config parser extracts database url" {
  echo 'DATABASE_URL=postgres://localhost/db' > "${TEST_TMPDIR}/env"
  run ./parse_config.sh "${TEST_TMPDIR}/env" DATABASE_URL
  [ "${status}" -eq 0 ]
  [ "${output}" = "postgres://localhost/db" ]
}
```

### Test Structure

| Rule | Detail |
|---|---|
| Test file per script | `tests/deploy.bats` for `scripts/deploy.sh` |
| `setup`/`teardown` in every file | Temp dirs, env vars |
| Use `run` to capture exit + output | `${status}` and `${output}` |
| Test exit codes explicitly | ✗ only test output |
| Test error paths | Missing args, bad input, missing deps |

### CI Integration

```yaml
# In pipeline — see cicd/STANDARDS.md
lint:
  - shellcheck -x scripts/*.sh
test:
  - bats tests/*.bats
```

ShellCheck runs before tests. Failing ShellCheck = failing build. No exceptions.

---

## 11. Script Structure

### Main Function Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="${0##*/}"

# Source libraries (after constants, before functions)
source "${SCRIPT_DIR}/lib/logging.sh"

# Functions (alphabetical or dependency order)
usage() { ... }
parse_args() { ... }
validate_env() { ... }
do_work() { ... }

# Main
main() {
  parse_args "$@"
  validate_env
  do_work
}

main "$@"
```

| Section | Order |
|---|---|
| 1 | Shebang + strict mode |
| 2 | Script description comment |
| 3 | Constants (`readonly`) |
| 4 | Source external libraries |
| 5 | Function definitions |
| 6 | `main()` function |
| 7 | `main "$@"` invocation |

### Source-able Libraries

Libraries that are `source`d by other scripts follow different rules:

```bash
#!/usr/bin/env bash
# lib/logging.sh — Structured logging functions
# Source this file; do not execute directly.

# Guard against double-sourcing
[[ -n "${_LIB_LOGGING_LOADED:-}" ]] && return 0
readonly _LIB_LOGGING_LOADED=1

# Guard against direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "This script is meant to be sourced, not executed" >&2
  exit 1
fi

log_info() { ... }
log_error() { ... }
```

| Rule | Detail |
|---|---|
| Include guard with `_LIB_*_LOADED` | Prevents double-sourcing side effects |
| Direct execution guard | ✗ `./lib/logging.sh` |
| ✗ `set -euo pipefail` in libraries | Caller controls strict mode |
| ✗ `main` function in libraries | Libraries export functions, not entry points |
| ✗ `exit` in library functions | Return codes only; caller decides to exit |

### Script Directory Resolution

```bash
# Robust — works with symlinks
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Wrong — fails with symlinks, sourced scripts, PATH lookup
SCRIPT_DIR="$(dirname "$0")"
```

`${BASH_SOURCE[0]}` over `$0` — correct when sourced. `cd + pwd` resolves symlinks.

---

## 12. Common Patterns

### Lock File

```bash
readonly LOCK_FILE="/var/run/${SCRIPT_NAME}.lock"

acquire_lock() {
  if ! mkdir "${LOCK_FILE}" 2>/dev/null; then
    die "Another instance is running (lock: ${LOCK_FILE})"
  fi
  trap 'rm -rf "${LOCK_FILE}"' EXIT
}
```

`mkdir` is atomic on all filesystems. ✗ check-then-create with `[ -f ]` — race condition.

### Retry Loop

```bash
retry() {
  local -i max_attempts="$1"; shift
  local -i delay="$1"; shift
  local -i attempt=1

  until "$@"; do
    if (( attempt >= max_attempts )); then
      die "Command failed after ${max_attempts} attempts: $*"
    fi
    log WARN "Attempt ${attempt}/${max_attempts} failed, retrying in ${delay}s..."
    sleep "${delay}"
    (( attempt++ ))
  done
}

# Usage
retry 3 5 curl -sf "https://api.example.com/health"
```

### Logging Library

```bash
readonly LOG_LEVELS=([DEBUG]=0 [INFO]=1 [WARN]=2 [ERROR]=3)
LOG_LEVEL="${LOG_LEVEL:-INFO}"

log() {
  local level="$1"; shift
  (( ${LOG_LEVELS[${level}]:-0} >= ${LOG_LEVELS[${LOG_LEVEL}]:-0} )) || return 0
  printf '[%s] [%-5s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${level}" "$*" >&2
}
```

### Parallel Execution

```bash
# GNU parallel (preferred)
find . -name '*.log' -print0 | parallel -0 gzip {}

# Bash background jobs with limited concurrency
readonly MAX_JOBS=4
for file in "${files[@]}"; do
  process_file "${file}" &
  # Limit concurrent jobs
  while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
    wait -n
  done
done
wait  # wait for remaining
```

### Confirmation Prompt

```bash
confirm() {
  local prompt="${1:-Continue?}"
  if [[ "${FORCE:-false}" == "true" ]]; then
    return 0
  fi
  read -r -p "${prompt} [y/N] " response
  [[ "${response}" =~ ^[Yy]$ ]]
}

confirm "Deploy to production?" || die "Aborted"
```

### Configuration File Parsing

```bash
# Simple key=value (no sections)
parse_env_file() {
  local file="$1"
  [[ -f "${file}" ]] || return 1
  while IFS='=' read -r key value; do
    [[ "${key}" =~ ^[[:space:]]*# ]] && continue  # skip comments
    [[ -z "${key}" ]] && continue                  # skip empty lines
    key=$(echo "${key}" | xargs)                   # trim whitespace
    export "${key}=${value}"
  done < "${file}"
}
```

---

## 13. Anti-Patterns

### Parsing `ls` Output

```bash
# ✗ WRONG — breaks on spaces, newlines, special chars
for file in $(ls *.txt); do
  process "$file"
done

# Correct — glob directly
for file in *.txt; do
  [[ -e "${file}" ]] || continue  # handle empty glob
  process "${file}"
done
```

### Useless `cat`

```bash
# ✗ WRONG — useless use of cat
cat file.txt | grep "pattern"
cat file.txt | wc -l

# Correct — direct input
grep "pattern" file.txt
wc -l < file.txt
```

### Unquoted Globs in Tests

```bash
# ✗ WRONG — glob expands if files match
if [ $var = *.txt ]; then

# Correct — double brackets, quoted
if [[ "${var}" == *.txt ]]; then
```

### String Comparison with `=` in `[ ]`

```bash
# ✗ WRONG — single = works but double bracket is safer
[ "$a" == "$b" ]    # == is not POSIX in [ ]

# Correct
[ "$a" = "$b" ]     # POSIX single bracket
[[ "$a" == "$b" ]]  # Bash double bracket
```

### Backtick Command Substitution

```bash
# ✗ WRONG — hard to nest, hard to read
result=`command \`nested\``

# Correct — $(  ) nests cleanly
result=$(command $(nested))
```

### Full Anti-Pattern Table

| Anti-Pattern | Risk | Correct Alternative |
|---|---|---|
| `for f in $(ls ...)` | Word splitting on spaces | `for f in glob*` or `find -print0` |
| `cat file \| cmd` | Useless process | `cmd < file` or `cmd file` |
| Unquoted `$var` | Word splitting + glob | `"${var}"` |
| `[ -z $var ]` | Fails if var has spaces | `[[ -z "${var}" ]]` |
| `echo $var` | Eats backslashes, expands | `printf '%s\n' "${var}"` |
| `` `cmd` `` | Can't nest, escaping | `$(cmd)` |
| `cd dir; cmd; cd ..` | Breaks on failure | `(cd dir && cmd)` or pushd/popd |
| `kill -9` first | No graceful shutdown | `kill` → wait → `kill -9` |
| `rm -rf "$DIR/"*` | Deletes `/` if DIR empty | `[[ -n "${DIR}" ]] && rm -rf "${DIR:?}/"*` |
| `[ "$?" -eq 0 ]` | Captured by `[` itself | `if command; then` |
| `export VAR=$(cmd)` | Masks exit code | `VAR=$(cmd); export VAR` |
| `echo "$(cat file)"` | Useless wrappers | `cat file` |
| `test -f file && source file` | No error on source fail | `[[ -f file ]] && source file \|\| die` |
| `PATH=$PATH:/new` in scripts | Accumulates duplicates | Conditional add or `declare` once |

---

## 14. Checklist

### New Script

- [ ] Shebang is `#!/usr/bin/env bash` (or `sh` for POSIX)
- [ ] `set -euo pipefail` on line 2
- [ ] Script description block (purpose, usage, deps, env vars)
- [ ] `usage()` function present
- [ ] Argument count validated
- [ ] Arguments parsed (getopts or manual while/case)
- [ ] Dependencies checked with `command -v`
- [ ] Exit codes defined as `readonly` constants
- [ ] `die()` and `warn()` helper functions present
- [ ] `trap cleanup EXIT` registered before temp file creation
- [ ] All temp files created with `mktemp`
- [ ] All variables quoted: `"${var}"`
- [ ] All function variables declared `local`
- [ ] `main()` function pattern used
- [ ] `main "$@"` at script bottom
- [ ] stdout = data only, stderr = messages only
- [ ] Colors gated on `[[ -t 2 ]]` check
- [ ] ShellCheck passes with zero warnings
- [ ] BATS tests written for success + failure paths
- [ ] File executable: `chmod +x script.sh`

### Library Script

- [ ] Include guard (`_LIB_*_LOADED`)
- [ ] Direct execution guard
- [ ] ✗ `set -euo pipefail` (caller controls)
- [ ] ✗ `exit` calls (return codes only)
- [ ] ✗ `main` function
- [ ] All functions documented with purpose comment
- [ ] ShellCheck passes

### Code Review

- [ ] No `eval` anywhere
- [ ] No unquoted variable expansions
- [ ] No `cat file | cmd` (useless cat)
- [ ] No `for f in $(ls ...)` patterns
- [ ] No backtick command substitution
- [ ] No hardcoded `/tmp/` paths
- [ ] No secrets in command-line arguments
- [ ] No `set +e` / `set -e` blocks
- [ ] No `function` keyword
- [ ] `rm -rf` guarded against empty variables
- [ ] Temp files cleaned up via trap
- [ ] Exit codes documented and consistent
