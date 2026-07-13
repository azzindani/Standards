# CLI Standards

> Rules for command-line tools that compose in pipelines, fail loudly, and behave identically in a terminal and in a script.

**ID** `cli` · **Tier** Interface · **Version** 1.0
**Owns** flag + argument conventions · `--help` / `--version` contract · exit codes · stdout/stderr channel discipline · machine-readable output modes · TTY detection + `NO_COLOR` · interactive vs non-interactive rules · signal handling · pipeline composition · CLI compatibility promise (flag deprecation · output-format stability)
**Defers to** semver + changelog + release tagging → [git](../git/STANDARDS.md) · config cascade + precedence → [configuration](../configuration/STANDARDS.md) · error taxonomy + boundaries → [error_handling](../error_handling/STANDARDS.md) · secrets + credential input → [security](../security/STANDARDS.md) · structured logs + metrics → [observability](../observability/STANDARDS.md) · packaging + distribution → [dependencies](../dependencies/STANDARDS.md) · release pipeline → [cicd](../cicd/STANDARDS.md) · coverage + pyramid → [testing](../testing/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [error_handling](../error_handling/STANDARDS.md) · [configuration](../configuration/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Argument Parsing](#2-argument-parsing)
3. [Help & Usage](#3-help--usage)
4. [Input Handling](#4-input-handling)
5. [Output Formatting](#5-output-formatting)
6. [Exit Codes](#6-exit-codes)
7. [Color & Terminal](#7-color--terminal)
8. [Progress & Verbosity](#8-progress--verbosity)
9. [Configuration](#9-configuration)
10. [Error Messages](#10-error-messages)
11. [Interactive vs Non-Interactive](#11-interactive-vs-non-interactive)
12. [Compatibility Promise](#12-compatibility-promise)
13. [Signals & Cancellation](#13-signals--cancellation)
14. [Piping & Composition](#14-piping--composition)
15. [Scale Matrix](#15-scale-matrix)
16. [Checklist](#16-checklist)

---

## 1. Principles

CLI = Tier 3 Interface. Parse → delegate → format. ✗ domain logic in the CLI layer. See [architecture](../architecture/STANDARDS.md).

| Principle | Rule |
|---|---|
| Do one thing | One binary = one core task. Subcommands only for related operations |
| Composable | Reads stdin, writes stdout — other tools pipe in and out freely |
| Deterministic | Same flags + same input → same output. ✗ hidden state between runs |
| Idempotent | Re-running a completed command changes nothing further, or says so and exits 0 |
| Quiet by default | Data → stdout · diagnostics → stderr. ✗ unsolicited decoration |
| Fail loud | Non-zero exit + a clear message on stderr. ✗ silent failure |
| Scriptable | Machine-parseable mode (`--json`) on every command producing data |
| Never surprise a script | ✗ prompt · ✗ color · ✗ progress bar when not attached to a TTY |
| Fast startup | < 200 ms to first output for trivial operations — lazy-load heavy dependencies |

| Naming rule | Detail |
|---|---|
| Binary name | Lowercase, hyphen-separated, 1–3 words. `data-lint` ✓ · `DataLinter` ✗ |
| Subcommands | Verb-first: `tool create` · `tool list` · `tool delete` |
| Verb vocabulary | Reuse one set across subcommands: `list` · `get` · `create` · `update` · `delete` · `validate` · `export` |
| ✗ abbreviations in binary names | `img-resize` ✗ → `image-resize` ✓ ; universally known (`ls`, `rm`, `cp`) |

---

## 2. Argument Parsing

POSIX/GNU conventions. ✗ invent a new flag grammar.

| Type | Use | Example |
|---|---|---|
| Positional | Primary input — 2 maximum | `tool <file>` |
| Boolean flag | Toggle | `--verbose` · `--dry-run` |
| Option | Named parameter with a value | `--format json` |
| Subcommand | Distinct operation group | `tool db migrate` |

| Rule | Detail |
|---|---|
| Long flags | `--kebab-case`. ✗ `--camelCase` · ✗ `--snake_case` |
| Short flags | Single letter, single dash (`-v`). Reserved for frequent flags only |
| Bundling | Short boolean flags bundle: `-vq` ≡ `-v -q` |
| Value forms | `--output=file` and `--output file` both accepted |
| Boolean negation | Paired `--no-` form: `--no-color`, `--no-cache` |
| Repetition | `-v` verbose · `-vv` debug · `-vvv` trace. Document repetition semantics |
| `--` terminator | Everything after `--` is a literal operand, never a flag |
| Unknown flag | Exit 2 + suggest the closest match. ✗ silently ignore |
| Mutually exclusive flags | Detected at parse time → exit 2. ✗ last-one-wins silently |

### Reserved Flags

| Flag | Short | Behavior |
|---|---|---|
| `--help` | `-h` | Usage → stdout, exit 0 |
| `--version` | `-V` | Version → stdout, exit 0 |
| `--verbose` | `-v` | Raise verbosity (repeatable) |
| `--quiet` | `-q` | Suppress all non-error output |
| `--json` | — | Machine-readable output |
| `--no-color` | — | Disable ANSI styling |
| `--dry-run` | — | Show what would change; ✗ mutate anything |
| `--yes` | `-y` | Auto-confirm prompts |

### Subcommands

| Rule | Detail |
|---|---|
| Depth ≤ 2 | `tool <cmd> <subcmd>`. ✗ `tool a b c d` |
| Global flags before the subcommand | `tool --verbose create` |
| Subcommand flags after it | `tool create --name foo` |
| ✗ implicit default subcommand | Bare `tool` → print help, exit 0 |
| `tool help <cmd>` ≡ `tool <cmd> --help` | Same output |

---

## 3. Help & Usage

`--help` output, in order:

1. One-line description of what the tool does.
2. Usage pattern — `Usage: tool [OPTIONS] <input>...`.
3. Positional arguments — type + description each.
4. Options — aligned columns: short · long · description · default.
5. Subcommands (if any) — name + one-line description.
6. Examples — 2–4 real invocations.
7. Environment variables that affect behavior.
8. Exit codes.

| Rule | Detail |
|---|---|
| Alignment | Every option description starts at the same column |
| Defaults shown | `--format <fmt>   Output format [default: table]` |
| Requiredness marked | `<required>` vs `[optional]` |
| Width | Wrap at 80 columns. ✗ require a wide terminal |
| ✗ auto-pager | ✗ pipe help through a pager. The user pipes to `less` if they want it |
| Help channel | `--help` → stdout, exit 0. Usage **error** → message on stderr + exit 2 + `try 'tool --help'` hint |
| Man page | Provided when installed system-wide. Sections: NAME · SYNOPSIS · DESCRIPTION · OPTIONS · EXIT STATUS · ENVIRONMENT · EXAMPLES · SEE ALSO |
| Single source | Man page + shell completions generated from the same parser definition. ✗ hand-maintained copies that drift |

---

## 4. Input Handling

| Priority | Source | Form |
|---|---|---|
| 1 | Explicit positional argument | `tool file.txt` |
| 2 | `--input` option | `tool --input file.txt` |
| 3 | stdin | `cat file.txt \| tool` |

| Rule | Detail |
|---|---|
| Detect stdin | Read stdin when it is a pipe or file. ✗ block on an interactive TTY with no data |
| `-` means stdin | `tool -` reads stdin explicitly, even from a TTY. POSIX convention |
| Positional `-` | `tool a.txt - b.txt` — stdin is consumed at that position |
| Stream, don't slurp | Process line-by-line. ✗ load an unbounded input fully into memory |
| Format detection | Extension first → content sniffing second → `--input-format` overrides both |
| Ambiguity → error | Undetectable format + no explicit flag → exit 3 + suggest `--input-format` |
| Encoding | UTF-8 default · `--encoding` to override · strip a UTF-8 BOM on read · ✗ emit a BOM |
| Secrets | Accept via env var or file path. ✗ accept a secret as a command-line argument — it lands in `ps` and shell history. See [security](../security/STANDARDS.md) |

---

## 5. Output Formatting

### Channel Discipline

| Channel | Content |
|---|---|
| stdout | Data only — results, records, computed values |
| stderr | Everything else — errors, warnings, progress, logs, summaries |

✗ mix the two. Pipeline consumers read stdout; a stray progress line corrupts the data stream.

### Modes

| Mode | Flag | Contract |
|---|---|---|
| Human table | default when stdout is a TTY | Aligned columns, truncated to terminal width |
| JSON | `--json` | JSON Lines (one object per line) \| a single array. Valid, parseable, complete |
| CSV | `--csv` | RFC 4180. Header row always present |
| Plain | `--plain` | Tab-separated, no header. Maximum script friendliness |
| Quiet | `--quiet` | No stdout. Exit code carries the result |

| Rule | Detail |
|---|---|
| Machine mode is exact | `--json` emits **only** JSON on stdout. Warnings, progress, and timing go to stderr — one stray line breaks every parser |
| Newline-terminated | Every line ends with `\n`, including the last |
| ✗ trailing decoration on stdout | "3 results found" → stderr |
| Stable field order | Same key/column order across invocations |
| Null representation | JSON `null` · CSV empty field · plain empty string. ✗ `"N/A"` · ✗ `"none"` |
| Stream large output | Emit records as produced. ✗ buffer the full result set then dump |
| `--output <file>` | Write to a file instead of stdout. `--output -` = stdout |
| Atomic file output | Write to a temp file → rename. A crash mid-write leaves no truncated artifact |

---

## 6. Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success — the operation completed as requested |
| 1 | General error — runtime failure, unhandled condition |
| 2 | Usage error — bad arguments, missing required flag, unknown subcommand |
| 3 | Data error — input malformed, validation failed, schema mismatch |
| 4 | Not found — requested resource does not exist |
| 5 | Permission error — insufficient access, read-only target, auth failure |
| 6 | Conflict — already exists, version conflict, lock contention |
| 7 | Timeout — operation exceeded its time limit |
| 64–78 | BSD `sysexits` range — domain-specific codes when 1–7 are insufficient. Document in `--help` |
| 126 | Found but not executable |
| 127 | Command or dependency not found |
| 128+N | Killed by signal N — 130 SIGINT · 141 SIGPIPE · 143 SIGTERM |

| Rule | Detail |
|---|---|
| ✗ exit 0 on failure | Anything short of the requested outcome → non-zero. Always |
| Partial success | Some items failed → exit 1 · successes on stdout · failures on stderr |
| `--strict` | Optional: promote any warning to a non-zero exit, for CI |
| Codes are documented | `--help` and the man page EXIT STATUS section list every code the tool returns |
| Codes are contract | Meaning of a code never changes without a major release (§12) |

---

## 7. Color & Terminal

Precedence, highest first: `--no-color` flag → `NO_COLOR` env → `FORCE_COLOR` env → TTY detection → `TERM` value.

| Condition | Behavior |
|---|---|
| stdout is a TTY | Color + styling enabled |
| stdout is a pipe or file | Color disabled automatically — ✗ ANSI escapes into a redirect |
| `--no-color` | Disabled, unconditionally |
| `NO_COLOR` set to any value | Disabled, unconditionally (no-color.org) |
| `FORCE_COLOR` set | Enabled even when not a TTY — for CI log renderers |
| `TERM=dumb` | Disabled |

| Rule | Detail |
|---|---|
| Red · yellow · green | Errors · warnings · success. ✗ other meanings |
| Blue/cyan · bold · dim | Headings · key values · secondary detail |
| ✗ color as the sole signal | Always pair with a text prefix (`error:`, `warn:`, `ok:`) — color-blind users and captured logs lose it |
| ✗ background colors | They collide with user terminal themes |
| Reset every span | ✗ leak ANSI state into subsequent output or into the shell prompt |
| Width | Detect terminal columns; default 80 when undetectable. Truncate structured columns, ✗ hard-wrap prose |
| ✗ width truncation when piped | A pipe has no width — emit full values |

---

## 8. Progress & Verbosity

All progress and diagnostics → stderr. ✗ progress on stdout.

| Level | Flag | Content |
|---|---|---|
| Silent | `--quiet` / `-q` | Errors only |
| Normal | default | Start/finish, warnings, errors |
| Verbose | `-v` | + operational detail — items processed, skipped, timing |
| Debug | `-vv` | + internal state, decision points, resolved configuration |
| Trace | `-vvv` | + raw I/O, full stack traces |

| Rule | Detail |
|---|---|
| Progress bar shown when | Expected duration > 2 s **and** the item count is known **and** stderr is a TTY |
| Spinner shown when | Duration unknown (network call, external process) and stderr is a TTY |
| Not a TTY | ✗ render a bar or spinner — emit periodic line-based updates instead |
| Redraw rate | ≤ 10 updates/second |
| Completion | Replace the bar with a single summary line |
| ETA | Show when more than 10 s remain |
| Machine mode | `--json` → ✗ any progress rendering that could reach stdout |

---

## 9. Configuration

Cascade, precedence rules, and secret sourcing → [configuration](../configuration/STANDARDS.md). CLI-specific bindings only:

| Priority | Source |
|---|---|
| 1 (lowest) | Built-in defaults |
| 2 | System config — `/etc/tool/config.yaml` |
| 3 | User config — `$XDG_CONFIG_HOME/tool/config.yaml` |
| 4 | Project config — `.tool.yaml`, discovered by walking up from cwd |
| 5 | Environment variables — `TOOL_OUTPUT_FORMAT=json` |
| 6 | `--config <path>` |
| 7 (highest) | CLI flags |

| Rule | Detail |
|---|---|
| Format | YAML \| TOML. ✗ JSON for human-edited config — no comments |
| XDG compliance | Respect `XDG_CONFIG_HOME` · `XDG_DATA_HOME` · `XDG_CACHE_HOME` |
| ✗ create files on install | Create config on `tool config init` or on first write |
| Validate on load | Unknown key → warning naming the key. ✗ silently ignore typos |
| Env var naming | `TOOLNAME_` prefix, uppercase, `_` for nesting: `MYTOOL_DB_HOST` → `db.host` |
| Introspection | `tool config show` prints the resolved config **and the source of each value** |
| Config subcommands | `config init` · `config show` · `config path` · `config validate` |

---

## 10. Error Messages

Every error states three things, in order: **what failed** · **why** · **how to fix it** (when a deterministic fix exists).

Format: `error: <what>: <why>` followed by an optional `→ <fix>` line.

| Rule | Detail |
|---|---|
| Prefix | `error:` for fatal · `warning:` for non-fatal — machine-greppable |
| Include the values | `error: cannot read config: /home/u/.config/tool/config.yaml: permission denied` |
| Suggest the fix | `→ run: chmod 644 ~/.config/tool/config.yaml` |
| ✗ generic messages | "An error occurred" tells the user nothing |
| ✗ bare error codes | `E1234` alone is unusable — always pair a code with human text |
| ✗ stack traces by default | Traces appear at `-vv` or higher only |
| One error per line | Greppable, log-parseable |
| Aggregate validation | Collect all failures → print all → exit once. ✗ stop at the first |
| stderr always | ✗ an error on stdout, ever |
| Exit after fatal | Print → clean up → exit non-zero. ✗ continue past an unrecoverable failure |

---

## 11. Interactive vs Non-Interactive

| Condition | Mode |
|---|---|
| stdin **and** stdout are TTYs | Interactive — prompts, color, progress bars allowed |
| Either is a pipe/file | Non-interactive — ✗ prompts, ✗ interactive UI |
| `--no-input` | Forced non-interactive |
| `CI` env var set | Forced non-interactive |
| `--yes` / `-y` | Auto-confirm every prompt |

| Rule | Detail |
|---|---|
| ✗ prompt in non-interactive mode | Missing required input → exit 2 immediately with the flag that would supply it. ✗ hang waiting on stdin |
| Destructive operations confirm | `Delete 47 records? [y/N]:` — the default is the **safe** option |
| Default marked | `[Y/n]` = yes default · `[y/N]` = no default |
| Prompt timeout | 30 s in interactive mode → take the default |
| Secret input | Echo disabled · ✗ printed · ✗ logged · ✗ stored in history |
| ✗ multi-step wizards | More than 3 prompts → require flags or a config file instead |
| Determinism | The same flags + input produce the same result whether or not a TTY is attached; only *rendering* may differ |

---

## 12. Compatibility Promise

Semver rules, changelog format, and release tagging → [git](../git/STANDARDS.md). ✗ restate the MAJOR/MINOR/PATCH table here. This section defines only what a CLI's **public surface** is and how it may change.

The CLI's public contract: flag names + semantics · subcommand names · exit code meanings · `--json` / `--csv` output schema · config file schema · environment variable names.

| Surface | Stability |
|---|---|
| Flag + subcommand names | ✗ rename \| remove without a major release |
| Exit code meanings | ✗ change without a major release |
| `--json` / `--csv` schema | Field **additions** are minor. Rename, removal, reorder, or type change → major |
| Config file schema | ✗ break existing files without a major release **and** an automated migration path |
| Environment variable names | ✗ rename without a major release |
| stderr text | No stability guarantee — human-readable, may change any release. ✗ parse stderr |
| Human table output | No stability guarantee. Scripts use `--json` |

### Flag Deprecation Protocol

Ordered — ✗ skip a step:

1. Introduce the replacement flag. Both accepted, identical behavior.
2. Deprecated flag emits `warning: --old-flag is deprecated → use --new-flag` on **stderr** (never stdout) on every invocation.
3. Mark it deprecated in `--help` and in the changelog.
4. Hold both for **≥ 2 minor releases**.
5. Remove only in a major release. Removed flag → exit 2 + a message naming the replacement. ✗ silent removal · ✗ silently ignore.

`--version` prints a single line: `tool-name 1.2.3`. Extended build metadata at higher verbosity, one field per line: `commit` · `built` (ISO 8601 UTC) · `runtime` version · `platform`.

---

## 13. Signals & Cancellation

| Signal | Exit | Handler |
|---|---|---|
| SIGINT (Ctrl+C) | 130 | Graceful: stop work · flush buffers · remove temp + partial files · exit |
| SIGTERM | 143 | Same as SIGINT — process managers send TERM before KILL |
| SIGPIPE | 141 | Exit silently. ✗ print an error when a downstream reader closes (`tool \| head`) |
| SIGHUP | 129 | Clean up and exit; long-running daemons may reload config instead |
| SIGQUIT | 131 | Dump debug state, then exit |
| SIGKILL · SIGSTOP | — | ✗ catchable. Design cleanup to tolerate their absence |

| Rule | Detail |
|---|---|
| Double SIGINT | First → graceful shutdown. Second within 2 s → exit immediately |
| Cleanup on every exit path | Temp files removed · partial output deleted · locks released |
| Atomic writes | Temp file → rename. A kill mid-write leaves no corrupt output |
| Flush before exit | stdout and stderr buffers flushed |
| Forward to children | Signals propagate to child processes. ✗ leave orphans |
| Report progress on interrupt | State what completed before exiting |
| `--timeout` | Duration format: `30s` · `5m` · `1h30m`. ✗ bare seconds only. Timeout behaves as SIGINT → exit 7 |
| ✗ unbounded network operations | Every network call has a default timeout, and it is documented |

---

## 14. Piping & Composition

| Rule | Detail |
|---|---|
| Read stdin when piped | No special flag required |
| Line-buffered when piped | ✗ block-buffer stdout into a pipe — it stalls real-time pipelines. Exception: large binary output, documented |
| stderr unbuffered | Diagnostics appear when they happen |
| Handle SIGPIPE cleanly | `tool \| head -5` exits quietly |
| ✗ terminal assumptions when piped | No width truncation, no color, no cursor control |
| Binary-safe | Pass binary data through without re-encoding |
| Multiple inputs | Files as positional args, processed in order |
| `--recursive` / `-r` | Directory recursion is opt-in. ✗ recurse by default |
| Composition target | The tool works correctly in `tool \| head`, `tool \| grep`, `tool \| wc -l`, and `tool --json \| jq` |

---

## 15. Scale Matrix

| Capability | Script (< 200 LOC) | Production Tool | Platform CLI |
|---|---|---|---|
| `--help` | Required | Required + examples | Required + man page + completions |
| `--version` | — | Required | Required + build metadata |
| Exit codes | 0/1 | Full table (§6) | Full table + documented domain codes |
| `--json` output | — | Required | Required + schema stability guarantee |
| `NO_COLOR` + TTY detection | — | Required | Required |
| Signal handling | — | SIGINT + SIGPIPE | Full table (§13) |
| Config file cascade | — | Required | Required + `config` subcommand |
| Subcommands | — | If needed | Required |
| Deprecation protocol | — | Required (§12) | Required + migration tooling |
| Progress reporting | — | For operations > 2 s | Required |

---

## 16. Checklist

- [ ] `--help` / `-h` prints structured usage to stdout and exits 0
- [ ] `--version` / `-V` prints `name version` to stdout and exits 0
- [ ] All long flags are `--kebab-case`; `--` terminator supported
- [ ] Positional arguments limited to 2; unknown flag → exit 2 with a suggestion
- [ ] stdin read automatically when piped; `-` accepted as explicit stdin
- [ ] No secret is accepted as a command-line argument
- [ ] Data → stdout, diagnostics → stderr, with zero mixing
- [ ] `--json` emits only valid JSON on stdout — no warnings, progress, or timing
- [ ] Output is newline-terminated with a stable field order
- [ ] File output written to a temp file, then renamed
- [ ] Exit 0 only on success; exit 2 on usage error; every code documented in `--help`
- [ ] Color auto-disabled when stdout is not a TTY; `NO_COLOR` respected
- [ ] Color never the sole signal — always paired with a text prefix
- [ ] Progress bars and spinners suppressed when stderr is not a TTY
- [ ] Every error states what failed, why, and how to fix it, prefixed `error:`
- [ ] Validation errors aggregated — all reported, not just the first
- [ ] No stack trace at default verbosity
- [ ] No prompt when stdin is not a TTY or `CI` is set → exit 2 instead of hanging
- [ ] Destructive operations confirm, defaulting to the safe answer; `--yes` bypasses
- [ ] `--dry-run` mutates nothing
- [ ] Config resolved by cascade; `config show` reveals the source of each value
- [ ] Deprecated flags warn on stderr for ≥ 2 minor releases before removal
- [ ] `--json` schema, flag names, and exit code meanings unchanged within a major version
- [ ] SIGINT and SIGTERM shut down gracefully; SIGPIPE exits silently
- [ ] Temp and partial files removed on every exit path
- [ ] Network operations have a documented default timeout
- [ ] Verified in a pipeline: `tool \| head`, `tool \| grep`, `tool --json \| jq`
