# S3UploadAndDeleteApp README

## Overview
S3UploadAndDeleteApp is a GUI application for uploading and deleting files in an AWS S3 bucket. Users can input their AWS credentials to easily perform file operations on S3 buckets. It also supports reading credentials from profiles.

## Requirements
- Python 3.x
- `boto3` library
- `tkinter` library (included in the Python standard library)

## Installation

### Method 1: Using Batch File (Recommended - Windows)

1. Double-click `run_s3_manager.bat` to run it.
   - On first run, it will automatically create a Python virtual environment (venv) and install the required libraries (boto3).
   - From the second run onwards, it will reuse the existing environment and launch the application immediately.

### Method 2: Manual Installation

1. Install the necessary Python packages.

    ```sh
    pip install boto3
    ```
   
2. Download the script and run it in your local environment.

## Usage

1. **Launch the Application**
   - **Method 1 (Recommended)**: Double-click `run_s3_manager.bat` to launch.
   - **Method 2**: Execute the Python script directly.
     ```sh
     python app.py
     ```

2. **Login Screen**
   - Upon launching, a login screen will appear.
   - If you have a profile, you can select an AWS profile from the `Select AWS Profile` dropdown menu. The saved access key and secret key will be automatically filled in upon profile selection.
   - If you do not have a profile or wish to input the access key and secret key manually, enter them directly into the fields.
   - Click the `Login` button to log in to AWS.

3. **Main Menu**
   - Upon successful login, the main menu will be displayed.
   - Select the bucket you wish to operate on from the `S3 Bucket` dropdown.
   - If needed, specify a particular folder by entering a prefix in the `S3 Prefix(Option)`.

4. **Upload Files**
   - Click the `Upload Files` button and select the files you want to upload to the bucket from the file selection dialog.
   - The selected files will be uploaded to the specified bucket. You can check the progress using the progress bar.

5. **Delete Files**
   - Click the `Delete Files` button to display the delete screen.
   - Select the files you wish to delete and click the `Delete Selected` button to delete them.
   - Click the `ALL Object Delete` button to delete all objects within the specified prefix.

# S3UploadAndDeleteApp README

## 概要
S3UploadAndDeleteAppは、AWS S3バケットにファイルをアップロードおよび削除するためのGUIアプリケーションです。ユーザーはAWS認証情報を入力して、S3バケットに対してファイル操作を簡単に実行できます。プロファイルからの認証情報の読み取りもサポートしています。

## 必要条件
- Python 3.x
- `boto3` ライブラリ
- `tkinter` ライブラリ（Python標準ライブラリに含まれる）

## インストール

### 方法1: バッチファイルを使用（推奨・Windows）

1. `run_s3_manager.bat`をダブルクリックして実行します。
   - 初回実行時に自動的にPython仮想環境（venv）を作成し、必要なライブラリ（boto3）をインストールします。
   - 2回目以降は既存の環境を再利用するため、すぐにアプリケーションが起動します。

### 方法2: 手動インストール

1. 必要なPythonパッケージをインストールします。

    ```sh
    pip install boto3
    ```
   
2. スクリプトをダウンロードし、ローカル環境で実行します。

## 使用方法

1. **アプリケーションの起動**
   - **方法1（推奨）**: `run_s3_manager.bat`をダブルクリックして起動します。
   - **方法2**: Pythonスクリプトを直接実行します。
     ```sh
     python app.py
     ```

2. **ログイン画面**
   - アプリケーションを起動するとログイン画面が表示されます。
   - プロファイルがある場合、`Select AWS Profile` ドロップダウンメニューからAWSプロファイルを選択できます。プロファイル選択時、保存されたアクセスキーとシークレットキーが自動的に入力されます。
   - プロファイルがない場合、または手動でアクセスキーとシークレットキーを入力したい場合は、各フィールドに直接入力します。
   - `Login` ボタンをクリックしてAWSにログインします。

3. **メインメニュー**
   - ログインに成功するとメインメニューが表示されます。
   - `S3 Bucket` ドロップダウンから操作したいバケットを選択します。
   - 必要な場合は、`S3 Prefix(Option)` にプレフィックスを入力して特定のフォルダを指定します。

4. **ファイルのアップロード**
   - `Upload Files` ボタンをクリックし、ファイル選択ダイアログからバケットにアップロードしたいファイルを選択します。
   - 選択したファイルは、指定したバケットにアップロードされます。進捗はプログレスバーで確認できます。

5. **ファイルの削除**
   - `Delete Files` ボタンをクリックして削除画面を表示します。
   - 削除したいファイルを選択し、`Delete Selected` ボタンをクリックして削除します。
   - `ALL Object Delete` ボタンをクリックすると、指定したプレフィックス内のすべてのオブジェクトを削除できます。
