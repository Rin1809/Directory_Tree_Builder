# Core/translations.py
class Translations:
    LANG_VI = "vi"
    LANG_EN = "en"
    LANG_JA = "ja"

    lang_map = {
        LANG_VI: "Tiếng Việt",
        LANG_EN: "English",
        LANG_JA: "日本語"
    }
    
    current_lang = LANG_VI

    translations = {
        # Tiêu đề & Cửa sổ
        "app_title": {"vi": "Trình tạo cây thư mục", "en": "Directory Tree Builder", "ja": "ディレクトリツリービルダー"},
        "background_not_found": {"vi": "Không tìm thấy hình nền", "en": "Background not found", "ja": "背景が見つかりません"},
        "confirm_exit_title": {"vi": "Xác nhận thoát", "en": "Confirm Exit", "ja": "終了の確認"},
        "confirm_exit_text": {"vi": "Một tiến trình đang chạy. Bạn có chắc muốn thoát?", "en": "A process is running. Are you sure you want to exit?", "ja": "プロセスが実行中です。本当に終了しますか？"},
        
        # Nhóm UI
        "input_group_title": {"vi": "1. Dán cây thư mục vào đây", "en": "1. Paste Directory Tree Here", "ja": "1. ディレクトリツリーをここに貼り付け"},
        "input_placeholder": {"vi": "Ví dụ:\nmy_project/\n├── src/\n│   └── main.py\n└── README.md", "en": "Example:\nmy_project/\n├── src/\n│   └── main.py\n└── README.md", "ja": "例:\nmy_project/\n├── src/\n│   └── main.py\n└── README.md"},
        "output_group_title": {"vi": "2. Chọn thư mục đầu ra", "en": "2. Select Output Directory", "ja": "2. 出力ディレクトリを選択"},
        "output_placeholder": {"vi": "Chọn một nơi để tạo cây thư mục...", "en": "Choose a place to create the tree...", "ja": "ツリーを作成する場所を選択..."},
        "log_group_title": {"vi": "3. Nhật ký & Kết quả", "en": "3. Log & Results", "ja": "3. ログと結果"},
        
        # Nút
        "browse_button": {"vi": "Duyệt...", "en": "Browse...", "ja": "参照..."},
        "run_button": {"vi": "Bắt đầu tạo", "en": "Start Building", "ja": "作成開始"},
        
        # Trạng thái
        "status_ready": {"vi": "Sẵn sàng", "en": "Ready", "ja": "準備完了"},
        "status_done": {"vi": "Hoàn tất!", "en": "Done!", "ja": "完了！"},
        
        # Thông báo lỗi & Cảnh báo
        "warn_missing_input": {"vi": "Thiếu thông tin", "en": "Missing Information", "ja": "情報不足"},
        "warn_paste_tree": {"vi": "Vui lòng dán cây thư mục vào ô nhập liệu.", "en": "Please paste the directory tree into the input box.", "ja": "入力ボックスにディレクトリツリーを貼り付けてください。"},
        "warn_select_output": {"vi": "Vui lòng chọn thư mục đầu ra.", "en": "Please select an output directory.", "ja": "出力ディレクトリを選択してください。"},
        "err_syntax": {"vi": "Lỗi cú pháp dòng {line_num}: Không thể phân tích '{line_content}'", "en": "Syntax error on line {line_num}: Cannot parse '{line_content}'", "ja": "行 {line_num} の構文エラー: '{line_content}' を解析できません"},
        "warn_indent": {"vi": "Cảnh báo: Cấu trúc thụt lề bất thường ở dòng {line_num}. Đang cố gắng xử lý.", "en": "Warning: Unusual indentation structure at line {line_num}. Attempting to process.", "ja": "警告: 行 {line_num} のインデント構造が異常です。処理を試みます。"},
        "err_permission": {"vi": "Lỗi quyền truy cập khi tạo: {path}", "en": "Permission error while creating: {path}", "ja": "作成中の権限エラー: {path}"},
        "err_os": {"vi": "Lỗi hệ thống khi tạo {path}: {error}", "en": "System error creating {path}: {error}", "ja": "{path} の作成中にシステムエラー: {error}"},
        "err_critical": {"vi": "Lỗi nghiêm trọng trong quá trình xử lý: {error}", "en": "Critical error during processing: {error}", "ja": "処理中に重大なエラー: {error}"},

        # Log
        "log_start_analysis": {"vi": "Bắt đầu phân tích cây thư mục...", "en": "Starting directory tree analysis...", "ja": "ディレクトリツリーの解析を開始..."},
        "log_stopped_by_user": {"vi": "Đã dừng bởi người dùng.", "en": "Stopped by user.", "ja": "ユーザーによって停止されました。"},
        "log_folder_created": {"vi": "Đã tạo thư mục: {name}", "en": "Created directory: {name}", "ja": "ディレクトリを作成しました: {name}"},
        "log_file_created": {"vi": "Đã tạo tệp: {name}", "en": "Created file: {name}", "ja": "ファイルを作成しました: {name}"},
    }

    @classmethod
    def set_language(cls, lang_code):
        if lang_code in cls.lang_map:
            cls.current_lang = lang_code

    @classmethod
    def get(cls, key, **kwargs):
        try:
            entry = cls.translations.get(key, {})
            raw_text = entry.get(cls.current_lang, entry.get(cls.LANG_EN, key.upper()))
            return raw_text.format(**kwargs) if kwargs else raw_text
        except KeyError:
            return key.upper()