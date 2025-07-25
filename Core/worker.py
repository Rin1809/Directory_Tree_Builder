# Core/worker.py
import os
import re
import time
from PySide6.QtCore import QObject, Signal, Slot

class StructureBuilderWorker(QObject):
    finished = Signal()
    progress_update = Signal(int, str)
    error_occurred = Signal(str)

    def __init__(self, tree_text, output_path, translations):
        super().__init__()
        self.tree_text = tree_text
        self.output_path = output_path
        self.is_running = True
        self.translations = translations

    @Slot()
    def run(self):
        try:
            self.progress_update.emit(0, self.translations.get("log_start_analysis"))
            lines = self.tree_text.strip().split('\n')
            total_lines = len(lines)
            
            def sanitize_name(name):
                name_no_hash = name.split('#', 1)[0]
                name_no_paren = re.sub(r'\(.*\)', '', name_no_hash)
                clean_name = name_no_paren.strip()
                # Biểu thức này vẫn đúng, nó dùng để làm sạch tên sau khi đã loại bỏ các dấu hiệu
                return re.sub(r'[<>:"/\\|?*]', '_', clean_name)

            path_stack = [self.output_path]
            os.makedirs(self.output_path, exist_ok=True)

            for i, line in enumerate(lines):
                if not self.is_running:
                    self.progress_update.emit(i * 100 // total_lines, self.translations.get("log_stopped_by_user"))
                    break
                
                if not line.strip():
                    continue

                match = re.match(r'^(?P<prefix>[│├└─\s]*)(?P<name>.*)', line)
                if not match:
                    self.error_occurred.emit(self.translations.get("err_syntax", line_num=i+1, line_content=line))
                    continue
                
                prefix = match.group('prefix')
                name_part = match.group('name').strip()
                
                level = len(prefix.replace('├──', '│  ').replace('└──', '   ')) // 4

                # 1. Kiểm tra xem có phải là thư mục hay không DỰA TRÊN CHUỖI GỐC.
                is_dir = name_part.rstrip().endswith('/')
                
                # 2. Lấy tên cần làm sạch: nếu là thư mục, loại bỏ dấu '/' ở cuối.
                name_to_clean = name_part.rstrip('/') if is_dir else name_part
                
                # 3. Gửi tên đã được xử lý (không còn dấu '/') vào hàm làm sạch.
                clean_name = sanitize_name(name_to_clean)
                
                if not clean_name:
                    continue

                while level >= len(path_stack):
                    self.error_occurred.emit(self.translations.get("warn_indent", line_num=i + 1))
                    path_stack.append(path_stack[-1])
                
                parent_path = path_stack[level]
                current_path = os.path.join(parent_path, clean_name)
                path_stack = path_stack[:level + 1]

                try:
                    if is_dir:
                        os.makedirs(current_path, exist_ok=True)
                        path_stack.append(current_path)
                        self.progress_update.emit((i + 1) * 100 // total_lines, self.translations.get("log_folder_created", name=clean_name))
                    else:
                        os.makedirs(os.path.dirname(current_path), exist_ok=True)
                        with open(current_path, 'w', encoding='utf-8') as f:
                            pass
                        self.progress_update.emit((i + 1) * 100 // total_lines, self.translations.get("log_file_created", name=clean_name))
                except PermissionError:
                    self.error_occurred.emit(self.translations.get("err_permission", path=current_path))
                except OSError as e:
                    self.error_occurred.emit(self.translations.get("err_os", path=current_path, error=e))
                
                time.sleep(0.01)

            if self.is_running:
                self.progress_update.emit(100, self.translations.get("status_done"))

        except Exception as e:
            self.error_occurred.emit(self.translations.get("err_critical", error=e))
        finally:
            self.finished.emit()

    def stop(self):
        self.is_running = False