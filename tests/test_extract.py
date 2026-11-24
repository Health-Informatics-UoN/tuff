"""tests using sqlgot to extract CTEs and bodies"""

import textwrap

from tuff import cte


def test_body_with_CTEs():

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

    expected = cte.SQLFragment(
        "so - yeah",
        textwrap.dedent(
            """
            SELECT
              *
            FROM third_cte
            """
        ).strip(),
        ("third_cte",),
    )
    obtained = cte.glot_body(sql)

    assert obtained == expected


def test_body_no_CTEs():

    sql = """
    -- so - yeah
    SELECT *
    FROM some_table;
    """

    expected = cte.SQLFragment(
        "so - yeah",
        textwrap.dedent(
            """
            SELECT
              *
            FROM some_table
            """
        ).strip(),
        ("some_table",),
    )
    obtained = cte.glot_body(sql)

    assert obtained == expected
