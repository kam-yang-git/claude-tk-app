import unittest
from unittest.mock import patch, MagicMock, mock_open
import tkinter as tk
import os

# claude_tk_app_multi.pyのClaudeChatAppをimport
from claude_tk.claude_tk_app_multi import ClaudeChatApp

class TestClaudeChatApp(unittest.TestCase):
    def setUp(self):
        # Tkinterのrootを作成（withdrawで非表示）
        self.root = tk.Tk()
        self.root.withdraw()
        # APIキーのmock
        patcher_env = patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy_key"})
        patcher_env.start()
        self.addCleanup(patcher_env.stop)
        # anthropicクライアントのmock
        patcher_client = patch("claude_tk.claude_tk_app_multi.anthropic.Anthropic", autospec=True)
        self.mock_client_class = patcher_client.start()
        self.addCleanup(patcher_client.stop)
        self.app = ClaudeChatApp(self.root)
        # client.messagesをMagicMockに差し替え
        self.app.client.messages = MagicMock()

    def tearDown(self):
        self.root.destroy()

    def test_markdown_to_text_basic(self):
        md = "# タイトル\n本文\n- 項目1\n- 項目2\n**太字**と*斜体*"
        text = self.app.markdown_to_text(md)
        self.assertIn("タイトル", text)
        self.assertIn("本文", text)
        self.assertIn("・項目1", text)
        self.assertIn("・項目2", text)
        self.assertIn("太字", text)
        self.assertIn("斜体", text)

    def test_center_window(self):
        # 例外が出ないことを確認
        self.app.center_window()

    def test_update_history_display_empty(self):
        self.app.conversation_history = []
        self.app.update_history_display()
        content = self.app.history_text.get("1.0", tk.END)
        self.assertEqual(content.strip(), "")

    def test_update_history_display_with_history(self):
        self.app.conversation_history = [
            {"role": "user", "content": "質問1"},
            {"role": "assistant", "content": "回答1"},
            {"role": "user", "content": "質問2"},
            {"role": "assistant", "content": "回答2"},
        ]
        self.app.update_history_display()
        content = self.app.history_text.get("1.0", tk.END)
        self.assertIn("【質問 1】", content)
        self.assertIn("【回答 1】", content)
        self.assertIn("【質問 2】", content)
        self.assertIn("【回答 2】", content)

    @patch("claude_tk.claude_tk_app_multi.messagebox.showwarning")
    def test_send_question_empty(self, mock_warn):
        self.app.question_text.delete("1.0", tk.END)
        self.app.send_question()
        mock_warn.assert_called_once()

    @patch("claude_tk.claude_tk_app_multi.messagebox.showerror")
    def test_send_question_api_error(self, mock_error):
        self.app.question_text.insert("1.0", "テスト質問")
        # APIクライアントのmessages.createで例外を発生させる
        self.app.client.messages.create.side_effect = Exception("API error")
        self.app.send_question()
        mock_error.assert_called_once()

    @patch("claude_tk.claude_tk_app_multi.messagebox.askyesno", return_value=True)
    def test_clear_conversation(self, mock_ask):
        self.app.conversation_history = [
            {"role": "user", "content": "質問1"},
            {"role": "assistant", "content": "回答1"},
        ]
        with patch.object(self.app, "prompt_save_conversation", return_value=True):
            self.app.clear_conversation()
        self.assertEqual(self.app.conversation_history, [])
        content = self.app.history_text.get("1.0", tk.END)
        self.assertEqual(content.strip(), "")

    @patch("claude_tk.claude_tk_app_multi.filedialog.asksaveasfilename", return_value="/tmp/test.json")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_conversation_history_json(self, mock_file, mock_dialog):
        self.app.conversation_history = [
            {"role": "user", "content": "質問1"},
            {"role": "assistant", "content": "回答1", "markdown": "回答1md"},
        ]
        with patch.object(self.app, "ask_save_format", return_value="json"):
            with patch("claude_tk.claude_tk_app_multi.messagebox.showinfo") as mock_info:
                result = self.app.save_conversation_history()
                self.assertTrue(result)
                mock_info.assert_called_once()
                mock_file.assert_called()

    @patch("claude_tk.claude_tk_app_multi.filedialog.asksaveasfilename", return_value="/tmp/test.md")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_conversation_history_markdown(self, mock_file, mock_dialog):
        self.app.conversation_history = [
            {"role": "user", "content": "質問1"},
            {"role": "assistant", "content": "回答1", "markdown": "回答1md"},
        ]
        with patch.object(self.app, "ask_save_format", return_value="markdown"):
            with patch("claude_tk.claude_tk_app_multi.messagebox.showinfo") as mock_info:
                result = self.app.save_conversation_history()
                self.assertTrue(result)
                mock_info.assert_called_once()
                mock_file.assert_called()

    def test_ask_save_format_cancel(self):
        # ask_save_formatはUIダイアログなので、ここでは呼び出しのみ
        # キャンセル時はNoneを返す想定
        with patch("claude_tk.claude_tk_app_multi.tk.Toplevel") as mock_top:
            instance = mock_top.return_value
            instance.wait_window.side_effect = lambda: None
            instance.destroy.side_effect = lambda: None
            # 返り値をNoneにするため内部変数を直接操作
            with patch("claude_tk.claude_tk_app_multi.ttk.Button"):
                with patch("claude_tk.claude_tk_app_multi.ttk.Radiobutton"):
                    with patch("claude_tk.claude_tk_app_multi.ttk.Label"):
                        with patch("claude_tk.claude_tk_app_multi.ttk.Frame"):
                            result = self.app.ask_save_format()
                            self.assertIsNone(result)

    @patch("claude_tk.claude_tk_app_multi.messagebox.askyesnocancel", return_value=None)
    def test_prompt_save_conversation_cancel(self, mock_ask):
        self.app.conversation_history = [{"role": "user", "content": "質問1"}]
        result = self.app.prompt_save_conversation("テスト")
        self.assertFalse(result)

    @patch("claude_tk.claude_tk_app_multi.messagebox.askyesnocancel", return_value=True)
    def test_prompt_save_conversation_yes(self, mock_ask):
        self.app.conversation_history = [{"role": "user", "content": "質問1"}]
        with patch.object(self.app, "save_conversation_history", return_value=True) as mock_save:
            result = self.app.prompt_save_conversation("テスト")
            self.assertTrue(result)
            mock_save.assert_called_once()

    @patch("claude_tk.claude_tk_app_multi.messagebox.askyesnocancel", return_value=False)
    def test_prompt_save_conversation_no(self, mock_ask):
        self.app.conversation_history = [{"role": "user", "content": "質問1"}]
        result = self.app.prompt_save_conversation("テスト")
        self.assertTrue(result)

    @patch("claude_tk.claude_tk_app_multi.messagebox.askyesnocancel", return_value=True)
    def test_exit_application(self, mock_ask):
        with patch.object(self.app, "save_conversation_history", return_value=True):
            with patch.object(self.root, "destroy") as mock_destroy:
                self.app.exit_application()
                mock_destroy.assert_called_once()

    @patch("claude_tk.claude_tk_app_multi.filedialog.askopenfilename", return_value="/tmp/test.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"conversation": [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "A"}]}')
    def test_resume_conversation(self, mock_file, mock_dialog):
        with patch("claude_tk.claude_tk_app_multi.messagebox.showinfo") as mock_info:
            self.app.resume_conversation()
            self.assertEqual(len(self.app.conversation_history), 2)
            self.assertEqual(self.app.conversation_history[0]["role"], "user")
            self.assertEqual(self.app.conversation_history[1]["role"], "assistant")
            mock_info.assert_called_once()

    @patch("claude_tk.claude_tk_app_multi.filedialog.askopenfilename", return_value="/tmp/test.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"invalid": 1}')
    def test_resume_conversation_invalid(self, mock_file, mock_dialog):
        with patch("claude_tk.claude_tk_app_multi.messagebox.showerror") as mock_error:
            self.app.resume_conversation()
            mock_error.assert_called_once()

if __name__ == "__main__":
    unittest.main() 