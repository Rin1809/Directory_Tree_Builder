# tree_builder_app.py
import sys
import os
import time
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QLineEdit, QPlainTextEdit,
    QProgressBar, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject, QPoint, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QColor

# =============================================================================
# WORKER - Chứa logic xử lý chạy nền
# =============================================================================

class StructureBuilderWorker(QObject):
    """
    Worker chạy trong một thread riêng để phân tích text và tạo cây thư mục,
    tránh làm đơ giao diện chính.
    """
    finished = Signal()
    progress_update = Signal(int, str)  # Gửi tín hiệu (phần trăm, thông điệp)
    error_occurred = Signal(str)

    def __init__(self, tree_text, output_path):
        super().__init__()
        self.tree_text = tree_text
        self.output_path = output_path
        self.is_running = True

    @Slot()
    def run(self):
        try:
            self.progress_update.emit(0, "Bắt đầu phân tích cây thư mục...")
            lines = self.tree_text.strip().split('\n')
            total_lines = len(lines)
            
            # --- Bộ phân tích (Parser) ---
            # Làm sạch các ký tự không hợp lệ trong tên file/thư mục trên Windows/Linux
            def sanitize_name(name):
                # Loại bỏ các comment như (Ko liet ke)
                name = re.sub(r'\(.*\)', '', name).strip()
                # Thay thế các ký tự không hợp lệ bằng gạch dưới
                return re.sub(r'[<>:"/\\|?*]', '_', name)

            # path_stack lưu đường dẫn của các thư mục ở mỗi cấp độ
            # Ví dụ: [ 'C:/output', 'C:/output/src', 'C:/output/src/components' ]
            path_stack = [self.output_path]
            os.makedirs(self.output_path, exist_ok=True)

            for i, line in enumerate(lines):
                if not self.is_running:
                    self.progress_update.emit(i * 100 // total_lines, "Đã dừng bởi người dùng.")
                    break
                
                if not line.strip():
                    continue

                # Xác định cấp độ (level) và tên (name)
                # Regex tìm các ký tự tiền tố của cây thư mục
                match = re.match(r'^(?P<prefix>[│├└─\s]*)(?P<name>.*)', line)
                if not match:
                    self.error_occurred.emit(f"Lỗi cú pháp dòng {i+1}: Không thể phân tích '{line}'")
                    continue
                
                prefix = match.group('prefix')
                name_part = match.group('name').strip()
                
                # Tính toán cấp độ dựa trên độ dài của tiền tố. Giả định mỗi cấp thụt vào 4 ký tự.
                level = len(prefix.replace('├──', '│  ').replace('└──', '   ')) // 4
                
                is_dir = name_part.endswith('/')
                clean_name = sanitize_name(name_part.rstrip('/'))

                if not clean_name:
                    self.error_occurred.emit(f"Cảnh báo: Tên rỗng ở dòng {i+1}, bỏ qua.")
                    continue

                # Đảm bảo path_stack có đủ cấp độ
                while level >= len(path_stack):
                    # Nếu có một bước nhảy cấp độ bất thường, ghi lỗi nhưng vẫn cố gắng xử lý
                    # bằng cách giả định nó là con của thư mục cuối cùng.
                    self.error_occurred.emit(f"Cảnh báo: Cấu trúc thụt lề bất thường ở dòng {i+1}. Cố gắng xử lý.")
                    path_stack.append(path_stack[-1])
                
                # Lấy đường dẫn của thư mục cha
                parent_path = path_stack[level]
                current_path = os.path.join(parent_path, clean_name)
                
                # Cắt ngắn path_stack về đúng cấp độ hiện tại
                path_stack = path_stack[:level + 1]

                # Tạo thư mục hoặc file
                try:
                    if is_dir:
                        os.makedirs(current_path, exist_ok=True)
                        path_stack.append(current_path)
                        self.progress_update.emit((i + 1) * 100 // total_lines, f"Đã tạo thư mục: {clean_name}")
                    else:
                        # Đảm bảo thư mục cha tồn tại trước khi tạo file
                        os.makedirs(os.path.dirname(current_path), exist_ok=True)
                        with open(current_path, 'w', encoding='utf-8') as f:
                            pass # Tạo file rỗng
                        self.progress_update.emit((i + 1) * 100 // total_lines, f"Đã tạo tệp: {clean_name}")
                except PermissionError:
                    self.error_occurred.emit(f"Lỗi quyền truy cập khi tạo: {current_path}")
                except OSError as e:
                    self.error_occurred.emit(f"Lỗi hệ thống khi tạo {current_path}: {e}")
                
                time.sleep(0.01) # Giả lập độ trễ nhỏ để thấy thanh tiến trình chạy

            if self.is_running:
                self.progress_update.emit(100, "Hoàn tất!")

        except Exception as e:
            self.error_occurred.emit(f"Lỗi nghiêm trọng trong quá trình xử lý: {e}")
        finally:
            self.finished.emit()

    def stop(self):
        self.is_running = False

# =============================================================================
# UI - Giao diện chính của ứng dụng
# =============================================================================

class TreeBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.thread = None

        self._setup_window()
        self._create_widgets()
        self._create_layout()
        self._connect_signals()
        self._apply_styles()
        
        # Cho phép kéo và thay đổi kích thước cửa sổ không khung
        self.setMouseTracking(True)
        self._is_dragging = False

    def _setup_window(self):
        self.setWindowTitle("Directory Tree Builder")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(900, 750)
        self.setMinimumSize(700, 600)
        
        # Tải icon
        icon_path = os.path.join("assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _create_widgets(self):
        # Container chính
        self.main_container = QWidget()
        self.main_container.setObjectName("mainContainer")
        self.setCentralWidget(self.main_container)

        # Hình nền
        self.background_label = QLabel(self.main_container)
        bg_path = os.path.join("assets", "background.jpg")
        self.original_pixmap = QPixmap(bg_path)
        if self.original_pixmap.isNull():
            self.background_label.setText("Không tìm thấy hình nền")
            self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Thanh tiêu đề tùy chỉnh
        self.title_bar = QWidget()
        self.title_bar.setObjectName("customTitleBar")
        self.title_bar.setFixedHeight(40)
        
        self.icon_label = QLabel("✧")
        self.title_label = QLabel("Directory Tree Builder")
        self.btn_minimize = QPushButton("–")
        self.btn_maximize = QPushButton("□")
        self.btn_close = QPushButton("✕")

        # Nội dung chính
        self.input_group = QGroupBox("1. Dán cây thư mục vào đây")
        self.tree_input_text = QPlainTextEdit()
        self.tree_input_text.setPlaceholderText("Ví dụ:\nmy_project/\n├── src/\n│   └── main.py\n└── README.md")

        self.output_group = QGroupBox("2. Chọn thư mục đầu ra")
        self.output_path_entry = QLineEdit()
        self.output_path_entry.setPlaceholderText("Chọn một nơi để tạo cây thư mục...")
        self.browse_btn = QPushButton("Duyệt...")

        self.run_btn = QPushButton("🚀 Bắt đầu tạo")
        self.run_btn.setObjectName("runButton")
        self.run_btn.setFixedHeight(45)

        self.log_group = QGroupBox("3. Nhật ký & Kết quả")
        self.log_output_text = QPlainTextEdit()
        self.log_output_text.setReadOnly(True)

        self.status_label = QLabel("Sẵn sàng")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)

    def _create_layout(self):
        # Layout tổng thể
        overall_layout = QVBoxLayout(self.main_container)
        overall_layout.setContentsMargins(0, 0, 0, 0)
        overall_layout.setSpacing(0)

        # Layout thanh tiêu đề
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        title_layout.addWidget(self.icon_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.btn_minimize)
        title_layout.addWidget(self.btn_maximize)
        title_layout.addWidget(self.btn_close)
        
        overall_layout.addWidget(self.title_bar)

        # Layout nội dung chính
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)
        
        # Group nhập liệu
        input_layout = QVBoxLayout(self.input_group)
        input_layout.addWidget(self.tree_input_text)
        content_layout.addWidget(self.input_group, 1) # Cho phép group này co giãn

        # Group đầu ra
        output_layout = QHBoxLayout(self.output_group)
        output_layout.addWidget(self.output_path_entry)
        output_layout.addWidget(self.browse_btn)
        content_layout.addWidget(self.output_group)
        
        # Nút chạy
        content_layout.addWidget(self.run_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Group log
        log_layout = QVBoxLayout(self.log_group)
        log_layout.addWidget(self.log_output_text)
        content_layout.addWidget(self.log_group, 1) # Cho phép group này co giãn

        # Thanh trạng thái
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.progress_bar, 1)
        content_layout.addLayout(status_layout)
        
        overall_layout.addWidget(content_widget)

    def _connect_signals(self):
        self.btn_close.clicked.connect(self.close)
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_maximize.clicked.connect(self._toggle_maximize)

        self.browse_btn.clicked.connect(self._browse_output_directory)
        self.run_btn.clicked.connect(self._start_process)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("□")
        else:
            self.showMaximized()
            self.btn_maximize.setText("")

    @Slot()
    def _browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Chọn thư mục đầu ra")
        if directory:
            self.output_path_entry.setText(os.path.normpath(directory))
            
    @Slot()
    def _start_process(self):
        tree_text = self.tree_input_text.toPlainText()
        output_path = self.output_path_entry.text()

        if not tree_text.strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng dán cây thư mục vào ô nhập liệu.")
            return
        if not output_path:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn thư mục đầu ra.")
            return

        self.run_btn.setEnabled(False)
        self.log_output_text.clear()
        self.progress_bar.setValue(0)
        
        self.thread = QThread()
        self.worker = StructureBuilderWorker(tree_text, output_path)
        self.worker.moveToThread(self.thread)

        # Kết nối signals từ worker đến slots của UI
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.error_occurred.connect(self.log_message)
        self.worker.finished.connect(lambda: self.run_btn.setEnabled(True))

        self.thread.start()

    @Slot(int, str)
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.log_message(f"[{value}%] {message}")

    @Slot(str)
    def log_message(self, message):
        self.log_output_text.appendPlainText(message)

    def _apply_styles(self):
        # Định nghĩa màu sắc theo theme của dự án mẫu
        WINDOW_BG_COLOR = "rgb(10, 12, 28)"
        CONTAINER_BG_COLOR = "rgba(20, 25, 50, 0.92)"
        TITLE_BAR_BG_COLOR = "rgba(15, 18, 35, 0.95)"
        PRIMARY_COLOR = "rgb(65, 75, 115)"
        ACCENT_COLOR = "rgb(130, 170, 255)"
        HOVER_COLOR = "rgb(85, 100, 145)"
        TEXT_COLOR = "rgb(225, 230, 245)"
        SUBTEXT_COLOR = "rgb(155, 160, 180)"
        INPUT_BG_COLOR = "rgba(12, 15, 32, 0.9)"
        INPUT_BORDER_COLOR = "rgba(140, 150, 190, 0.5)"
        INPUT_FOCUS_BORDER_COLOR = "rgb(160, 190, 255)"
        SUCCESS_COLOR = "rgb(80, 180, 120)"
        ERROR_COLOR = "rgb(220, 90, 100)"
        
        qss = f"""
            QMainWindow {{ background: transparent; }}
            QWidget#mainContainer {{
                background-color: {WINDOW_BG_COLOR};
                border-radius: 12px;
            }}
            /* Thanh tiêu đề */
            QWidget#customTitleBar {{
                background-color: {TITLE_BAR_BG_COLOR};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid rgba(200, 205, 220, 0.1);
            }}
            QWidget#customTitleBar QLabel {{ color: {TEXT_COLOR}; font-size: 11pt; font-weight: bold; }}
            QWidget#customTitleBar QLabel#icon_label {{ color: {ACCENT_COLOR}; font-size: 14pt; padding-bottom: 3px; }}
            QWidget#customTitleBar QPushButton {{
                background-color: transparent; border: none; border-radius: 8px;
                color: {SUBTEXT_COLOR}; font-family: "Segoe Fluent Icons", "Segoe MDL2 Assets"; font-size: 10pt;
                min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px;
            }}
            QWidget#customTitleBar QPushButton:hover {{ background-color: {HOVER_COLOR}; color: white; }}
            QWidget#customTitleBar QPushButton#btn_close:hover {{ background-color: {ERROR_COLOR}; color: white; }}

            /* Nội dung chung */
            QGroupBox {{
                background-color: rgba(25,30,55,0.6); border: 1px solid {INPUT_BORDER_COLOR};
                border-radius: 9px; margin-top: 12px; padding: 15px; font-weight: bold;
                color: {ACCENT_COLOR};
            }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; margin-left: 10px; }}
            
            QLineEdit, QPlainTextEdit {{
                background-color: {INPUT_BG_COLOR}; border: 1px solid {INPUT_BORDER_COLOR};
                border-radius: 8px; padding: 10px; color: {TEXT_COLOR}; font-size: 10pt;
            }}
            QLineEdit:focus, QPlainTextEdit:focus {{ border: 1.5px solid {INPUT_FOCUS_BORDER_COLOR}; }}
            
            QPushButton {{
                background-color: {PRIMARY_COLOR}; border: none; border-radius: 8px;
                padding: 10px 18px; font-weight: bold; color: {TEXT_COLOR};
            }}
            QPushButton:hover {{ background-color: {HOVER_COLOR}; }}
            QPushButton:disabled {{ background-color: #555; color: #888; }}
            
            QPushButton#runButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {SUCCESS_COLOR}, stop:1 {QColor(SUCCESS_COLOR).lighter(130).name()});
                font-size: 12pt; color: white;
            }}
            QPushButton#runButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {QColor(SUCCESS_COLOR).lighter(110).name()}, stop:1 {QColor(SUCCESS_COLOR).lighter(140).name()});
            }}
            
            /* Thanh trạng thái */
            QLabel {{ color: {SUBTEXT_COLOR}; font-size: 9pt; }}
            QProgressBar {{
                border: 1px solid {INPUT_BORDER_COLOR}; border-radius: 7px; text-align: center;
                background-color: {INPUT_BG_COLOR}; height: 12px;
            }}
            QProgressBar::chunk {{
                background-color: {SUCCESS_COLOR}; border-radius: 6px; margin: 1px;
            }}
            
            /* Thanh cuộn */
            QScrollBar:vertical {{
                border: none; background: rgba(0,0,0,0.2); width: 12px;
                margin: 15px 0 15px 0; border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {PRIMARY_COLOR}; min-height: 30px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {HOVER_COLOR}; }}
        """
        self.setStyleSheet(qss)

    # --- Các hàm xử lý sự kiện cho cửa sổ không khung ---
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.original_pixmap.isNull():
            scaled_pixmap = self.original_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.background_label.setPixmap(scaled_pixmap)
            self.background_label.setGeometry(self.rect())
        self.background_label.lower()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.title_bar.geometry().contains(event.position().toPoint()):
                self._is_dragging = True
                self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._is_dragging:
            self.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        event.accept()
        
    def closeEvent(self, event):
        # Đảm bảo worker dừng lại khi đóng cửa sổ
        if self.thread and self.thread.isRunning():
            reply = QMessageBox.question(self, "Xác nhận thoát", 
                                         "Một tiến trình đang chạy. Bạn có chắc muốn thoát?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.thread.quit()
                self.thread.wait() # Chờ thread kết thúc hẳn
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # Đặt App ID cho Windows để icon hiển thị đúng trên taskbar
    if os.name == 'nt':
        import ctypes
        myappid = u'mycompany.treebuilder.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
    app = QApplication(sys.argv)
    
    # Set font chung
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    window = TreeBuilderApp()
    window.show()
    
    # Thêm hiệu ứng mờ dần khi mở
    anim = QPropertyAnimation(window, b"windowOpacity")
    anim.setDuration(400)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    anim.start()
    
    sys.exit(app.exec())