# Python Standards

> Idiomatic Python: style, typing, packaging, async, and the uv · ruff · mypy toolchain.

**ID** `python` · **Tier** Language · **Version** 1.0
**Owns** Python style · identifier naming · type hints · uv packaging · import order · dataclass/Pydantic selection · asyncio idioms · pytest/ruff/mypy invocation · Python anti-patterns
**Defers to** test strategy + coverage thresholds + mocking policy → [testing](../testing/STANDARDS.md) · error taxonomy + boundaries + recovery → [error_handling](../error_handling/STANDARDS.md) · lockfile + pinning + supply-chain policy → [dependencies](../dependencies/STANDARDS.md) · layering + dependency direction → [architecture](../architecture/STANDARDS.md) · file + directory naming → [directory](../directory/STANDARDS.md) · pipeline stages → [cicd](../cicd/STANDARDS.md) · budgets + profiling method → [performance](../performance/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md) · [testing](../testing/STANDARDS.md) · [error_handling](../error_handling/STANDARDS.md) · [dependencies](../dependencies/STANDARDS.md)

---

## Table of Contents

1. [Baseline & Toolchain](#1-baseline--toolchain)
2. [Style & Naming](#2-style--naming)
3. [Type Hints](#3-type-hints)
4. [Project Structure](#4-project-structure)
5. [Packaging & Environments](#5-packaging--environments)
6. [Imports](#6-imports)
7. [Data Models](#7-data-models)
8. [Exceptions](#8-exceptions)
9. [Strings & Logging](#9-strings--logging)
10. [Async](#10-async)
11. [Testing Tools](#11-testing-tools)
12. [Lint · Format · Typecheck](#12-lint--format--typecheck)
13. [Performance Idioms](#13-performance-idioms)
14. [Anti-Patterns](#14-anti-patterns)
15. [Checklist](#15-checklist)

---

## 1. Baseline & Toolchain

Baseline **Python 3.12**. 3.13 permitted once every pinned dependency publishes wheels for it.

| Job | Tool | ✗ Superseded |
|---|---|---|
| Package + env + Python version | `uv` | `pip` · `pip-tools` · `poetry` · `pipenv` · `conda` · `virtualenv` |
| Lint + format + import sort | `ruff` | `black` · `isort` · `flake8` · `pylint` · `pyupgrade` |
| Type check | `mypy --strict` \| `pyright` | — |
| Test | `pytest` | `unittest` for new code · `nose` |
| Build backend + metadata | `hatchling` + `pyproject.toml` | `setup.py` · `setup.cfg` · `requirements.txt` |

One config file: `pyproject.toml`. ✗ scatter tool config across `.flake8`, `setup.cfg`, `tox.ini`.

---

## 2. Style & Naming

PEP 8 baseline. Deviations below are the only ones permitted.

| PEP 8 | Override |
|---|---|
| Line length 79 | **100** — ruff `line-length = 100` |
| Trailing comma optional | **Required** in multi-line collections — stable diffs |
| Quote style unspecified | Double quotes |

### Identifier Naming

| Construct | Convention | Example |
|---|---|---|
| Module | `snake_case` | `data_loader` |
| Class · Exception · TypedDict | `PascalCase` | `DataLoader` · `ConfigError` |
| Function · method · variable | `snake_case` | `load_data` |
| Constant | `UPPER_SNAKE` | `MAX_RETRIES` |
| Private | `_leading_underscore` | `_internal_cache` |
| Name-mangled | `__double_leading` | Rare — prefer `_single` |
| Type variable | `PascalCase` + `T` | `ItemT` · `ResponseT` |

File and directory naming → [directory](../directory/STANDARDS.md).

### Docstrings

Google style on every public module, class, function. ✗ docstring on private helper unless logic non-obvious. ✗ restate type hints in the docstring — they are in the signature.

```python
def fetch_records(query: str, limit: int = 100) -> list[Record]:
    """Fetch records matching query from primary store.

    Args:
        limit: Max rows. 0 → unlimited.

    Raises:
        QueryError: Query syntax invalid.
    """
```

---

## 3. Type Hints

Required on every public function, method, and module-level variable. Internal helpers typed too — `disallow_untyped_defs = true`.

| Rule | Detail |
|---|---|
| Return type always explicit | Including `-> None` |
| `Optional[X]` → `X \| None` | PEP 604 union syntax |
| `Dict`/`List`/`Tuple`/`Set` → `dict`/`list`/`tuple`/`set` | Lowercase builtins |
| `Any` requires a comment | State why the type is unknowable |
| `cast()` requires a comment | State why the cast is sound |
| `# type: ignore` requires an error code | `# type: ignore[attr-defined]` — bare ignore ✗ |
| `py.typed` marker in every distributed package | Otherwise consumers get no types |
| Structural typing over ABC inheritance | `typing.Protocol` — `class Serializable(Protocol): def to_dict(self) -> dict[str, object]: ...` |

Gradual typing: new code fully typed from day one · untyped code typed on touch · mypy strict in CI · ✗ merge with type errors.

`[tool.mypy]` → `strict = true` · `warn_unreachable = true` · `disallow_untyped_defs = true`.

---

## 4. Project Structure

| Layout | When | Root |
|---|---|---|
| **src** | Library · PyPI package · multi-package repo | `src/mylib/` |
| **flat** | App · script · CLI · MCP server | `myapp/` |

src layout is mandatory for anything published to an index — it prevents importing the working tree instead of the installed package.

```text
project-root/
├── pyproject.toml · uv.lock · .python-version
├── src/mylib/__init__.py · py.typed · core.py · models.py · _internal.py
└── tests/conftest.py · test_core.py
```

### `__init__.py`

| Rule | Detail |
|---|---|
| Every package directory has one | Explicit packages only — ✗ namespace packages by accident |
| Contains imports + `__all__` only | ✗ logic · ✗ side effects · ✗ I/O at import time |
| `__all__` defined | Declares public surface, controls `import *` |

```python
from .core import Engine
from .models import Config, Result

__all__ = ["Config", "Engine", "Result"]
```

Layering and dependency direction → [architecture](../architecture/STANDARDS.md).

---

## 5. Packaging & Environments

`uv` performs every package, environment, and interpreter operation.

| Rule | Detail |
|---|---|
| ✗ `setup.py` · `setup.cfg` | Dead formats — `pyproject.toml` only |
| ✗ `requirements.txt` as source of truth | `uv.lock` — deterministic, cross-platform, hash-verified |
| ✗ bare `pip install` | `uv add` \| `uv sync` |
| `uv.lock` committed | Always, including for applications |
| `.python-version` committed | Pins interpreter; uv downloads it if absent |
| `.venv/` gitignored | One venv per project, in project root |
| ✗ system Python for project work | ✗ `conda` · ✗ `virtualenv` |

```toml
[project]
name = "myproject"
requires-python = ">=3.12"
dependencies = ["httpx>=0.27", "pydantic>=2.7"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pytest>=8", "pytest-cov>=5", "mypy>=1.10", "ruff>=0.5"]
```

```bash
uv sync                  # install exactly what uv.lock says
uv add httpx             # add dep + update lock
uv add --dev pytest      # add dev dep
uv run pytest -x         # run inside the venv without activating
uv lock --upgrade        # deliberate lock refresh
```

Pinning policy, supply-chain review, and vulnerability scanning → [dependencies](../dependencies/STANDARDS.md).

---

## 6. Imports

Three groups, blank-line separated, enforced by ruff `I`: stdlib → third-party → first-party.

| Rule | Detail |
|---|---|
| Absolute imports | `from myapp.models import User` |
| Relative imports | Permitted only within the same package: `from .models import User` |
| ✗ wildcard imports | `from module import *` outside `__init__.py` |
| ✗ aliasing | Except name collision or established convention (`import numpy as np`) |
| ✗ `import a, b` on one line | One module per `import` statement |
| ✗ side effects at import time | No I/O, no network, no mutation of global state |
| `TYPE_CHECKING` block for cycle-breaking | Import used only in annotations |

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.engine import Engine   # annotation-only → no runtime import → no cycle
```

---

## 7. Data Models

| Need | Use |
|---|---|
| Internal data container | `@dataclass` |
| Immutable · hashable · dict key | `@dataclass(frozen=True, slots=True)` |
| Untrusted external data (API · config · DB row) | `pydantic.BaseModel` |
| Many instances, fixed attributes | `@dataclass(slots=True)` |
| Lightweight positional record, tuple-compatible | `typing.NamedTuple` |

Validation of external input is a security boundary — Pydantic (or equivalent) is mandatory there, never a raw `dict`.

```python
@dataclass(frozen=True, slots=True)
class CacheKey:
    namespace: str
    key: str

@dataclass
class ServerConfig:
    host: str
    port: int = 8080
    tags: list[str] = field(default_factory=list)   # ✓ factory — ✗ tags: list = []
```

```python
class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    age: int = Field(ge=0, le=150)

    @field_validator("email")
    @classmethod
    def normalize(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("invalid email")   # → pydantic ValidationError at the boundary
        return v.lower()
```

| ✗ | → |
|---|---|
| Plain `dict` for structured data | `dataclass` \| Pydantic model |
| `TypedDict` for runtime validation | Pydantic — `TypedDict` has zero runtime checks |
| Pydantic for internal-only data | `dataclass` — lower overhead |
| Mutable default on a field | `field(default_factory=...)` |

---

## 8. Exceptions

Error taxonomy, boundary placement, and recovery policy → [error_handling](../error_handling/STANDARDS.md). Python mechanism below.

| Rule | Detail |
|---|---|
| ✗ bare `except:` | Catches `SystemExit` · `KeyboardInterrupt` — name the type |
| ✗ `except Exception` below the boundary | Broad catch only at the top-level boundary |
| ✗ `except ...: pass` | Silent swallow — the failure becomes invisible |
| ✗ `except ...: return None` | Caller cannot distinguish "absent" from "failed" |
| Chain always | `raise NewError(...) from err` — ✗ drop `__cause__` |
| One project base exception | Every custom exception inherits from it |
| Resource cleanup via context manager | `contextlib.contextmanager` · `asynccontextmanager` — ✗ manual `try/finally` chains |

```python
class AppError(Exception): ...
class ConfigError(AppError): ...
class ValidationError(AppError): ...
```

```python
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    raise ValidationError(f"invalid JSON: {e}") from e   # ✓ specific catch + chain
```

```python
async def handle(request: Request) -> Response:          # ✓ boundary — the only broad catch
    try:
        return Response(data=await process(request))
    except AppError as e:
        return Response(error=str(e), status=400)
    except Exception:
        logger.exception("unhandled")
        return Response(error="internal error", status=500)
```

---

## 9. Strings & Logging

| Form | Status |
|---|---|
| f-string | Default for all interpolation |
| `%`-style args to `logger` | **Required** in logging calls — deferred formatting |
| `str.format()` · `%` operator | ✗ new code |
| `+` for 3+ parts | ✗ — use f-string \| `"".join(parts)` |

```python
logger.info("processed %d records in %.2fs", count, elapsed)   # ✓ lazy — no cost if filtered
logger.info(f"processed {count} records")                      # ✗ formats even when suppressed
```

Log levels, structured fields, and correlation IDs → [observability](../observability/STANDARDS.md).

---

## 10. Async

| Workload | Model |
|---|---|
| I/O-bound: HTTP · DB · file | Async |
| CPU-bound | Sync; offload to `ProcessPoolExecutor` |
| CLI · scripts | Sync |
| ASGI servers · MCP servers | Async |

| Rule | Detail |
|---|---|
| ✗ `asyncio.run()` inside async code | Nested loop → `RuntimeError`. Use `await` |
| ✗ `time.sleep()` in async code | `await asyncio.sleep()` |
| ✗ blocking I/O in a coroutine | `await asyncio.to_thread(fn)` — a blocked loop stalls every task. Use `httpx.AsyncClient`, ✗ `requests` |
| `asyncio.TaskGroup` over `gather` | Structured concurrency: cancels siblings on failure |
| ✗ fire-and-forget `create_task` | Keep a reference; unreferenced tasks are garbage-collected mid-flight |
| `async with` for connections and sessions | Deterministic teardown |
| Entry point | `asyncio.run(main())` under `if __name__ == "__main__":` |

```python
async def fetch_all(urls: list[str]) -> list[Response]:
    async with asyncio.TaskGroup() as tg:                 # ✓ 3.11+
        tasks = [tg.create_task(fetch(u)) for u in urls]
    return [t.result() for t in tasks]

async def bad(url: str) -> str:
    return requests.get(url).text                         # ✗ blocks the event loop
```

---

## 11. Testing Tools

Pyramid, coverage thresholds, mocking policy, and test classification → [testing](../testing/STANDARDS.md). Python tooling below.

| Tool | Purpose |
|---|---|
| `pytest` | Runner — ✗ `unittest` for new code |
| `pytest-cov` | Coverage |
| `pytest-asyncio` | Async tests (`asyncio_mode = "auto"`) |
| `hypothesis` | Property-based testing |
| `time-machine` | Time freezing — ✗ `freezegun` (slower) |
| `respx` \| `pytest-httpx` | `httpx` transport mocking |
| `testcontainers` | Real DB/broker in integration tests |

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-ra", "--strict-markers", "--strict-config"]
markers = ["slow: deselect with -m 'not slow'", "integration: needs external services"]
asyncio_mode = "auto"
```

| Rule | Detail |
|---|---|
| Test name states behavior | `test_empty_input_raises` — ✗ `test_1` · ✗ `test_it_works` |
| `pytest.raises` with `match=` | Assert the message, not just the type |
| `@pytest.mark.parametrize` over copy-pasted cases | One test body, N inputs |
| Shared fixtures in `tests/conftest.py` | Yield-fixtures roll back and close |

```python
@pytest.mark.parametrize(("val", "expected"), [("a", 1), ("bb", 2)])
def test_lengths(val: str, expected: int) -> None:
    assert length(val) == expected

def test_empty_input_raises() -> None:
    with pytest.raises(ValidationError, match="must not be empty"):
        Processor().run("")

@given(st.text(min_size=1, max_size=1000))          # property-based
def test_roundtrip(text: str) -> None:
    assert decode(encode(text)) == text
```

---

## 12. Lint · Format · Typecheck

`ruff` lints and formats. `mypy` (or `pyright`) type-checks. ✗ `black` · `isort` · `flake8` · `pylint` — ruff subsumes all four.

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "A", "SIM", "TCH", "PTH", "ERA", "S", "ASYNC", "RUF"]
ignore = ["E501"]                                  # formatter owns line length
per-file-ignores = { "tests/**/*.py" = ["S101"] }  # assert allowed in tests

[tool.ruff.format]
quote-style = "double"
```

Rule set: `E`/`W` pycodestyle · `F` pyflakes · `I` isort · `N` naming · `UP` pyupgrade · `B` bugbear · `A` builtin shadowing · `SIM` simplify · `TCH` type-checking blocks · `PTH` pathlib · `ERA` dead code · `S` bandit · `ASYNC` async correctness · `RUF` ruff-specific.

Local + CI gate — every command must exit 0 before merge:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest --cov=src
```

Same commands run in pre-commit hooks and in CI — ✗ divergence between the two. Pipeline stages, caching, and gating → [cicd](../cicd/STANDARDS.md).

✗ disable a check to make a build pass. Fix the code or record the suppression with an error code and a reason.

---

## 13. Performance Idioms

Budgets, profiling methodology, and optimization order → [performance](../performance/STANDARDS.md). Python idioms below.

| Idiom | When |
|---|---|
| Comprehension over `for` + `.append()` | Building any collection |
| Generator expression | Large or streamed data — full list not needed in memory |
| `set` / `dict` for membership | `x in large_list` is O(n) → O(1) |
| `@dataclass(slots=True)` | >1000 instances with fixed attributes — 40–50% less memory |
| `functools.lru_cache(maxsize=N)` | Pure function, repeated inputs — bounded |
| `functools.cache` | Unbounded — small, closed key space only |
| `"".join(parts)` | Many strings — repeated `+=` is O(n²) |
| `itertools` | Chaining · grouping · windowing |
| `cProfile` \| `py-spy` | Before any optimization — ✗ optimize on intuition |

Caches must be bounded in long-lived processes. ✗ `@cache` on a method taking `self` — it pins every instance forever.

---

## 14. Anti-Patterns

| Anti-pattern | Failure | Fix |
|---|---|---|
| Mutable default arg — `def f(x, items=[])` | Default is created once and shared across all calls | `items: list \| None = None` + `if items is None: items = []` |
| Late-binding closure — `[lambda: i for i in range(5)]` | Every lambda returns 4 | `[lambda i=i: i for i in range(5)]` |
| Module-level mutable state — `_cache = {}` | Import-order dependence · test pollution · races | Encapsulate in a class or pass explicitly |
| `isinstance()` chains | Fragile, violates open-closed | Protocol · `match` · dispatch |
| `hasattr()` for control flow | Hides bugs | Explicit check \| Protocol |
| `eval()` · `exec()` on any external input | Remote code execution | ✗ never in production code |
| Catching `KeyboardInterrupt` / `SystemExit` | Blocks clean shutdown | Let them propagate |
| `os.path` string manipulation | Error-prone, platform-dependent | `pathlib.Path` |
| `open(f)` without `encoding` | Platform-dependent default → mojibake | `open(f, encoding="utf-8")` |
| `datetime.now()` without tz | Naive datetime compared to aware → `TypeError` | `datetime.now(tz=UTC)` |
| Mutating a list while iterating it | Silently skipped elements | Iterate a copy \| build a new list |
| `assert` for runtime validation | Stripped under `python -O` | `if not cond: raise ValidationError(...)` |

---

## 15. Checklist

- [ ] `requires-python = ">=3.12"` in `pyproject.toml`
- [ ] `uv.lock` and `.python-version` committed; `.venv/` gitignored
- [ ] ✗ `setup.py` · `setup.cfg` · `requirements.txt` as dependency source
- [ ] `py.typed` marker present in every distributed package
- [ ] src layout used for any package published to an index
- [ ] `__init__.py` contains only imports + `__all__` — no logic, no side effects
- [ ] Every public function annotated, including `-> None` returns
- [ ] Every `# type: ignore` carries an error code; every `Any` carries a comment
- [ ] Imports ordered stdlib → third-party → first-party; ✗ wildcard imports
- [ ] External input parsed into a validated model, never a raw `dict`
- [ ] ✗ mutable default arguments
- [ ] ✗ bare `except:`; broad `except Exception` only at the boundary
- [ ] Every re-raise chains with `from`
- [ ] Logging calls use `%`-style deferred args, ✗ f-strings
- [ ] ✗ blocking calls inside coroutines; `asyncio.TaskGroup` over bare `gather`
- [ ] `pathlib.Path` used; `encoding="utf-8"` on every `open()`
- [ ] `datetime.now(tz=UTC)` — no naive datetimes
- [ ] ✗ `assert` used for runtime validation
- [ ] `ruff check .` exits 0
- [ ] `ruff format --check .` exits 0
- [ ] `mypy --strict` exits 0
- [ ] `pytest` passes at the coverage threshold set in [testing](../testing/STANDARDS.md)
- [ ] Pre-commit hooks run the identical commands CI runs
- [ ] Lock file regenerated in the same commit as any dependency change
