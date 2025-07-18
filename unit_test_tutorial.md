# ユニットテスト入門（初心者向け）

このドキュメントでは、`claude_tk` ディレクトリ内の各種ユニットテスト（`test_claude_tk_app_image.py`、`test_claude_tk_app_multi_image.py`、`test_claude_tk_app_multi.py`、`test_claude_tk_app_simple.py`）について、初心者向けに解説します。

---

## 1. ユニットテストとは

**ユニットテスト**とは、プログラムの最小単位（関数やクラスなど）ごとに、正しく動作するかどうかを自動で確認するテストです。バグの早期発見や、リファクタリング時の安全性確保に役立ちます。

---

## 2. ユニットテストの実行方法

Python の標準ライブラリ `unittest` を使ってテストを実行します。コマンドプロンプトやターミナルで、テストファイルがあるディレクトリに移動し、次のコマンドを実行します。

```
python -m unittest claude_tk/test_claude_tk_app_image.py
python -m unittest claude_tk/test_claude_tk_app_multi_image.py
python -m unittest claude_tk/test_claude_tk_app_multi.py
python -m unittest claude_tk/test_claude_tk_app_simple.py
```

または、`claude_tk` ディレクトリ内のすべてのテストをまとめて実行する場合：

```
python -m unittest discover -s claude_tk
```

---

## 3. カバレージとは

**カバレージ（Coverage）**とは、テストがどれだけソースコードを網羅しているか（どのくらいの行数がテストで実行されたか）を示す指標です。カバレージが高いほど、テストが多くのコードをチェックしていることになります。

---

## 4. カバレージの見方

カバレージツールを使うと、どのファイルのどの行がテストで実行されたかをレポートとして確認できます。たとえば、`htmlcov/index.html` で色分けされたカバレージ結果をブラウザで見ることができます。

- 緑色：テストで実行された行
- 赤色：テストで実行されなかった行

---

## 5. カバレージの実行方法

まず、カバレージツールをインストールします（初回のみ）：

```
pip install coverage
```

テストをカバレージ付きで実行するには、次のコマンドを使います。

```
coverage run -m unittest discover -s claude_tk
```

カバレージレポート（テキスト）を表示するには：

```
coverage report
```

### カバレージレポート（テキスト）の見方

`coverage report` コマンドを実行すると、次のような表が表示されます。

> ※下記の数値はあくまで例です。実際のプロジェクトで得られる値とは異なります。

```
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
claude_tk/claude_tk_app_image.py       200     10    95%
claude_tk/claude_tk_app_multi.py       180     20    89%
claude_tk/claude_tk_app_simple.py      100      5    95%
--------------------------------------------------------
TOTAL                                 480     35    93%
```

- **Name**: ファイル名（どのソースファイルか）
- **Stmts**: そのファイルの全コード行数（ステートメント数）
- **Miss**: テストで実行されなかった行数
- **Cover**: カバレージ（網羅率）。100%に近いほど、テストがよく書かれていることを示します。

**ポイント**
- Cover（カバレージ）が高いほど、テストがしっかり書かれている証拠です。
- Miss（未実行行）が多い場合は、その部分のテストが足りていない可能性があります。
- TOTAL行でプロジェクト全体のカバレージが分かります。

---

## 6. 各テストコードの解説

### claude_tk/test_claude_tk_app_simple.py のテスト関数解説

- **test_markdown_to_text_basic**
  - Markdown形式のテキストが正しく変換されるかをテストします。
- **test_center_window**
  - ウィンドウの中央寄せ処理で例外が発生しないかをテストします。
- **test_setup_ui**
  - UIセットアップ処理で例外が発生しないかをテストします。
- **test_send_question_empty**
  - 質問欄が空のまま送信しようとした場合、警告ダイアログが表示されるかをテストします。
- **test_send_question_api_error**
  - 質問送信時にAPIエラーが発生した場合、エラーダイアログが表示されるかをテストします。
- **test_save_conversation_history_json/markdown**
  - 質問・回答をJSON/Markdown形式で保存した場合、ファイルが正しく作成されるかをテストします。
- **test_prompt_save_conversation_yes/no/cancel**
  - 履歴保存確認ダイアログで「はい」「いいえ」「キャンセル」を選んだ場合の挙動をテストします。
- **test_new_question**
  - 新しい質問ボタンで、入力欄や回答欄がリセットされるかをテストします。
- **test_on_exit**
  - アプリ終了時にウィンドウが閉じるかをテストします。
- **test_ask_save_format_cancel**
  - 保存形式選択ダイアログでキャンセルした場合の挙動をテストします。

---

### claude_tk/test_claude_tk_app_image.py のテスト関数解説

- **test_markdown_to_text_basic**
  - Markdown形式のテキストが、正しくプレーンテキストに変換されるかをテストします。見出しやリスト、強調、リンクなどが抜け落ちていないかを確認します。
- **test_select_image_success**
  - 画像ファイルを選択したとき、画像データが正しく読み込まれ、プレビューが更新されるかをテストします。
- **test_select_image_cancel**
  - 画像選択ダイアログでキャンセルした場合、画像データやパスがリセットされるかをテストします。
- **test_remove_image**
  - 画像削除ボタンを押したとき、選択中の画像情報がリセットされ、プレビューも消えるかをテストします。
- **test_send_question_no_question**
  - 質問欄が空のまま送信しようとした場合、警告ダイアログが表示されるかをテストします。
- **test_send_question_with_image**
  - 質問文と画像を送信したとき、APIレスポンスが正しく処理され、履歴に保存されるかをテストします。
- **test_new_question**
  - 新しい質問ボタンで、入力欄や履歴がリセットされるかをテストします。
- **test_exit_application**
  - アプリ終了時に保存確認ダイアログが出て、OKならウィンドウが閉じるかをテストします。
- **test_prompt_save_qa_cancel/yes/no**
  - 履歴保存確認ダイアログでキャンセル/はい/いいえを選んだ場合の挙動をテストします。
- **test_save_qa_history_no_history**
  - 履歴が空のとき、保存処理がスキップされるかをテストします。
- **test_ask_save_format_cancel**
  - 保存形式選択ダイアログでキャンセルした場合の挙動をテストします。
- **test_save_qa_history_json_cancel/markdown_cancel**
  - 保存ダイアログでキャンセルした場合、保存処理が中断されるかをテストします。
- **test_save_qa_history_json_exception/markdown_exception**
  - 保存時にファイル書き込みエラーが発生した場合、エラーダイアログが表示されるかをテストします。
- **test_save_qa_history_both_success**
  - 履歴をJSONとMarkdown両方で保存する場合、両方のファイルが正しく作成されるかをテストします。
- **test_save_qa_history_md_image_copy_error**
  - 画像付き履歴の保存時、画像コピーでエラーが発生した場合の挙動をテストします。
- **test_select_image_open_error**
  - 画像ファイルの読み込みでエラーが発生した場合、エラーダイアログが表示され、画像情報がリセットされるかをテストします。
- **test_update_image_preview_error**
  - プレビュー画像の生成でエラーが発生した場合、プレビュー欄にエラーメッセージが表示されるかをテストします。

---

### claude_tk/test_claude_tk_app_multi.py のテスト関数解説

- **test_markdown_to_text_basic**
  - Markdown形式のテキストが正しく変換されるかをテストします。
- **test_center_window**
  - ウィンドウの中央寄せ処理で例外が発生しないかをテストします。
- **test_update_history_display_empty/with_history**
  - 履歴が空/履歴ありの場合に、履歴表示が正しく行われるかをテストします。
- **test_send_question_empty**
  - 質問欄が空のまま送信しようとした場合、警告ダイアログが表示されるかをテストします。
- **test_send_question_api_error**
  - 質問送信時にAPIエラーが発生した場合、エラーダイアログが表示されるかをテストします。
- **test_clear_conversation**
  - 履歴クリア時、履歴がリセットされ、表示も空になるかをテストします。
- **test_save_conversation_history_json/markdown**
  - 履歴をJSON/Markdown形式で保存した場合、ファイルが正しく作成されるかをテストします。
- **test_ask_save_format_cancel**
  - 保存形式選択ダイアログでキャンセルした場合の挙動をテストします。
- **test_prompt_save_conversation_cancel/yes/no**
  - 履歴保存確認ダイアログでキャンセル/はい/いいえを選んだ場合の挙動をテストします。
- **test_exit_application**
  - アプリ終了時に保存確認ダイアログが出て、OKならウィンドウが閉じるかをテストします。
- **test_resume_conversation/test_resume_conversation_invalid**
  - 履歴ファイルの復元が正常/不正な場合の挙動をテストします。

---

### claude_tk/test_claude_tk_app_multi_image.py のテスト関数解説

- **test_markdown_to_text_basic**
  - Markdown形式のテキストが正しく変換されるかをテストします。
- **test_get_mime_type**
  - 画像ファイルの拡張子からMIMEタイプが正しく判定されるかをテストします。
- **test_save_conversation_history_json/markdown/both**
  - 会話履歴をJSON（ZIP）形式、Markdown（ZIP）形式、両方で保存した場合に、ファイルが正しく作成されるかをテストします。
  - 画像付き履歴も含めて保存できるかを確認します。
  - 保存完了時のポップアップ（messagebox.showinfo）がテスト中に表示されないようpatchしています。
- **test_save_conversation_history_save_type_none/no_conversation**
  - 保存形式が選択されなかった場合や、履歴が空の場合に保存処理がスキップされるかをテストします。
- **test_ask_save_format_options**
  - 保存形式選択ダイアログで「markdown」「json」「both」「キャンセル」など各選択肢を選んだ場合の挙動をテストします。
- **test_save_conversation_history_zip_error/markdown_error**
  - 保存時にZIPファイル作成でエラーが発生した場合、エラーダイアログが表示されるかをテストします。
- **test_update_history_display_no_error**
  - 履歴が空でも履歴表示の更新でエラーが出ないかをテストします。
- **test_prompt_save_conversation_cancel/yes/no**
  - 履歴保存確認ダイアログでキャンセル/はい/いいえを選んだ場合の挙動をテストします。
- **test_resume_conversation_json_import**
  - ZIPファイルから会話履歴（JSON）が正しく復元されるかをテストします。
- **test_attach_image_cancel**
  - 画像添付ダイアログでキャンセルした場合、画像パスがセットされないかをテストします。
- **test_attach_image_error**
  - 画像添付時に画像ファイルの読み込みでエラーが発生した場合、エラーダイアログが表示されるかをテストします。
- **test_remove_image**
  - 添付画像の削除ボタンで画像パスがリセットされるかをテストします。
- **test_clear_conversation_empty/confirm_yes/confirm_no**
  - 履歴クリア時、履歴が空/確認ダイアログで「はい」/「いいえ」を選んだ場合の挙動をテストします。
- **test_update_history_display_image_error**
  - 履歴表示時、画像の読み込みでエラーが発生しても例外にならないかをテストします。
- **test_send_question_empty**
  - 質問欄が空のまま送信しようとした場合、警告ダイアログが表示されるかをテストします。
- **test_send_question_api_error**
  - 質問送信時にAPIエラーが発生した場合、エラーダイアログが表示されるかをテストします。
- **test_resume_conversation_no_json/invalid_conversation/invalid_message**
  - ZIPファイルにJSONがない/不正な形式/不正なメッセージの場合、エラーダイアログが表示されるかをテストします。

---

## まとめ

- ユニットテストは、アプリの品質を保つためにとても重要です。
- テストの実行やカバレージの確認は、コマンド一つで簡単にできます。
- テストコードを読むことで、アプリの使い方や想定されるエラー処理も理解できます。

困ったときはこのドキュメントを見返してみてください！ 