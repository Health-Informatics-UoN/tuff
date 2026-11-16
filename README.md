# tuff / like T-SQL Ruff?

SQL formatter/checker - checks your `.sql` but doesn't change it.
It's really crude.

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
