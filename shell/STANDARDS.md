# Shell Standards

> Structure, error handling, variable, and function rules for every shell script that runs unattended.

**ID** `shell` · **Tier** Language · **Version** 1.0
**Owns** script header · strict mode · exit codes · traps · variables · quoting · functions · argument parsing · output channels · script layout
**Defers to** portability · GNU vs BSD · file operations · injection vectors · secrets · shellcheck · bats → [shell/HARDENING.md](HARDENING.md) · error taxonomy · recovery policy → [error_handling](../error_handling/STANDARDS.md) · validation boundary · access control → [security](../security/STANDARDS.md) · CLI ergonomics · help text contract → [cli](../cli/STANDARDS.md) · function length · naming → [code_writing](../code_writing/STANDARDS.md) · pipeline stages → [cicd](../cicd/STANDARDS.md)
**Load with** [shell/HARDENING.md](HARDENING.md) · [code_writing](../code_writing/STANDARDS.md) · [cli](../cli/STANDARDS.md) · [security](../security/STANDARDS.md)

---

## Table of Contents

1. [Script Header](#1-script-header)
2. [Error Handling](#2-error-handling)
3. [Variable Rules](#3-variable-rules)
4. [Functions](#4-functions)
5. [Argument Handling](#5-argument-handling)
6. [Output Channels](#6-output-channels)
7. [Script Structure](#7-script-structure)
8. [Common Patterns](#8-common-patterns)
9. [Anti-Patterns](#9-anti-patterns)
10. [Checklist](#10-checklist)

---

## 1. Script Header

Three elements, in this exact order: shebang → strict mode → description comment.

```bash
#!/usr/bin/env bash
set -euo pipefail
```

The description comment follows immediately, one `#` line per field — purpose (`# deploy.sh — Deploy to staging or production`) · usage (`# Usage: deploy.sh <environment> [--force]`) · dependencies (`# Dependencies: jq, curl, aws`) · environment (`# Environment: AWS_PROFILE (required), LOG_LEVEL (default: info)`). A script whose dependencies are undeclared fails in production, not at review.

### 1.1 Shebang

`#!/usr/bin/env bash` | `#!/usr/bin/env sh`. ✗ `#!/bin/bash` · ✗ `#!/bin/sh` · ✗ `#!/usr/local/bin/bash` — `env` resolves the interpreter through `PATH`; hardcoded paths break on macOS (bash 3.2 at `/bin/bash`), NixOS, and Homebrew. Bash vs POSIX selection → [HARDENING §1](HARDENING.md#1-bash-vs-posix).

### 1.2 Strict Mode — `set -euo pipefail`

| Flag | Effect |
|---|---|
| `-e` | Exit on any non-zero return not otherwise handled |
| `-u` | Error on reference to an unset variable |
| `-o pipefail` | Pipeline exit code = rightmost non-zero, ✗ last command's |

Line 2, immediately after the shebang. ✗ inside a function · ✗ after `source` · ✗ split across lines. Without `pipefail`, `false | true` succeeds and every `cmd | tee log` hides its own failure.

`set -E` additionally — required whenever `trap … ERR` is used, or the trap does not fire inside functions, subshells, or command substitutions.

`IFS=$'\n\t'` — optional hardening. Removes the space from the default `IFS=$' \n\t'`, so an unquoted expansion splits on newlines and tabs only. A seatbelt, ✗ a substitute for quoting (§3.2).

---

## 2. Error Handling

Error taxonomy and recovery policy → [error_handling](../error_handling/STANDARDS.md). This standard owns the shell mechanism: exit codes and traps.

### 2.1 Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General error |
| `2` | Usage / argument error |
| `3` | Missing dependency |
| `4` | Permission denied |
| `5` | Resource not found |
| `126` | Command found but not executable (reserved) |
| `127` | Command not found (reserved) |
| `128+N` | Killed by signal N (reserved — `130` = SIGINT) |

✗ define custom codes above `125` — the shell owns that range. Declare the set once: `readonly EX_OK=0 EX_ERR=1 EX_USAGE=2 EX_NODEP=3`.

### 2.2 `die` and `warn`

Both write to stderr. `die` exits with the given code (default 1); `warn` continues.

```bash
die()  { printf '%s: error: %s\n'   "${0##*/}" "$1" >&2; exit "${2:-1}"; }
warn() { printf '%s: warning: %s\n' "${0##*/}" "$1" >&2; }
```

### 2.3 Traps

```bash
cleanup() { rm -rf "${TMPDIR_SCRIPT:-}"; }   # `:-` — the trap can fire before the var is set
trap cleanup EXIT                            # BEFORE the first temp file is created
```

| Rule | Detail |
|---|---|
| Register `trap … EXIT` BEFORE the first temp file | ! Ordering is load-bearing — a trap set afterwards leaks on early exit |
| Name the handler | ✗ `trap 'rm -rf ...' EXIT` — a named function is testable and readable |
| Guard every variable in the handler | The trap runs even when `set -u` killed the script mid-init |
| ✗ `trap … EXIT` inside a function | Silently replaces the script-level trap |
| `EXIT` coverage | Fires on normal exit · `die` · `set -e` failure. Does NOT fire on `SIGKILL` |
| Signal traps | `trap 'exit 130' INT` · `trap 'exit 143' TERM` when cleanup must precede signal exit |

ERR trap — bash only, requires `set -E`:

```bash
on_error() { printf 'ERROR: %s line %d: exit %d\n' "${BASH_SOURCE[1]}" "${BASH_LINENO[0]}" "$?" >&2; }
trap on_error ERR
```

### 2.4 Expected Failures

`set -e` does NOT trigger inside a condition, a `&&`/`||` chain, or a negated command. Exploit that; ✗ disable it.

```bash
if ! grep -q "pattern" file.txt; then …; fi    # ✓ failure is data, not an error
status=0
command_that_may_fail || status=$?             # ✓ capture the code
(( status == 0 )) || warn "exited ${status}"
set +e; some_commands; set -e                  # ✗ hides every error in the block
local ver; ver=$(get_version)                  # ✓ declare, THEN assign
local ver=$(get_version)                       # ✗ `local` returns 0 — masks cmd's status
```

! `local var=$(cmd)` and `export VAR=$(cmd)` both swallow the command's exit code — the builtin's status wins. Always split the declaration from the assignment.

---

## 3. Variable Rules

### 3.1 Naming

| Scope | Convention | Example |
|---|---|---|
| Exported / environment | `UPPER_SNAKE` | `DATABASE_URL` |
| Script constant | `UPPER_SNAKE` + `readonly` | `readonly CONFIG_DIR="/etc/app"` |
| Function-local | `lower_snake` | `local file_count=0` |
| Internal library symbol | `_leading_underscore` | `_lib_logging_loaded` |

### 3.2 Quoting — Every Expansion

! Every variable expansion is double-quoted. Unquoted `$var` undergoes word splitting AND glob expansion — a filename containing a space or a `*` becomes arbitrary arguments.

```bash
cp "${src}" "${dest}"              # ✓
cp $src $dest                      # ✗ splits on IFS, expands globs
```

Exceptions, and only these: `$(( … ))` arithmetic (operands are integers, not words) · the RHS of a simple assignment `var=$other` · deliberate splitting (rare — comment it, prefer an array).

Inside `[[ ]]` bash does not word-split — quote anyway, because the RHS of `==` is a pattern: `[[ "$a" == "$b" ]]` compares, `[[ "$a" == $b ]]` glob-matches.

### 3.3 Declaration

| Rule | Detail |
|---|---|
| `readonly` for constants | Mutation becomes an error, not a surprise |
| `local` for every variable in a function | ✗ implicit globals — they leak across calls |
| `local -i` integer · `local -a` array · `local -A` assoc array | `-A` requires bash 4+ |
| Declare at function top | ✗ mid-function declarations after logic |
| `local x; x=$(cmd)` | Two statements when the value comes from a command (§2.4) |

### 3.4 Defaults

```bash
log_level="${LOG_LEVEL:-info}"                       # default if unset or empty
db_url="${DATABASE_URL:?DATABASE_URL must be set}"   # fail fast with a message
: "${TMPDIR:=/tmp}"                                  # assign default in place
count="${1-}"                                        # `-` not `:-` → empty string is valid
```

`:-` treats empty as unset; `-` treats only unset as unset. Pick deliberately. ✗ `[ -z "$var" ] && var=default` — parameter expansion exists.

### 3.5 Arrays

| Form | Meaning |
|---|---|
| `"${arr[@]}"` | Each element a separate word — the only safe iteration form |
| `"${arr[*]}"` | Elements joined by the first `IFS` char — display only |
| `$arr` | ✗ the FIRST element only — a silent bug |
| `${#arr[@]}` | Element count |

! Build command lines as arrays, never as strings — a string command line re-splits and re-globs on expansion.

```bash
local -a cmd=(curl -sS)
[[ -n "${token:-}" ]] && cmd+=(--header "Authorization: Bearer ${token}")
"${cmd[@]}" "${url}"
```

! Under `set -u`, bash < 4.4 errors on `"${arr[@]}"` when the array is empty. Target bash 4.4+, or write `"${arr[@]+"${arr[@]}"}"`.

---

## 4. Functions

`name() {` — POSIX form. ✗ `function name {` — a bashism with zero benefit. Define every function before `main`. One function, one task. Max 40 lines → [code_writing](../code_writing/STANDARDS.md).

### 4.1 Arguments

Name positional arguments on the first lines of the body — `local file="$1"`, `local -i max="${2:-1000}"`. ✗ `$1` scattered through a function: unreadable, and it breaks the moment the signature changes. `"$@"` forwards arguments preserving word boundaries; ✗ `$*` — it flattens them into one string.

### 4.2 Return Values

| Need | Mechanism |
|---|---|
| String / data | `printf '%s\n'` to stdout; caller captures with `$( )` |
| Success / failure | `return 0` / `return 1` — the exit status IS the boolean |
| Integer status | `return N` — 0–255 only; larger values wrap |
| ✗ global assignment | Hidden coupling; two callers collide |
| ✗ value from a subshell | A variable set in `( )` or a pipeline is lost on exit |

```bash
get_version()  { printf '%s\n' "$(<VERSION)"; }        # ✓ data on stdout
is_installed() { command -v "$1" >/dev/null 2>&1; }    # ✓ status as boolean

version=$(get_version)
is_installed jq || die "jq required" "${EX_NODEP}"
```

! `cmd | while read -r x; do count=$((count+1)); done` — the loop body runs in a subshell; `count` is 0 afterwards. Use `while read … done < <(cmd)` (process substitution) instead.

---

## 5. Argument Handling

Help text and CLI ergonomics contract → [cli](../cli/STANDARDS.md). Semantic validation of untrusted input → [security](../security/STANDARDS.md) and [HARDENING §4](HARDENING.md#4-injection-vectors).

### 5.1 Usage

```bash
usage() {
  cat <<'EOF'                          # ! quoted delimiter — else $ and ` expand
Usage: deploy.sh <environment> [options]

Options:
  -f, --force    Skip confirmation prompt
  -h, --help     Show this help

Environment:
  AWS_PROFILE    AWS credential profile (required)
EOF
}
```

`usage` writes to stdout and does NOT exit; the caller chooses the code (`0` for `--help`, `2` for a usage error).

### 5.2 Parsing

```bash
parse_args() {
  while (( $# > 0 )); do
    case "$1" in
      -f|--force)   force=true; shift ;;
      -n|--dry-run) dry_run=true; shift ;;
      -h|--help)    usage; exit "${EX_OK}" ;;
      --)           shift; args+=("$@"); break ;;   # everything after -- is positional
      -*)           usage >&2; die "Unknown option: $1" "${EX_USAGE}" ;;
      *)            args+=("$1"); shift ;;
    esac
  done
}
```

| Approach | Use when |
|---|---|
| Manual `while` + `case` | Long options needed — bash. Handles `--` correctly |
| `getopts` | Short options only · POSIX `sh` scripts. Reset `local OPTIND=1` per call |
| ✗ `getopt(1)` | GNU vs BSD behaviour diverges — unusable portably |

Validate argument count before any work: `(( $# >= 1 )) || { usage >&2; exit "${EX_USAGE}"; }`.

### 5.3 Dependency Check

Check every external command before the first side effect, not at point of use. `command -v`, ✗ `which` — POSIX, builtin, no subprocess.

```bash
require_commands() {
  local -a missing=(); local cmd
  for cmd in "$@"; do
    command -v "${cmd}" >/dev/null 2>&1 || missing+=("${cmd}")
  done
  (( ${#missing[@]} == 0 )) || die "Missing commands: ${missing[*]}" "${EX_NODEP}"
}
```

---

## 6. Output Channels

| Channel | Content |
|---|---|
| `stdout` | Data only — results a caller may pipe or capture |
| `stderr` | Everything else — progress, warnings, errors, logs |

✗ mix them. A single progress line on stdout corrupts every downstream pipe.

### 6.1 `printf`, ✗ `echo`

`echo` behaviour with `-e`, `-n`, and backslashes is undefined across shells. `printf '%s\n' "$var"` is exact and portable. A variable is NEVER the format string: `printf '%s' "${var}"`, ✗ `printf "${var}"` — a `%s` in the data becomes a format directive.

### 6.2 Logging

```bash
log() {
  local level="$1"; shift
  printf '[%s] [%-5s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${level}" "$*" >&2
}
```

Timestamps in UTC, ISO-8601. Log field conventions → [observability](../observability/STANDARDS.md).

### 6.3 Colour

```bash
if [[ -t 2 && "${TERM:-dumb}" != "dumb" && -z "${NO_COLOR:-}" ]]; then
  readonly RED=$'\033[0;31m' GREEN=$'\033[0;32m' RESET=$'\033[0m'
else
  readonly RED='' GREEN='' RESET=''
fi
```

Gate on all three: `[[ -t 2 ]]` (a tty) · `TERM` not `dumb` · `NO_COLOR` unset. ✗ escape codes in redirected output — they poison logs and CI artefacts. ✗ `echo -e`; use `$'…'`. ✗ spinners in non-interactive scripts.

---

## 7. Script Structure

### 7.1 Executable Script

Fixed order: shebang → `set -euo pipefail` → description → constants → `source` → functions → `main()` → `main "$@"`.

```bash
#!/usr/bin/env bash
set -euo pipefail
#--- description block: purpose · usage · dependencies · environment (§1)

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly SCRIPT_NAME="${0##*/}"
readonly EX_OK=0 EX_ERR=1 EX_USAGE=2 EX_NODEP=3

source "${SCRIPT_DIR}/lib/logging.sh"

usage() { …; }; parse_args() { …; }; do_work() { …; }

main() {
  parse_args "$@"
  require_commands pg_dump aws
  do_work
}

main "$@"
```

! `main "$@"` on the LAST line — bash reads a script incrementally, so a script edited while running can execute a half-written body. A single trailing `main "$@"` makes that impossible.

`${BASH_SOURCE[0]}`, ✗ `$0` — `$0` is wrong when the script is sourced. `cd -- … && pwd -P` resolves symlinks; `--` protects against paths beginning with `-`.

### 7.2 Sourceable Library

```bash
#!/usr/bin/env bash
#--- lib/logging.sh — Logging helpers. Source; do not execute.

[[ -n "${_LIB_LOGGING_LOADED:-}" ]] && return 0   # include guard
readonly _LIB_LOGGING_LOADED=1

[[ "${BASH_SOURCE[0]}" != "${0}" ]] || {          # direct-execution guard
  printf 'lib/logging.sh must be sourced, not executed\n' >&2; exit 1
}

log_info() { printf '[INFO ] %s\n' "$*" >&2; }
```

| Rule | Detail |
|---|---|
| Include guard `_LIB_<NAME>_LOADED` | Double-sourcing must be a no-op — `readonly` re-assignment otherwise fails |
| Direct-execution guard | A library invoked as a program does nothing useful |
| ✗ `set -euo pipefail` in a library | The caller owns shell options; a library must not mutate them |
| ✗ `exit` in a library function | `return` a code — the caller decides whether it is fatal |
| ✗ `main` in a library | Libraries export functions, not entry points |

---

## 8. Common Patterns

### 8.1 Single Instance Lock

```bash
acquire_lock() {
  local lock_dir="/var/lock/${SCRIPT_NAME}.lock"
  mkdir "${lock_dir}" 2>/dev/null || die "Already running (${lock_dir})"
  trap 'rmdir "${lock_dir}"' EXIT
}
```

`mkdir` is atomic on every filesystem — create and test are one syscall. ✗ `[[ -f lock ]] && exit` then `touch lock` — the gap between test and create is a race. `flock(1)` is stronger, but Linux-only.

### 8.2 Retry with Backoff

Retry idempotent operations only. ✗ retry a non-idempotent POST without an idempotency key.

```bash
retry() {
  local -i max="$1" delay="$2"; shift 2
  local -i attempt=1
  until "$@"; do
    (( attempt >= max )) && die "Failed after ${max} attempts: $*"
    log WARN "Attempt ${attempt}/${max} failed; retrying in ${delay}s"
    sleep "${delay}"
    (( attempt++, delay *= 2 ))          # exponential
  done
}
```

### 8.3 Bounded Parallelism

```bash
readonly MAX_JOBS=4
for file in "${files[@]}"; do
  while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do wait -n; done
  process_file "${file}" &
done
wait                                     # ! omit → orphans outlive the script
```

`wait -n` requires bash 4.3+. `xargs -P` where available: `find . -print0 | xargs -0 -P4 -n1 gzip`.

### 8.4 Confirmation

! A prompt in a non-interactive context (CI, cron) hangs forever. Gate on `[[ -t 0 ]]`, fail loudly, offer an override flag.

```bash
confirm() {
  [[ "${force:-false}" == "true" ]] && return 0
  [[ -t 0 ]] || die "Refusing to prompt without a tty; pass --force"
  local response
  read -r -p "${1:-Continue?} [y/N] " response
  [[ "${response}" =~ ^[Yy]$ ]]
}
```

---

## 9. Anti-Patterns

| Anti-pattern | Failure | Correct |
|---|---|---|
| `for f in $(ls *.txt)` | Splits on whitespace in names | `for f in *.txt; do [[ -e "$f" ]] \|\| continue` |
| Unquoted `$var` | Word splitting + glob expansion | `"${var}"` |
| `cat file \| grep p` | Useless process | `grep p file` |
| `echo "$var"` | Mangles `-n`, `-e`, backslashes | `printf '%s\n' "${var}"` |
| `printf "${var}"` | Data interpreted as a format string | `printf '%s' "${var}"` |
| `` `cmd` `` | Cannot nest; escaping is unreadable | `$(cmd)` |
| `[ $var = x ]` | Breaks on empty / spaced values | `[[ "${var}" == x ]]` |
| `[ "$?" -eq 0 ]` | `[` overwrites `$?` | `if cmd; then` |
| `set +e` … `set -e` | Suppresses every error in the block | `\|\| status=$?` · `if ! cmd` |
| `local v=$(cmd)` | `local` masks the exit code of `cmd` | `local v; v=$(cmd)` |
| `export V=$(cmd)` | `export` masks the exit code | `V=$(cmd); export V` |
| `cd dir; cmd` | `cmd` runs in the wrong dir if `cd` fails | `(cd dir && cmd)` \| `cd dir \|\| die` |
| `rm -rf "$DIR/"*` | Deletes `/` when `DIR` is empty | `rm -rf "${DIR:?DIR unset}/"*` |
| `cmd \| while read` | Loop body's variables die with the subshell | `while read … done < <(cmd)` |
| `function f()` | Bashism with no benefit | `f() {` |
| `trap 'rm -f "$T"' EXIT` before `T` is set | `set -u` kills the trap itself | `"${T:-}"` inside a named handler |
| `kill -9` first | No graceful shutdown, no cleanup | `kill` → `wait` → `kill -9` |

---

## 10. Checklist

- [ ] Shebang is `#!/usr/bin/env bash` (or `sh`) — no hardcoded interpreter path
- [ ] `set -euo pipefail` on line 2, before any `source`
- [ ] `set -E` present whenever an `ERR` trap is used
- [ ] Description block declares purpose, usage, dependencies, and env vars
- [ ] Exit codes defined as `readonly` constants; none above `125`
- [ ] `die()` and `warn()` present and writing to stderr
- [ ] `trap cleanup EXIT` registered before the first temp file is created
- [ ] Trap handler guards every variable it touches (`"${var:-}"`)
- [ ] Zero `set +e` blocks — expected failures use `if !`, `||`, or `|| status=$?`
- [ ] Command substitutions assigned separately from `local` / `export`
- [ ] Every variable expansion double-quoted
- [ ] Every function variable declared `local`
- [ ] Arrays iterated as `"${arr[@]}"`; command lines built as arrays, not strings
- [ ] Functions declared with `name() {`, defined before `main`, ≤ 40 lines
- [ ] Positional arguments named on the first lines of each function
- [ ] Functions return data on stdout and status via `return` — no global writes
- [ ] Argument count validated before any side effect
- [ ] `usage()` present, writes to stdout, does not exit
- [ ] `--` handled as the end-of-options marker
- [ ] Dependencies checked with `command -v` before work begins
- [ ] stdout carries data only; all messages go to stderr
- [ ] `printf` used everywhere; zero `echo`; no variable used as a format string
- [ ] Colour gated on `[[ -t 2 ]]` · `TERM` · `NO_COLOR`
- [ ] `main "$@"` is the final line of every executable script
- [ ] Libraries have an include guard and a direct-execution guard, and set no shell options
- [ ] Prompts guarded by `[[ -t 0 ]]` with a non-interactive override flag
