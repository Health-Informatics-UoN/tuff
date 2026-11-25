import textwrap

from tuff import clean, entry


def test_full_and_slow():
    expected = (
        textwrap.dedent(
            """
            SELECT
              foor
            FROM
              bar
            """
        ).strip()
        + "\n"
    )

    original = "seLect foor From bar"

    config = entry.Config(None)

    obtained = clean.default_format(config, original)

    assert obtained == expected


def test_fast_but_useless():
    expected = "seLect foor From bar\n"

    original = "   seLect foor From bar"

    config = entry.Config(None, no_npx=True)

    obtained = clean.default_format(config, original)

    assert obtained == expected


def test_strip_comments():
    expected = (
        textwrap.dedent(
            """
            SELECT 
              foor
            FROM
              bar
            """
        ).strip()
        + "\n"
    )

    original = (
        textwrap.dedent(
            """
            SELECT -- foo!
              foor
            FROM
              bar
            """
        ).strip()
        + "\n"
    )

    # config = entry.Config(None)

    obtained = clean.strip_sql_comments(original)

    assert obtained == expected
