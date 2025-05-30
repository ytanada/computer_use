# Browser Agent with Azure Computer Use Preview
このプロジェクトは、Azure OpenAI の `computer-use-preview` モデルと Playwright を組み合わせて、スクリーンショットを元にブラウザ操作を行う Python エージェントの実装です。

## 📁 ディレクトリ構成
.
├── .chrome-profile/ # Chromeブラウザのユーザープロファイル（キャッシュ等）
├── .env # APIキーなどの環境変数設定ファイル（機密情報は除外推奨）
├── .gitignore # Git管理対象外のファイル指定
├── Dockerfile # 実行環境の構成
├── browser_agent_local.py # メインスクリプト（Playwright + Azure OpenAI連携）
├── requirements.txt # Python依存ライブラリ
└── screenshots/ # 撮影されたスクリーンショットの保存先



## 🚀 機能概要
- Azure OpenAI の `computer-use-preview` モデルを用いて、スクリーンショットと指示をもとに自動でGUI操作を推論・実行。
- Playwright を使って Chromium ブラウザを操作。
- ユーザの入力に従って検索・遷移・入力・スクリーンショットを繰り返し実行。
- エラー時にはリトライ機能とデバッグ用JSON出力をサポート。



## 🔧 環境構築
### 1. `.env` ファイルの作成
以下のように `.env` を作成し、各種設定値を記述します（ファイル内容は Git 管理対象外推奨）。

```dotenv
API_KEY=＜Azure OpenAIのAPIキー＞
AZURE_ENDPOINT=https://xxxxxxx.openai.azure.com
API_VERSION=2025-03-01-preview
MODEL=computer-use-preview
DISPLAY_WIDTH=1920
DISPLAY_HEIGHT=1200
ITERATIONS=9
```

### 2. Dockerコンテナでの実行
# イメージのビルド
```
docker build -t browser-agent .
```

# コンテナの起動
```
docker run -it --rm \
  --net=host \
  -v $(pwd):/home/ubuntu/work \
  browser-agent
```

### 3. 実行
1) pythonコマンドでPlaywrightを起動します。
```
# python browser_agent_local.py
```
2) 起動後、ターミナルに表示されるプロンプトで操作内容（例："ChatGPTについて調べて"）を入力してください。画面操作後、スクリーンショットと操作結果が表示されます。


### 4. 備考
・ wait アクションが新たにサポートされ、モデルによる待機指示にも対応しています。
・ .chrome-profile ディレクトリを用いてブラウザの状態を保持します（例：ログイン情報）。
・ screenshots/ にスクリーンショットが保存されます。


### 5. 注意点
.env には APIキーなどの秘密情報を含むため、Gitに含めないでください。
Azure OpenAI の computer-use-preview は 事前申請が必要 です。
