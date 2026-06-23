## Mô tả
So sánh hành vi cancel subscription giữa Android và iOS
— tìm điểm khác biệt về timing, reason, cohort

## Scope
- App: Android Heart Rate + iOS Heart Rate
- Country: United States
- Date range: 
- Filter:

## Nguồn dữ liệu
- Project BQ: team-begamob
- Bảng iOS: `MMP_Adjust_RawData.iOS_Heart_Rate_Raw_Export_PARTITION`
- Bảng Android: `MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION`
- Filter: `_activity_kind_ = 'subscription'`
- Credential: dùng từ `../../ios-heart-rate/funnel/intro7-vs-intro6/gcloud_credentials.json` (KHÔNG commit bản copy)

## Quy ước query
- `_subscription_event_type_ IN ('activation','trial_started','discounted_offer')` = subscription start events
- `_subscription_event_type_ = 'cancellation'` = cancel event
- Join cancel → start dùng `_subscription_original_transaction_id_`
- D0 = cancel trong vòng 86400 giây (24h) kể từ start_ts

## Findings chính (2026-06-23)
- D0 cancel Android (US): ~27% vs iOS: 36–51% tùy product
- Product `discounted_offer` ($0.99 intro) có ever-cancel thấp nhất: 20.7% global
- iOS cancel trigger: `DID_CHANGE_RENEWAL_STATUS` (ngay khi tắt auto-renewal)
- Android cancel trigger: `SUBSCRIPTION_CANCELED` (muộn hơn, thường sau expiry)