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
    obtained = list(cte.find_cte((test_data / "with-some-cte.sql").read_text()))
    expected = sorted(
        [
            "CustomerSummary",
            "CustomerTrends",
            "EnrichedCustomers",
            "MonthlySales",
        ]
    )

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
        FROM
            EnrichedCustomers AS ec
        WHERE
            ec.ActiveMonths >= 3 -- ignore one-off buyers
        ORDER BY
            ec.TotalRevenue DESC,
            ec.CompanyName
        """
    )
    obtained = cte.glot_body((test_data / "with-some-cte.sql").read_text())
    assert obtained.body == expected.strip()


def test_cache(tmp_path):
    file = tmp_path / "query.sql"
    file.write_text((test_data / "with-some-cte.sql").read_text())

    cache = cte.cache()

    val = cache(file)

    assert val.note == ""
    assert val.uses == [
        "CustomerSummary",
        "CustomerTrends",
        "EnrichedCustomers",
        "MonthlySales",
    ]

    file.unlink()

    assert not file.is_file()

    val = cache(file)

    assert val.note == ""
    assert val.uses == [
        "CustomerSummary",
        "CustomerTrends",
        "EnrichedCustomers",
        "MonthlySales",
    ]

    cache.cache_clear()

    with pytest.raises(RuntimeError) as re:
        val = cache(file)

    assert f"in {file=}" == str(re.value)


def glot_uses(sql: str) -> list[str]:
    """reads all tables/CTEs that are selected from; lets you check for what CTEs should be there"""
    raise RuntimeError("???")


def glot_body(sql: str) -> str:
    """the file without the header or top-level CTEs"""
    raise RuntimeError("???")
