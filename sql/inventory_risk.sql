-- Snapshot of stock ageing by category. Aging is measured against the most
-- recent inventory record in the dataset, not today's date, so the sample
-- stays stable as it ages.
WITH bounds AS (
  SELECT MAX(DATE(created_at)) AS max_date
  FROM `bigquery-public-data.thelook_ecommerce.inventory_items`
)
SELECT
  product_category AS category,
  COUNT(*) AS units,
  COUNTIF(sold_at IS NULL) AS unsold_units,
  ROUND(SAFE_DIVIDE(COUNTIF(sold_at IS NULL), COUNT(*)) * 100, 2) AS unsold_pct,
  ROUND(SUM(IF(sold_at IS NULL, cost, 0)), 2) AS unsold_cost,
  ROUND(AVG(IF(sold_at IS NOT NULL, DATE_DIFF(DATE(sold_at), DATE(created_at), DAY), NULL)), 1) AS avg_days_to_sell,
  ROUND(MAX(IF(sold_at IS NULL, DATE_DIFF((SELECT max_date FROM bounds), DATE(created_at), DAY), NULL)), 0) AS oldest_unsold_days
FROM `bigquery-public-data.thelook_ecommerce.inventory_items`
GROUP BY category
ORDER BY unsold_cost DESC
