WITH
    -- CTE 1: Aggregate raw sales into per-customer, per-month totals
    MonthlySales AS (
        SELECT
            so.CustomerID,
            DATEFROMPARTS(YEAR(so.OrderDate), MONTH(so.OrderDate), 1) AS SalesMonth,
            SUM(so.TotalAmount) AS MonthRevenue,
            COUNT(DISTINCT so.OrderID) AS OrderCount
        FROM
            Sales.Orders AS so
        WHERE
            so.OrderDate >= DATEADD(MONTH, -12, GETDATE())
            AND so.Status = 'Completed'
        GROUP BY
            so.CustomerID,
            DATEFROMPARTS(YEAR(so.OrderDate), MONTH(so.OrderDate), 1)
    ),
    -- CTE 2: Add a running total and a rank per customer using window functions
    CustomerTrends AS (
        SELECT
            ms.CustomerID,
            ms.SalesMonth,
            ms.MonthRevenue,
            ms.OrderCount,
            SUM(ms.MonthRevenue) OVER (
                PARTITION BY
                    ms.CustomerID
                ORDER BY
                    ms.SalesMonth ROWS BETWEEN UNBOUNDED PRECEDING
                    AND CURRENT ROW
            ) AS RunningRevenue,
            RANK() OVER (
                PARTITION BY
                    ms.CustomerID
                ORDER BY
                    ms.MonthRevenue DESC
            ) AS RevenueRankWithinCustomer
        FROM
            MonthlySales AS ms
    ),
    -- CTE 3: Roll up to a per-customer summary with totals and averages
    CustomerSummary AS (
        SELECT
            ct.CustomerID,
            COUNT(*) AS ActiveMonths,
            SUM(ct.MonthRevenue) AS TotalRevenue,
            AVG(ct.MonthRevenue) AS AvgMonthlyRevenue,
            MAX(ct.RunningRevenue) AS FinalRunningRevenue,
            SUM(ct.OrderCount) AS TotalOrders
        FROM
            CustomerTrends AS ct
        GROUP BY
            ct.CustomerID
    ),
    -- CTE 4: Enrich with customer name and tier classification
    EnrichedCustomers AS (
        SELECT
            cs.CustomerID,
            c.CompanyName,
            c.Country,
            cs.ActiveMonths,
            cs.TotalRevenue,
            cs.AvgMonthlyRevenue,
            cs.TotalOrders,
            CASE
                WHEN cs.TotalRevenue >= 100000 THEN 'Platinum'
                WHEN cs.TotalRevenue >= 50000 THEN 'Gold'
                WHEN cs.TotalRevenue >= 10000 THEN 'Silver'
                ELSE 'Bronze'
            END AS CustomerTier
        FROM
            CustomerSummary AS cs
            INNER JOIN Sales.Customers AS c ON c.CustomerID = cs.CustomerID
    )
    -- Final SELECT: pull the report
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