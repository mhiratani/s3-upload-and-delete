@echo off
chcp 65001 > nul
echo S3 Manager 実行環境セットアップ中...
echo.

REM Pythonの実行環境確認
python --version > nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません。
    echo Pythonをインストールしてから再実行してください。
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Pythonが見つかりました。
python --version

REM 現在のディレクトリにvenvがあるかチェック
if exist "venv" (
    echo 既存のvenv環境が見つかりました。
    echo venv環境を有効化中...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo エラー: venv環境の有効化に失敗しました。
        pause
        exit /b 1
    )
    echo venv環境が有効化されました。
) else (
    echo venv環境が見つかりません。新しく作成します...
    python -m venv venv
    if errorlevel 1 (
        echo エラー: venv環境の作成に失敗しました。
        pause
        exit /b 1
    )
    echo venv環境を有効化中...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo エラー: venv環境の有効化に失敗しました。
        pause
        exit /b 1
    )
    echo venv環境が作成・有効化されました。
    
    echo boto3ライブラリをインストール中...
    pip install boto3
    if errorlevel 1 (
        echo エラー: boto3ライブラリのインストールに失敗しました。
        pause
        exit /b 1
    )
    echo boto3ライブラリのインストールが完了しました。
)

REM boto3ライブラリがインストールされているかチェック
python -c "import boto3" > nul 2>&1
if errorlevel 1 (
    echo boto3ライブラリが見つかりません。インストール中...
    pip install boto3
    if errorlevel 1 (
        echo エラー: boto3ライブラリのインストールに失敗しました。
        pause
        exit /b 1
    )
    echo boto3ライブラリのインストールが完了しました。
)

echo.
echo セットアップ完了！S3 Managerを起動します...
echo.

REM Pythonスクリプトを実行
python app.py

echo.
echo プログラムが終了しました。
pause
