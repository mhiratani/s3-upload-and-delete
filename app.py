"""
S3 Upload and Delete Application
"""

import os
import threading
from typing import List, Optional, Tuple, Dict, Any
from configparser import ConfigParser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import boto3
from botocore.exceptions import ClientError


# ===== 定数定義 =====
class AppConstants:
    """アプリケーション全体で使用する定数"""
    COLOR_BG_DARK = "#2b2b2b"
    COLOR_BG_LIGHT = "#f5f5f5"
    COLOR_FG_DARK = "#333333"
    COLOR_FG_LIGHT = "#666666"
    COLOR_BORDER = "#cccccc"
    COLOR_HOVER = "#e0e0e0"
    COLOR_WHITE = "#ffffff"
    
    # フォント設定
    FONT_TITLE = ("Segoe UI", 16, "bold")
    FONT_LARGE = ("Segoe UI", 12)
    FONT_NORMAL = ("Segoe UI", 10)
    FONT_SMALL = ("Segoe UI", 9)
    
    # サイズ設定
    WINDOW_WIDTH = 700
    WINDOW_HEIGHT = 600
    PADDING_LARGE = 20
    PADDING_MEDIUM = 10
    PADDING_SMALL = 5
    
    # S3設定
    MAX_KEYS_PER_PAGE = 25
    DELETE_BATCH_SIZE = 100


# ===== S3マネージャークラス =====
class S3Manager:
    """S3操作を管理するクラス"""
    
    def __init__(self, access_key: str, secret_key: str):
        """
        S3マネージャーの初期化
        
        Args:
            access_key: AWS アクセスキー
            secret_key: AWS シークレットキー
        """
        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        self.s3_client = self.session.client('s3')
    
    def list_buckets(self) -> List[str]:
        """S3バケットのリストを取得"""
        try:
            response = self.s3_client.list_buckets()
            return [bucket["Name"] for bucket in response.get("Buckets", [])]
        except ClientError as e:
            raise Exception(f"バケットリストの取得に失敗: {str(e)}")
    
    def list_objects(
        self, 
        bucket: str, 
        prefix: str = "", 
        max_keys: int = 25,
        continuation_token: Optional[str] = None
    ) -> Tuple[List[str], Optional[str]]:
        """
        S3オブジェクトのリストを取得
        
        Args:
            bucket: バケット名
            prefix: プレフィックス
            max_keys: 最大取得数
            continuation_token: 継続トークン
            
        Returns:
            (オブジェクトキーのリスト, 次の継続トークン)
        """
        try:
            params = {
                'Bucket': bucket,
                'Prefix': prefix,
                'MaxKeys': max_keys
            }
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            
            response = self.s3_client.list_objects_v2(**params)
            objects = [obj['Key'] for obj in response.get('Contents', [])]
            next_token = response.get('NextContinuationToken')
            
            return objects, next_token
        except ClientError as e:
            raise Exception(f"オブジェクトリストの取得に失敗: {str(e)}")
    
    def upload_file(self, file_path: str, bucket: str, s3_key: str) -> None:
        """ファイルをS3にアップロード"""
        try:
            self.s3_client.upload_file(file_path, bucket, s3_key)
        except ClientError as e:
            raise Exception(f"アップロード失敗 ({s3_key}): {str(e)}")
    
    def delete_objects(self, bucket: str, keys: List[str]) -> Dict[str, Any]:
        """複数のオブジェクトを削除"""
        try:
            delete_keys = [{'Key': key} for key in keys]
            response = self.s3_client.delete_objects(
                Bucket=bucket,
                Delete={'Objects': delete_keys}
            )
            return response
        except ClientError as e:
            raise Exception(f"削除失敗: {str(e)}")


# ===== AWS認証情報マネージャー =====
class AWSCredentialsManager:
    """AWS認証情報を管理するクラス"""
    
    @staticmethod
    def load_profiles() -> List[str]:
        """AWS CLIのプロファイルリストを取得"""
        credentials_path = os.path.join(os.path.expanduser('~'), '.aws', 'credentials')
        profiles = []
        
        if os.path.exists(credentials_path):
            with open(credentials_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        profiles.append(line[1:-1])
        
        return profiles
    
    @staticmethod
    def get_credentials(profile: str) -> Tuple[str, str]:
        """指定されたプロファイルの認証情報を取得"""
        credentials_path = os.path.join(os.path.expanduser('~'), '.aws', 'credentials')
        config = ConfigParser()
        config.read(credentials_path, encoding='utf-8')
        
        if profile in config:
            access_key = config[profile].get('aws_access_key_id', '')
            secret_key = config[profile].get('aws_secret_access_key', '')
            return access_key, secret_key
        
        return '', ''


# ===== UIコンポーネント =====
class StyledFrame(ttk.Frame):
    """スタイル付きフレーム"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(relief="flat", borderwidth=1)


class HoverButton(ttk.Button):
    """ホバー効果付きボタン"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        self.configure(cursor="hand2")
    
    def _on_leave(self, event):
        self.configure(cursor="")


# ===== メインアプリケーションクラス =====
class S3UploadAndDeleteApp:
    """S3ファイル管理アプリケーションのメインクラス"""
    
    def __init__(self, root: tk.Tk):
        """
        アプリケーションの初期化
        
        Args:
            root: Tkinterのルートウィンドウ
        """
        self.root = root
        self.s3_manager: Optional[S3Manager] = None
        self.credentials_manager = AWSCredentialsManager()
        
        self._setup_window()
        self._setup_styles()
        self._show_login_screen()
    
    def _setup_window(self) -> None:
        """メインウィンドウの初期設定"""
        self.root.title("S3 Manager - Upload & Delete")
        self.root.geometry(f"{AppConstants.WINDOW_WIDTH}x{AppConstants.WINDOW_HEIGHT}")
        self.root.configure(bg=AppConstants.COLOR_BG_LIGHT)
        
        # ウィンドウを中央に配置
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (AppConstants.WINDOW_WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (AppConstants.WINDOW_HEIGHT // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def _setup_styles(self) -> None:
        """ttk スタイルの設定"""
        style = ttk.Style()
        
        # フレームスタイル
        style.configure(
            "Card.TFrame",
            background=AppConstants.COLOR_WHITE,
            relief="flat",
            borderwidth=1
        )
        
        # ラベルスタイル
        style.configure(
            "Title.TLabel",
            font=AppConstants.FONT_TITLE,
            background=AppConstants.COLOR_WHITE,
            foreground=AppConstants.COLOR_FG_DARK
        )
        
        style.configure(
            "Subtitle.TLabel",
            font=AppConstants.FONT_LARGE,
            background=AppConstants.COLOR_WHITE,
            foreground=AppConstants.COLOR_FG_LIGHT
        )
        
        # ボタンスタイル
        style.configure(
            "Primary.TButton",
            font=AppConstants.FONT_LARGE,
            padding=(20, 10)
        )
        
        style.configure(
            "Secondary.TButton",
            font=AppConstants.FONT_NORMAL,
            padding=(15, 8)
        )
    
    # ===== ログイン画面 =====
    
    def _show_login_screen(self) -> None:
        """ログイン画面を表示"""
        self.login_frame = ttk.Frame(self.root)
        self.login_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # カードコンテナ
        card = ttk.Frame(self.login_frame, style="Card.TFrame", relief="solid", borderwidth=1)
        card.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_frame = ttk.Frame(card, style="Card.TFrame")
        title_frame.pack(fill=tk.X, padx=30, pady=(30, 20))
        
        ttk.Label(
            title_frame,
            text="🔐 AWS S3 Manager",
            style="Title.TLabel"
        ).pack()
        
        ttk.Label(
            title_frame,
            text="認証情報を入力してログイン",
            style="Subtitle.TLabel"
        ).pack(pady=(5, 0))
        
        # フォーム
        form_frame = ttk.Frame(card, style="Card.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # プロファイル選択
        ttk.Label(
            form_frame,
            text="AWS Profile",
            font=AppConstants.FONT_NORMAL,
            background=AppConstants.COLOR_WHITE
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.profile_var = tk.StringVar()
        profiles = self.credentials_manager.load_profiles()
        
        self.profile_combo = ttk.Combobox(
            form_frame,
            textvariable=self.profile_var,
            values=profiles,
            font=AppConstants.FONT_NORMAL,
            width=40,
            state="readonly"
        )
        self.profile_combo.grid(row=1, column=0, pady=(0, 15), sticky="ew")
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
        
        # アクセスキー
        ttk.Label(
            form_frame,
            text="Access Key",
            font=AppConstants.FONT_NORMAL,
            background=AppConstants.COLOR_WHITE
        ).grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        self.access_key_entry = ttk.Entry(
            form_frame,
            font=AppConstants.FONT_NORMAL,
            width=40
        )
        self.access_key_entry.grid(row=3, column=0, pady=(0, 15), sticky="ew")
        
        # シークレットキー
        ttk.Label(
            form_frame,
            text="Secret Key",
            font=AppConstants.FONT_NORMAL,
            background=AppConstants.COLOR_WHITE
        ).grid(row=4, column=0, sticky="w", pady=(0, 5))
        
        self.secret_key_entry = ttk.Entry(
            form_frame,
            font=AppConstants.FONT_NORMAL,
            width=40,
            show="●"
        )
        self.secret_key_entry.grid(row=5, column=0, pady=(0, 25), sticky="ew")
        
        # ログインボタン
        login_btn = HoverButton(
            form_frame,
            text="ログイン",
            command=self._handle_login,
            style="Primary.TButton"
        )
        login_btn.grid(row=6, column=0, pady=(0, 20))
        
        # 初期プロファイル選択
        if profiles:
            self.profile_combo.current(0)
            self._on_profile_selected()
    
    def _on_profile_selected(self, event=None) -> None:
        """プロファイル選択時の処理"""
        profile = self.profile_var.get()
        access_key, secret_key = self.credentials_manager.get_credentials(profile)
        
        self.access_key_entry.delete(0, tk.END)
        self.access_key_entry.insert(0, access_key)
        
        self.secret_key_entry.delete(0, tk.END)
        self.secret_key_entry.insert(0, secret_key)
    
    def _handle_login(self) -> None:
        """ログイン処理"""
        access_key = self.access_key_entry.get().strip()
        secret_key = self.secret_key_entry.get().strip()
        
        if not access_key or not secret_key:
            messagebox.showerror("エラー", "アクセスキーとシークレットキーを入力してください")
            return
        
        try:
            self.s3_manager = S3Manager(access_key, secret_key)
            # 接続テスト
            self.s3_manager.list_buckets()
            
            self.login_frame.destroy()
            self._show_main_screen()
        except Exception as e:
            messagebox.showerror("認証エラー", f"ログインに失敗しました:\n{str(e)}")
    
    # ===== メイン画面 =====
    
    def _show_main_screen(self) -> None:
        """メイン画面を表示"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # カードコンテナ
        card = ttk.Frame(self.main_frame, style="Card.TFrame", relief="solid", borderwidth=1)
        card.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_frame = ttk.Frame(card, style="Card.TFrame")
        title_frame.pack(fill=tk.X, padx=30, pady=(30, 20))
        
        ttk.Label(
            title_frame,
            text="📦 S3 Bucket Manager",
            style="Title.TLabel"
        ).pack()
        
        # フォーム
        form_frame = ttk.Frame(card, style="Card.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # バケット選択
        ttk.Label(
            form_frame,
            text="S3 Bucket",
            font=AppConstants.FONT_NORMAL,
            background=AppConstants.COLOR_WHITE
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.bucket_var = tk.StringVar()
        bucket_names = self.s3_manager.list_buckets()
        
        self.bucket_combo = ttk.Combobox(
            form_frame,
            textvariable=self.bucket_var,
            values=bucket_names,
            font=AppConstants.FONT_NORMAL,
            width=50,
            state="readonly"
        )
        self.bucket_combo.grid(row=1, column=0, pady=(0, 20), sticky="ew")
        
        # プレフィックス
        ttk.Label(
            form_frame,
            text="S3 Prefix (オプション)",
            font=AppConstants.FONT_NORMAL,
            background=AppConstants.COLOR_WHITE
        ).grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        self.prefix_var = tk.StringVar()
        self.prefix_entry = ttk.Entry(
            form_frame,
            textvariable=self.prefix_var,
            font=AppConstants.FONT_NORMAL,
            width=50
        )
        self.prefix_entry.grid(row=3, column=0, pady=(0, 30), sticky="ew")
        
        # ボタンフレーム
        button_frame = ttk.Frame(card, style="Card.TFrame")
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        self.upload_btn = HoverButton(
            button_frame,
            text="📤 ファイルをアップロード",
            command=self._handle_upload,
            style="Primary.TButton"
        )
        self.upload_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.upload_dir_btn = HoverButton(
            button_frame,
            text="📁 ディレクトリをアップロード",
            command=self._handle_directory_upload,
            style="Primary.TButton"
        )
        self.upload_dir_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.delete_btn = HoverButton(
            button_frame,
            text="🗑️ ファイルを削除",
            command=self._handle_delete,
            style="Primary.TButton"
        )
        self.delete_btn.pack(side=tk.LEFT)
        
        # プログレスバー
        self.progress = ttk.Progressbar(
            card,
            orient="horizontal",
            length=400,
            mode="determinate"
        )
        self.progress.pack(padx=30, pady=(10, 5))
        
        self.progress_label = ttk.Label(
            card,
            text="",
            font=AppConstants.FONT_SMALL,
            background=AppConstants.COLOR_WHITE,
            foreground=AppConstants.COLOR_FG_LIGHT
        )
        self.progress_label.pack(padx=30, pady=(0, 30))
    
    # ===== アップロード処理 =====
    
    def _handle_upload(self) -> None:
        """ファイルアップロードの処理"""
        bucket = self.bucket_var.get()
        if not bucket:
            messagebox.showwarning("警告", "バケットを選択してください")
            return
        
        file_paths = filedialog.askopenfilenames(title="アップロードするファイルを選択")
        if not file_paths:
            return
        
        self._disable_buttons()
        
        def upload_thread():
            try:
                total = len(file_paths)
                self.progress["maximum"] = total
                
                for i, file_path in enumerate(file_paths, 1):
                    filename = os.path.basename(file_path)
                    s3_key = self._get_s3_key(filename)
                    
                    self.s3_manager.upload_file(file_path, bucket, s3_key)
                    
                    self.progress["value"] = i
                    self.progress_label.config(text=f"アップロード中: {i}/{total} 完了")
                    self.root.update_idletasks()
                
                self.progress_label.config(text="✓ アップロード完了!")
                messagebox.showinfo("完了", f"{total}個のファイルをアップロードしました")
            except Exception as e:
                messagebox.showerror("エラー", f"アップロード中にエラーが発生:\n{str(e)}")
            finally:
                self._enable_buttons()
                self.progress["value"] = 0
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def _handle_directory_upload(self) -> None:
        """ディレクトリアップロードの処理"""
        bucket = self.bucket_var.get()
        if not bucket:
            messagebox.showwarning("警告", "バケットを選択してください")
            return
        
        directory_path = filedialog.askdirectory(title="アップロードするディレクトリを選択")
        if not directory_path:
            return
        
        self._disable_buttons()
        
        def upload_thread():
            try:
                # ディレクトリをスキャン
                self.progress_label.config(text="ディレクトリをスキャン中...")
                self.root.update_idletasks()
                
                file_list = self._scan_directory(directory_path)
                
                if not file_list:
                    messagebox.showinfo("情報", "アップロードするファイルが見つかりませんでした")
                    return
                
                total = len(file_list)
                self.progress["maximum"] = total
                
                # 各ファイルをアップロード
                for i, (file_path, relative_path) in enumerate(file_list, 1):
                    s3_key = self._get_s3_key_for_directory(relative_path)
                    
                    self.s3_manager.upload_file(file_path, bucket, s3_key)
                    
                    self.progress["value"] = i
                    self.progress_label.config(
                        text=f"アップロード中: {i}/{total} - {relative_path}"
                    )
                    self.root.update_idletasks()
                
                self.progress_label.config(text="✓ ディレクトリのアップロード完了!")
                messagebox.showinfo(
                    "完了",
                    f"ディレクトリから{total}個のファイルをアップロードしました"
                )
            except Exception as e:
                messagebox.showerror("エラー", f"アップロード中にエラーが発生:\n{str(e)}")
            finally:
                self._enable_buttons()
                self.progress["value"] = 0
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def _scan_directory(self, directory_path: str) -> List[Tuple[str, str]]:
        """
        ディレクトリを再帰的にスキャンしてファイルリストを取得
        
        Args:
            directory_path: スキャンするディレクトリのパス
            
        Returns:
            [(ファイルの絶対パス, ベースディレクトリからの相対パス), ...]のリスト
        """
        file_list = []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                # ベースディレクトリからの相対パスを計算
                relative_path = os.path.relpath(file_path, directory_path)
                # Windowsのパス区切り文字をS3用のスラッシュに変換
                relative_path = relative_path.replace('\\', '/')
                file_list.append((file_path, relative_path))
        
        return file_list
    
    def _get_s3_key_for_directory(self, relative_path: str) -> str:
        """
        ディレクトリアップロード用のS3キーを生成
        
        Args:
            relative_path: ベースディレクトリからの相対パス
            
        Returns:
            S3キー（prefixを含む）
        """
        prefix = self.prefix_var.get().strip()
        if prefix:
            if not prefix.endswith('/'):
                prefix += '/'
            return f"{prefix}{relative_path}"
        return relative_path
    
    # ===== 削除処理 =====
    
    def _handle_delete(self) -> None:
        """ファイル削除の処理"""
        bucket = self.bucket_var.get()
        if not bucket:
            messagebox.showwarning("警告", "バケットを選択してください")
            return
        
        prefix = self.prefix_var.get().strip()
        
        try:
            objects, next_token = self.s3_manager.list_objects(
                bucket, prefix, AppConstants.MAX_KEYS_PER_PAGE
            )
            
            if not objects:
                messagebox.showinfo("情報", "指定されたプレフィックスにオブジェクトが見つかりません")
                return
            
            self._show_delete_dialog(bucket, prefix, objects, next_token)
        except Exception as e:
            messagebox.showerror("エラー", f"オブジェクトリストの取得に失敗:\n{str(e)}")
    
    def _show_delete_dialog(
        self,
        bucket: str,
        prefix: str,
        initial_objects: List[str],
        initial_token: Optional[str]
    ) -> None:
        """削除ダイアログを表示"""
        dialog = tk.Toplevel(self.root)
        dialog.title("ファイル削除")
        dialog.geometry("800x700")
        dialog.configure(bg=AppConstants.COLOR_BG_LIGHT)
        
        # 状態管理
        pages = [[obj, False] for obj in initial_objects]  # [key, checked]
        all_pages = [pages]
        current_page = [0]
        continuation_token = [initial_token]
        
        # タイトル
        title_frame = ttk.Frame(dialog, style="Card.TFrame")
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(
            title_frame,
            text="🗑️ 削除するファイルを選択",
            style="Title.TLabel"
        ).pack()
        
        # ページラベル
        page_label = ttk.Label(
            dialog,
            text=f"ページ 1 / 1",
            font=AppConstants.FONT_NORMAL,
            background=AppConstants.COLOR_BG_LIGHT
        )
        page_label.pack(pady=(0, 10))
        
        # チェックボックスフレーム（スクロール可能）
        checkbox_container = ttk.Frame(dialog, relief="solid", borderwidth=1)
        checkbox_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(checkbox_container, bg=AppConstants.COLOR_WHITE)
        scrollbar = ttk.Scrollbar(checkbox_container, orient="vertical", command=canvas.yview)
        checkbox_frame = ttk.Frame(canvas, style="Card.TFrame")
        
        checkbox_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def update_checkboxes():
            """チェックボックスを更新"""
            for widget in checkbox_frame.winfo_children():
                widget.destroy()
            
            current_data = all_pages[current_page[0]]
            
            for i, (obj_key, checked) in enumerate(current_data):
                var = tk.BooleanVar(value=checked)
                
                cb = ttk.Checkbutton(
                    checkbox_frame,
                    text=obj_key,
                    variable=var,
                    style="Card.TCheckbutton"
                )
                cb.pack(anchor="w", padx=10, pady=2)
                
                # チェック状態の更新
                var.trace_add(
                    "write",
                    lambda *args, idx=i, v=var: update_check_state(idx, v.get())
                )
            
            page_label.config(text=f"ページ {current_page[0] + 1} / {len(all_pages)}")
        
        def update_check_state(index: int, checked: bool):
            """チェック状態を保存"""
            all_pages[current_page[0]][index][1] = checked
        
        def load_next_page():
            """次のページを読み込み"""
            if current_page[0] + 1 < len(all_pages):
                current_page[0] += 1
                update_checkboxes()
            elif continuation_token[0]:
                try:
                    objects, next_token = self.s3_manager.list_objects(
                        bucket, prefix, AppConstants.MAX_KEYS_PER_PAGE, continuation_token[0]
                    )
                    
                    new_page = [[obj, False] for obj in objects]
                    all_pages.append(new_page)
                    continuation_token[0] = next_token
                    current_page[0] += 1
                    update_checkboxes()
                except Exception as e:
                    messagebox.showerror("エラー", f"次のページの読み込みに失敗:\n{str(e)}")
        
        def load_previous_page():
            """前のページに戻る"""
            if current_page[0] > 0:
                current_page[0] -= 1
                update_checkboxes()
        
        def delete_selected():
            """選択されたファイルを削除"""
            selected_keys = [
                obj_key for page in all_pages
                for obj_key, checked in page if checked
            ]
            
            if not selected_keys:
                messagebox.showwarning("警告", "削除するファイルを選択してください")
                return
            
            if not messagebox.askyesno(
                "確認",
                f"{len(selected_keys)}個のファイルを削除しますか？"
            ):
                return
            
            self._execute_delete(dialog, bucket, selected_keys, False)
        
        def delete_all():
            """すべてのファイルを削除"""
            if not messagebox.askyesno(
                "確認",
                f"プレフィックス '{prefix}' 配下のすべてのファイルを削除しますか？\n"
                "この操作は取り消せません。"
            ):
                return
            
            self._execute_delete(dialog, bucket, [], True, prefix)
        
        # 初期表示
        update_checkboxes()
        
        # ナビゲーションボタン
        nav_frame = ttk.Frame(dialog, style="Card.TFrame")
        nav_frame.pack(fill=tk.X, padx=20, pady=10)
        
        HoverButton(
            nav_frame,
            text="◀ 前のページ",
            command=load_previous_page,
            style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        HoverButton(
            nav_frame,
            text="次のページ ▶",
            command=load_next_page,
            style="Secondary.TButton"
        ).pack(side=tk.LEFT)
        
        # 削除ボタン
        delete_frame = ttk.Frame(dialog, style="Card.TFrame")
        delete_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        HoverButton(
            delete_frame,
            text="選択したファイルを削除",
            command=delete_selected,
            style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        HoverButton(
            delete_frame,
            text="すべて削除",
            command=delete_all,
            style="Primary.TButton"
        ).pack(side=tk.LEFT)
    
    def _execute_delete(
        self,
        parent_dialog: tk.Toplevel,
        bucket: str,
        selected_keys: List[str],
        delete_all: bool,
        prefix: str = ""
    ) -> None:
        """削除を実行"""
        progress_dialog = tk.Toplevel(parent_dialog)
        progress_dialog.title("削除中")
        progress_dialog.geometry("400x200")
        progress_dialog.configure(bg=AppConstants.COLOR_BG_LIGHT)
        
        # プログレスバー
        ttk.Label(
            progress_dialog,
            text="ファイルを削除しています...",
            font=AppConstants.FONT_LARGE,
            background=AppConstants.COLOR_BG_LIGHT
        ).pack(pady=20)
        
        progress_bar = ttk.Progressbar(
            progress_dialog,
            length=300,
            mode="determinate"
        )
        progress_bar.pack(pady=10)
        
        status_label = ttk.Label(
            progress_dialog,
            text="",
            font=AppConstants.FONT_NORMAL,
            background=AppConstants.COLOR_BG_LIGHT
        )
        status_label.pack(pady=10)
        
        ok_button = HoverButton(
            progress_dialog,
            text="OK",
            command=lambda: self._close_progress_dialog(parent_dialog, progress_dialog),
            style="Primary.TButton"
        )
        ok_button.pack(pady=10)
        ok_button['state'] = 'disabled'
        
        def delete_thread():
            try:
                if delete_all:
                    # すべて削除
                    self._delete_all_with_prefix(
                        bucket, prefix, progress_bar, status_label
                    )
                else:
                    # 選択されたファイルを削除
                    total = len(selected_keys)
                    progress_bar['maximum'] = total
                    
                    # バッチで削除
                    for i in range(0, total, AppConstants.DELETE_BATCH_SIZE):
                        batch = selected_keys[i:i + AppConstants.DELETE_BATCH_SIZE]
                        self.s3_manager.delete_objects(bucket, batch)
                        
                        progress_bar['value'] = min(i + AppConstants.DELETE_BATCH_SIZE, total)
                        status_label.config(
                            text=f"削除済み: {min(i + AppConstants.DELETE_BATCH_SIZE, total)}/{total}"
                        )
                        progress_dialog.update_idletasks()
                
                status_label.config(text="✓ 削除完了!")
                ok_button['state'] = 'normal'
            except Exception as e:
                messagebox.showerror("エラー", f"削除中にエラーが発生:\n{str(e)}")
                ok_button['state'] = 'normal'
        
        threading.Thread(target=delete_thread, daemon=True).start()
    
    def _delete_all_with_prefix(
        self,
        bucket: str,
        prefix: str,
        progress_bar: ttk.Progressbar,
        status_label: ttk.Label
    ) -> None:
        """プレフィックス配下のすべてのオブジェクトを削除"""
        total_deleted = 0
        continuation_token = None
        
        progress_bar['maximum'] = 1000  # 進捗表示用の仮の最大値
        
        while True:
            objects, continuation_token = self.s3_manager.list_objects(
                bucket, prefix, AppConstants.DELETE_BATCH_SIZE, continuation_token
            )
            
            if not objects:
                break
            
            self.s3_manager.delete_objects(bucket, objects)
            total_deleted += len(objects)
            
            status_label.config(text=f"削除済み: {total_deleted} ファイル")
            progress_bar['value'] = min(progress_bar['value'] + 10, 990)
            
            if not continuation_token:
                break
        
        progress_bar['value'] = 1000
    
    def _close_progress_dialog(
        self,
        parent_dialog: tk.Toplevel,
        progress_dialog: tk.Toplevel
    ) -> None:
        """プログレスダイアログを閉じる"""
        progress_dialog.destroy()
        parent_dialog.destroy()
    
    def _get_s3_key(self, filename: str) -> str:
        """ファイル名からS3キーを生成"""
        prefix = self.prefix_var.get().strip()
        if prefix:
            if not prefix.endswith('/'):
                prefix += '/'
            return f"{prefix}{filename}"
        return filename
    
    def _disable_buttons(self) -> None:
        """ボタンを無効化"""
        self.upload_btn['state'] = 'disabled'
        self.upload_dir_btn['state'] = 'disabled'
        self.delete_btn['state'] = 'disabled'
    
    def _enable_buttons(self) -> None:
        """ボタンを有効化"""
        self.upload_btn['state'] = 'normal'
        self.upload_dir_btn['state'] = 'normal'
        self.delete_btn['state'] = 'normal'


# ===== アプリケーションのエントリーポイント =====
if __name__ == "__main__":
    root = tk.Tk()
    app = S3UploadAndDeleteApp(root)
    root.mainloop()
