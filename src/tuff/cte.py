# Copyright 2026 Peter LaValle
#
# This file is part of tuff.
#
# tuff is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# tuff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with tuff.  If not, see <https://www.gnu.org/licenses/>.

"""functions for manipulating/extracting/removing the CTE section of queries"""

import functools
import re
from collections.abc import Callable as call
from collections.abc import Generator as gen
from dataclasses import dataclass
from pathlib import Path

import sqlglot


@dataclass(frozen=True)
class CachedCTE:
    note: str
    body: str
    uses: tuple[str, ...]


def cache() -> call[[Path], CachedCTE]:
    """given a file, load it as .sql and split up the query into;
    - note; leading comment block
    - uses; names of any/all CTE
    - body; the main SQL SELECT statement

    ... will strip comments between CTE sections ... but that's okay?
    """

    @functools.cache
    def cte_cache(file: Path) -> CachedCTE:
        try:
            full = (file).read_text()
            body = drop_cte(full).strip()
            uses = sorted(find_cte(full))
            note = ""
            for line in full.splitlines():
                line = line.strip()
                if not line.startswith("--"):
                    break
                note += ("-- " + line[2:].strip()).strip() + "\n"
            return CachedCTE(note.strip(), body, uses)
        except Exception as ae:
            raise RuntimeError(f"in {file=}") from ae

    return cte_cache


def find_cte(src: str):
    in_with = False
    indent = None

    for num, line in enumerate(src.splitlines()):
        if "--" in line:
            line = line[: line.find("--")]

        if line == "WITH":
            in_with = True
            continue

        if line == "SELECT" or line == "SELECT DISTINCT":
            return

        if not in_with or not line.strip():
            continue

        if indent:
            assert line.startswith(indent), f"{num}: {line=} {indent=}"

            if line != (indent + ")") and line != (indent + "),"):
                continue
            indent = None
            continue

        chop = line.strip()
        chop = re.sub(r"\s+", " ", chop)
        chop = chop.strip()

        if (line != chop) and chop.endswith(" AS ("):
            name = chop.removesuffix(" AS (").strip()

            indent = line.removesuffix(f"{name} AS (")

            yield name
            continue

        raise RuntimeError(f"Unhandled case {line=}")


def drop_cte(src) -> str:
    out = None
    for line in src.splitlines():
        if out is not None:
            out += line + "\n"
        else:
            if "--" in line:
                text = line[: line.find("--")]
            else:
                text = line
            if text.startswith("SELECT"):
                assert text.startswith("SELECT ") or text.strip() == "SELECT", (
                    f"{text=}"
                )
                out = line + "\n"
    assert out is not None
    return out


@dataclass(frozen=True)
class SQL:
    note: str | None
    body: str
    uses: tuple[str, ...]


@dataclass(frozen=True)
class CTE:
    name: str
    note: str | None
    body: str
    uses: tuple[str, ...]


def glot_ctes(sql: str) -> gen[CTE]:
    with_clause = sqlglot.parse_one(sql, read="tsql").args.get("with_")

    if isinstance(with_clause, sqlglot.exp.With):
        for cte in with_clause.expressions:
            body = cte.this.sql(pretty=True, dialect="tsql").splitlines()
            note = []
            while body and body[0].startswith("/*"):
                assert body[0].endswith("*/")
                note.append(
                    body[0]
                    .removeprefix("/*")
                    .removeprefix(" ")
                    .removesuffix("*/")
                    .removesuffix(" ")
                )
                body = body[1:]

            yield CTE(
                cte.alias_or_name,
                None if not note else "\n".join(f"-- {n}" for n in note),
                "\n".join(body) + "\n",
                tuple(
                    sorted(
                        {table.name for table in cte.this.find_all(sqlglot.exp.Table)}
                    )
                ),
            )


def glot_body(sql: str) -> SQL:
    raise RuntimeError("??? - glot_body")
