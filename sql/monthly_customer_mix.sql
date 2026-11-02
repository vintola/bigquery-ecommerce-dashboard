-- New vs returning customers by month, based on each customer's first order month.
WITH orders AS (
  SELECT DISTINCT
    user_id,
    order_id,
    DATE_TRUNC(DATE(created_at), MONTH) AS month
  FROM `bigquery-public-data.thelook_ecommerce.order_items`
  WHERE status != 'Cancelled'
    AND DATE(created_at) < DATE_TRUNC(
      DATE((SELECT MAX(created_at) FROM `bigquery-public-data.thelook_ecommerce.order_items`)),
      MONTH
    )
),
first_order AS (
  SELECT user_id, MIN(month) AS first_month
  FROM orders
  GROUP BY user_id
)
SELECT
  o.month,
  COUNT(DISTINCT IF(o.month = f.first_month, o.user_id, NULL)) AS new_customers,
  COUNT(DISTINCT IF(o.month > f.first_month, o.user_id, NULL)) AS returning_customers
FROM orders AS o
JOIN first_order AS f USING (user_id)
GROUP BY o.month
ORDER BY o.month
