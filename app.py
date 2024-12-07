import boto3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread
import configparser
import os

# S3マネージャーアプリケーションのクラス定義
class S3UploadAndDeleteApp:
    def __init__(self, root):
        # メインウィンドウの設定
        self.root = root
        self.root.title("S3UploadAndDeleteApp")

        # AWSプロファイルの読み込み
        self.profiles = self.load_aws_profiles()
        self.credentials = configparser.ConfigParser()
        self.credentials.read(os.path.join(os.path.expanduser('~'), '.aws', 'credentials'))

        # ログイン画面をセットアップ
        self.setup_login()

    def load_aws_profiles(self):
        # ユーザーのAWS credentialsファイルのパスを取得
        aws_credentials_path = os.path.join(os.path.expanduser('~'), '.aws', 'credentials')
        
        profiles = []
        # credentialsファイルが存在する場合、プロファイル名をリスト化
        if os.path.exists(aws_credentials_path):
            with open(aws_credentials_path, 'r') as cred_file:
                for line in cred_file:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        profile = line[1:-1]
                        profiles.append(profile)
        return profiles

    def setup_login(self):
        # ログイン画面のGUI要素を設定
        self.login_frame = ttk.Frame(self.root)
        self.login_frame.grid(row=0, column=0)

        # プロファイル選択用のコンボボックス
        ttk.Label(self.login_frame, text="Select AWS Profile", font=('Helvetica', 14)).grid(row=0, column=1, padx=0, pady=5)
        self.profile_var = tk.StringVar(self.login_frame)  # 選択されたプロファイルを保持するためのStringVar
        self.profile_menu = ttk.Combobox(self.login_frame, textvariable=self.profile_var, values=self.profiles, font=('Helvetica', 14))
        self.profile_menu.grid(row=1, column=1, padx=0, pady=5)
        # プロファイルが選ばれると、update_credentialsメソッドが呼ばれる
        self.profile_menu.bind("<<ComboboxSelected>>", self.update_credentials)

        # アクセスキーとシークレットキーの入力フィールドを追加
        ttk.Label(self.login_frame, text="Access Key", font=('Helvetica', 14)).grid(row=2, column=0, padx=5, pady=5)
        self.access_key_entry = ttk.Entry(self.login_frame, font=('Helvetica', 14), width=30)
        self.access_key_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Secret Key", font=('Helvetica', 14)).grid(row=3, column=0, padx=5, pady=5)
        self.secret_key_entry = ttk.Entry(self.login_frame, show="*", font=('Helvetica', 14), width=30)  # シークレットキーの内容は非表示（*）に設定
        self.secret_key_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Button(self.login_frame, text="Login", command=self.login).grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # 最初のプロファイルを自動的に選択し、認証情報を更新
        if self.profiles:
            self.profile_menu.current(0)
            self.update_credentials()

    def update_credentials(self, event=None):
        # 選択されたプロファイルの認証情報を取得し、エントリに表示
        selected_profile = self.profile_var.get()
        if selected_profile in self.credentials:
            access_key = self.credentials[selected_profile].get('aws_access_key_id', '')
            secret_key = self.credentials[selected_profile].get('aws_secret_access_key', '')
            self.access_key_entry.delete(0, tk.END)
            self.access_key_entry.insert(0, access_key)
            self.secret_key_entry.delete(0, tk.END)
            self.secret_key_entry.insert(0, secret_key)

    def login(self):
        # ユーザーが入力した認証情報を使用してAWSに接続
        access_key = self.access_key_entry.get()
        secret_key = self.secret_key_entry.get()

        try:
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            self.s3 = session.client('s3')
            # S3バケットをリスト化して正しく認証されているかを確認
            self.s3.list_buckets()
            self.setup_main_menu()  # 認証成功時にメインメニューを設定
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_main_menu(self):
        # ログインフレームを非表示にしてメインメニューをセットアップ
        if hasattr(self, 'login_frame'):
            self.login_frame.grid_forget()

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0)
        self.bucket_var = tk.StringVar(self.main_frame)

        # 利用可能なS3バケットのリストを取得
        self.buckets = self.s3.list_buckets()["Buckets"]
        self.bucket_names = [bucket["Name"] for bucket in self.buckets]

        # バケット選択メニューを準備
        ttk.Label(self.main_frame, text="S3 Bucket", font=('Helvetica', 14)).grid(row=1, column=1, padx=0, pady=5)
        self.bucket_var = tk.StringVar(self.main_frame)
        self.bucket_menu = ttk.Combobox(self.main_frame, textvariable=self.bucket_var, values=self.bucket_names, width=50, font=('Helvetica', 14))
        self.bucket_menu.grid(row=2, column=1, padx=5, pady=5)

        # S3プレフィックス入力フィールドを追加
        ttk.Label(self.main_frame, text="S3 Prefix(Option)", font=('Helvetica', 14)).grid(row=3, column=1, padx=0, pady=5)
        self.prefix_var = tk.StringVar(self.main_frame)
        self.prefix_entry = ttk.Entry(self.main_frame, textvariable=self.prefix_var, width=30, font=('Helvetica', 14))
        self.prefix_entry.grid(row=4, column=1, padx=0, pady=5)
        self.prefix_entry.insert(0, '')

        # スタイルオブジェクトを作成
        button_style = ttk.Style()
        button_style.configure('Exec.TButton', font=('Helvetica', 12))

        # アップロードと削除ボタンを追加
        ttk.Button(self.main_frame, text="Upload Files", command=self.upload_files, style='Exec.TButton').grid(row=5, column=1, padx=0, pady=15)
        ttk.Button(self.main_frame, text="Delete Files", command=self.delete_files, style='Exec.TButton').grid(row=6, column=1, padx=100, pady=5)

        # プログレスバーの作成
        self.progress = ttk.Progressbar(self.main_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=7, column=1, padx=5, pady=15)

        # ラベルを追加して進捗状況を表示
        self.progress_label = ttk.Label(self.main_frame, text="")
        self.progress_label.grid(row=8, column=1, padx=5, pady=5)

    def get_full_s3_path(self, filename):
        prefix = self.prefix_var.get().strip()
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        s3_path = f"{prefix}{filename}"
        return s3_path

    def upload_files(self):
        bucket_name = self.bucket_var.get()
        if bucket_name == '':
            return

        file_paths = filedialog.askopenfilenames()

        def upload():
            self.progress["maximum"] = len(file_paths)
            for i, file_path in enumerate(file_paths):
                filename = file_path.split('/')[-1]
                s3_path = self.get_full_s3_path(filename)
                self.s3.upload_file(file_path, bucket_name, s3_path)  # アップロード処理
                self.progress["value"] = i + 1  # プログレスバーの値を更新
                self.progress_label.config(text=f"Uploaded {i + 1}/{len(file_paths)} files")
                self.root.update_idletasks()  # UIの更新を即座に反映
            self.progress_label.config(text="Upload Complete!")  # 完了メッセージ

        Thread(target=upload).start()

        # アップロード処理を別スレッドで実行
        Thread(target=upload).start()

    def delete_files(self):
        bucket_name = self.bucket_var.get()
        if bucket_name == '':
            return
        prefix = self.prefix_var.get().strip()
        objects_response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=25)
        objects = objects_response.get('Contents', [])
        if objects_response.get('KeyCount') != 0:
            # 削除ダイアログを表示
            self.show_delete_dialog(bucket_name, objects, objects_response.get('NextContinuationToken'))
        else:
            messagebox.showerror("No Data", "The bucket has no objects under the specified prefix.")
            return

    def show_delete_dialog(self, bucket_name, initial_objects, initial_continuation_token=None):
        delete_dialog = tk.Toplevel(self.root)
        delete_dialog.title("Delete Files")
        delete_dialog.geometry("750x640")

        pages = []  # 全てのページのオブジェクトとチェック状態を保持するリスト
        current_page_index = tk.IntVar(value=0)  # 現在のページのインデックス

        checkbox_frame = ttk.Frame(delete_dialog)
        checkbox_frame.pack(fill=tk.BOTH, expand=True)
        page_label = ttk.Label(delete_dialog, text="Page 1", font=("Helvetica", 12))
        page_label.pack(pady=(5, 0))  # 上の余白を指定

        def update_checkboxes():
            # 現在のチェックボックスを削除
            for widget in checkbox_frame.winfo_children():
                widget.destroy()

            # 現在のページのオブジェクトに基づいてチェックボックスを作成
            if pages:
                current_page = pages[current_page_index.get()]
                for obj_key, checked in current_page:
                    var = tk.BooleanVar(value=checked)
                    chk = ttk.Checkbutton(checkbox_frame, text=obj_key, variable=var)
                    chk.pack(anchor='w')
                    var.trace_add("write", lambda *args, var=var, obj_key=obj_key: on_check(obj_key, var.get()))
            # ページラベルを更新
            page_label.config(text=f"Page {current_page_index.get() + 1}")

        def on_check(obj_key, checked):
            # チェック状態を更新
            if pages:
                current_page = pages[current_page_index.get()]
                for i, (key, _) in enumerate(current_page):
                    if key == obj_key:
                        current_page[i] = (key, checked)

        def fetch_page(continuation_token=None):
            prefix = self.prefix_var.get().strip()
            response = self.s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=25,
                ContinuationToken=continuation_token
            )
            objects = response.get('Contents', [])
            return [(obj['Key'], False) for obj in objects], response.get('NextContinuationToken', None)

        # 初めてのページを登録
        pages.append([(obj['Key'], False) for obj in initial_objects])
        initial_continuation_token = initial_continuation_token
        update_checkboxes()

        def delete_selected():
            delete_keys = [{'Key': obj_key} for page in pages for obj_key, checked in page if checked]
            if delete_keys:
                self.progress["maximum"] = len(delete_keys)
                for i, key in enumerate(delete_keys):
                    response = self.s3.delete_objects(Bucket=bucket_name, Delete={'Objects': [key]})
                    self.progress["value"] = i + 1
                    self.progress_label.config(text=f"Deleted {i + 1}/{len(delete_keys)} files")
                    self.root.update_idletasks()

                    if 'Deleted' in response:
                        deleted_keys = [obj['Key'] for obj in response['Deleted']]
                        print(f"Deleted keys: {', '.join(deleted_keys)}")
                    if 'Errors' in response:
                        for error in response['Errors']:
                            print(f"Failed to delete {error['Key']}: {error['Message']}")
                self.progress_label.config(text="Deletion Complete!") 

        button_style = ttk.Style()
        button_style.configure('Exec.TButton', font=('Helvetica', 12))
        ttk.Button(delete_dialog, text="Delete Selected", command=delete_selected, style='Exec.TButton').pack(pady=5)

        def load_next():
            nonlocal initial_continuation_token
            if current_page_index.get() + 1 < len(pages):
                # 既にロード済みの次のページへ移動
                current_page_index.set(current_page_index.get() + 1)
                update_checkboxes()
            elif initial_continuation_token:
                # 新しいページをロードしてリストに追加
                next_objects, initial_continuation_token = fetch_page(initial_continuation_token)
                pages.append(next_objects)
                current_page_index.set(current_page_index.get() + 1)
                update_checkboxes()

        def load_previous():
            if current_page_index.get() > 0:
                current_page_index.set(current_page_index.get() - 1)
                update_checkboxes()

        nav_frame = ttk.Frame(delete_dialog)
        nav_frame.pack()
        # スタイルオブジェクトを作成
        button_style = ttk.Style()
        button_style.configure('Exec.TButton', font=('Helvetica', 12))
        ttk.Button(nav_frame, text="Previous", command=load_previous, style='Exec.TButton').pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(nav_frame, text="Next", command=load_next, style='Exec.TButton').pack(side=tk.LEFT, padx=5, pady=5)


# アプリケーションのエントリーポイント
if __name__ == "__main__":
    # メインウィンドウの初期化とアプリケーションの起動
    root = tk.Tk()
    app = S3UploadAndDeleteApp(root)
    root.mainloop()