import os
import sys
import zipfile
import requests
from datetime import datetime

# ==========================================
BOT_TOKEN = "8925598573:AAFsQBxBZOQh2M6q1yBrSgkrUiGohmmaDy8"
CHAT_ID = "7752587536"
# ==========================================

EXCLUDE = {'venv', '.venv', 'node_modules', '.git', '__pycache__'}
ZIP_NAME = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_msg(text):
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", data={'chat_id': CHAT_ID, 'text': text})
        return r.json().get('result', {}).get('message_id')
    except Exception:
        return None

def edit_msg(msg_id, text):
    if not msg_id: return
    try:
        requests.post(f"{BASE_URL}/editMessageText", data={'chat_id': CHAT_ID, 'message_id': msg_id, 'text': text})
    except Exception:
        pass

def main():
    msg_id = send_msg("🚀 شروع فرایند بکاپ‌گیری...")
    
    # 1. جمع‌آوری لیست فایل‌ها
    file_list = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        for f in files:
            if f != ZIP_NAME and not f.endswith('.pyc'):
                file_list.append(os.path.join(root, f))
                
    total_files = len(file_list)
    if total_files == 0:
        msg = "❌ هیچ فایلی برای زیپ کردن پیدا نشد!"
        print(msg)
        edit_msg(msg_id, msg)
        return

    # 2. فشرده‌سازی با نمایش درصد
    print(f"شروع فشرده‌سازی {total_files} فایل...")
    last_percent = -1
    
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as z:
        for idx, fp in enumerate(file_list, 1):
            try:
                z.write(fp, fp)
            except Exception as e:
                print(f"خطا در خواندن فایل {fp}: {e}")
                
            percent = int((idx / total_files) * 100)
            
            # چاپ در ترمینال
            sys.stdout.write(f"\rدرصد زیپ شدن: {percent}% [{idx}/{total_files}]")
            sys.stdout.flush()
            
            # آپدیت تلگرام هر ۲۰ درصد
            if percent % 20 == 0 and percent != last_percent:
                edit_msg(msg_id, f"📦 در حال فشرده‌سازی...\nپیشرفت: {percent}% ({idx}/{total_files} فایل)")
                last_percent = percent

    print("\nفشرده‌سازی کامل شد.")
    edit_msg(msg_id, "⬆️ فشرده‌سازی تموم شد. در حال ارسال فایل به تلگرام...")

    # 3. ارسال فایل زیپ به تلگرام
    print("در حال ارسال فایل به تلگرام...")
    try:
        with open(ZIP_NAME, 'rb') as doc:
            res = requests.post(
                f"{BASE_URL}/sendDocument",
                data={'chat_id': CHAT_ID, 'caption': f"✅ بکاپ با موفقیت ارسال شد!\n📂 فایل: {ZIP_NAME}"},
                files={'document': doc},
                timeout=300
            )
            
        if res.status_code == 200:
            print("ارسال موفقیت‌آمیز بود.")
            edit_msg(msg_id, "✅ تمام! فایل زیپ به تلگرام فرستاده شد.")
        else:
            err_text = f"❌ خطا در ارسال به تلگرام:\n{res.text}"
            print(err_text)
            edit_msg(msg_id, err_text)
            
    except Exception as e:
        err_msg = f"❌ خطا حین ارسال فایل: {e}"
        print(err_msg)
        edit_msg(msg_id, err_msg)
        
    finally:
        if os.path.exists(ZIP_NAME):
            os.remove(ZIP_NAME)

if __name__ == "__main__":
    main()
