# CLI Tool Standards

Rules for building command-line tools that compose well, fail clearly,
and work identically in interactive terminals and automated pipelines.

Derived from: Unix Philosophy, POSIX conventions, GNU Coding Standards,
12-Factor App (config), `errno.h` exit code conventions, `getopt` long
option style, and TTY/PTY terminal architecture.

Composable with: architecture/STANDARDS.md (CLI = Tier 3 interface),
error_handling/STANDARDS.md, configuration/STANDARDS.md,
observability/STANDARDS.md.

---

## Table of Contents

1. [CLI Design Philosophy](#1-cli-design-philosophy)
2. [Argument Parsing](#2-argument-parsing)
3. [Help & Usage](#3-help--usage)
4. [Input Handling](#4-input-handling)
5. [Output Formatting](#5-output-formatting)
6. [Exit Codes](#6-exit-codes)
7. [Color & Formatting](#7-color--formatting)
8. [Progress Reporting](#8-progress-reporting)
9. [Configuration](#9-configuration)
10. [Error Messages](#10-error-messages)
11. [Interactive vs Non-Interactive](#11-interactive-vs-non-interactive)
12. [Versioning](#12-versioning)
13. [Signal Handling](#13-signal-handling)
14. [Piping & Composition](#14-piping--composition)
15. [Scale Matrix](#15-scale-matrix)
16. [Checklist](#16-checklist)

---

## 1. CLI Design Philosophy

CLI is a Tier 3 interface (see architecture/STANDARDS.md §2). It adapts
user input into calls to Tier 2 services and formats Tier 1 results for
terminal output. ✗ domain logic in CLI layer — parse, delegate, format.

| Principle | Rule |
|---|---|
| Do one thing | One binary = one core task. Subcommands for related operations only |
| Composable | Read stdin, write stdout. Other tools can pipe in/out freely |
| Predictable | Same inputs → same outputs. ✗ hidden state between runs |
| Quiet by default | Data to stdout. Progress/diagnostics to stderr. ✗ unsolicited decoration |
| Fail loud | Non-zero exit + clear error on stderr. ✗ silent failures |
| Script-friendly | Machine-parseable output mode (`--json`, `--csv`). ✗ humans-only output |
| Offline-first | Work without network unless networking is core purpose |
| Fast startup | < 200ms to first output for simple operations. Lazy-load heavy deps |

### Naming

| Rule | Detail |
|---|---|
| Binary name | Lowercase, hyphen-separated. 1–3 words. `data-lint` ✓ `DataLinter` ✗ |
| Subcommands | Verb-first: `tool create`, `tool list`, `tool delete` |
| ✗ abbreviations in binary names | `img-resize` ✗ → `image-resize` ✓ ; except universally known: `ls`, `rm`, `cp` |
| Consistent verb vocabulary | `list` · `get` · `create` · `update` · `delete` · `validate` · `export` |

---

## 2. Argument Parsing

### Argument Types

| Type | When | Example |
|---|---|---|
| Positional | Primary input (1–2 max) | `tool <file>` |
| Flag (boolean) | Toggle behavior | `--verbose`, `--dry-run` |
| Option (key=value) | Named parameter with value | `--output dir/`, `--format json` |
| Subcommand | Distinct operation group | `tool db migrate` |

### Naming Conventions

| Rule | Detail |
|---|---|
| Long flags | `--kebab-case`. ✗ `--camelCase` · ✗ `--snake_case` |
| Short flags | Single letter, single dash: `-v`, `-o`. Reserve for frequent flags only |
| Boolean negation | `--no-color`, `--no-cache`. ✗ `--color=false` as only negation form |
| Value separator | `--output=file` and `--output file` both accepted |
| Repeatable | `-v` → verbose, `-vv` → debug, `-vvv` → trace. Document repetition semantics |

### Reserved Flags (every CLI tool must support)

| Flag | Short | Purpose |
|---|---|---|
| `--help` | `-h` | Print usage and exit 0 |
| `--version` | `-V` | Print version and exit 0 |
| `--verbose` | `-v` | Increase output verbosity |
| `--quiet` | `-q` | Suppress non-error output |
| `--no-color` | — | Disable colored output |
| `--json` | — | Machine-readable JSON output |

### Subcommand Rules

| Rule | Detail |
|---|---|
| Depth limit | Max 2 levels: `tool <cmd> <subcmd>`. ✗ `tool a b c d` |
| Global flags before subcommand | `tool --verbose create` ✓ |
| Subcommand-specific flags after | `tool create --name foo` ✓ |
| Default subcommand | ✗ implicit default. Bare `tool` → show help |
| `help` subcommand mirrors `--help` | `tool help create` = `tool create --help` |

---

## 3. Help & Usage

### `--help` Output Structure

Every `--help` output follows this order:

1. **One-line description** — what the tool does
2. **Usage pattern** — `Usage: tool [OPTIONS] <input>...`
3. **Positional arguments** — each with type and description
4. **Options table** — aligned columns: short, long, description, default
5. **Subcommand list** (if applicable) — name + one-line description
6. **Examples** — 2–4 real invocations showing common use cases
7. **Environment variables** — relevant env vars with prefix

### Help Formatting Rules

| Rule | Detail |
|---|---|
| Alignment | All option descriptions start at same column |
| Defaults shown | `--format <fmt>  Output format [default: table]` |
| Required marked | `<required>` for required, `[optional]` for optional |
| Width | Wrap at 80 columns. ✗ require wide terminal |
| No pager | ✗ pipe help through pager by default. User pipes to `less` if needed |
| Stderr for error-triggered help | `--help` → stdout. Bad usage → stderr with "try --help" hint |

### Man Pages

| Rule | Detail |
|---|---|
| Provide if installable system-wide | Package managers expect man pages |
| Sections | NAME, SYNOPSIS, DESCRIPTION, OPTIONS, EXIT STATUS, ENVIRONMENT, EXAMPLES, SEE ALSO |
| Generate from source | Single source of truth. ✗ hand-maintained man pages diverging from `--help` |

---

## 4. Input Handling

### Input Sources (precedence: first available wins)

| Priority | Source | When |
|---|---|---|
| 1 | Explicit argument | `tool file.txt` |
| 2 | `--input` flag | `tool --input file.txt` |
| 3 | stdin | `cat file.txt | tool` or `tool < file.txt` |

### stdin Rules

| Rule | Detail |
|---|---|
| Detect stdin | Check if stdin is a pipe/file (not TTY). ✗ block waiting on empty TTY stdin |
| `-` means stdin | `tool -` explicitly reads stdin even if TTY. Convention from POSIX |
| Combine with args | `tool --config cfg.yaml - < data.txt`. Positional `-` = stdin |
| Stream processing | Process stdin line-by-line when possible. ✗ slurp entire stdin into memory for large inputs |
| Binary safety | If tool processes binary, handle encoding explicitly. Document expected encoding |

### Format Detection

| Rule | Detail |
|---|---|
| By extension first | `.json` → JSON, `.csv` → CSV, `.yaml` → YAML |
| By content sniffing second | Stdin has no filename — detect by content patterns |
| Explicit override wins | `--input-format json` overrides all detection |
| Fail on ambiguity | If format undetectable and not specified → error with suggestion to use `--input-format` |

### Encoding

| Rule | Detail |
|---|---|
| Default UTF-8 | All text I/O defaults to UTF-8 |
| `--encoding` flag | Override when needed: `--encoding latin1` |
| BOM handling | Detect and strip UTF-8 BOM. ✗ emit BOM in output |

---

## 5. Output Formatting

### Channel Discipline

| Channel | Content | Example |
|---|---|---|
| stdout | Data output — results, records, computed values | Query results, converted files, generated data |
| stderr | Human messages — errors, warnings, progress, diagnostics | `Error: file not found`, progress bars, `--verbose` logs |

✗ mix data and messages on same channel. Pipeline consumers read stdout;
progress/errors must not corrupt data stream.

### Output Modes

| Mode | Flag | Use |
|---|---|---|
| Human table | (default when TTY) | Aligned columns, truncated to terminal width |
| JSON | `--json` | One JSON object per line (JSON Lines) or single JSON array |
| CSV | `--csv` | RFC 4180 compliant. Header row always present |
| Plain | `--plain` | Tab-separated, no headers. Maximum script friendliness |
| Quiet | `--quiet` | No stdout output. Exit code only |

### Output Rules

| Rule | Detail |
|---|---|
| Newline terminated | Every output line ends with `\n`. Last line included |
| No trailing decoration | ✗ summary lines ("3 results found") on stdout. Put on stderr |
| Consistent field order | JSON keys and CSV columns in same order across invocations |
| Null representation | JSON: `null`. CSV: empty field. Plain: empty string. ✗ "N/A" or "none" |
| Large output | Stream records as produced. ✗ buffer entire result set then dump |
| `--output` flag | Write to file instead of stdout: `--output results.json` |
| Filename `-` | `--output -` explicitly means stdout (default) |

---

## 6. Exit Codes

| Code | Meaning | When |
|---|---|---|
| 0 | Success | Operation completed as requested |
| 1 | General error | Runtime failure, unhandled exception, logic error |
| 2 | Usage error | Bad arguments, missing required flag, unknown subcommand |
| 3 | Data error | Input data malformed, validation failed, schema mismatch |
| 4 | Not found | Requested resource does not exist (file, record, endpoint) |
| 5 | Permission error | Insufficient access, read-only target, auth failure |
| 6 | Conflict | Resource already exists, version conflict, lock contention |
| 7 | Timeout | Operation exceeded time limit |
| 64–78 | BSD sysexits range | Use for domain-specific codes if 1–7 insufficient. Document in `--help` |
| 126 | Cannot execute | Command found but not executable |
| 127 | Not found | Command/dependency not found |
| 128+N | Signal N | Killed by signal: 130 = SIGINT (Ctrl+C), 137 = SIGKILL, 143 = SIGTERM |

### Exit Code Rules

| Rule | Detail |
|---|---|
| ✗ exit 0 on error | If operation did not complete successfully → non-zero. Always |
| Partial success | If tool processes N items and some fail → exit 1 + report failures on stderr + output successes on stdout |
| `--strict` flag | Optional: exit non-zero on any warning (for CI pipelines) |
| Document codes | List all exit codes in `--help` and man page EXIT STATUS section |
| Pipeline-friendly | Exit code reflects last operation's result, not cumulative |

---

## 7. Color & Formatting

### TTY Detection

| Condition | Behavior |
|---|---|
| stdout is TTY | Color and formatting enabled |
| stdout is pipe/file | Color and formatting disabled automatically |
| `--no-color` flag | Disable regardless of TTY |
| `NO_COLOR` env var set (any value) | Disable regardless of TTY. See https://no-color.org |
| `FORCE_COLOR` env var set | Enable regardless of TTY (for CI systems wanting color in logs) |
| `TERM=dumb` | Disable color |

Precedence: `--no-color` flag > `NO_COLOR` env > `FORCE_COLOR` env > TTY detection > `TERM` value.

### Color Usage Rules

| Rule | Detail |
|---|---|
| Red | Errors only |
| Yellow | Warnings |
| Green | Success confirmations |
| Blue/Cyan | Informational highlights, headings |
| Bold | Emphasis on key values (filenames, counts) |
| Dim | Secondary information (timestamps, metadata) |
| ✗ color as sole signal | Always pair color with text prefix: `error:`, `warn:`, `ok:` |
| ✗ background colors | Conflict with user terminal themes |
| Reset after every colored span | ✗ leak ANSI codes into subsequent output |

### Terminal Width

| Rule | Detail |
|---|---|
| Detect width | Read terminal columns. Default to 80 if undetectable |
| Truncate tables | Truncate columns to fit terminal width. Show `...` for overflow |
| ✗ hard-wrap prose | Let terminal wrap naturally. Only truncate structured data |

---

## 8. Progress Reporting

### Channel Rule

All progress output → stderr. ✗ progress on stdout — corrupts data stream.

### Verbosity Levels

| Level | Flag | Content |
|---|---|---|
| Silent | `--quiet` / `-q` | Errors only (stderr) |
| Normal | (default) | Start/finish messages, warnings, errors |
| Verbose | `-v` | + operational details (files processed, skipped, timing) |
| Debug | `-vv` | + internal state, decision points, config resolution |
| Trace | `-vvv` | + raw I/O, system calls, full stack traces |

### Progress Bar Rules

| Rule | Detail |
|---|---|
| Show when | Operation > 2 seconds expected and item count known |
| Format | `[###-------] 34% (170/500) Processing file.txt` |
| Update frequency | Max 10 updates/second. ✗ flood terminal with redraws |
| Pipe detection | ✗ render progress bar when stderr is not TTY — emit periodic line-based updates instead |
| Clear on completion | Replace progress bar with final summary line |
| ETA | Show estimated time remaining when > 10 seconds remain |

### Spinner Rules

| Rule | Detail |
|---|---|
| Show when | Operation duration unknown (network call, external process) |
| Location | stderr only |
| Disable when not TTY | Replace with periodic dot/line updates |

---

## 9. Configuration

### Config Discovery (cascade order — last wins)

| Priority | Source | Example |
|---|---|---|
| 1 (lowest) | Built-in defaults | Compiled into binary |
| 2 | System config | `/etc/tool/config.yaml` |
| 3 | User config | `~/.config/tool/config.yaml` (XDG_CONFIG_HOME) |
| 4 | Project config | `.tool.yaml` in project root (walk up from cwd) |
| 5 | Environment variables | `TOOL_OUTPUT_FORMAT=json` |
| 6 | Config file via flag | `--config /path/to/config.yaml` |
| 7 (highest) | CLI flags | `--format json` |

See configuration/STANDARDS.md for full cascade rules.

### Config File Rules

| Rule | Detail |
|---|---|
| Format | YAML or TOML. ✗ JSON for human-edited config (no comments). ✗ INI (limited nesting) |
| XDG compliance | Respect `XDG_CONFIG_HOME` (~/.config), `XDG_DATA_HOME` (~/.local/share), `XDG_CACHE_HOME` (~/.cache) |
| Create on demand | ✗ create config file on install. Create on `tool config init` or first write operation |
| Validate on load | Reject unknown keys with warning. ✗ silently ignore typos |
| `--config-dump` | Print resolved config from all sources. Show which source provided each value |
| Env var naming | Prefix with tool name, uppercase, underscores: `MYTOOL_LOG_LEVEL` |
| Nested env mapping | `MYTOOL_DB_HOST` → `db.host` in config file |

### Config Subcommands

| Subcommand | Purpose |
|---|---|
| `tool config init` | Generate default config file with comments |
| `tool config show` | Print resolved config (merged from all sources) |
| `tool config path` | Print config file locations searched |
| `tool config validate` | Check config file for errors |

---

## 10. Error Messages

### Error Message Structure

Every error message contains three parts:

1. **What failed** — specific operation that did not succeed
2. **Why it failed** — cause, including relevant values
3. **How to fix** — actionable suggestion when deterministic fix exists

Format: `error: <what>: <why> [→ <fix>]`

See error_handling/STANDARDS.md for full error taxonomy and boundary rules.

### Error Rules

| Rule | Detail |
|---|---|
| Prefix with `error:` | Machine-parseable prefix. `warning:` for non-fatal |
| Include context values | `error: cannot read config: /home/user/.config/tool/config.yaml: permission denied` |
| Suggest fix when known | `→ run: chmod 644 ~/.config/tool/config.yaml` |
| ✗ stack traces by default | Stack trace only at `-vv` or higher. Users need messages, not internals |
| ✗ "An error occurred" | ✗ generic messages. State exactly what failed |
| ✗ error codes without text | `E1234` alone means nothing. Always pair code with human description |
| One error per line | Each error on own line. Parseable by `grep` and log tools |
| Exit after fatal error | Print error → cleanup → exit non-zero. ✗ continue after unrecoverable |
| Aggregated errors | When validating multiple items: collect all errors, print all, then exit. ✗ stop at first |
| stderr always | All error output to stderr. ✗ errors on stdout |

---

## 11. Interactive vs Non-Interactive

### TTY Detection Rules

| Condition | Mode | Behavior |
|---|---|---|
| stdin is TTY + stdout is TTY | Interactive | Prompts, color, progress bars, confirmation dialogs |
| stdin is pipe OR stdout is pipe | Non-interactive | ✗ prompts, ✗ interactive elements, machine output |
| `--no-input` flag | Forced non-interactive | ✗ prompts — use defaults or fail |
| `--yes` / `-y` flag | Auto-confirm | Answer "yes" to all confirmation prompts |
| `CI=true` env var | Non-interactive | Same as `--no-input` |

### Prompt Rules

| Rule | Detail |
|---|---|
| Confirmation for destructive ops | `Delete 47 records? [y/N]:` — default is safe option (No) |
| Default shown in brackets | `[Y/n]` = default yes, `[y/N]` = default no |
| Timeout | Prompts timeout after 30s in interactive mode → use default |
| ✗ prompt in pipeline | If stdin is not TTY and confirmation needed → error + suggest `--yes` |
| Password/secret input | Disable echo. ✗ show characters. ✗ log input |
| Selection lists | Number each option. Accept number or exact text |
| ✗ multi-step wizards | If > 3 prompts needed → require config file or flags instead |

### Non-Interactive Guarantees

| Guarantee | Detail |
|---|---|
| Deterministic | Same flags + same input → same output. ✗ behavior changes based on TTY |
| No blocking reads | ✗ wait for user input when stdin is pipe and no data arrives |
| Fail-fast on missing input | If required value missing and no prompt possible → exit 2 immediately |
| Logging format | When not TTY: timestamps + structured format. When TTY: human-friendly |

---

## 12. Versioning

### `--version` Output

Single line: `tool-name 1.2.3`

Optional extended format with `-vv --version`:
```
tool-name 1.2.3
commit: abc1234
built: 2025-01-15T10:30:00Z
go: 1.22.0 / python: 3.12.1 / rust: 1.75.0
platform: linux/amd64
```

### Version Rules

| Rule | Detail |
|---|---|
| SemVer | MAJOR.MINOR.PATCH. Follow semver.org strictly |
| MAJOR bump | Breaking: removed flags, changed output format, changed exit codes |
| MINOR bump | New flags, new subcommands, new output fields (additive) |
| PATCH bump | Bug fixes, performance improvements, documentation |
| Pre-release | `1.2.3-beta.1` for unstable releases |
| ✗ 0.x in production | Tools used by others → 1.0+ with stability commitment |
| Deprecation warnings | Deprecated flags: warn for 2 minor versions before removal |
| Changelog | Maintain CHANGELOG.md. Every release documented |

### Compatibility Promises

| Category | Promise |
|---|---|
| Flag names | ✗ rename or remove without MAJOR bump |
| Exit codes | ✗ change meaning without MAJOR bump |
| stdout format | ✗ change field names/order in `--json` output without MAJOR bump |
| stderr format | No stability guarantee — human-readable output may change |
| Config file format | ✗ break existing config files without MAJOR bump + migration path |

---

## 13. Signal Handling

### Required Signal Handlers

| Signal | Code | Handler |
|---|---|---|
| SIGINT (Ctrl+C) | 130 | Graceful shutdown: stop work, flush buffers, cleanup temp files, exit 130 |
| SIGTERM | 143 | Same as SIGINT. Process manager sends TERM before KILL |
| SIGPIPE | 141 | Exit silently with 141. ✗ print error when downstream pipe closes |
| SIGHUP | 129 | Cleanup and exit. Optional: reload config if long-running |
| SIGQUIT (Ctrl+\\) | 131 | Dump debug state (goroutines, stack) then exit |

### Signal Handling Rules

| Rule | Detail |
|---|---|
| Double SIGINT = force quit | First SIGINT → graceful shutdown. Second SIGINT within 2s → immediate exit |
| Cleanup on all exits | Temp files removed, partial output deleted, locks released |
| Flush before exit | Flush stdout/stderr buffers before exiting |
| ✗ catch SIGKILL/SIGSTOP | Cannot be caught. Design cleanup to tolerate missing these |
| Atomic writes | Write to temp file → rename. SIGKILL mid-write leaves no corrupt output |
| Progress indication | On SIGINT during long operation: print what completed before exiting |
| Child process forwarding | Forward signals to child processes. ✗ leave orphan processes |

### Timeout Support

| Rule | Detail |
|---|---|
| `--timeout` flag | Set maximum operation duration: `--timeout 30s`, `--timeout 5m` |
| Duration format | Accept: `30s`, `5m`, `2h`, `1h30m`. ✗ raw seconds only |
| Timeout behavior | Same as SIGINT: graceful shutdown, cleanup, exit 7 |
| ✗ infinite by default for network ops | Network operations require default timeout. Document the default |

---

## 14. Piping & Composition

### Composability Rules

| Rule | Detail |
|---|---|
| Read stdin when piped | If stdin is a pipe, read from it. No special flags needed |
| Write stdout always | Primary data output goes to stdout. No exceptions |
| Line-buffered when piped | ✗ block-buffer stdout when piped. Flush each line for real-time pipeline processing |
| ✗ assume terminal width when piped | Output full-width data. ✗ truncate for 80 cols when stdout is pipe |
| Handle partial reads | If downstream closes pipe (SIGPIPE), exit cleanly. ✗ error message |
| Binary-safe piping | If tool handles binary data, pass through without encoding conversion |

### Pipeline Patterns

| Pattern | Composition |
|---|---|
| Filter | `tool list --json \| jq '.[] \| select(.status=="active")'` |
| Transform | `tool export --csv \| tool-b import --csv` |
| Fan-out | `tool list --json \| tee >(tool-a) \| tool-b` |
| Aggregate | `tool process file1 file2 file3` (multi-file as args, not pipeline) |

### Buffering Rules

| Scenario | Buffering |
|---|---|
| stdout is TTY | Line-buffered (default terminal behavior) |
| stdout is pipe | Line-buffered. ✗ block-buffered — breaks real-time pipelines |
| stderr always | Unbuffered or line-buffered |
| Large binary output | Block-buffered for performance. Document this exception |

### Multi-Input Conventions

| Rule | Detail |
|---|---|
| Files as arguments | `tool file1.txt file2.txt` — process each in order |
| Glob support | Tool handles globs if shell does not expand: `tool "*.csv"` |
| `--` separator | Arguments after `--` are literal, not flags: `tool -- --weirdfilename` |
| Mixed stdin + files | `tool file1.txt - file2.txt` — `-` reads stdin at that position |
| Recursive directory | `--recursive` / `-r` flag. ✗ recurse by default without flag |
