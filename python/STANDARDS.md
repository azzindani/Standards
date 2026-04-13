# Python Standards

Language-specific rules for Python projects. Extends and specializes
general standards from `architecture/`, `code_writing/`, `testing/`,
and `dependencies/` — Python-specific tooling, idioms, anti-patterns here.

Baseline: Python 3.11+. All rules assume modern Python unless noted.

---

## Table of Contents

1. [Style](#1-style)
2. [Type Hints](#2-type-hints)
3. [Project Structure](#3-project-structure)
4. [Package Management](#4-package-management)
5. [Virtual Environments](#5-virtual-environments)
6. [Import Style](#6-import-style)
7. [Data Classes & Models](#7-data-classes--models)
8. [Error Handling](#8-error-handling)
9. [String Formatting](#9-string-formatting)
10. [Async Patterns](#10-async-patterns)
11. [Testing Tools](#11-testing-tools)
12. [Linting & Formatting](#12-linting--formatting)
13. [Python-Specific Anti-Patterns](#13-python-specific-anti-patterns)
14. [Performance](#14-performance)
15. [Checklist](#15-checklist)

---

## 1. Style

PEP 8 as baseline with documented deviations.

### Deviations from PEP 8

| PEP 8 Default | Override | Rationale |
|---|---|---|
| Line length 79 | **100** | Modern screens; 79 causes excessive wrapping |
| `snake_case` class attrs | Preserved | No deviation |
| Trailing comma optional | **Required** in multi-line collections | Cleaner diffs |

### Naming Conventions

| Construct | Convention | Example |
|---|---|---|
| Module | `snake_case` | `data_loader.py` |
| Class | `PascalCase` | `DataLoader` |
| Function / method | `snake_case` | `load_data()` |
| Constant | `UPPER_SNAKE` | `MAX_RETRIES` |
| Private | `_leading_underscore` | `_internal_cache` |
| Name-mangled | `__double_leading` | `__secret` (rare; prefer `_single`) |
| Type variable | `PascalCase` + `T` suffix | `ItemT`, `ResponseT` |

### Whitespace

One blank line between methods. Two blank lines between top-level definitions.
Trailing commas required in multi-line collections.

### Docstrings

Google-style for all public functions, classes, modules.

```python
def fetch_records(query: str, limit: int = 100) -> list[Record]:
    """Fetch records matching query from primary store.

    Args:
        query: SQL-compatible filter expression.
        limit: Max rows returned. 0 → unlimited.

    Returns:
        Matching records ordered by creation time descending.

    Raises:
        QueryError: If query syntax invalid.
    """
```

✗ Docstrings on private helpers unless logic non-obvious.
✗ Restating type hints in docstring — types visible in signature.

---

## 2. Type Hints

Required for all public API (functions, classes, module-level vars).
Internal helpers: type hints strongly encouraged, enforced via mypy.

### Core Rules

| Rule | Detail |
|---|---|
| Return type always explicit | Even `-> None` |
| `Optional[X]` → `X \| None` | Modern union syntax (3.10+) |
| `Dict/List/Tuple` → `dict/list/tuple` | Lowercase builtins (3.9+) |
| `Any` requires comment | Explain why type unknown |
| `cast()` requires comment | Explain why cast safe |
| `# type: ignore` requires error code | `# type: ignore[attr-defined]` |

### Protocols

```python
from typing import Protocol

class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...

def serialize_all(items: list[Serializable]) -> list[dict[str, Any]]:
    return [item.to_dict() for item in items]
```

### Gradual Typing Strategy

1. All new code → fully typed from day one
2. Existing untyped code → type on touch (modify function → add types)
3. `py.typed` marker in all packages
4. mypy strict mode in CI — ✗ merge with type errors

```toml
# pyproject.toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 3. Project Structure

Two layouts exist. Choose based on project type.

### Layout Selection

| Layout | When | Example |
|---|---|---|
| **src layout** | Libraries, packages published to PyPI, multi-package repos | `src/mylib/` |
| **Flat layout** | Single-purpose apps, scripts, MCP servers, CLI tools | `myapp/` |

### src Layout (libraries, PyPI packages)

```
project-root/
├── pyproject.toml · uv.lock · .python-version
├── src/mylib/
│   ├── __init__.py · py.typed
│   ├── core.py · models.py · _internal.py
├── tests/
│   ├── conftest.py · test_core.py · test_models.py
```

### Flat Layout (apps, scripts, MCP servers, CLI tools)

```
project-root/
├── pyproject.toml · uv.lock · .python-version
├── myapp/
│   ├── __init__.py · main.py · config.py
│   └── handlers/__init__.py · handlers/api.py
├── tests/
```

### `__init__.py` Rules

| Rule | Detail |
|---|---|
| Every package dir has `__init__.py` | Even if empty — explicit packages only |
| Public API exported in `__init__.py` | `from .core import Engine` |
| ✗ logic in `__init__.py` | Only imports + `__all__` |
| `__all__` defined | Controls `from pkg import *` and documents public surface |

```python
# mylib/__init__.py
from .core import Engine
from .models import Config, Result

__all__ = ["Engine", "Config", "Result"]
```

See `architecture/STANDARDS.md` §5 for module boundary principles.
See `directory/STANDARDS.md` for general project layout rules.

---

## 4. Package Management

**uv** is the primary tool for all Python package operations.

### Rules

| Rule | Detail |
|---|---|
| ✗ `setup.py` | Dead format — `pyproject.toml` only |
| ✗ `requirements.txt` for deps | Use `uv.lock` — deterministic, cross-platform |
| ✗ `pip install` directly | Use `uv pip install` or `uv sync` |
| ✗ `setup.cfg` | Migrate to `pyproject.toml` |
| Lock file committed | `uv.lock` in version control always |

### `pyproject.toml` Structure

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27", "pydantic>=2.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"

[tool.uv]
dev-dependencies = ["pytest>=8.0", "pytest-cov>=5.0", "mypy>=1.10", "ruff>=0.5", "pre-commit>=3.7"]
```

### Common uv Commands

```bash
uv init myproject              # new project
uv add httpx pydantic          # add dependencies
uv add --dev pytest ruff mypy  # add dev dependencies
uv sync                        # install from lock file
uv run pytest                  # run within venv
uv run mypy src/               # type-check
uv lock                        # regenerate lock file
```

See `dependencies/STANDARDS.md` for general dependency management rules.

---

## 5. Virtual Environments

Every project runs in an isolated virtual environment. ✗ system Python for project work.

### Rules

| Rule | Detail |
|---|---|
| One venv per project | In project root as `.venv/` |
| Created via `uv venv` | Or auto-created by `uv sync` |
| `.venv/` in `.gitignore` | ✗ committed to version control |
| `.python-version` committed | Pin Python version per project |
| ✗ `conda` for app projects | uv manages Python versions directly |
| ✗ `virtualenv` / `venv` module | Use `uv venv` — faster, consistent |

```bash
uv venv --python 3.12     # creates .venv/ with Python 3.12
uv sync                    # install all deps from lock
uv run pytest -x           # run within venv (preferred over activating)
```

Pin version in `.python-version` (just `3.12`). `uv` reads it automatically, downloads if missing.

---

## 6. Import Style

### Ordering (enforced by ruff `I` rules)

Three groups, separated by blank line:

```python
# 1. Standard library
import os
import sys
from pathlib import Path

# 2. Third-party
import httpx
from pydantic import BaseModel

# 3. Internal / project
from myapp.config import Settings
from myapp.models import User
```

### Rules

| Rule | Detail |
|---|---|
| Absolute imports preferred | `from myapp.models import User` |
| Relative imports allowed | Only within same package: `from .models import User` |
| ✗ wildcard imports | `from module import *` — unpredictable namespace |
| ✗ import aliasing | Unless name collision or established convention (`import numpy as np`) |
| One import per line | `from x import a, b` acceptable; `import a, b` → split to two lines |
| `TYPE_CHECKING` block for cycle-breaking | Runtime-free imports for type hints only |
| `__future__` annotations first | `from __future__ import annotations` at top if needed |

### Type-Checking Imports

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.engine import Engine  # avoid circular import

class Handler:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
```

---

## 7. Data Classes & Models

### Selection Criteria

| Need | Use | Why |
|---|---|---|
| Simple data container, internal | `dataclass` | Stdlib, zero deps, fast |
| Immutable record, hashable | `NamedTuple` | Lightweight, tuple-compatible |
| External data validation (API, config, DB) | `Pydantic BaseModel` | Validation, serialization, schema |
| High-performance, many instances | `dataclass` + `__slots__` | Lower memory, faster attribute access |
| Frozen/immutable internal data | `dataclass(frozen=True)` | Hashable, prevents mutation |

### dataclass Examples

```python
from dataclasses import dataclass, field

@dataclass
class ServerConfig:
    host: str
    port: int = 8080
    tags: list[str] = field(default_factory=list)  # ✓ factory for mutable

@dataclass(frozen=True, slots=True)
class CacheKey:
    namespace: str
    key: str
```

### Pydantic Examples

```python
from pydantic import BaseModel, Field, field_validator

class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str
    age: int = Field(ge=0, le=150)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("invalid email format")
        return v.lower()
```

### NamedTuple Example

```python
from typing import NamedTuple

class Coordinate(NamedTuple):
    lat: float
    lon: float
    alt: float = 0.0

# Unpacking works
lat, lon, alt = Coordinate(59.33, 18.07)
```

### ✗ Avoid

| Anti-Pattern | Use Instead |
|---|---|
| Plain `dict` for structured data | `dataclass` or Pydantic model |
| `TypedDict` for runtime validation | Pydantic model (TypedDict has no runtime checks) |
| Pydantic for internal-only data | `dataclass` (less overhead) |
| Mutable default on dataclass field | `field(default_factory=...)` |

---

## 8. Error Handling

See `architecture/STANDARDS.md` §7 for error architecture principles.

### Rules

| Rule | Detail |
|---|---|
| ✗ bare `except:` | Always specify exception type |
| ✗ `except Exception:` at low level | Catch specific exceptions; broad catch only at boundary |
| ✗ Pokemon exception handling | `except Exception as e: pass` — swallows all errors silently |
| ✗ `except` + `return None` silently | Caller cannot distinguish "no result" from "error" |
| Exception chains preserved | `raise NewError(...) from original` |
| Custom exceptions per domain | Inherit from project base exception |

### Exception Hierarchy Pattern

```python
class AppError(Exception):
    """Base for all project exceptions."""

class ConfigError(AppError):
    """Configuration loading or validation failed."""

class StorageError(AppError):
    """Database or file storage operation failed."""

class ValidationError(AppError):
    """Input data failed validation."""
```

### Correct Patterns

```python
# ✓ Specific catch + chain
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    raise ValidationError(f"invalid JSON in config: {e}") from e

# ✓ Boundary-level broad catch (top of call stack)
async def handle_request(request: Request) -> Response:
    try:
        result = await process(request)
        return Response(data=result)
    except AppError as e:
        return Response(error=str(e), status=400)
    except Exception:
        logger.exception("unhandled error")
        return Response(error="internal error", status=500)

# ✓ Context managers for cleanup
from contextlib import contextmanager

@contextmanager
def managed_connection(url: str):
    conn = connect(url)
    try:
        yield conn
    finally:
        conn.close()
```

---

## 9. String Formatting

### Rules

| Method | Status |
|---|---|
| f-strings | **Preferred** for all new code |
| `str.format()` | Acceptable only in logging lazy format: `logger.info("x=%s", val)` |
| `%` formatting | ✗ Forbidden in new code |
| `+` concatenation | ✗ Forbidden for >2 parts — use f-string or `join()` |

```python
msg = f"processed {count} records in {elapsed:.2f}s"       # ✓ f-string
logger.info("processed %d records in %.2fs", count, elapsed)  # ✓ lazy log format
msg = "processed %d records" % count                        # ✗ forbidden
msg = "processed {} records".format(count)                  # ✗ forbidden
```

---

## 10. Async Patterns

### When to Use Async

| Scenario | Sync or Async |
|---|---|
| I/O-bound: HTTP calls, DB queries, file I/O | Async |
| CPU-bound: data crunching, parsing | Sync (offload to thread/process pool) |
| CLI tools, simple scripts | Sync |
| Web servers (FastAPI, Starlette) | Async |
| MCP servers | Async |

### Rules

| Rule | Detail |
|---|---|
| ✗ mixing `asyncio.run()` inside async code | Nest → crash. Use `await` |
| ✗ `time.sleep()` in async code | Use `await asyncio.sleep()` |
| ✗ blocking I/O in async functions | Offload: `await asyncio.to_thread(blocking_fn)` |
| Gather for concurrent I/O | `asyncio.gather(*tasks)` or `TaskGroup` (3.11+) |
| `TaskGroup` preferred over `gather` | Structured concurrency, better error handling |
| Async context managers for resources | `async with` for connections, sessions |

### Patterns

```python
# ✓ TaskGroup (Python 3.11+) — structured concurrency
async def fetch_all(urls: list[str]) -> list[Response]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(url)) for url in urls]
    return [t.result() for t in tasks]

# ✓ Offload blocking work to thread
async def process_file(path: Path) -> Data:
    content = await asyncio.to_thread(path.read_bytes)
    return parse(content)

# ✗ Wrong — blocking in async
async def bad_fetch(url: str) -> str:
    return requests.get(url).text  # blocks event loop!
```

Entry point: `asyncio.run(main())` in `if __name__ == "__main__":` block.

---

## 11. Testing Tools

See `testing/STANDARDS.md` for general test strategy. Python-specific tooling here.

### Tool Stack

| Tool | Purpose |
|---|---|
| `pytest` | Test runner — ✗ `unittest` for new projects |
| `pytest-cov` | Coverage reporting |
| `pytest-asyncio` | Async test support |
| `hypothesis` | Property-based / fuzz testing |
| `time-machine` | Time mocking (✗ `freezegun` — slower) |
| `respx` / `pytest-httpx` | HTTP mocking for `httpx` |
| `factory_boy` | Test data factories |

### pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "-x",                  # stop on first failure during dev
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: requires external services",
]
asyncio_mode = "auto"
```

### Test Patterns

```python
import pytest
from myapp.processor import Processor

class TestProcessor:
    def test_valid_input(self) -> None:
        assert Processor().run("valid data").status == "ok"

    def test_empty_input_raises(self) -> None:
        with pytest.raises(ValidationError, match="must not be empty"):
            Processor().run("")

    @pytest.mark.parametrize(("val", "expected"), [("a", 1), ("bb", 2), ("ccc", 3)])
    def test_lengths(self, val: str, expected: int) -> None:
        assert Processor().length(val) == expected
```

### Fixtures in `tests/conftest.py`

```python
@pytest.fixture
def sample_config() -> dict[str, str]:
    return {"host": "localhost", "port": "8080"}

@pytest.fixture
async def db_session():
    session = await create_test_session()
    yield session
    await session.rollback()
    await session.close()
```

### Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
def test_roundtrip(text: str) -> None:
    assert decode(encode(text)) == text
```

### Coverage

Minimum 80% line coverage enforced in CI. Critical paths → 95%+.

```bash
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

---

## 12. Linting & Formatting

**ruff** handles both linting and formatting. **mypy** for type checking.
✗ `black`, `isort`, `flake8`, `pylint` — ruff replaces all of them.

### ruff Configuration

```toml
# pyproject.toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "A",    # flake8-builtins
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "RUF",  # ruff-specific rules
    "PTH",  # flake8-use-pathlib
    "ERA",  # eradicate (commented-out code)
    "S",    # flake8-bandit (security)
]
ignore = [
    "E501",  # line length — formatter handles this
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101"]  # allow assert in tests

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]
```

### CI Pipeline Commands

```bash
uv run ruff check .              # lint
uv run ruff format --check .     # format check (no write)
uv run mypy src/                 # type check
uv run pytest --cov=src          # test + coverage
```

All four must pass before merge. ✗ disabling checks for convenience.

---

## 13. Python-Specific Anti-Patterns

### Mutable Default Arguments

```python
# ✗ WRONG — list shared across all calls
def append_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

# ✓ CORRECT — None sentinel + factory
def append_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

### Late Binding Closures

```python
# ✗ WRONG — all lambdas capture i=4 (last value)
funcs = [lambda: i for i in range(5)]
[f() for f in funcs]  # [4, 4, 4, 4, 4]

# ✓ CORRECT — default argument captures current value
funcs = [lambda i=i: i for i in range(5)]
[f() for f in funcs]  # [0, 1, 2, 3, 4]
```

### Global State

```python
# ✗ WRONG — module-level mutable state
_cache = {}  # any import side-effects, any module can mutate

# ✓ CORRECT — encapsulate in class or function scope
class Cache:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
```

### Other Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `isinstance()` chains | Fragile, violates open-closed | Protocol / dispatch / match-case |
| Nested `try/except` | Hard to reason about | Flatten; one try per operation |
| `hasattr()` for flow control | Hides bugs, slow | Explicit check or Protocol |
| `eval()` / `exec()` | Security hole | ✗ Never in production code |
| Star imports in non-`__init__` | Namespace pollution | Explicit imports |
| Catching `KeyboardInterrupt` | Prevents clean exit | Let it propagate |
| `os.path` for new code | String-based, error-prone | `pathlib.Path` |
| `open()` without encoding | Platform-dependent default | `open(f, encoding="utf-8")` |
| `datetime.now()` without tz | Naive datetime bugs | `datetime.now(tz=UTC)` |

---

## 14. Performance

### General Rules

| Pattern | When |
|---|---|
| List comprehension over `for`+`append` | All collection building |
| Generator expression for large data | When full list not needed in memory |
| `__slots__` on data-heavy classes | Many instances (>1000) with fixed attrs |
| `dict` / `set` for membership tests | ✗ `if x in large_list` — O(n) vs O(1) |
| `functools.lru_cache` | Pure functions with repeated inputs |
| `itertools` over manual iteration | Chaining, grouping, combinations |

### Comprehensions vs Loops

```python
# ✓ Comprehension — faster, clearer
squares = [x * x for x in range(1000)]

# ✓ Generator — lazy evaluation for large data
total = sum(x * x for x in range(1_000_000))

# ✓ Dict comprehension
index = {item.id: item for item in items}

# ✗ Loop+append — slower, verbose
squares = []
for x in range(1000):
    squares.append(x * x)
```

### `__slots__`

```python
# ✓ Slots — 40-50% less memory per instance
class Point:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

# Or use dataclass with slots=True (3.10+)
@dataclass(slots=True)
class Point:
    x: float
    y: float
    z: float
```

### Caching

```python
from functools import lru_cache, cache

# ✓ Bounded cache — evicts LRU entries
@lru_cache(maxsize=256)
def expensive_lookup(key: str) -> Result:
    return db.query(key)

# ✓ Unbounded cache (3.9+) — use only for small key spaces
@cache
def parse_config(path: str) -> Config:
    return load_and_parse(path)
```

### String Building

```python
# ✓ join() for many strings
result = "".join(parts)

# ✓ io.StringIO for complex string assembly
import io
buffer = io.StringIO()
for chunk in data:
    buffer.write(chunk)
result = buffer.getvalue()

# ✗ repeated concatenation — O(n²) for large n
result = ""
for chunk in data:
    result += chunk
```

### Profiling

Use `cProfile` / `py-spy` before optimizing. ✗ premature optimization.

```bash
uv run python -m cProfile -s cumtime src/myapp/main.py
```

---

## 15. Checklist

### New Project Setup

- [ ] `pyproject.toml` with project metadata, dependencies, tool config
- [ ] `uv.lock` committed
- [ ] `.python-version` committed
- [ ] `.venv/` in `.gitignore`
- [ ] `py.typed` marker in package root
- [ ] ruff + mypy configured in `pyproject.toml`
- [ ] pre-commit hooks installed
- [ ] src layout or flat layout chosen deliberately
- [ ] `__init__.py` with `__all__` in every package

### Every File

- [ ] Type hints on all public functions (params + return)
- [ ] Google-style docstring on public API
- [ ] Imports ordered: stdlib → third-party → internal
- [ ] ✗ wildcard imports
- [ ] ✗ mutable default arguments
- [ ] ✗ bare `except:`
- [ ] f-strings for formatting (except logging)
- [ ] `pathlib.Path` over `os.path`
- [ ] `encoding="utf-8"` on `open()` calls

### Every PR

- [ ] `ruff check` passes
- [ ] `ruff format --check` passes
- [ ] `mypy --strict` passes
- [ ] `pytest` passes with ≥80% coverage
- [ ] No new `# type: ignore` without error code + comment
- [ ] No new `Any` without justification comment
- [ ] Lock file updated if deps changed

### Async Code

- [ ] ✗ blocking calls in async functions
- [ ] `TaskGroup` used over bare `gather` where possible
- [ ] Async context managers for resource lifecycle
- [ ] ✗ `time.sleep()` — use `asyncio.sleep()`

### Cross-References

- `architecture/STANDARDS.md` — tier model, function contracts, error architecture
- `code_writing/STANDARDS.md` — general readability, function style
- `testing/STANDARDS.md` — test pyramid, coverage strategy
- `dependencies/STANDARDS.md` — dependency management principles
