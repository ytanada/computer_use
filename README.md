# Browser Agent with Azure Computer Use Preview
Azure OpenAI の `computer-use-preview` モデルと`Playwright`を連携させ、モデルがスクリーンショットを取得した結果をトリガーにして、ブラウザ操作を自動で実行するPythonエージェントの実装になります。
## 📁 ディレクトリ構成
```
.
├── .chrome-profile/       # Chromeブラウザのユーザープロファイル（キャッシュ等）
├── .env                   # APIキーなどの環境変数設定ファイル（機密情報は除外推奨）
├── .gitignore             # Git管理対象外のファイル指定
├── Dockerfile             # 実行環境の構成
├── main.py                # メインスクリプト（エージェント起動エントリポイント）
├── core/                  # エージェントの処理ロジックをまとめたモジュール群
│   ├── __init__.py
│   ├── agent_core.py      # GUI操作の実行アクションの定義、API呼び出しのリトライ処理
│   ├── config.py          # 環境変数の読み込みと全体設定
│   ├── processor.py       # モデル出力を処理してステップごとにアクションを進める中核関数を定義
│   └── screenshot.py      # スクリーンショットの取得とBase64変換
├── requirements.txt       # Python依存ライブラリ
└── screenshots/           # 撮影されたスクリーンショットの保存先
```


## 🚀 機能概要
- Azure OpenAI の `computer-use-preview` モデルを用いて、スクリーンショットと指示をもとに、<br>自動でGUI操作を推論・実行
- Playwright を使って Chromium ブラウザを操作
- ユーザの入力に従って検索・遷移・入力・スクリーンショットを繰り返し実行
- エラー時にはリトライ機能とデバッグ用JSON出力をサポート



## 🔧 環境構築
### 1. `.env` ファイルの作成
以下のように `.env` を作成し、各種設定値を記述します（Git管理対象外推奨）：

```dotenv
API_KEY=＜Azure OpenAIのAPIキー＞
AZURE_ENDPOINT=https://xxxxxxx.openai.azure.com
API_VERSION=2025-03-01-preview
MODEL=computer-use-preview
DISPLAY_WIDTH=1920
DISPLAY_HEIGHT=1200
ITERATIONS=9
SCREENSHOT_ROOT=screenshots
```

### 2. Dockerコンテナでの実行
#### イメージのビルド
```
docker build -t browser-agent .
```

#### コンテナの起動
```
docker run -it --rm \
  --net=host \
  -v $(pwd):/home/ubuntu/work \
  browser-agent
```

### 3. 実行
1) 以下のコマンドでエージェントを起動します：
```
# python main.py
```
2) 起動後、ターミナルに表示されるプロンプトで操作内容（例：`ChatGPTについて調べて`）を入力してください。
その後、モデルによるブラウザ操作・スクリーンショット取得・結果出力が自動的に行われます。



### 4. 備考
- wait アクションにも対応し、モデルが指示する「待機」操作が可能です。<br>
- `.chrome-profile` によりブラウザ状態（例：ログイン情報など）を保持します。<br>
- `screenshots/` にスクリーンショットが保存されます。<br>


### 5. 注意点
- `.env` には APIキーなどの秘密情報を含むため、Gitに含まれていません。
- Azure OpenAI の `computer-use-preview` は 事前申請が必要 です。
