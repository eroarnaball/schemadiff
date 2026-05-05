# schemadiff

> A lightweight tool to compare and report schema drift between database versions or environments.

---

## Installation

```bash
pip install schemadiff
```

Or install from source:

```bash
git clone https://github.com/yourname/schemadiff.git
cd schemadiff && pip install -e .
```

---

## Usage

Compare two database schemas and generate a drift report:

```python
from schemadiff import SchemaDiff

diff = SchemaDiff(
    source="postgresql://user:pass@localhost/db_production",
    target="postgresql://user:pass@localhost/db_staging"
)

report = diff.compare()
report.print_summary()
```

Or use the CLI:

```bash
schemadiff compare \
  --source postgresql://user:pass@localhost/db_production \
  --target postgresql://user:pass@localhost/db_staging \
  --output report.json
```

**Example output:**

```
[+] Table added:    user_sessions
[-] Table removed:  legacy_tokens
[~] Column changed: orders.status → type mismatch (varchar vs text)
```

---

## Features

- Detects added, removed, and modified tables, columns, and indexes
- Supports PostgreSQL, MySQL, and SQLite
- Outputs reports in plain text, JSON, or HTML

---

## License

This project is licensed under the [MIT License](LICENSE).