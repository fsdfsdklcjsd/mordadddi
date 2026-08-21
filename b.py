import os
import sys
import zipfile
import requests
from datetime import datetime

# ==========================================
BOT_TOKEN = "8925598573:AAFsQBxBZOQh2M6q1yBrSgkrUiGohmmaDy8"
CHAT_ID = "7752587536"
# ==========================================

ZIP_NAME = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# لیست پوشه‌ها و فایل‌های استثنا (می‌توانید مواردی که نمی‌خواهید زیپ شوند را ویرایش کنید)
EXCLUDE_EXACT_DIRS = {'node_modules', '.git', '__pycache__', '.cache'}
EXCLUDE_EXACT_FILES = {ZIP_NAME, '.DS_Store'}
EXCLUDE_EXTENSIONS = ('.pyc', '.pyo', '.log', '.sqlite3', '.db')

def is_excluded_dir(dir_name):
    # نادیده گرفتن تمام پوشه‌هایی که با venv یا .venv شروع می‌شوند
    if dir_name.startswith('venv') or dir_name.startswith('.venv'):
        return True
    if dir_name in EXCLUDE_EXACT_DIRS:
        return True
    return False

def is_excluded_file(file_name):
    if file_name in EXCLUDE_EXACT_FILES:
        return True
    if file_name.endswith(EXCLUDE_EXTENSIONS):
        return True
    return False

def send_msg(text):
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", data={'chat_id': CHAT_ID, 'text': text}, timeout=10)
        return r.json().get('result', {}).get('message_id')
    except Exception:
        return None

def edit_msg(msg_id, text):
    if not msg_id: return
    try:
        requests.post(f"{BASE_URL}/editMessageText", data={'chat_id': CHAT_ID, 'message_id': msg_id, 'text': text}, timeout=10)
    except Exception:
        pass

def main():
    msg_id = send_msg("🚀 شروع فرایند بکاپ‌گیری...")
    
    file_list = []
    for root, dirs, files in os.walk('.'):
        # حذف پوشه‌های استثنا شده از پیمایش
        dirs[:] = [d for d in dirs if not is_excluded_dir(d)]
        for f in files:
            if not is_excluded_file(f):
                file_list.append(os.path.join(root, f))
                
    total_files = len(file_list)
    if total_files == 0:
        msg = "❌ هیچ فایلی برای زیپ کردن پیدا نشد!"
        print(msg)
        edit_msg(msg_id, msg)
        return

    print(f"شروع فشرده‌سازی {total_files} فایل...")
    last_percent = -1
    
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as z:
        for idx, fp in enumerate(file_list, 1):
            try:
                z.write(fp, fp)
            except Exception as e:
                print(f"\nخطا در خواندن {fp}: {e}")
                
            percent = int((idx / total_files) * 100)
            
            # نمایش پیشرفت شفاف در ترمینال
            sys.stdout.write(f"\r[+] پیشرفت زیپ: {percent}% [{idx}/{total_files}]")
            sys.stdout.flush()
            
            # بروزرسانی پیام تلگرام در بازه‌های ۱۰ درصدی
            if percent % 10 == 0 and percent != last_percent:
                edit_msg(msg_id, f"📦 در حال فشرده‌سازی سورس‌کد...\nپیشرفت: {percent}% ({idx}/{total_files} فایل)")
                last_percent = percent

    print("\n[+] فشرده‌سازی کامل شد. در حال ارسال به تلگرام...")
    edit_msg(msg_id, "⬆️ فشرده‌سازی تموم شد. در حال آپلود فایل زیپ به تلگرام...")

    try:
        zip_size_mb = os.path.getsize(ZIP_NAME) / (1024 * 1024)
        if zip_size_mb > 49.5:
            err_size = f"❌ حجم فایل زیپ ({zip_size_mb:.1f}MB) بیش از حد مجاز ربات تلگرام (۵۰ مگابایت) است!"
            print(f"\n{err_size}")
            edit_msg(msg_id, err_size)
            return

        with open(ZIP_NAME, 'rb') as doc:
            res = requests.post(
                f"{BASE_URL}/sendDocument",
                data={
                    'chat_id': CHAT_ID,
                    'caption': f"✅ بکاپ با موفقیت دریافت شد!\n📦 فایل: {ZIP_NAME}\n📏 حجم: {zip_size_mb:.2f} MB"
                },
                files={'document': doc},
                timeout=600
            )
            
        if res.status_code == 200:
            print("[+] ارسال با موفقیت انجام شد.")
            edit_msg(msg_id, f"✅ تمام! فایل زیپ ({zip_size_mb:.2f} MB) با موفقیت در تلگرام آپلود شد.")
        else:
            print(f"\n[-] خطا در ارسال: {res.text}")
            edit_msg(msg_id, f"❌ خطا در ارسال به تلگرام:\n{res.text}")
            
    except Exception as e:
        print(f"\n[-] خطا: {e}")
        edit_msg(msg_id, f"❌ خطا حین آپلود: {e}")
        
    finally:
        if os.path.exists(ZIP_NAME):
            os.remove(ZIP_NAME)

if __name__ == "__main__":
    main()
