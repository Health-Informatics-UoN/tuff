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
    yield from sorted(
        [cte.alias_or_name for cte in sqlglot.parse_one(src, read="tsql").ctes]
    )


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
