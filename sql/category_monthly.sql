-- Category and department performance by month. Ratios are recomputed in the app
-- after the selected months are aggregated.
SELECT
  DATE_TRUNC(DATE(oi.created_at), MONTH) AS month,
  p.category,
  p.department,
  COUNT(DISTINCT oi.order_id) AS orders,
  COUNT(*) AS units,
  COUNT(DISTINCT oi.user_id) AS customers,
  SUM(CASE WHEN oi.returned_at IS NOT NULL THEN 1 ELSE 0 END) AS returned_units,
  ROUND(SUM(oi.sale_price), 2) AS revenue,
  ROUND(SUM(p.cost), 2) AS cogs,
  ROUND(SUM(oi.sale_price - p.cost), 2) AS gross_profit,
  ROUND(SAFE_DIVIDE(SUM(oi.sale_price - p.cost), SUM(oi.sale_price)) * 100, 2) AS gross_margin_pct,
  ROUND(SAFE_DIVIDE(SUM(CASE WHEN oi.returned_at IS NOT NULL THEN 1 ELSE 0 END), COUNT(*)) * 100, 2) AS return_rate_pct
FROM `bigquery-public-data.thelook_ecommerce.order_items` AS oi
JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
  ON p.id = oi.product_id
WHERE oi.status != 'Cancelled'
  AND DATE(oi.created_at) < DATE_TRUNC(
    DATE((SELECT MAX(created_at) FROM `bigquery-public-data.thelook_ecommerce.order_items`)),
    MONTH
  )
GROUP BY month, category, department
ORDER BY month, revenue DESC
