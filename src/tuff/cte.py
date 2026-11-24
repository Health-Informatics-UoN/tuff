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
            main = glot_body(full)
            body = main.body
            uses = main.uses
            note = ""
            for line in main.note.splitlines():
                line = line.strip()
                if not line.startswith("--"):
                    break
                note += ("-- " + line[2:].strip()).strip() + "\n"
            return CachedCTE(note.strip(), body, uses)
        except Exception as ae:
            raise RuntimeError(f"in {file=}") from ae

    return cte_cache


@dataclass(frozen=True)
class SQLFragment:
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

    if with_clause is None:
        pass
    elif isinstance(with_clause, sqlglot.exp.With):
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
    else:
        raise TypeError


def glot_body(sql: str) -> SQLFragment:
    """using SQLGlot extract the body, uses and header comments / notes"""
    parsed = sqlglot.parse_one(sql, read="tsql")

    # collect the comments before the WITH statement
    comments = None
    used: dict[str, list[str]] = {}
    if ctes := parsed.args.get("with_"):
        comments = ctes.comments

        for cte in ctes.expressions:
            assert cte.alias not in used
            used[cte.alias] = [table.name for table in cte.find_all(sqlglot.exp.Table)]

        # remove the with statement
        parsed.args.pop("with_")

    # add in comments on the main statement
    comments = ([] if comments is None else comments) + parsed.comments

    # we removed with, so, any remaining tables are things we're really looking at
    uses = loop(used, [table.name for table in parsed.find_all(sqlglot.exp.Table)])

    # remove the comments now, then, pretty print the body
    parsed.comments = []
    body = parsed.sql(pretty=True, dialect="tsql")

    # pack the result into the fragment
    return SQLFragment(
        note="\n".join(c.strip() for c in comments),
        body=body.strip(),
        uses=tuple(uses),
    )


def loop(used: dict[str, list[str]], todo: list[str]):
    seen = []
    while todo:
        head = todo[0]
        todo = todo[1:]

        if head not in seen:
            seen.append(head)

            yield head
            todo += used.get(head, [])
