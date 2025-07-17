import unittest
from unittest.mock import patch, MagicMock, mock_open
import tkinter as tk
import os
from datetime import datetime

# テスト対象のモジュールをインポート
import claude_tk.claude_tk_app_simple as app_simple

class TestClaudeChatApp(unittest.TestCase):
    def setUp(self):
        # Tkinterのrootを作成（withdrawで非表示）
        self.root = tk.Tk()
        self.root.withdraw()
        # APIキーのモック
        patcher = patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy_key"})
        patcher.start()
        self.addCleanup(patcher.stop)
        # anthropicクライアントのモック
        anthropic_patcher = patch("claude_tk.claude_tk_app_simple.anthropic.Anthropic", autospec=True)
        self.mock_anthropic = anthropic_patcher.start()
        self.addCleanup(anthropic_patcher.stop)
        # インスタンス作成
        self.app = app_simple.ClaudeChatApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_markdown_to_text_basic(self):
        md = "# 見出し\n本文\n- 項目1\n- 項目2\n**太字**と*斜体*\n[リンク](http://example.com)"
        text = self.app.markdown_to_text(md)
        self.assertIn("見出し", text)
        self.assertIn("本文", text)
        self.assertIn("・項目1", text)
        self.assertIn("・項目2", text)
        self.assertIn("太字", text)
        self.assertIn("斜体", text)
        self.assertIn("リンク", text)

    def test_center_window(self):
        # 例外が出ないことを確認
        try:
            self.app.center_window()
        except Exception as e:
            self.fail(f"center_window() raised Exception: {e}")

    def test_setup_ui(self):
        # 既にsetUpで呼ばれているが、再度呼んでも例外が出ないこと
        try:
            self.app.setup_ui()
        except Exception as e:
            self.fail(f"setup_ui() raised Exception: {e}")

    @patch("tkinter.messagebox.showwarning")
    def test_send_question_empty(self, mock_warn):
        self.app.question_text.delete("1.0", tk.END)
        self.app.send_question()
        mock_warn.assert_called_once()

    @patch("tkinter.messagebox.showerror")
    def test_send_question_api_error(self, mock_error):
        # APIクライアントのmessages.createで例外を発生させる
        self.app.question_text.insert("1.0", "テスト質問")
        self.app.client.messages = MagicMock()
        self.app.client.messages.create.side_effect = Exception("API error")
        self.app.send_question()
        mock_error.assert_called_once()

    @patch("tkinter.messagebox.showinfo")
    @patch("tkinter.filedialog.asksaveasfilename", return_value="/tmp/test.json")
    @patch("builtins.open", new_callable=mock_open)
    @patch.object(app_simple.ClaudeChatApp, "ask_save_format", return_value="json")
    def test_save_conversation_history_json(self, mock_format, mock_openfile, mock_dialog, mock_info):
        q, a = "Q", "A"
        result = self.app.save_conversation_history(q, a)
        self.assertTrue(result)
        mock_openfile.assert_called_once()
        mock_info.assert_called_once()

    @patch("tkinter.messagebox.showinfo")
    @patch("tkinter.filedialog.asksaveasfilename", return_value="/tmp/test.md")
    @patch("builtins.open", new_callable=mock_open)
    @patch.object(app_simple.ClaudeChatApp, "ask_save_format", return_value="markdown")
    def test_save_conversation_history_markdown(self, mock_format, mock_openfile, mock_dialog, mock_info):
        q, a = "Q", "A"
        result = self.app.save_conversation_history(q, a)
        self.assertTrue(result)
        mock_openfile.assert_called_once()
        mock_info.assert_called_once()

    @patch("tkinter.messagebox.askyesnocancel", return_value=True)
    @patch.object(app_simple.ClaudeChatApp, "save_conversation_history", return_value=True)
    def test_prompt_save_conversation_yes(self, mock_save, mock_ask):
        self.app.question_text.insert("1.0", "Q")
        self.app.answer_text.config(state=tk.NORMAL)
        self.app.answer_text.insert("1.0", "A")
        self.app.answer_text.config(state=tk.DISABLED)
        result = self.app.prompt_save_conversation("テスト")
        self.assertTrue(result)
        mock_save.assert_called_once()

    @patch("tkinter.messagebox.askyesnocancel", return_value=False)
    def test_prompt_save_conversation_no(self, mock_ask):
        self.app.question_text.insert("1.0", "Q")
        self.app.answer_text.config(state=tk.NORMAL)
        self.app.answer_text.insert("1.0", "A")
        self.app.answer_text.config(state=tk.DISABLED)
        result = self.app.prompt_save_conversation("テスト")
        self.assertTrue(result)

    @patch("tkinter.messagebox.askyesnocancel", return_value=None)
    def test_prompt_save_conversation_cancel(self, mock_ask):
        self.app.question_text.insert("1.0", "Q")
        self.app.answer_text.config(state=tk.NORMAL)
        self.app.answer_text.insert("1.0", "A")
        self.app.answer_text.config(state=tk.DISABLED)
        result = self.app.prompt_save_conversation("テスト")
        self.assertFalse(result)

    @patch.object(app_simple.ClaudeChatApp, "prompt_save_conversation", return_value=True)
    def test_new_question(self, mock_prompt):
        self.app.question_text.insert("1.0", "Q")
        self.app.answer_text.config(state=tk.NORMAL)
        self.app.answer_text.insert("1.0", "A")
        self.app.answer_text.config(state=tk.DISABLED)
        self.app.new_question()
        self.assertEqual(self.app.question_text.get("1.0", tk.END).strip(), "")
        self.assertEqual(self.app.answer_text.get("1.0", tk.END).strip(), "")

    @patch.object(app_simple.ClaudeChatApp, "prompt_save_conversation", return_value=True)
    def test_on_exit(self, mock_prompt):
        # destroyが呼ばれることを確認
        with patch.object(self.root, "destroy") as mock_destroy:
            self.app.on_exit()
            mock_destroy.assert_called_once()

    def test_ask_save_format_cancel(self):
        # ask_save_formatはUIダイアログなので、キャンセル時の値だけテスト
        with patch("tkinter.Toplevel") as mock_top:
            instance = MagicMock()
            instance.wait_window.side_effect = lambda: None
            instance.winfo_width.return_value = 320
            instance.winfo_height.return_value = 160
            instance.winfo_screenwidth.return_value = 1920
            instance.winfo_screenheight.return_value = 1080
            mock_top.return_value = instance
            # キャンセルボタンを押した場合
            with patch("tkinter.StringVar", return_value=MagicMock(get=lambda: None)):
                result = self.app.ask_save_format()
                self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main() 