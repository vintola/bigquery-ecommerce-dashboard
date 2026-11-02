-- Lifetime performance by acquisition source. Users who never ordered are
-- excluded because the join is to order_items.
SELECT
  u.traffic_source,
  COUNT(DISTINCT u.id) AS customers,
  COUNT(DISTINCT oi.order_id) AS orders,
  ROUND(SUM(oi.sale_price), 2) AS revenue,
  ROUND(SAFE_DIVIDE(SUM(oi.sale_price), COUNT(DISTINCT oi.order_id)), 2) AS aov,
  ROUND(SAFE_DIVIDE(COUNT(DISTINCT oi.order_id), COUNT(DISTINCT u.id)), 2) AS orders_per_customer
FROM `bigquery-public-data.thelook_ecommerce.users` AS u
JOIN `bigquery-public-data.thelook_ecommerce.order_items` AS oi
  ON oi.user_id = u.id
WHERE oi.status != 'Cancelled'
  AND DATE(oi.created_at) < DATE_TRUNC(
    DATE((SELECT MAX(created_at) FROM `bigquery-public-data.thelook_ecommerce.order_items`)),
    MONTH
  )
GROUP BY u.traffic_source
ORDER BY revenue DESC
