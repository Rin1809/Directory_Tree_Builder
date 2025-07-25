# Core/main_app.py
import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QLineEdit, QPlainTextEdit, QProgressBar,
    QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QPoint, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont

from .worker import StructureBuilderWorker
from .translations import Translations

ASSETS_DIR_NAME = "assets"

class TreeBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.thread = None
        
        # Thêm thuộc tính để lưu animation
        self.anim_open = None

        Translations.set_language(Translations.LANG_VI)

        self._setup_window()
        self._create_widgets()
        self._create_layout()
        self._connect_signals()
        
        self.retranslate_ui()
        self._apply_styles()
        
        self.setMouseTracking(True)
        self._is_dragging = False

    def _setup_window(self):
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(900, 750)
        self.setMinimumSize(700, 600)
        # Đặt độ trong suốt ban đầu để chuẩn bị cho animation
        self.setWindowOpacity(0.0)

    def _create_widgets(self):
        self.main_container = QWidget()
        self.main_container.setObjectName("mainContainer")
        self.setCentralWidget(self.main_container)

        self.background_label = QLabel(self.main_container)
        bg_path = os.path.join(ASSETS_DIR_NAME, "background.jpg")
        self.original_pixmap = QPixmap(bg_path)
        if self.original_pixmap.isNull():
            self.background_label.setText(Translations.get("background_not_found"))
            self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_bar = QWidget()
        self.title_bar.setObjectName("customTitleBar")
        self.title_bar.setFixedHeight(40)
        
        self.icon_label = QLabel("✧")
        self.title_label = QLabel()
        self.lang_combo = QComboBox()
        self.btn_minimize = QPushButton("–")
        self.btn_maximize = QPushButton("□")
        self.btn_close = QPushButton("❌")

        self.input_group = QGroupBox()
        self.tree_input_text = QPlainTextEdit()
        self.output_group = QGroupBox()
        self.output_path_entry = QLineEdit()
        self.browse_btn = QPushButton()
        self.run_btn = QPushButton()
        self.run_btn.setObjectName("runButton")
        self.run_btn.setFixedHeight(45)
        self.log_group = QGroupBox()
        self.log_output_text = QPlainTextEdit()
        self.log_output_text.setReadOnly(True)
        self.status_label = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)

    def _create_layout(self):
        overall_layout = QVBoxLayout(self.main_container)
        overall_layout.setContentsMargins(0, 0, 0, 0)
        overall_layout.setSpacing(0)

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        title_layout.setSpacing(10)
        title_layout.addWidget(self.icon_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.lang_combo)
        title_layout.addWidget(self.btn_minimize)
        title_layout.addWidget(self.btn_maximize)
        title_layout.addWidget(self.btn_close)
        overall_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)
        
        input_layout = QVBoxLayout(self.input_group)
        input_layout.addWidget(self.tree_input_text)
        content_layout.addWidget(self.input_group, 1)

        output_layout = QHBoxLayout(self.output_group)
        output_layout.addWidget(self.output_path_entry)
        output_layout.addWidget(self.browse_btn)
        content_layout.addWidget(self.output_group)
        
        content_layout.addWidget(self.run_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        log_layout = QVBoxLayout(self.log_group)
        log_layout.addWidget(self.log_output_text)
        content_layout.addWidget(self.log_group, 1)

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
        self.lang_combo.currentIndexChanged.connect(self._on_language_change)
    
    def retranslate_ui(self):
        self.setWindowTitle(Translations.get("app_title"))
        self.title_label.setText(Translations.get("app_title"))
        self.input_group.setTitle(Translations.get("input_group_title"))
        self.tree_input_text.setPlaceholderText(Translations.get("input_placeholder"))
        self.output_group.setTitle(Translations.get("output_group_title"))
        self.output_path_entry.setPlaceholderText(Translations.get("output_placeholder"))
        self.browse_btn.setText(Translations.get("browse_button"))
        self.run_btn.setText(Translations.get("run_button"))
        self.log_group.setTitle(Translations.get("log_group_title"))
        self.status_label.setText(Translations.get("status_ready"))

        self.lang_combo.blockSignals(True)
        self.lang_combo.clear()
        for code, name in Translations.lang_map.items():
            self.lang_combo.addItem(name, code)
        current_index = self.lang_combo.findData(Translations.current_lang)
        if current_index != -1:
            self.lang_combo.setCurrentIndex(current_index)
        self.lang_combo.blockSignals(False)
    
    def _apply_styles(self):
        font_family = "Meiryo, Segoe UI, Arial" if Translations.current_lang == Translations.LANG_JA else "Segoe UI, Arial"
        self.setStyleSheet(f"""
            * {{ font-family: "{font_family}"; }}
            QMainWindow {{ background: transparent; }}
            QWidget#mainContainer {{ background-color: rgb(10, 12, 28); border-radius: 12px; }}
            QGroupBox {{
                background-color: rgba(25,30,55,0.6); border: 1px solid rgba(140, 150, 190, 0.5);
                border-radius: 9px; margin-top: 12px; padding: 15px; font-weight: bold;
                color: rgb(130, 170, 255);
            }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; margin-left: 10px; }}
            QLabel {{ color: rgb(155, 160, 180); font-size: 9pt; }}
            QWidget#customTitleBar {{
                background-color: rgba(15, 18, 35, 0.95);
                border-top-left-radius: 12px; border-top-right-radius: 12px;
                border-bottom: 1px solid rgba(200, 205, 220, 0.1);
            }}
            QWidget#customTitleBar QLabel {{ color: rgb(225, 230, 245); font-size: 11pt; font-weight: bold; }}
            QWidget#customTitleBar > QLabel:first-child {{ color: rgb(130, 170, 255); font-size: 14pt; padding-bottom: 3px; }}
            QWidget#customTitleBar QPushButton {{
                background-color: transparent; border: none; border-radius: 8px;
                color: rgb(155, 160, 180); font-family: "Segoe Fluent Icons", "Segoe MDL2 Assets"; font-size: 10pt;
                min-width: 36px; max-width: 36px; min-height: 30px; max-height: 30px;
            }}
            QWidget#customTitleBar QPushButton:hover {{ background-color: rgb(85, 100, 145); color: white; }}
            QWidget#customTitleBar QPushButton#btn_close:hover {{ background-color: rgb(220, 90, 100); color: white; }}
            QComboBox {{
                background-color: rgba(12, 15, 32, 0.9); color: rgb(225, 230, 245);
                border: 1px solid rgba(140, 150, 190, 0.5); border-radius: 7px;
                padding: 4px 8px; min-width: 100px;
            }}
            QComboBox:hover {{ border-color: rgb(130, 170, 255); }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: rgb(25, 30, 55); border: 1px solid rgb(130, 170, 255);
                selection-background-color: rgb(130, 170, 255); selection-color: black;
            }}
            QLineEdit, QPlainTextEdit {{
                background-color: rgba(12, 15, 32, 0.9); border: 1px solid rgba(140, 150, 190, 0.5);
                border-radius: 8px; padding: 10px; color: rgb(225, 230, 245); font-size: 10pt;
            }}
            QLineEdit:focus, QPlainTextEdit:focus {{ border: 1.5px solid rgb(160, 190, 255); }}
            QPushButton {{
                background-color: rgb(65, 75, 115); border: none; border-radius: 8px;
                padding: 10px 18px; font-weight: bold; color: rgb(225, 230, 245);
            }}
            QPushButton:hover {{ background-color: rgb(85, 100, 145); }}
            QPushButton:disabled {{ background-color: #555; color: #888; }}
            QPushButton#runButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb(60, 110, 220), stop:1 rgb(130, 170, 255));
                font-size: 12pt; color: white;
            }}
            QPushButton#runButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb(80, 130, 240), stop:1 rgb(150, 190, 255));
            }}
            QProgressBar {{
                border: 1px solid rgba(140, 150, 190, 0.5); border-radius: 7px;
                background-color: rgba(12, 15, 32, 0.9); height: 12px;
            }}
            QProgressBar::chunk {{
                background-color: rgb(80, 180, 120); border-radius: 6px; margin: 1px;
            }}
            QScrollBar:vertical {{
                border: none; background: rgba(0,0,0,0.2); width: 12px;
                margin: 15px 0 15px 0; border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: rgb(65, 75, 115); min-height: 30px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{ background: rgb(85, 100, 145); }}
        """)
        self.update()

    @Slot(int)
    def _on_language_change(self, index):
        lang_code = self.lang_combo.itemData(index)
        if lang_code and lang_code != Translations.current_lang:
            Translations.set_language(lang_code)
            self.retranslate_ui()
            self._apply_styles()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self.btn_maximize.setText("" if self.isMaximized() else "□")

    @Slot()
    def _browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, Translations.get("output_group_title"))
        if directory:
            self.output_path_entry.setText(os.path.normpath(directory))
            
    @Slot()
    def _start_process(self):
        tree_text = self.tree_input_text.toPlainText()
        output_path = self.output_path_entry.text()
        if not tree_text.strip():
            QMessageBox.warning(self, Translations.get("warn_missing_input"), Translations.get("warn_paste_tree"))
            return
        if not output_path:
            QMessageBox.warning(self, Translations.get("warn_missing_input"), Translations.get("warn_select_output"))
            return
        self.run_btn.setEnabled(False)
        self.log_output_text.clear()
        self.progress_bar.setValue(0)
        self.thread = QThread()
        self.worker = StructureBuilderWorker(tree_text, output_path, Translations)
        self.worker.moveToThread(self.thread)
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

    #  HÀM SHOW
    def show(self):
        # Hiển thị cửa sổ trước khi bắt đầu animation
        super().show() 
        
        # Tạo và lưu trữ animation trong self.anim_open
        self.anim_open = QPropertyAnimation(self, b"windowOpacity")
        self.anim_open.setDuration(400)
        # Bắt đầu từ độ trong suốt hiện tại (0.0) và kết thúc ở 1.0 (hoàn toàn rõ)
        self.anim_open.setStartValue(self.windowOpacity()) 
        self.anim_open.setEndValue(1.0)
        self.anim_open.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim_open.start()

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
        if self.thread and self.thread.isRunning():
            reply = QMessageBox.question(self, Translations.get("confirm_exit_title"), 
                                         Translations.get("confirm_exit_text"),
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.thread.quit()
                self.thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()