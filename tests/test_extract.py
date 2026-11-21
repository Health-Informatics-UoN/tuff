"""tests using sqlgot to extract CTEs and bodies"""

import textwrap

from tuff import cte


def test_no_ctes():

    sql = """
        SELECT id, name
        FROM users
        WHERE active = TRUE
    """

    ctes = list(cte.glot_ctes(sql))

    assert ctes == []


def test_extract_cte():

    sql = """
    WITH first_cte AS (
        -- well then!
        SELECT id, name
        FROM users
        WHERE active = TRUE
    ),
    second_cte AS (
        SELECT user_id, COUNT(*) AS order_count
        FROM orders
        GROUP BY user_id
    ),
    third_cte AS (
        --  oh yeah
        --oh my!
        SELECT f.name, s.order_count
        FROM first_cte AS f
        LEFT JOIN second_cte AS s
            ON f.id = s.user_id
    )
    SELECT *
    FROM third_cte;
    """

    obtained = list(cte.glot_ctes(sql))

    assert obtained == [
        cte.CTE(
            "first_cte",
            "-- well then!",
            textwrap.dedent(
                """
                    SELECT
                      id,
                      name
                    FROM users
                    WHERE
                      active = 1
                """
            ).strip()
            + "\n",
            ("users",),
        ),
        cte.CTE(
            "second_cte",
            None,
            textwrap.dedent(
                """
                    SELECT
                      user_id,
                      COUNT(*) AS order_count
                    FROM orders
                    GROUP BY
                      user_id
                """
            ).strip()
            + "\n",
            ("orders",),
        ),
        cte.CTE(
            "third_cte",
            textwrap.dedent(
                """
                --  oh yeah
                -- oh my!
                """
            ).strip(),
            textwrap.dedent(
                """
                    SELECT
                      f.name,
                      s.order_count
                    FROM first_cte AS f
                    LEFT JOIN second_cte AS s
                      ON f.id = s.user_id
                """
            ).strip()
            + "\n",
            (
                "first_cte",
                "second_cte",
            ),
        ),
    ]


def test_extract_body():

    sql = """
    -- so - yeah
    WITH first_cte AS (
        -- well then!
        SELECT id, name
        FROM users
        WHERE active = TRUE
    ),
    second_cte AS (
        SELECT user_id, COUNT(*) AS order_count
        FROM orders
        GROUP BY user_id
    ),
    third_cte AS (
        --  oh yeah
        --oh my!
        SELECT f.name, s.order_count
        FROM first_cte AS f
        LEFT JOIN second_cte AS s
            ON f.id = s.user_id
    )
    SELECT *
    FROM third_cte;
    """

    expected = cte.SQL(
        "so - yeah",
        textwrap.dedent(
            """
            SELECT *
            FROM third_cte
            """
        ),
        ("third_cte",),
    )
    obtained = cte.glot_body(sql)

    assert obtained == expected
