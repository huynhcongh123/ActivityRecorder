import os
import sys
import time
import socket
import threading
import io
from PIL import ImageGrab

# Cấu hình thời gian (giây)
CAPTURE_INTERVAL = 5
COMPUTER_NAME = socket.gethostname()
running = True

# Chỉ giữ ảnh gần nhất và tối đa 200 ký tự trong bộ nhớ.
# Không gửi dữ liệu ra ngoài và không ghi ảnh/phím bấm xuống file.
last_screenshot_bytes = None
keylog_buffer = ""


def take_screenshot():
    """Chụp màn hình và giữ ảnh gần nhất trong bộ nhớ."""
    global last_screenshot_bytes
    try:
        screenshot = ImageGrab.grab()
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG', optimize=True)
        last_screenshot_bytes = img_bytes.getvalue()
    except Exception as e:
        print(f"Lỗi chụp ảnh: {e}")


def capture_loop():
    """Vòng lặp chụp ảnh."""
    while running:
        take_screenshot()
        for _ in range(CAPTURE_INTERVAL):
            if not running:
                break
            time.sleep(1)


def on_press(key):
    """Ghi nhận phím bấm trong bộ nhớ; Esc dừng chương trình."""
    global running, keylog_buffer
    try:
        if hasattr(key, 'char') and key.char:
            keylog_buffer = (keylog_buffer + key.char)[-200:]
        else:
            key_name = str(key).replace('Key.', '')
            if key_name == 'esc':
                print("Dừng chương trình...")
                running = False
                return False
            keylog_buffer = (keylog_buffer + f"[{key_name}]")[-200:]
    except Exception as e:
        print(f"Lỗi ghi nhận phím: {e}")



def add_to_startup():
    """Thêm vào Startup"""
    try:
        if getattr(sys, 'frozen', False):
            current_path = sys.executable
        else:
            current_path = os.path.abspath(__file__)

        startup_folder = os.path.join(
            os.environ['APPDATA'],
            'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
        )

        shortcut_name = "RemoteMonitor.lnk"
        shortcut_path = os.path.join(startup_folder, shortcut_name)

        if os.path.exists(shortcut_path):
            return True

        vbs_script = f'''
        Set WshShell = CreateObject("WScript.Shell")
        Set shortcut = WshShell.CreateShortcut("{shortcut_path}")
        shortcut.TargetPath = "{current_path}"
        shortcut.WorkingDirectory = "{os.path.dirname(current_path)}"
        shortcut.Description = "Remote Monitor"
        shortcut.Save
        '''

        vbs_path = os.path.join(os.environ['TEMP'], 'create_shortcut.vbs')
        with open(vbs_path, 'w', encoding='utf-8') as f:
            f.write(vbs_script)

        os.system(f'cscript //nologo "{vbs_path}"')
        os.remove(vbs_path)
        return True

    except Exception as e:
        print(f"⚠️ Lỗi startup: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove":
            # Chức năng gỡ Startup chưa được triển khai.
            sys.exit(0)
        elif sys.argv[1] == "--add":
            add_to_startup()
            sys.exit(0)

    print(f"ACTIVITY RECORDER - {COMPUTER_NAME}")
    print("Chụp màn hình định kỳ và ghi nhận phím bấm trong bộ nhớ.")
    print("Nhấn Esc hoặc Ctrl+C để dừng.")

    add_to_startup()
    threading.Thread(target=capture_loop, daemon=True).start()

    from pynput import keyboard

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
    finally:
        listener.stop()
        listener.join()
        print("Đã dừng chương trình")
