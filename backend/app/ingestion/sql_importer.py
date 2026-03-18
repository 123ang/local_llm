"""
Parse MySQL / MariaDB SQL dumps and convert them to PostgreSQL-compatible
CREATE TABLE + INSERT statements.

Handles the full range of phpMyAdmin / mysqldump output:
  - /*!40101 … */ conditional comments
  - SET SQL_MODE, START TRANSACTION, COMMIT, LOCK/UNLOCK TABLES
  - backtick identifiers → double-quote
  - UNSIGNED, AUTO_INCREMENT, ON UPDATE, ENGINE=, CHARSET=, COLLATE=
  - ALTER TABLE … ADD PRIMARY KEY (separate from CREATE TABLE)
  - ALTER TABLE … MODIFY … AUTO_INCREMENT (→ SERIAL / BIGSERIAL)
  - MySQL type mapping (bigint(20), varchar(N), tinyint, enum, etc.)
  - MySQL backslash-escaped strings in INSERT VALUES
  - table-name prefixing with c{company_id}_ for namespace isolation
  - duplicate table detection / auto-suffixing
"""

import re
from dataclasses import dataclass, field
from app.core.logger import logger

# ── MySQL → PostgreSQL type mapping ──────────────────────────────────

MYSQL_TO_PG_TYPE: dict[str, str] = {
    "bigint": "BIGINT",
    "int": "INTEGER",
    "integer": "INTEGER",
    "mediumint": "INTEGER",
    "smallint": "SMALLINT",
    "tinyint": "SMALLINT",
    "decimal": "NUMERIC",
    "numeric": "NUMERIC",
    "float": "REAL",
    "double": "DOUBLE PRECISION",
    "varchar": "VARCHAR",
    "char": "CHAR",
    "text": "TEXT",
    "mediumtext": "TEXT",
    "longtext": "TEXT",
    "tinytext": "TEXT",
    "blob": "BYTEA",
    "mediumblob": "BYTEA",
    "longblob": "BYTEA",
    "tinyblob": "BYTEA",
    "date": "DATE",
    "datetime": "TIMESTAMP",
    "timestamp": "TIMESTAMP",
    "time": "TIME",
    "year": "SMALLINT",
    "enum": "TEXT",
    "set": "TEXT",
    "boolean": "BOOLEAN",
    "bool": "BOOLEAN",
    "json": "JSONB",
    "binary": "BYTEA",
    "varbinary": "BYTEA",
    "bit": "BIT",
}


# ── Data classes ─────────────────────────────────────────────────────

@dataclass
class ParsedColumn:
    name: str
    pg_type: str
    nullable: bool = True
    is_primary_key: bool = False
    original_type: str = ""


@dataclass
class ParsedTable:
    original_name: str
    columns: list[ParsedColumn] = field(default_factory=list)
    insert_values: list[list[str]] = field(default_factory=list)
    row_count: int = 0
    preview_rows: list[dict] = field(default_factory=list)


# ── Pre-processing ───────────────────────────────────────────────────

def _preprocess(sql: str) -> str:
    """Strip MySQL-specific noise that would confuse the parser."""
    # Remove /*!40101 … */ conditional comments (can span lines)
    sql = re.sub(r"/\*!\d+.*?\*/", "", sql, flags=re.DOTALL)
    # Remove single-line MySQL comments (-- …)
    sql = re.sub(r"--[^\n]*", "", sql)
    # Remove C-style block comments
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    # Remove SET, START TRANSACTION, COMMIT, LOCK/UNLOCK, USE directives
    sql = re.sub(
        r"^\s*(SET|START\s+TRANSACTION|COMMIT|LOCK\s+TABLES|UNLOCK\s+TABLES|USE)\b[^;]*;",
        "",
        sql,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    return sql


# ── Type helpers ─────────────────────────────────────────────────────

def _map_mysql_type(raw_type: str, params: str | None) -> str:
    key = raw_type.lower().strip()
    pg = MYSQL_TO_PG_TYPE.get(key, "TEXT")
    if key in ("varchar", "char") and params:
        return f"{pg}({params})"
    if key in ("decimal", "numeric") and params:
        return f"{pg}({params})"
    return pg


# ── Column parser ────────────────────────────────────────────────────

def _parse_column_line(line: str) -> ParsedColumn | None:
    """Parse a single column definition line from a CREATE TABLE body."""
    stripped = line.strip().rstrip(",")
    if not stripped or stripped.startswith(")"):
        return None

    upper = stripped.upper()
    skip_prefixes = (
        "PRIMARY", "KEY", "INDEX", "UNIQUE", "CONSTRAINT",
        "FULLTEXT", "SPATIAL", "CHECK", "FOREIGN",
    )
    if any(upper.startswith(p) for p in skip_prefixes):
        return None

    m = re.match(r"^`(\w+)`\s+(\w+)(?:\(([^)]*)\))?(.*)", stripped, re.IGNORECASE)
    if not m:
        return None

    name = m.group(1)
    raw_type = m.group(2)
    params = m.group(3)
    rest = m.group(4).upper() if m.group(4) else ""

    pg_type = _map_mysql_type(raw_type, params)
    nullable = "NOT NULL" not in rest

    original_type = f"{raw_type}({params})" if params else raw_type
    if "UNSIGNED" in rest:
        original_type += " unsigned"

    return ParsedColumn(
        name=name,
        pg_type=pg_type,
        nullable=nullable,
        is_primary_key=False,
        original_type=original_type,
    )


# ── Body-level PK detection ─────────────────────────────────────────

def _extract_primary_key_from_body(body: str) -> str | None:
    """Find PRIMARY KEY (`col`) inside CREATE TABLE body."""
    m = re.search(r"PRIMARY\s+KEY\s*\(\s*`(\w+)`", body, re.IGNORECASE)
    return m.group(1) if m else None


# ── INSERT VALUES parser (handles MySQL backslash escaping) ──────────

def _parse_insert_values(values_str: str) -> list[list[str]]:
    """Parse the VALUES portion into rows of string values."""
    rows: list[list[str]] = []
    i = 0
    n = len(values_str)

    while i < n:
        if values_str[i] == "(":
            vals: list[str] = []
            i += 1
            while i < n and values_str[i] != ")":
                if values_str[i] in (" ", "\t", "\n", "\r"):
                    i += 1
                    continue
                if values_str[i] == ",":
                    i += 1
                    continue

                if values_str[i] == "'":
                    # Quoted string — handle both \' and '' escaping
                    j = i + 1
                    parts: list[str] = []
                    while j < n:
                        if values_str[j] == "\\" and j + 1 < n:
                            ch = values_str[j + 1]
                            if ch == "'":
                                parts.append("'")
                            elif ch == "\\":
                                parts.append("\\")
                            elif ch == "n":
                                parts.append("\n")
                            elif ch == "r":
                                parts.append("\r")
                            elif ch == "t":
                                parts.append("\t")
                            elif ch == "0":
                                parts.append("")
                            else:
                                parts.append(ch)
                            j += 2
                        elif values_str[j] == "'" and j + 1 < n and values_str[j + 1] == "'":
                            parts.append("'")
                            j += 2
                        elif values_str[j] == "'":
                            break
                        else:
                            parts.append(values_str[j])
                            j += 1
                    vals.append("".join(parts))
                    i = j + 1
                else:
                    # Unquoted token (number, NULL, etc.)
                    j = i
                    while j < n and values_str[j] not in (",", ")"):
                        j += 1
                    vals.append(values_str[i:j].strip())
                    i = j
            rows.append(vals)
            i += 1
        else:
            i += 1

    return rows


def _find_values_span(block: str, after_values_pos: int) -> tuple[int, int]:
    """Return (start, end) of the VALUES content, from after_values_pos until the next
    semicolon that is outside quoted strings and outside parentheses.
    """
    i = after_values_pos
    n = len(block)
    depth = 0
    in_string = False
    escape_next = False
    start = -1
    while i < n:
        if escape_next:
            escape_next = False
            i += 1
            continue
        c = block[i]
        if in_string:
            if c == "\\" and i + 1 < n:
                escape_next = True
                i += 1
                continue
            if c == "'" and i + 1 < n and block[i + 1] == "'":
                i += 2
                continue
            if c == "'":
                in_string = False
            i += 1
            continue
        if c == "'":
            in_string = True
            i += 1
            continue
        if c == "(":
            if depth == 0:
                start = i if start < 0 else start
            depth += 1
            i += 1
            continue
        if c == ")":
            depth -= 1
            i += 1
            continue
        if c == ";" and depth == 0:
            return (start, i) if start >= 0 else (after_values_pos, i)
        i += 1
    return (start, n) if start >= 0 else (after_values_pos, n)


# ── Split by semicolon, respecting single-quoted strings ─────────────

def _split_sql_statements(content: str) -> list[str]:
    """Split SQL on semicolons, but not when inside a single-quoted string.
    Handles MySQL-style \\' and '' escaping inside strings.
    """
    blocks: list[str] = []
    start = 0
    i = 0
    n = len(content)
    in_string = False
    escape_next = False

    while i < n:
        if escape_next:
            escape_next = False
            i += 1
            continue
        c = content[i]
        if in_string:
            if c == "\\" and i + 1 < n:
                escape_next = True
                i += 1
                continue
            if c == "'" and i + 1 < n and content[i + 1] == "'":
                i += 2  # skip escaped ''
                continue
            if c == "'":
                in_string = False
            i += 1
            continue
        if c == "'":
            in_string = True
            i += 1
            continue
        if c == ";":
            block = content[start:i].strip()
            if block:
                blocks.append(block)
            start = i + 1
            i += 1
            continue
        i += 1

    if start < n:
        block = content[start:n].strip()
        if block:
            blocks.append(block)
    return blocks


# ── Main parser ──────────────────────────────────────────────────────

_RE_CREATE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?\s*\(",
    re.IGNORECASE,
)
_RE_INSERT = re.compile(
    r"INSERT\s+INTO\s+`?(\w+)`?\s*\(([^)]*)\)\s*VALUES\s*",
    re.IGNORECASE,
)
_RE_ALTER_PK = re.compile(
    r"ALTER\s+TABLE\s+`?(\w+)`?\s+ADD\s+PRIMARY\s+KEY\s*\(\s*`(\w+)`",
    re.IGNORECASE,
)
_RE_ALTER_AI = re.compile(
    r"ALTER\s+TABLE\s+`?(\w+)`?\s+MODIFY\s+`?(\w+)`?\s+.*?AUTO_INCREMENT",
    re.IGNORECASE,
)


def parse_sql_dump(content: str) -> list[ParsedTable]:
    """Parse a full MySQL/MariaDB SQL dump and return ParsedTable objects."""
    content = _preprocess(content)
    tables: dict[str, ParsedTable] = {}

    blocks = _split_sql_statements(content)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # ── CREATE TABLE ─────────────────────────────────────────
        create_match = _RE_CREATE.search(block)
        if create_match:
            tname = create_match.group(1)
            paren_pos = block.index("(", create_match.end() - 1)
            start = paren_pos + 1
            depth = 1
            end = start
            while end < len(block) and depth > 0:
                if block[end] == "(":
                    depth += 1
                elif block[end] == ")":
                    depth -= 1
                end += 1
            body = block[start : end - 1]

            pk_col = _extract_primary_key_from_body(body)
            cols: list[ParsedColumn] = []
            for line in body.split("\n"):
                col = _parse_column_line(line)
                if col:
                    if pk_col and col.name == pk_col:
                        col.is_primary_key = True
                        col.nullable = False
                        if col.pg_type in ("INTEGER", "BIGINT", "SMALLINT"):
                            col.pg_type = "BIGSERIAL" if col.pg_type == "BIGINT" else "SERIAL"
                    cols.append(col)

            tables[tname] = ParsedTable(original_name=tname, columns=cols)
            continue

        # ── INSERT INTO ──────────────────────────────────────────
        insert_match = _RE_INSERT.search(block)
        if insert_match:
            tname = insert_match.group(1)
            # If table not yet created, block may contain CREATE TABLE (e.g. after bad split on ; in data)
            if tname not in tables:
                create_in_block = re.search(
                    rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?{re.escape(tname)}`?\s*\(",
                    block,
                    re.IGNORECASE,
                )
                if create_in_block:
                    sub = block[create_in_block.start() :]
                    end = sub.index(";") + 1 if ";" in sub else len(sub)
                    sub = sub[:end]
                    for sub_block in [sub]:
                        cm = _RE_CREATE.search(sub_block)
                        if cm and cm.group(1) == tname:
                            paren_pos = sub_block.index("(", cm.end() - 1)
                            start = paren_pos + 1
                            depth = 1
                            end_pos = start
                            while end_pos < len(sub_block) and depth > 0:
                                if sub_block[end_pos] == "(":
                                    depth += 1
                                elif sub_block[end_pos] == ")":
                                    depth -= 1
                                end_pos += 1
                            body = sub_block[start : end_pos - 1]
                            pk_col = _extract_primary_key_from_body(body)
                            cols = []
                            for line in body.split("\n"):
                                col = _parse_column_line(line)
                                if col:
                                    if pk_col and col.name == pk_col:
                                        col.is_primary_key = True
                                        col.nullable = False
                                        if col.pg_type in ("INTEGER", "BIGINT", "SMALLINT"):
                                            col.pg_type = "BIGSERIAL" if col.pg_type == "BIGINT" else "SERIAL"
                                    cols.append(col)
                            tables[tname] = ParsedTable(original_name=tname, columns=cols)
                            break
            # VALUES: use the span right after this INSERT's column list, up to next ;
            values_start, values_end = _find_values_span(block, insert_match.end())
            values_str = block[values_start:values_end]
            rows = _parse_insert_values(values_str)
            if tname in tables:
                tables[tname].insert_values.extend(rows)
                tables[tname].row_count += len(rows)
            continue

        # ── ALTER TABLE … ADD PRIMARY KEY ────────────────────────
        pk_match = _RE_ALTER_PK.search(block)
        if pk_match:
            tname = pk_match.group(1)
            pk_col_name = pk_match.group(2)
            if tname in tables:
                for col in tables[tname].columns:
                    if col.name == pk_col_name and not col.is_primary_key:
                        col.is_primary_key = True
                        col.nullable = False
                        if col.pg_type in ("INTEGER", "BIGINT", "SMALLINT"):
                            col.pg_type = "BIGSERIAL" if col.pg_type == "BIGINT" else "SERIAL"
            continue

        # ── ALTER TABLE … MODIFY … AUTO_INCREMENT ────────────────
        ai_match = _RE_ALTER_AI.search(block)
        if ai_match:
            tname = ai_match.group(1)
            ai_col = ai_match.group(2)
            if tname in tables:
                for col in tables[tname].columns:
                    if col.name == ai_col:
                        col.is_primary_key = True
                        col.nullable = False
                        if col.pg_type in ("INTEGER", "BIGINT", "SMALLINT"):
                            col.pg_type = "BIGSERIAL" if col.pg_type == "BIGINT" else "SERIAL"
            continue

    # Build preview rows
    for t in tables.values():
        col_names = [c.name for c in t.columns]
        for row_vals in t.insert_values[:10]:
            row_dict: dict[str, str] = {}
            for ci, cn in enumerate(col_names):
                row_dict[cn] = row_vals[ci] if ci < len(row_vals) else ""
            t.preview_rows.append(row_dict)

    return list(tables.values())


# ── PostgreSQL SQL generation ────────────────────────────────────────

def build_pg_create_sql(table: ParsedTable, pg_table_name: str) -> str:
    """Generate a PostgreSQL CREATE TABLE statement."""
    col_parts: list[str] = []
    for col in table.columns:
        nullable = "" if col.nullable else " NOT NULL"
        if col.is_primary_key:
            col_parts.append(f'"{col.name}" {col.pg_type} PRIMARY KEY')
        else:
            col_parts.append(f'"{col.name}" {col.pg_type}{nullable}')
    cols_sql = ", ".join(col_parts)
    return f'CREATE TABLE IF NOT EXISTS "{pg_table_name}" ({cols_sql})'


def build_pg_insert_sql(
    table: ParsedTable, pg_table_name: str,
) -> tuple[str, list[dict]]:
    """Generate a PostgreSQL parameterised INSERT and list of row dicts.

    Skips the auto-increment PK column so PostgreSQL can assign SERIAL
    values itself — avoids clashing with the SERIAL sequence.
    """
    skip_pk = any(
        c.is_primary_key and c.pg_type in ("SERIAL", "BIGSERIAL")
        for c in table.columns
    )

    if skip_pk:
        pk_names = {c.name for c in table.columns if c.is_primary_key}
        insert_cols = [c for c in table.columns if c.name not in pk_names]
        pk_indices = {
            i for i, c in enumerate(table.columns) if c.name in pk_names
        }
    else:
        insert_cols = list(table.columns)
        pk_indices = set()

    col_names = [c.name for c in insert_cols]
    col_list = ", ".join(f'"{c}"' for c in col_names)
    placeholders = ", ".join(f":{c}" for c in col_names)
    sql = f'INSERT INTO "{pg_table_name}" ({col_list}) VALUES ({placeholders})'

    records: list[dict] = []
    all_col_count = len(table.columns)
    for row_vals in table.insert_values:
        record: dict = {}
        insert_i = 0
        for i in range(all_col_count):
            if i in pk_indices:
                continue
            col = insert_cols[insert_i]
            val = row_vals[i] if i < len(row_vals) else None
            if val is not None and val.upper() == "NULL":
                val = None
            record[col.name] = val
            insert_i += 1
        records.append(record)

    return sql, records


# ── Duplicate-name helper ────────────────────────────────────────────

def make_unique_table_name(
    desired: str,
    existing_names: set[str],
) -> str:
    """Return *desired* if unique, otherwise append _2, _3, … until unique."""
    if desired not in existing_names:
        return desired
    suffix = 2
    while f"{desired}_{suffix}" in existing_names:
        suffix += 1
    return f"{desired}_{suffix}"
