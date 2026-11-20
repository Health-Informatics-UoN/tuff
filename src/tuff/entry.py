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

import subprocess
import sys
from collections.abc import Callable as call
from dataclasses import dataclass, field
from pathlib import Path

from tuff import clean, cte


@dataclass
class Config:
    root: Path

    cache: call[[Path], cte.CachedCTE]

    # -no-npx; don't invoke the npx steps (and save time)
    no_npx: bool = False

    # -auto-strip; if fixing would fix the diff; just save the changes file silently
    auto_strip: bool = False

    # -auto-comment; apply changes automatically when the only differences are comments
    auto_comment: bool = False

    # cache to prevent emitting the same message more than twice
    _seen: dict[str, bool] = field(default_factory=dict)

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


def launch(cwd: Path, args: list[str]):

    if not (cwd / "sql").is_dir():
        sys.exit(f"no sql/ --> {cwd} <")

    if not (cwd / "sql/cte").is_dir():
        sys.exit(f"no sql/cte/ --> {cwd} <")

    if 0 == len(list((cwd / "sql/cte").glob("*.sql"))):
        sys.exit(f"no sql/cte/*.sql --> {cwd} <")

    if 0 == len(list((cwd / "sql").glob("*.sql"))):
        sys.exit(f"no sql/*.sql in --> {cwd} <")

    config = Config(cwd, cte.cache())

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


def diff(config: Config) -> None:
    print(f">> running tuff in {config.root}\n")

    todo = []
    todo += sorted(each for each in (config.root / "sql/cte").glob("*.sql"))
    todo += sorted(each for each in (config.root / "sql/").glob("*.sql"))

    for src in todo:
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
        if good.strip() == text.strip():
            if config.auto_strip:
                src.write_text(good)
                config.log(src, "overwrote a .strip() difference")
                config.cache.cache_clear()
            else:
                config.log(
                    src,
                    "the only differences can be erased with .strip()",
                )
            continue

        # strip comments and compare that
        if (
            clean.strip_sql_comments(good).strip()
            == clean.strip_sql_comments(text).strip()
        ):
            if config.auto_comment:
                src.write_text(good)
                config.log(src, "overwrote a comment difference")
                config.cache.cache_clear()
            else:
                config.log(
                    src,
                    "files have different comments",
                )
            continue
        import hashlib

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


import textwrap

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


def code_diff(expect: Path, actual: Path):
    """use vscode's diff tool (which always returns 0)"""

    # remove the marker from the actual file
    actual.write_text(
        actual.read_text()
        .strip()
        .removeprefix(expected_header)
        .removeprefix(expected_header.strip())
        .strip()
        + "\n"
    )
    # remove/add the marker to the expected file
    expect.write_text(
        expected_header
        + expect.read_text()
        .strip()
        .removeprefix(expected_header)
        .removeprefix(expected_header.strip())
        .strip()
        + "\n"
    )

    subprocess.run(
        # ["code", "--wait", "-d", expect, actual],
        # don't bother waiting - just toss up all the different files in one blast
        ["code", "-d", expect, actual],
        check=True,
    )


def build(config, seen: list[str], need: list[str]):
    need = [each for each in need if each not in seen]
    if not need:
        return

    head = need[0]

    self = config.cache(config.root / "sql/cte" / (head + ".sql"))

    uses = [each for each in sorted(self.uses) if each not in seen]
    if not uses:
        code = f"  {head} AS (\n"
        for each in (self.note + "\n" + self.body).strip().splitlines():
            code += f"    {each}\n"
        code += "  )"

        yield code
        yield from build(config, seen + [head], need)
    else:
        yield from build(config, seen, uses + need)
