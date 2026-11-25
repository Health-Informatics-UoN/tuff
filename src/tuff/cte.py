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
from dataclasses import dataclass
from pathlib import Path

import sqlglot


@dataclass(frozen=True)
class SQLBody:
    note: str
    body: str
    uses: tuple[str, ...]


def cache() -> call[[Path], SQLBody]:
    """given a file, load it as .sql and split up the query into;
    - note; leading comment block
    - uses; names of any/all CTE
    - body; the main SQL SELECT statement

    ... will strip comments between CTE sections ... but that's okay?
    """

    @functools.cache
    def cte_cache(file: Path) -> SQLBody:
        try:
            return glot_body((file).read_text())
        except Exception as ae:
            raise RuntimeError(f"in {file=}") from ae

    return cte_cache


def glot_body(sql: str) -> SQLBody:
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
    return SQLBody(
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
