import os
import sys
import zipfile
import requests
from datetime import datetime

# ==========================================
BOT_TOKEN = "8925598573:AAFsQBxBZOQh2M6q1yBrSgkrUiGohmmaDy8"
CHAT_ID = "7752587536"
# ==========================================

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
ZIP_NAME = f"backup_{TIMESTAMP}.zip"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
PART_SIZE = 40 * 1024 * 1024  # پارت‌های ۴۰ مگابایتی

EXCLUDE_EXACT_DIRS = {'venv9', 'node_modules', '.git', '__pycache__', '.cache'}

def is_excluded_dir(dir_name):
    if dir_name == 'venv9' or dir_name.startswith('venv9'):
        return True
    if dir_name.startswith('venv') or dir_name.startswith('.venv'):
        return True
    return dir_name in EXCLUDE_EXACT_DIRS

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

def split_file(file_path, chunk_size):
    parts = []
    part_num = 1
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            part_name = f"{file_path}.part{part_num}"
            with open(part_name, 'wb') as chunk_file:
                chunk_file.write(chunk)
            parts.append(part_name)
            part_num += 1
    return parts

def main():
    msg_id = send_msg("🚀 شروع فشرده‌سازی سورس...")
    
    file_list = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not is_excluded_dir(d)]
        for f in files:
            if f != ZIP_NAME and not f.endswith('.pyc') and not '.part' in f:
                file_list.append(os.path.join(root, f))
                
    total_files = len(file_list)
    if total_files == 0:
        msg = "❌ هیچ فایلی پیدا نشد!"
        print(msg)
        edit_msg(msg_id, msg)
        return

    print(f"شروع فشرده‌سازی {total_files} فایل...")
    last_percent = -1
    
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as z:
        for idx, fp in enumerate(file_list, 1):
            try:
                z.write(fp, fp)
            except Exception:
                pass
            percent = int((idx / total_files) * 100)
            sys.stdout.write(f"\r[+] پیشرفت زیپ: {percent}% [{idx}/{total_files}]")
            sys.stdout.flush()
            
            if percent % 10 == 0 and percent != last_percent:
                edit_msg(msg_id, f"📦 در حال فشرده‌سازی...\nپیشرفت: {percent}% ({idx}/{total_files} فایل)")
                last_percent = percent

    zip_size = os.path.getsize(ZIP_NAME)
    zip_size_mb = zip_size / (1024 * 1024)
    print(f"\n[+] زیپ کامل شد. حجم کل: {zip_size_mb:.2f} MB")

    parts = []
    if zip_size > PART_SIZE:
        edit_msg(msg_id, f"✂️ حجم فایل ({zip_size_mb:.1f}MB) بالاست. در حال تقسیم به پارت‌های ۴۰ مگابایتی...")
        print("[+] در حال تقسیم فایل به پارت‌ها...")
        parts = split_file(ZIP_NAME, PART_SIZE)
        os.remove(ZIP_NAME) # حذف فایل اصلی
    else:
        parts = [ZIP_NAME]

    total_parts = len(parts)
    for i, part in enumerate(parts, 1):
        p_size = os.path.getsize(part) / (1024 * 1024)
        edit_msg(msg_id, f"⬆️ در حال ارسال پارت {i} از {total_parts} ({p_size:.1f} MB)...")
        print(f"[+] ارسال {part}...")
        
        try:
            with open(part, 'rb') as doc:
                res = requests.post(
                    f"{BASE_URL}/sendDocument",
                    data={'chat_id': CHAT_ID, 'caption': f"📦 بکاپ (پارت {i} از {total_parts})\n📂 فایل: {part}\n📏 حجم: {p_size:.1f} MB"},
                    files={'document': doc},
                    timeout=600
                )
            if res.status_code == 200:
                print(f"[+] پارت {i} فرستاده شد.")
            else:
                print(f"[-] خطا در ارسال پارت {i}: {res.text}")
        except Exception as e:
            print(f"[-] خطا: {e}")
        finally:
            if os.path.exists(part):
                os.remove(part)

    edit_msg(msg_id, f"✅ تمام! تمام {total_parts} پارت با موفقیت به تلگرام ارسال شدند.")

if __name__ == "__main__":
    main()
