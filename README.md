# tuff / like T-SQL Ruff?

SQL formatter/checker - checks your `.sql` but doesn't change it.
It's really crude.

## Use

You can invoke it with [uvx](https://docs.astral.sh/uv/guides/tools/) like this ...

```bash
$ uvx --from git+https://codeberg.org/paintgoblin/tuff.git tuff
```

## Needs

It needs to be run from a dir with `sql/` in it, and it needs [`npx`](https://nodejs.org/en/download) and [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed.
My setup is ...

```bash
$ ls
README.md       sql

$ npx -v
11.17.0

$ uvx -v
DEBUG Searching for user configuration in: `/Users/peter/.config/uv/uv.toml`
DEBUG uv 0.11.19 (7b2cff1c3 2026-06-03 aarch64-apple-darwin)
Provide a command to run with `uvx <command>`.

See `uvx --help` for more information.


$ uvx --from git+https://codeberg.org/paintgoblin/tuff.git tuff
```

## Does

- run in folder `sql/`
  - will check `sql/cte/*.sql` for CTEs
    - run `npx sql-formatter` on each; error if it changes them
    - check CTEs don't have CTEs
  - will check all `sql/*.sql`
    - run `npx sql-formatter` on each; error if it changes them
    - check any CTEs match what was above

## Want

- sqlfluff linting - and more?
- sql-formatter running from python as well
- read/save settings from .vscode file
- detect / complain about nested-CTEs using sql-glot
  - ... maybe just switch to that instead of the string matching
- pre-commit job
- dump/copy CTEs with their deps
- prepare/show "live queries" that replace specific CTEs (so ... sql/cte/live/?)
- convert to a vscode extension
