from pathlib import Path

from tuff import entry


def test_take_args():
    # arrange
    expected_args = ["-a", "-c"]
    expected_b = True
    expected_d = False

    # act
    obtained_args = ["-a", "b", "-c"]
    obtained_d = entry.take_arg(obtained_args, "_D")
    obtained_b = entry.take_arg(obtained_args, "b")

    # assert
    assert obtained_args == expected_args
    assert obtained_b == expected_b
    assert obtained_d == expected_d


def test_bad_dir(tmp_path: Path):
    try:
        entry.launch(tmp_path, [])
    except SystemExit as e:
        assert f"no sql/ --> {tmp_path} <" == str(e)


def test_no_cte_dir(tmp_path: Path):
    (tmp_path / "sql").mkdir()
    try:
        entry.launch(tmp_path, [])
    except SystemExit as e:
        assert f"no sql/cte/ --> {tmp_path} <" == str(e)


def test_no_cte_sql(tmp_path: Path):
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "cte").mkdir()
    try:
        entry.launch(tmp_path, [])
    except SystemExit as e:
        assert f"no sql/cte/*.sql --> {tmp_path} <" == str(e)


def test_no_sql_src(tmp_path: Path):
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "cte").mkdir()
    (tmp_path / "sql" / "cte" / "foo.sql").write_text("yo")
    try:
        entry.launch(tmp_path, [])
    except SystemExit as e:
        assert f"no sql/*.sql in --> {tmp_path} <" == str(e)


def test_weird_args(tmp_path: Path):
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "cte").mkdir()
    (tmp_path / "sql" / "cte" / "foo.sql").write_text("yo")
    (tmp_path / "sql" / "bar.sql").write_text("yo")
    try:
        entry.launch(tmp_path, ["foo"])
    except SystemExit as e:
        assert "What are args=['foo']?" == str(e)


def test_weird_param(tmp_path: Path):
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "cte").mkdir()
    (tmp_path / "sql" / "cte" / "foo.sql").write_text("yo")
    (tmp_path / "sql" / "bar.sql").write_text("yo")
    try:
        entry.launch(tmp_path, ["-foo"])
    except SystemExit as e:
        assert "parameters unknown=['-foo']" == str(e)


def test_diff(tmp_path: Path):
    raise RuntimeError(
        "run a test of the diff() entry point with a monkey-patched Config to check what's invoked and logged"
    )
