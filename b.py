import os
import zipfile
import requests
from datetime import datetime

# ==========================================
BOT_TOKEN = "8925598573:AAFsQBxBZOQh2M6q1yBrSgkrUiGohmmaDy8"
CHAT_ID = "7752587536"
# ==========================================

EXCLUDE = {'venv', '.venv', 'node_modules', '.git', '__pycache__'}
ZIP_NAME = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

print("در حال فشرده‌سازی فایل‌ها...")
with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        for f in files:
            if f != ZIP_NAME and not f.endswith('.pyc'):
                fp = os.path.join(root, f)
                z.write(fp, fp)

print("در حال ارسال به تلگرام...")
with open(ZIP_NAME, 'rb') as doc:
    res = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
        data={'chat_id': CHAT_ID, 'caption': f"📦 Backup: {ZIP_NAME}"},
        files={'document': doc}
    )

if res.status_code == 200:
    print("ارسال شد.")
else:
    print(f"خطا: {res.text}")

if os.path.exists(ZIP_NAME):
    os.remove(ZIP_NAME)
