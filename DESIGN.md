# Claude Chat Desktop App 設計書

## 1. 構成図

```mermaid
graph TD
  A[ユーザー] -->|GUI操作| B[Tkinterアプリ]
  B -->|質問・画像送信| C[Anthropic Claude API]
  B -->|会話履歴保存/復元| D[ローカルファイル(JSON/Markdown/zip)]
  B -->|画像プレビュー| E[Pillow (画像処理)]
  B -->|APIキー取得| F[.envファイル]
```

## 2. 機能一覧

| バージョン | テキスト質問 | 画像添付 | 会話履歴 | 履歴保存/再開 |
|:---|:---:|:---:|:---:|:---:|
| claude_tk_app_simple.py | ○ | × | × | × |
| claude_tk_app_image.py | ○ | ○ | × | × |
| claude_tk_app_multi.py | ○ | × | ○ | ○ |
| claude_tk_app_multi_image.py | ○ | ○ | ○ | ○ |

### 共通機能
- Anthropic Claude APIとの連携（APIキーは.envから取得）
- Markdown形式の回答をプレーンテキストに自動変換
- Ctrl+Enterで質問送信
- エラー時のダイアログ表示

### バージョン別機能
- **シンプル版**: テキストチャットのみ
- **画像対応版**: 画像添付・プレビュー・画像付き質問
- **マルチターン版**: 会話履歴の保持・保存・再開
- **マルチターン＋画像対応版**: 画像付き会話履歴の保存・復元（zip形式）

## 3. 画面構成（例: マルチターン＋画像対応版）

- 左: 画像選択・プレビュー・質問入力欄
- 右: 会話履歴表示（質問・回答ペア、画像サムネイル付き、色分け）
- 下部: 送信・クリア・再開・終了ボタン

## 4. 処理フロー

### 質問送信時
1. ユーザーが質問（＋画像）を入力
2. [送信]ボタンまたはCtrl+Enterで送信
3. APIキーを.envから取得し、Anthropic APIへリクエスト
4. Claudeからの回答を受信
5. Markdown→テキスト変換し、画面に表示
6. （マルチターン版は履歴に追加）

### 会話履歴の保存
1. [保存]ボタン押下
2. 保存形式（Markdown/JSON/両方）を選択
3. 画像付きの場合はimg/フォルダに画像をコピー
4. zipファイルとして保存

### 会話履歴の復元
1. [再開]ボタン押下
2. zipファイル選択
3. JSONとimg/を一時ディレクトリに展開
4. 履歴・画像を画面に復元

## 5. 保存データの構造

### JSON形式（zip内）
```json
{
  "metadata": {
    "created_at": "2024-06-01T12:34:56",
    "model": "claude-sonnet-4-20250514",
    "total_messages": 4
  },
  "conversation": [
    { "role": "user", "content": "質問文", "image_path": "img/xxx.png" },
    { "role": "assistant", "content": "回答文（Markdown）" },
    ...
  ]
}
```
- 画像はimg/配下に保存、image_pathで参照

### Markdown形式（zip内）
- 質問・回答ペアをMarkdownで記述
- 画像は`img/ファイル名`で参照

### zipファイル構成例
```
claude_conversation_20240601_123456_json.zip
├─ claude_conversation_20240601_123456.json
└─ img/
    ├─ 画像1.png
    └─ 画像2.jpg
```

## 6. 依存パッケージ
- anthropic
- python-dotenv
- markdown
- Pillow

## 7. 注意事項
- APIキーは.envファイルで管理
- インターネット接続必須
- 画像はbase64エンコードでAPI送信
- zip復元時は一時ディレクトリを利用
- Markdownの表や複雑なコードは正しく変換されない場合あり 