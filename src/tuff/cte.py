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

from collections.abc import (
    Collection as collection,
)
from collections.abc import (
    Generator as gen,
)
from collections.abc import (
    Iterable as iterable,
)
from collections.abc import (
    Mapping as mapping,
)
from dataclasses import dataclass
from typing import TypeVar

import sqlglot

E = TypeVar("E")


@dataclass(frozen=True)
class SQLBody:
    note: str
    body: str
    uses: tuple[str, ...]


def glot_body(sql: str) -> SQLBody:
    """given sql code as text - parse/extract just the "body" discarding all CTEs

    - reformats the "main body" of the query (turns it to an AST the recreates it)
    - keeps any comments at the top of the file and combines them with ones from the query
    - scans for CTEs we use and our CTEs used (... or should we only do ones we directly use?)

    ... will strip comments between CTE sections ... but that's okay?
    """
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
    uses = sorted(
        transitive_listing(
            used, [table.name for table in parsed.find_all(sqlglot.exp.Table)]
        )
    )

    # remove the comments now, then, pretty print the body
    parsed.comments = []
    body = parsed.sql(pretty=True, dialect="tsql")

    # pack the result into the fragment
    return SQLBody(
        note="\n".join(c.strip() for c in comments),
        body=body.strip(),
        uses=tuple(uses),
    )


def transitive_listing(used: mapping[E, collection[E]], todo: iterable[E]) -> gen[E]:
    """given a full dict @used, for each entry in @todo; yield that entry and any entries it uses"""
    seen: set[E] = set()
    while todo:
        head = todo[0]
        todo = todo[1:]

        if head not in seen:
            seen.add(head)

            yield head
            todo += used.get(head, [])
