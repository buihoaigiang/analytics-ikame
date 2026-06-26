# CLAUDE.md -- trend_explore

## Description

## Scope
- App: ios_heart_rate
- Country:
- Date range:
- Filter:

## Data Source
- BQ Project: team-begamob
- Credential: gcloud_credentials.json (DO NOT commit)

### Tables & Metrics

**Bảng 1 — Installs**
```
iOS_Heart_Rate_CACHED_Events_03.sdk_iap_installs
```
- New Users = `SUM(new_users)`

**Bảng 2 — Purchase Start**
```
iOS_Heart_Rate_CACHED_Events_03.sdk_iap_pay_start_cohort_all_product
```
- Purchase Start Amount =
  ```sql
  CASE
    WHEN View_at = 'User Level' THEN SUM(purchase_start_users)
    WHEN View_at = 'Event Level' THEN SUM(purchase_start_total)
  END
  ```

**Bảng 3 — Conversion / Pay Actual**
```
iOS_Heart_Rate_CACHED_Events_03.sdk_iap_conversion_cohort_all_product
```
- Pay Actual Amount =
  ```sql
  CASE
    WHEN View_at = 'User Level' THEN SUM(sub_pay_actual_users)
    WHEN View_at = 'Event Level' THEN SUM(sub_pay_actual_value)
  END
  ```

### KPI Definitions

| KPI | Công thức |
|-----|-----------|
| **Pay Rate Start** | `IFNULL(SUM(Purchase Start Amount), 0) / IFNULL(SUM(New Users), 0)` |
| **Pay Rate Actual** | `(IFNULL(SUM(IAP Amount), 0) + IFNULL(SUM(Pay Actual Amount), 0)) / SUM(New Users)` |

- **Pay Rate Start**: tỷ lệ user bắt đầu trial / tổng install
- **Pay Rate Actual**: tỷ lệ user thực sự mua / tổng install

## Session Management
- /note <insight>
- /wrap