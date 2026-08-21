import os
import sys
import zipfile
import requests
from datetime import datetime

# ==========================================
BOT_TOKEN = "8925598573:AAFsQBxBZOQh2M6q1yBrSgkrUiGohmmaDy8"
CHAT_ID = "7752587536"
# ==========================================

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
EXCLUDE_EXACT_DIRS = {'node_modules', '.git', '__pycache__', '.cache'}

def is_excluded_dir(dir_name):
    if dir_name.startswith('venv') or dir_name.startswith('.venv'):
        return True
    if dir_name in EXCLUDE_EXACT_DIRS:
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

def send_folder_as_zip(target_path, zip_name, display_name, msg_id):
    file_list = []
    
    if os.path.isfile(target_path):
        file_list.append(target_path)
    else:
        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if not is_excluded_dir(d)]
            for f in files:
                if not f.endswith(('.pyc', '.pyo', '.log', '.sqlite3', '.db')) and f != zip_name:
                    file_list.append(os.path.join(root, f))

    total_files = len(file_list)
    if total_files == 0:
        print(f"[-] پوشه {display_name} خالی است یا فایل معتبری ندارد.")
        return

    print(f"\n[+] در حال زیپ کردن: {display_name} ({total_files} فایل)")
    edit_msg(msg_id, f"📦 در حال فشرده‌سازی پوشه: {display_name}...\nتعداد فایل‌ها: {total_files}")

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
        for idx, fp in enumerate(file_list, 1):
            try:
                z.write(fp, fp)
            except Exception:
                pass
            percent = int((idx / total_files) * 100)
            sys.stdout.write(f"\rزیپ {display_name}: {percent}% [{idx}/{total_files}]")
            sys.stdout.flush()

    zip_size_mb = os.path.getsize(zip_name) / (1024 * 1024)
    print(f"\n[+] حجم زیپ: {zip_size_mb:.2f} MB")

    if zip_size_mb > 49.5:
        err_msg = f"❌ پوشه {display_name} بیش از ۴۹ مگابایت است ({zip_size_mb:.1f}MB) و ارسال نشد."
        print(err_msg)
        edit_msg(msg_id, err_msg)
        if os.path.exists(zip_name): os.remove(zip_name)
        return

    edit_msg(msg_id, f"⬆️ در حال ارسال زیپ پوشه {display_name} به تلگرام...")
    
    try:
        with open(zip_name, 'rb') as doc:
            res = requests.post(
                f"{BASE_URL}/sendDocument",
                data={'chat_id': CHAT_ID, 'caption': f"📂 بکاپ پوشه: {display_name}\n📏 حجم: {zip_size_mb:.2f} MB"},
                files={'document': doc},
                timeout=600
            )
        if res.status_code == 200:
            print(f"[+] پوشه {display_name} با موفقیت ارسال شد.")
        else:
            print(f"[-] خطا در ارسال {display_name}: {res.text}")
    except Exception as e:
        print(f"[-] خطا در آپلود {display_name}: {e}")
    finally:
        if os.path.exists(zip_name):
            os.remove(zip_name)

def main():
    status_msg_id = send_msg("🚀 شروع فرایند بکاپ‌گیری مجزا برای هر پوشه...")
    
    # 1. زیپ و ارسال فایل‌های موجود در ریشه اصلی
    root_files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.endswith(('.pyc', '.log', '.sqlite3', '.db'))]
    if root_files:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_root = f"root_files_{timestamp}.zip"
        send_folder_as_zip('.', zip_root, "فایل‌های اصلی Root", status_msg_id)

    # 2. پیمایش تک‌تک پوشه‌های فرعی
    items = [d for d in os.listdir('.') if os.path.isdir(d) and not is_excluded_dir(d)]
    total_folders = len(items)

    for index, folder in enumerate(items, 1):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f"{folder}_{timestamp}.zip"
        print(f"\n================ [{index}/{total_folders}] ================")
        send_folder_as_zip(folder, zip_name, folder, status_msg_id)

    edit_msg(status_msg_id, "✅ تمام! تمام پوشه‌ها به‌صورت مجزا بررسی و زیپ‌هایشان ارسال شد.")

if __name__ == "__main__":
    main()
