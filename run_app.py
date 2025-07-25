# run_app.py
import sys
import os
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon, QFont

# Thiết lập đường dẫn để import từ thư mục Core
project_root_dir = os.path.dirname(os.path.abspath(__file__))
core_module_dir = os.path.join(project_root_dir, "Core")
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

from Core.main_app import TreeBuilderApp

ASSETS_DIR_NAME = "assets"
DEFAULT_ICON_NAME = "icon.ico"

if os.name == 'nt':
    try:
        import ctypes
        myappid = u'mycompany.texttreebuilder.pyside6.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except (ImportError, AttributeError):
        pass

def main():
    # *** THÊM KHỐI TRY...EXCEPT ĐỂ BẮT LỖI KHỞI TẠO ***
    try:
        app = QApplication(sys.argv)
        font = QFont("Segoe UI", 10)
        app.setFont(font)

        icon_path = os.path.join(project_root_dir, ASSETS_DIR_NAME, DEFAULT_ICON_NAME)
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Application icon not found at '{icon_path}'")

        window = TreeBuilderApp()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        # Hiển thị lỗi ra hộp thoại thay vì thoát trong im lặng
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setText("Đã xảy ra lỗi nghiêm trọng khi khởi động ứng dụng.")
        error_dialog.setInformativeText(f"Lỗi: {e}")
        error_dialog.setDetailedText(traceback.format_exc())
        error_dialog.setWindowTitle("Lỗi khởi động")
        error_dialog.exec()

if __name__ == "__main__":
    main()