-- Lifetime order count distribution per customer (used for repeat rate and
-- the customer value view).
WITH customers AS (
  SELECT
    user_id,
    COUNT(DISTINCT order_id) AS orders,
    SUM(sale_price) AS spend
  FROM `bigquery-public-data.thelook_ecommerce.order_items`
  WHERE status != 'Cancelled'
    AND DATE(created_at) < DATE_TRUNC(
      DATE((SELECT MAX(created_at) FROM `bigquery-public-data.thelook_ecommerce.order_items`)),
      MONTH
    )
  GROUP BY user_id
)
SELECT
  orders,
  COUNT(*) AS customers,
  ROUND(SUM(spend), 2) AS revenue,
  ROUND(AVG(spend), 2) AS avg_spend
FROM customers
GROUP BY orders
ORDER BY orders
