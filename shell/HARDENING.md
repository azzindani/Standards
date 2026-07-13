# Shell Hardening Standards

> Portability, file operations, injection defence, and test tooling for shell scripts that must survive hostile input and foreign platforms.

**ID** `shell/hardening` · **Tier** Language · **Version** 1.0
**Owns** bash vs POSIX · GNU vs BSD divergence · temp files · atomic writes · filename-safe traversal · shell injection vectors · secret handling in shell · shellcheck · shfmt · bats
**Defers to** script structure · strict mode · traps · quoting · functions → [shell](STANDARDS.md) · validation boundary · access control · secret storage → [security](../security/STANDARDS.md) · test pyramid · coverage · mocking policy → [testing](../testing/STANDARDS.md) · pipeline stages · gates → [cicd](../cicd/STANDARDS.md)
**Load with** [shell](STANDARDS.md) · [security](../security/STANDARDS.md) · [testing](../testing/STANDARDS.md)

---

## Table of Contents

1. [Bash vs POSIX](#1-bash-vs-posix)
2. [Platform Divergence](#2-platform-divergence)
3. [File Operations](#3-file-operations)
4. [Injection Vectors](#4-injection-vectors)
5. [Secrets and Permissions](#5-secrets-and-permissions)
6. [Static Analysis](#6-static-analysis)
7. [Testing](#7-testing)
8. [Checklist](#8-checklist)

---

## 1. Bash vs POSIX

Decide the target shell before the first line. The choice is binary — a "mostly POSIX" script that uses one bashism fails on `dash` at the worst moment.

| Script type | Target | Reason |
|---|---|---|
| CI pipeline · project automation · cron | bash | `pipefail` and arrays are mandatory |
| Docker entrypoint | `sh` | Alpine ships `busybox ash`; bash is absent |
| Public install script (`curl \| sh`) | `sh` | Runs on whatever the user has |
| macOS-targeting script | bash 4+ explicitly installed, or `sh` | `/bin/bash` on macOS is 3.2 (2007) |

### 1.1 Feature Matrix

| Feature | POSIX `sh` | bash |
|---|---|---|
| `[[ ]]` | ✗ | Yes — prefer over `[ ]` in bash |
| Arrays | ✗ | Yes |
| Associative arrays `local -A` | ✗ | bash 4+ |
| `set -o pipefail` | ✗ | Yes |
| `local` | Not POSIX, but supported everywhere | Yes |
| `=~` regex | ✗ | bash 3+ |
| `${var,,}` lowercase | ✗ | bash 4+ |
| `&>` redirect | ✗ | Yes |
| Process substitution `<()` | ✗ | Yes |
| `wait -n` | ✗ | bash 4.3+ |
| `$( )` · `$(( ))` | Yes | Yes |

### 1.2 macOS bash Is 3.2

! `/bin/bash` on macOS is bash 3.2. Anything bash 4+ breaks silently or with a syntax error: associative arrays · `${var,,}` · `wait -n` · `mapfile`/`readarray` · `**` globstar · `"${arr[@]}"` under `set -u` when empty.

Options: target bash 3.2 · require bash 4+ and assert it · use POSIX `sh`.

```bash
(( BASH_VERSINFO[0] >= 4 )) || die "bash 4+ required (found ${BASH_VERSION})"
```

### 1.3 POSIX Substitutions

| bash | POSIX `sh` |
|---|---|
| `[[ "$a" == "$b" ]]` | `[ "$a" = "$b" ]` — `==` is not POSIX inside `[ ]` |
| `echo "${var,,}"` | `printf '%s' "$var" \| tr '[:upper:]' '[:lower:]'` |
| `(( count++ ))` | `count=$((count + 1))` |
| `array+=("item")` | No equivalent — use positional params (`set --`) or a file |
| `read -r -a arr` | No equivalent |
| `source file` | `. file` |
| `cmd &> log` | `cmd > log 2>&1` |
| `<(cmd)` | Temp file + trap cleanup |

---

## 2. Platform Divergence

GNU coreutils (Linux) and BSD userland (macOS) share command names and diverge on flags. A script tested only on Linux is untested for macOS.

| Command | GNU (Linux) | BSD (macOS) |
|---|---|---|
| `sed -i` | `sed -i 's/a/b/' f` — no argument | `sed -i '' 's/a/b/' f` — empty argument REQUIRED |
| `readlink -f` | Supported | ✗ — use `realpath`, or `python3 -c` |
| `date -d '1 day ago'` | Supported | ✗ — `date -v-1d` |
| `date +%s` | Supported | Supported |
| `stat` | `stat -c '%s' f` | `stat -f '%z' f` |
| `grep -P` (PCRE) | Supported | ✗ — use `grep -E` |
| `mktemp` | `mktemp -d` | `mktemp -d -t prefix` — `-t` required |
| `find -printf` | Supported | ✗ — use `-exec` or `-print0` |
| `sort -h` | Supported | ✗ |
| `base64 -w0` | Supported | ✗ — `base64` wraps by default |
| `xargs -r` | Supported | ✗ — BSD `xargs` skips empty input anyway |

### 2.1 Handling Divergence

Ranked. Prefer the earliest that works.

| Rank | Strategy |
|---|---|
| 1 | Use only flags common to both — the intersection is large |
| 2 | Pick a portable tool: `awk`/`perl` over `sed -i`, `find -exec` over `-printf` |
| 3 | Detect the implementation once at startup, store the invocation in an array |
| 4 | Require GNU coreutils and assert it — acceptable only for CI-only scripts |

```bash
if sed --version >/dev/null 2>&1; then      # GNU sed accepts --version; BSD errors
  SED_INPLACE=(sed -i)
else
  SED_INPLACE=(sed -i '')
fi
"${SED_INPLACE[@]}" 's/old/new/' file.txt   # ✓ array — the empty arg survives expansion
```

! Detection must be by capability, never by `uname`. `uname` says nothing about which `sed` is first on `PATH` — Homebrew GNU coreutils on macOS breaks every `uname`-based branch.

---

## 3. File Operations

### 3.1 Temp Files

! `mktemp` for every temp file and directory. ✗ hardcoded `/tmp/myfile` — predictable names are a symlink-attack vector and a collision between concurrent runs.

```bash
readonly TMPDIR_SCRIPT="$(mktemp -d)"       # ✗ mktemp -d -t app  → BSD/GNU differ
trap 'rm -rf "${TMPDIR_SCRIPT:-}"' EXIT     # register BEFORE anything is written
tmpfile="$(mktemp "${TMPDIR_SCRIPT}/data.XXXXXX")"
```

Order is load-bearing: create the temp dir → register the trap → write. A trap registered after the first write leaks on any early exit. Trap mechanics → [shell §2.3](STANDARDS.md#2-error-handling).

### 3.2 Atomic Writes

Never write in place. Write to a temp file on the SAME filesystem, then `mv` — rename is atomic within a filesystem; a reader sees the old file or the new one, never a half-written one.

```bash
write_config() {
  local dest="$1" tmp
  tmp="$(mktemp "${dest}.XXXXXX")"          # same directory → same filesystem
  generate_config > "${tmp}" || { rm -f "${tmp}"; return 1; }
  chmod 644 "${tmp}"                        # mktemp creates 0600 — set the real mode
  mv -f "${tmp}" "${dest}"
}
```

✗ `generate_config > "${dest}"` — a crash mid-write leaves a truncated file that looks valid. ✗ `mv` across filesystems (it degrades to copy+unlink, which is not atomic).

### 3.3 Existence Tests

| Test | Asserts |
|---|---|
| `[[ -f "$p" ]]` | Regular file exists |
| `[[ -d "$p" ]]` | Directory exists |
| `[[ -r "$p" ]]` · `[[ -w "$p" ]]` · `[[ -x "$p" ]]` | Readable · writable · executable |
| `[[ -s "$p" ]]` | Exists and is non-empty |
| `[[ -e "$p" ]]` | Exists — ✗ when you actually mean `-f` |

Test for the property you depend on. `-e` on something you are about to `source` or read as a file is a bug waiting for a directory or a device node.

! Test-then-use is a TOCTOU race: the file can change between the test and the use. For anything security-relevant, act and handle the failure instead of testing first.

### 3.4 Filename-Safe Traversal

! Filenames may contain spaces, newlines, quotes, and leading dashes. Only NUL-delimited iteration is safe.

```bash
while IFS= read -r -d '' file; do           # ✓ NUL-delimited
  process "${file}"
done < <(find "${dir}" -type f -name '*.log' -print0)

for file in $(find "${dir}" -name '*.log'); do   # ✗ splits on whitespace in names
  process "${file}"
done
```

`IFS=` (empty) preserves leading and trailing whitespace · `-r` stops backslash mangling · `-d ''` reads to NUL.

Process substitution `< <(cmd)` over a pipe: a piped `while` loop runs in a subshell, so every variable it sets is lost. Globs are safe and simpler when the depth is one: `for f in *.log; do [[ -e "$f" ]] || continue; done` — the guard handles the no-match case, where the glob expands to itself.

Pass filenames to commands with `--` to terminate option parsing: `rm -- "${file}"`. Without it, a file named `-rf` is an argument list.

---

## 4. Injection Vectors

The validation boundary, allowlist policy, and threat model → [security](../security/STANDARDS.md). This section owns the shell-specific vectors: every one of them turns data into code.

### 4.1 ✗ `eval`

```bash
eval "${user_input}"                        # ✗ arbitrary code execution
bash -c "${user_input}"                     # ✗ identical
"${user_input}"                             # ✗ command name from a variable
$(printf '%s' "${user_input}")              # ✗ substitution as a command

case "${action}" in                         # ✓ allowlist — the only safe dispatch
  start|stop|restart) systemctl "${action}" myservice ;;
  *) die "Invalid action: ${action}" "${EX_USAGE}" ;;
esac
```

`eval` has no legitimate use in a production script. If a design appears to require it, the design is wrong — use an array, a function, or a `case` allowlist.

### 4.2 Vector Table

| Vector | Exploit | Defence |
|---|---|---|
| Unquoted expansion | `rm $file` with `file="a b"` → two arguments | Quote every expansion |
| Unquoted expansion | `file="*"` → glob expands to every file | Quote every expansion |
| `eval` / `bash -c "$v"` | Arbitrary code | ✗ — allowlist `case` |
| Command from a variable | `"$cmd"` where `cmd` is user-supplied | Allowlist the command name |
| Argument injection | `--flag` in a value → `curl "$url"` with `url="-o/etc/passwd"` | `--` before positional args: `curl -- "$url"` |
| Path traversal | `../../etc/passwd` in a filename | Resolve + prefix-check (§4.3) |
| Format-string | `printf "$user"` where `user` contains `%s` | `printf '%s' "$user"` |
| Sourcing untrusted files | `.env` writes `PATH` or defines a function | Verify ownership + mode before `source` |
| `IFS` poisoning | Attacker-controlled `IFS` in the environment | Set `IFS` explicitly at script start |
| `PATH` hijack | A malicious `curl` earlier on `PATH` | Set `PATH` explicitly in cron/systemd/setuid contexts |
| Heredoc expansion | `$(cmd)` inside an unquoted heredoc runs | `<<'EOF'` when the body is not a template |

### 4.3 Path Validation

```bash
validate_path() {
  local path="$1" base="$2" resolved
  resolved="$(realpath -m -- "${path}")"      # -m: need not exist yet
  [[ "${resolved}" == "${base}"/* ]] || die "Path traversal: ${path}"
  printf '%s\n' "${resolved}"
}
```

Resolve first, THEN compare — the order is load-bearing. A string check before resolution is defeated by `../`, by a symlink, and by `//`. `realpath` is absent on stock macOS (§2) — provide a fallback or require coreutils.

✗ trust a path from an argument, an environment variable, a config file, or a filename inside an archive.

---

## 5. Secrets and Permissions

Secret storage, rotation, and scope → [security](../security/STANDARDS.md). This section owns how a shell process leaks them.

### 5.1 Leak Channels

| Channel | Leak | Defence |
|---|---|---|
| Command arguments | `ps aux` · `/proc/*/cmdline` shows every argument to every user | ✗ `mysql -p"$PASS"` → env var or stdin |
| Environment | `/proc/<pid>/environ` — readable by the owner, inherited by children | Scope per-command: `VAR=x cmd`; `unset` after use |
| `set -x` | Traces the secret to stderr and into CI logs | ✗ `set -x` in any block touching a secret |
| Temp files | Default `0600` from `mktemp`, but `umask` can widen a redirect | `umask 077` before writing |
| Shell history | An interactive `export SECRET=…` persists | Never paste secrets into an interactive shell |
| Error messages | `die "auth failed with ${TOKEN}"` | Never interpolate a secret into a message |

```bash
mysql -p"${DB_PASS}" -e "$q"                # ✗ visible in the process list
MYSQL_PWD="${DB_PASS}" mysql -e "$q"        # ✓ per-command environment scope
printf '%s' "${TOKEN}" | docker login --password-stdin -u "${USER}"   # ✓ stdin
```

### 5.2 Permissions

```bash
umask 077                                   # before creating anything sensitive
printf '%s' "${token}" > "${TMPDIR_SCRIPT}/auth"

owner="$(stat -c '%u' -- "${config}" 2>/dev/null || stat -f '%u' -- "${config}")"
[[ "${owner}" == "$(id -u)" ]] || die "Refusing to source: ${config} not owned by $(id -un)"
source -- "${config}"
```

✗ `source` a file that is not owned by the current user · ✗ execute anything from a world-writable directory (`chmod o+w`) · ✗ `chmod 777`, ever. A sourced file executes with the script's full privileges — treat it as code, because it is.

---

## 6. Static Analysis

### 6.1 ShellCheck — Mandatory

! Every script passes `shellcheck` with zero warnings. A failing ShellCheck fails the build. No exceptions, no baselines.

| Invocation | Purpose |
|---|---|
| `shellcheck -x -s bash scripts/*.sh` | `-x` follows `source`d files · `-s` pins the dialect |
| `shellcheck --format=gcc …` | CI-parseable output |
| `shellcheck -S style …` | Raise the floor to include style hints |
| `.shellcheckrc` | Project-wide `external-sources=true` and `shell=bash` |

Suppression is per-line and carries a reason. ✗ a file-level `# shellcheck disable=` — it silences rules you have not read.

```bash
                    # shellcheck disable=SC2059  # format string is a validated constant
printf "${fmt}" "${args[@]}"
```

`-s` is not optional: ShellCheck infers the dialect from the shebang, and a `sh` script checked as bash passes with bashisms intact.

### 6.2 shfmt

`shfmt -i 2 -ci -bn -d .` in CI · `-w` locally. Formatting is decided by the tool, not in review. Indent 2 · switch-cases indented · binary operators at line start.

### 6.3 CI Wiring

Stage definitions and gate ordering → [cicd](../cicd/STANDARDS.md). Shell contributes exactly two gates, in this order:

| Gate | Command |
|---|---|
| Lint | `shfmt -d .` then `shellcheck -x scripts/*.sh` |
| Test | `bats --print-output-on-failure tests/` |

Lint before test — a script that does not parse cannot be meaningfully tested.

---

## 7. Testing

Pyramid, coverage, and what to test → [testing](../testing/STANDARDS.md). This section owns the shell tooling.

### 7.1 Framework

`bats-core` — the default. `shunit2` for POSIX `sh` scripts where bash is unavailable in the test environment.

| Helper library | Purpose |
|---|---|
| `bats-support` | Failure formatting; a prerequisite for the others |
| `bats-assert` | `assert_success` · `assert_failure N` · `assert_output --partial` |
| `bats-file` | `assert_file_exists` · `assert_file_permission` |

### 7.2 Structure

```bash
#!/usr/bin/env bats

setup() {
  TEST_TMPDIR="$(mktemp -d)"                     # per-test, not per-file
  export TEST_TMPDIR
}
teardown() { rm -rf "${TEST_TMPDIR}"; }

@test "deploy exits 2 with no arguments" {
  run ./deploy.sh
  [ "${status}" -eq 2 ]                          # ! assert the exit code, not just output
  [[ "${output}" == *"Usage"* ]]
}

@test "deploy rejects an unknown environment" {
  run ./deploy.sh not_an_env
  [ "${status}" -eq 1 ]
}
```

| Rule | Detail |
|---|---|
| One `.bats` file per script | `tests/deploy.bats` ↔ `scripts/deploy.sh` |
| `run` captures `${status}` and `${output}` | Without `run`, a non-zero exit aborts the test |
| Assert the exit code in every test | Output-only assertions pass on a script that crashed |
| `setup`/`teardown` isolate state | Fresh temp dir per test — tests must not share state or order |
| Cover the failure paths | Missing args · bad input · missing dependency · non-writable target |

### 7.3 Testability

A script whose logic lives inside `main` cannot be unit-tested. Guard the entry point so the file can be sourced by a test, then call the functions directly:

```bash
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then     # only when executed, not when sourced
  main "$@"
fi
```

Extract pure logic into functions that take arguments and print to stdout — parsers, validators, and formatters need no mocks. Push I/O to the edges so the untestable part is thin. ✗ mock the shell; ✗ stub `curl` by shadowing it on `PATH` inside a unit test — that is an integration test, and it belongs in one.

---

## 8. Checklist

- [ ] Target shell (bash | POSIX `sh`) chosen deliberately and matched by the shebang
- [ ] bash 4+ features guarded by a `BASH_VERSINFO` assertion, or avoided for macOS support
- [ ] Zero bashisms in any script whose shebang is `sh`
- [ ] Every GNU-only flag (`sed -i`, `readlink -f`, `date -d`, `stat -c`, `grep -P`, `base64 -w0`) either avoided or capability-detected
- [ ] Capability detection uses a probe, never `uname`
- [ ] Every temp file and directory created with `mktemp`; zero hardcoded `/tmp` paths
- [ ] Temp cleanup trap registered before the first write
- [ ] Every file write is atomic: temp file on the same filesystem → `chmod` → `mv -f`
- [ ] Existence tests assert the specific property (`-f`, `-d`, `-r`, `-s`) — not bare `-e`
- [ ] Directory traversal is NUL-delimited (`find -print0` + `read -r -d ''`); zero `for f in $(find …)`
- [ ] `--` terminates option parsing before every user-supplied path
- [ ] Zero `eval`, zero `bash -c "$var"`, zero command names taken from variables
- [ ] Dispatch on user input goes through an allowlist `case`
- [ ] Every user-supplied path resolved with `realpath` then prefix-checked against a base directory
- [ ] Variables are never used as `printf` format strings
- [ ] `PATH` and `IFS` set explicitly in cron, systemd, and setuid contexts
- [ ] Zero secrets in command arguments — environment scope or stdin only
- [ ] Zero `set -x` in any code path that touches a secret
- [ ] `umask 077` set before any sensitive file is written
- [ ] Ownership and mode verified before `source`ing any file
- [ ] `shellcheck -x -s <shell>` passes with zero warnings; the CI gate is blocking
- [ ] Zero file-level `shellcheck disable`; per-line suppressions carry a reason
- [ ] `shfmt -d` passes in CI
- [ ] Lint gate runs before the test gate
- [ ] Every script has a `.bats` file covering success AND failure paths
- [ ] Every test asserts an exit code, not just output
- [ ] Entry point guarded (`[[ "${BASH_SOURCE[0]}" == "${0}" ]]`) so tests can source the script
