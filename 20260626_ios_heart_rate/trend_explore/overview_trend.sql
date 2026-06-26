-- Overview Metrics — ios_heart_rate
-- Chart: Bar (New Users) + Line (%Pay Rate Start, %Pay Rate Actual)
-- Dimension: install_date (daily)
--
-- Params to adjust:
--   date range       : DATE_FROM / DATE_TO
--   cohort day       : COHORT_DAY  (= number_day_install)
--   data source      : DATA_SOURCE ('Adjust' | 'Firebase')
--   view at          : User Level  → _users cols
--                      Event Level → _total/_value cols

WITH installs AS (
  SELECT
    install_date,
    SUM(new_users) AS new_users
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_03.sdk_iap_installs`
  WHERE install_date BETWEEN '2026-01-01' AND '2026-06-25'
    AND data_source = 'Adjust'
  GROUP BY install_date
),

pay_start AS (
  SELECT
    install_date,
    -- User Level: purchase_start_users / iap_users
    -- Event Level: purchase_start_total / iap_total
    SUM(purchase_start_users) AS purchase_start_amt,
    SUM(iap_users)            AS iap_amt
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_03.sdk_iap_pay_start_cohort_all_product`
  WHERE install_date BETWEEN '2026-01-01' AND '2026-06-25'
    AND number_day_install = 60
    AND data_source        = 'Adjust'
  GROUP BY install_date
),

conversion AS (
  SELECT
    install_date,
    -- User Level: sub_pay_actual_users
    -- Event Level: sub_pay_actual_total / sub_pay_actual_value
    SUM(sub_pay_actual_users) AS pay_actual_amt
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_03.sdk_iap_conversion_cohort_all_product`
  WHERE install_date BETWEEN '2026-01-01' AND '2026-06-25'
    AND number_day_install = 60
    AND data_source        = 'Adjust'
  GROUP BY install_date
)

SELECT
  i.install_date,
  i.new_users,
  IFNULL(ps.purchase_start_amt, 0)                                    AS purchase_start_amt,
  IFNULL(ps.iap_amt,            0)                                    AS iap_amt,
  IFNULL(c.pay_actual_amt,      0)                                    AS pay_actual_amt,

  -- %Pay Rate Start = purchase_start / new_users
  ROUND(SAFE_DIVIDE(
    IFNULL(ps.purchase_start_amt, 0),
    i.new_users
  ) * 100, 2)                                                         AS pct_pay_rate_start,

  -- %Pay Rate Actual = (iap + pay_actual) / new_users
  ROUND(SAFE_DIVIDE(
    IFNULL(ps.iap_amt, 0) + IFNULL(c.pay_actual_amt, 0),
    i.new_users
  ) * 100, 2)                                                         AS pct_pay_rate_actual

FROM installs i
LEFT JOIN pay_start  ps ON i.install_date = ps.install_date
LEFT JOIN conversion c  ON i.install_date = c.install_date
ORDER BY i.install_date
