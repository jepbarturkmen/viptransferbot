Google Sheets entegrasyonu için adımlar (güncellendi) — 2025-08-13

1) Google Cloud Console
   - Yeni bir proje aç.
   - “APIs & Services > Enabled APIs & services” → “+ ENABLE APIS AND SERVICES”
   - **Google Sheets API** ve **Google Drive API**'yi etkinleştir.

2) Service Account (Hizmet Hesabı) oluştur
   - “IAM & Admin > Service Accounts” → “Create service account”
   - Bir ad ver, devam et; “Create & Continue” de geçebilir.
   - “Keys” sekmesinde → “Add key” → “Create new key” → JSON anahtar indir.
   - Bu dosyayı projende `vip_bot/credentials/credentials.json` olarak kaydet (veya
     `GOOGLE_APPLICATION_CREDENTIALS` çevre değişkenine tam yol olarak yaz).

3) Google Sheet hazırlanması
   - Google Drive'da bir Sheet oluştur: örn. “VIP Transfer Bookings”.
   - Sheet'i **servis hesabının e‑mail adresi** (…@…iam.gserviceaccount.com) ile **Editor** olarak paylaş.
   - Tercihen Sheet ID’yi kullan: URL’de `/d/<SHEET_ID>/` kısmı. Bu ID’yi
     `SHEETS_SPREADSHEET_ID` çevre değişkenine yaz ya da .env/config’e ekle.

4) Python paketleri
   pip install gspread google-auth

5) Yapılandırma (tercih)
   - Ortam değişkenleri:
       GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/credentials.json
       SHEETS_SPREADSHEET_ID=<your_sheet_id>
     # ID vermek istemezsen isimle de çalışır (SHEETS_SPREADSHEET_NAME).

6) Kod tarafı
   - `sheet_service.py` (bu patch içinde) modern kimlik doğrulama ile çalışır.
   - `handlers/confirm_handler.py` rezervasyon onayında Sheets’e satır ekler.
   - Hata olursa bot çökmez; log’a yazar ve devam eder.

7) Sheet kolon şeması (ilk sayfa / Sheet1)
   A: Name
   B: Phone
   C: From
   D: To
   E: Pax
   F: BabySeat
   G: Extras
   H: Date
   I: Time
   J: Flight
   K: TelegramUserId
