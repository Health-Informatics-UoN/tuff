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

from tuff import cte

test_data = Path(__file__).parent / "test_data" / __name__


def test_cte_names():
    obtained = list(cte.find_cte((test_data / "with-some-cte.sql").read_text()))
    expected = [
        "MonthlySales",
        "CustomerTrends",
        "CustomerSummary",
        "EnrichedCustomers",
    ]

    assert obtained == expected


def test_drop_cte():
    obtained = cte.drop_cte((test_data / "with-some-cte.sql").read_text())
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

    assert obtained.strip() == expected.strip()
