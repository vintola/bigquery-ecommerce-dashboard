-- Monthly acquisition cohorts and their retention over the following 12 months.
WITH orders AS (
  SELECT
    user_id,
    order_id,
    DATE_TRUNC(DATE(created_at), MONTH) AS order_month,
    sale_price
  FROM `bigquery-public-data.thelook_ecommerce.order_items`
  WHERE status != 'Cancelled'
    AND DATE(created_at) < DATE_TRUNC(
      DATE((SELECT MAX(created_at) FROM `bigquery-public-data.thelook_ecommerce.order_items`)),
      MONTH
    )
),
first_order AS (
  SELECT user_id, MIN(order_month) AS cohort_month
  FROM orders
  GROUP BY user_id
),
activity AS (
  SELECT
    f.cohort_month,
    DATE_DIFF(o.order_month, f.cohort_month, MONTH) AS period,
    o.user_id,
    o.order_id,
    o.sale_price
  FROM orders AS o
  JOIN first_order AS f USING (user_id)
)
SELECT
  cohort_month,
  period,
  COUNT(DISTINCT user_id) AS customers,
  COUNT(DISTINCT order_id) AS orders,
  ROUND(SUM(sale_price), 2) AS revenue
FROM activity
WHERE period BETWEEN 0 AND 12
GROUP BY cohort_month, period
ORDER BY cohort_month, period
