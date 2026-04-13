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
