-- Monthly product performance for the 500 highest-revenue products.
-- Limiting to the head of the range keeps the published extract small while
-- still covering the products that drive the business.
WITH sales AS (
  SELECT
    DATE_TRUNC(DATE(oi.created_at), MONTH) AS month,
    oi.product_id,
    COUNT(DISTINCT oi.order_id) AS orders,
    COUNT(*) AS units,
    SUM(CASE WHEN oi.returned_at IS NOT NULL THEN 1 ELSE 0 END) AS returned_units,
    SUM(oi.sale_price) AS revenue,
    SUM(p.cost) AS cogs,
    SUM(oi.sale_price - p.cost) AS gross_profit,
    AVG(oi.sale_price) AS avg_sale_price
  FROM `bigquery-public-data.thelook_ecommerce.order_items` AS oi
  JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
    ON p.id = oi.product_id
  WHERE oi.status != 'Cancelled'
    AND DATE(oi.created_at) < DATE_TRUNC(
      DATE((SELECT MAX(created_at) FROM `bigquery-public-data.thelook_ecommerce.order_items`)),
      MONTH
    )
  GROUP BY month, oi.product_id
),
top_products AS (
  SELECT product_id
  FROM sales
  GROUP BY product_id
  ORDER BY SUM(revenue) DESC
  LIMIT 500
)
SELECT
  s.month,
  s.product_id,
  p.name,
  p.brand,
  p.category,
  p.department,
  p.retail_price,
  p.cost,
  s.orders,
  s.units,
  s.returned_units,
  ROUND(s.revenue, 2) AS revenue,
  ROUND(s.cogs, 2) AS cogs,
  ROUND(s.gross_profit, 2) AS gross_profit,
  ROUND(SAFE_DIVIDE(s.gross_profit, s.revenue) * 100, 2) AS gross_margin_pct,
  ROUND(SAFE_DIVIDE(s.returned_units, s.units) * 100, 2) AS return_rate_pct,
  ROUND(s.avg_sale_price, 2) AS avg_sale_price
FROM sales AS s
JOIN top_products USING (product_id)
JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
  ON p.id = s.product_id
ORDER BY s.month, s.product_id
