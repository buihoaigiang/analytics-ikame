"""
Diagnostic: kiểm tra table tồn tại + event có sẵn trong GA4 raw
"""
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

CRED_PATH = r"C:\Users\admin\Desktop\analytics-ikame\20260623_ios_face_scanner\scan-vs-purchase-analysis\gcloud_credentials.json"
PROJECT = "team-begamob"

creds = Credentials.from_authorized_user_file(CRED_PATH)
client = bigquery.Client(credentials=creds, project=PROJECT)

# 1. Liệt kê các table trong dataset
print("=" * 60)
print("1. TABLES TRONG ios-face-scanner.analytics_540983063")
print("=" * 60)
dataset_ref = bigquery.DatasetReference("ios-face-scanner", "analytics_540983063")
tables = list(client.list_tables(dataset_ref))
table_names = sorted([t.table_id for t in tables])
print(f"Tổng số tables: {len(table_names)}")
if table_names:
    print("Các table gần nhất:")
    for t in table_names[-10:]:
        print(f"  {t}")
else:
    print("Không có table nào!")

# 2. Xem event names có trong table mới nhất
if table_names:
    latest = table_names[-1]
    print(f"\n{'=' * 60}")
    print(f"2. EVENT NAMES TRONG {latest}")
    print("=" * 60)
    q = f"""
    SELECT event_name, COUNT(*) AS cnt
    FROM `ios-face-scanner.analytics_540983063.{latest}`
    GROUP BY event_name
    ORDER BY cnt DESC
    LIMIT 20
    """
    df = client.query(q).to_dataframe()
    print(df.to_string(index=False))

    # 3. Thử xem có revenue-related event không
    print(f"\n{'=' * 60}")
    print("3. TÌM EVENT LIÊN QUAN ĐẾN PURCHASE/REVENUE")
    print("=" * 60)
    q2 = f"""
    SELECT event_name, COUNT(*) AS cnt
    FROM `ios-face-scanner.analytics_540983063.events_*`
    WHERE event_name LIKE '%purchase%'
       OR event_name LIKE '%revenue%'
       OR event_name LIKE '%payment%'
       OR event_name LIKE '%subscribe%'
       OR event_name LIKE '%subscription%'
    GROUP BY event_name
    ORDER BY cnt DESC
    """
    df2 = client.query(q2).to_dataframe()
    if df2.empty:
        print("Không tìm thấy event nào liên quan đến purchase/revenue!")
    else:
        print(df2.to_string(index=False))

    # 4. Date range có data
    print(f"\n{'=' * 60}")
    print("4. DATE RANGE CÓ DATA")
    print("=" * 60)
    q3 = """
    SELECT MIN(event_date) AS min_date, MAX(event_date) AS max_date, COUNT(DISTINCT event_date) AS num_days
    FROM `ios-face-scanner.analytics_540983063.events_*`
    """
    df3 = client.query(q3).to_dataframe()
    print(df3.to_string(index=False))
