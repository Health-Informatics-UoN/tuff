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

"""
entry point and main code to do the things

"""

import functools
import hashlib
import subprocess
import sys
import textwrap
from collections.abc import Callable as call
from collections.abc import Generator as gen
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from tuff import clean, cte


@dataclass
class Config:
    root: Path

    # -no-npx; don't invoke the npx steps (and save time)
    no_npx: bool = False

    # -auto-strip; if fixing would fix the diff; just save the changes file silently
    auto_strip: bool = False

    # -auto-comment; apply changes automatically when the only differences are comments
    auto_comment: bool = False

    # cache to prevent emitting the same message more than twice
    _seen: dict[str, bool] = field(default_factory=dict)

    @functools.cached_property
    def cache(self) -> call[[Path], cte.SQLBody]:
        @functools.cache
        def cache(file: Path) -> cte.SQLBody:
            try:
                return cte.glot_body((file).read_text())
            except Exception as ae:
                raise RuntimeError(f"in {file=}") from ae

        return cache

    def log(self, file: Path, *lines: str):
        if not lines:
            return

        full = "\n\t".join(lines)
        name = f"; {str(file).removeprefix(str(self.root))[1:]}\n"

        # check the message cache
        if full in self._seen:
            if self._seen[full]:
                return
            self._seen[full] = True
            full += "\n  ... this message will not repeat again ..."
        else:
            self._seen[full] = False

        # print the message
        print(name + full + "\n")

    def run(self, *args: Path | str):
        subprocess.run(
            args,
            check=True,
            cwd=self.root,
        )

    def write_sql(self, path: Path, text: str):
        path.write_text(text.strip() + "\n")


def launch(cwd: Path, args: list[str]):

    if not (cwd / "sql").is_dir():
        sys.exit(f"no sql/ --> {cwd} <")

    if not (cwd / "sql/cte").is_dir():
        sys.exit(f"no sql/cte/ --> {cwd} <")

    if 0 == len(list((cwd / "sql/cte").glob("*.sql"))):
        sys.exit(f"no sql/cte/*.sql --> {cwd} <")

    if 0 == len(list((cwd / "sql").glob("*.sql"))):
        sys.exit(f"no sql/*.sql in --> {cwd} <")

    config = Config(cwd)

    config.no_npx = take_arg(args, "-no-npx")
    config.auto_strip = take_arg(args, "-auto-strip")
    config.auto_comment = take_arg(args, "-auto-comment")

    unknown = [arg for arg in args if arg.startswith("-")]
    if unknown:
        sys.exit(f"parameters {unknown=}")

    if args == []:
        diff(config)
    else:
        sys.exit(f"What are {args=}?")


def take_arg(args, key: str):
    """test for and removes a key from the args list"""
    if key in args:
        args.remove(key)
        return True
    else:
        return False


def diff(config: Config, todo: list[Path] | None = None) -> None:
    config.log(config.root, f">> running tuff in {config.root}\n")

    if todo is None:
        todo = []
        todo += sorted(each for each in (config.root / "sql/cte").glob("*.sql"))
        todo += sorted(each for each in (config.root / "sql/").glob("*.sql"))

    @cache
    def read_cte(src: Path) -> tuple[cte.CTE, ...]:
        raise RuntimeError("???")

    @cache
    def sql_body(src: Path) -> cte.CTE:
        raise RuntimeError("???")

    for src in todo:
        # TODO

        # so we split up the query into;
        # - note; leading comment block
        # - uses; names of any/all CTE
        # - body; the main SQL SELECT statement
        split_query = config.cache(src)

        good = None
        for each in build(config, [], sorted(split_query.uses)):
            if good is None:
                good = split_query.note + "\nWITH\n"
            else:
                good += ",\n"
            good += each
        if good is None:
            # if good is still none - there were no CTE (which we need to support)
            good = split_query.note

        # compute the final query
        good = (
            clean.default_format(config, good + "\n" + split_query.body).strip() + "\n"
        )

        # compare it to the query on disk
        text = src.read_text()
        if good == text:
            # file is up to date
            continue

        # difference can be stripped away
        if good.strip() == text.strip() and config.auto_strip:
            src.write_text(good)
            config.log(src, "overwrote a .strip() difference")
            config.cache.cache_clear()
            continue

        # strip comments and compare that
        if (
            clean.strip_sql_comments(good).strip()
            == clean.strip_sql_comments(text).strip()
        ) and config.auto_comment:
            src.write_text(good)
            config.log(src, "overwrote a comment difference")
            config.cache.cache_clear()
            continue

        temp: Path = (
            config.root
            # use a temp dir
            / ".temp"
            # use something of the original name to prevent collisions
            / hashlib.md5(str(src).encode("utf-8")).hexdigest()[:6]
            / ("expected-" + src.name)
        )
        temp.parent.mkdir(exist_ok=True, parents=True)
        temp.write_text(good)

        # just use vscode's diff
        code_diff(temp, src)

    print("== sql checks complete - now checking usage\n")

    used = []
    for src in (config.root / "sql").glob("*.sql"):
        used += [
            config.root / "sql/cte" / (each + ".sql") for each in config.cache(src).uses
        ]
    for src in (config.root / "sql/cte").glob("*.sql"):
        if src not in used:
            print("unused " + src.name)

    print("<<< ... done!")


expected_header = (
    textwrap.dedent(
        """
        --
        -->> this is the expected version of the file <<--
        --
        """
    ).strip()
    + "\n"
)


def code_diff(config: Config, expect: Path, actual: Path):
    """use vscode's diff tool (which always returns 0)"""

    # remove the marker from the actual file
    config.write_sql(
        actual,
        actual.read_text()
        .strip()
        .removeprefix(expected_header)
        .removeprefix(expected_header.strip()),
    )

    # remove/add the marker to the expected file
    config.write_sql(
        expect,
        expected_header
        + expect.read_text()
        .strip()
        .removeprefix(expected_header)
        .removeprefix(expected_header.strip()),
    )

    # don't bother waiting - just toss up all the different files in one blast
    config.run("code", "-d", expect, actual)


def build(config, seen: list[str], need: list[str]) -> gen[str]:
    """runs a loop to recursively build a list of full qu"""

    # update the list of need'ed CTE
    need = [each for each in need if each not in seen]

    # if there's nothing left to do, return
    if not need:
        return

    # we'll process this CTE next
    name = need[0]

    # TODO; check for view-tables we are allowed?

    # TODO; check if there's a CTE or not

    self = config.cache(config.root / "sql/cte" / (name + ".sql"))

    # sort the list of other CTEs that our CTE needs
    uses = sorted(each for each in self.uses if each not in seen)
    if uses:
        # if there are CTEs that we need (and haven't loaded) add them to the front of the list so they'll be looked up first
        # ... this breaks infinite loops as long as the CTEs themselves aren't circular
        yield from build(config, seen, uses + need)
    else:
        # all CTEs we need have been loaded; yield this CTE
        code = f"  {name} AS (\n"
        for each in (self.note + "\n" + self.body).strip().splitlines():
            code += f"    {each}\n"
        code += "  )"
        yield code

        # now continue, adding this CTE to the list of ones that are done
        yield from build(config, seen + [name], need)
