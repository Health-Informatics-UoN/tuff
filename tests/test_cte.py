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

import textwrap
from pathlib import Path

import pytest

from tuff import cte

test_data = Path(__file__).parent / "test_data" / __name__


def test_cte_names():
    source = (test_data / "with-some-cte.sql").read_text()
    expected = sorted(
        [
            "CustomerSummary",
            "CustomerTrends",
            "EnrichedCustomers",
            "MonthlySales",
            "Orders",  # a real table that we'll pickup anyway
            "Customers",  # a real table that we'll pickup anyway
        ]
    )

    sql_body = cte.glot_body(source)
    obtained = sorted(sql_body.uses)

    assert obtained == expected


def test_drop_cte():
    expected = textwrap.dedent(
        """
        SELECT
          ec.CustomerTier,
          ec.CompanyName,
          ec.Country,
          ec.ActiveMonths,
          ec.TotalOrders,
          FORMAT(ec.TotalRevenue, 'C', 'en-US') AS TotalRevenue,
          FORMAT(ec.AvgMonthlyRevenue, 'C', 'en-US') AS AvgMonthlyRevenue
        FROM EnrichedCustomers AS ec
        WHERE
          ec.ActiveMonths >= 3 /* ignore one-off buyers */
        ORDER BY
          ec.TotalRevenue DESC,
          ec.CompanyName
        """
    )
    obtained = cte.glot_body((test_data / "with-some-cte.sql").read_text())
    assert obtained.body == expected.strip()


from tuff import entry


def test_cache(tmp_path):
    file = tmp_path / "query.sql"
    file.write_text((test_data / "with-some-cte.sql").read_text())

    config = entry.Config(None)

    # load the file/value normally
    val1 = config.cache(file)

    assert (
        val1.note == "Final SELECT: pull the report"
    )  # the note is not actually at the head; it'll be moved there
    assert val1.uses == tuple(
        sorted(
            [
                "Customers",
                "Orders",
                "CustomerSummary",
                "CustomerTrends",
                "EnrichedCustomers",
                "MonthlySales",
            ]
        )
    )

    # remove the file so that the cache needs to reload it
    file.unlink()
    assert not file.is_file()
    val2 = config.cache(file)

    assert val2.note == "Final SELECT: pull the report"
    assert val2.uses == tuple(
        sorted(
            [
                "Customers",
                "Orders",
                "CustomerSummary",
                "CustomerTrends",
                "EnrichedCustomers",
                "MonthlySales",
            ]
        )
    )

    assert val1 == val2

    # check that clearing the cache and calling again DOES now raise an error
    config.cache.cache_clear()
    with pytest.raises(RuntimeError) as re:
        val3 = config.cache(file)
        assert False, f"cache should have failed, but, it returned {val3=}"

    assert f"in {file=}" == str(re.value)


def glot_uses(sql: str) -> list[str]:
    """reads all tables/CTEs that are selected from; lets you check for what CTEs should be there"""
    raise RuntimeError("???")


def glot_body(sql: str) -> str:
    """the file without the header or top-level CTEs"""
    raise RuntimeError("???")
