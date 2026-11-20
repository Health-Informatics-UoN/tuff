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

"""functions for manipulating and cleaning sql as a whole string"""

import json
import re
import subprocess


def default_format(config, sql: str) -> str:
    """the default configuration"""
    # sql = format_sql(sql)
    # sql = sqlfluff.fix(sql, dialect="tsql").strip()

    if config.no_npx:
        pass  # skip npx
    else:
        sql = npx_sql_formatter(sql)

    sql = sql.strip() + "\n"

    return sql


def strip_sql_comments(sql: str) -> str:
    pattern = re.compile(
        r"""
        (                       # group 1: things to KEEP intact
            '(?:[^']|'')*'      #   single-quoted string ('' = escaped quote)
          | "(?:[^"]|"")*"      #   double-quoted string
        )
        |                       # OR
        --[^\n]*                # line comment  (discard)
        | /\*.*?\*/             # block comment (discard, non-greedy)
        """,
        re.VERBOSE | re.DOTALL,
    )

    def repl(m):
        # If group 1 matched, it's a string literal -> keep it
        return m.group(1) if m.group(1) is not None else ""

    return pattern.sub(repl, sql)


def npx_sql_formatter(src: str) -> str:
    return _npx_external(
        src,
        "sql-formatter",
        "-c",
        json.dumps(
            {
                "language": "transactsql",
                "keywordCase": "upper",
                "tabWidth": 2,
            }
        ),
    )


_npx_external_warn = True


def _npx_external(input: str, *cmd: str):
    global _npx_external_warn
    if _npx_external_warn:
        _npx_external_warn = False
        print("(WARNING; using external npx programs - this will be slow)\n")

    return (
        subprocess.run(
            ["npx"] + list(cmd),
            input=input,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        + "\n"
    )
