import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import shutil
import json
from claude_tk.claude_tk_app_multi_image import ClaudeChatApp

class TestClaudeChatApp(unittest.TestCase):
    def setUp(self):
        # Tkinter rootをモック
        self.root = MagicMock()
        # anthropicクライアントもモック
        patcher = patch('claude_tk.claude_tk_app_multi_image.anthropic.Anthropic')
        self.addCleanup(patcher.stop)
        self.mock_anthropic = patcher.start()
        # .envロードもモック
        patcher_env = patch('claude_tk.claude_tk_app_multi_image.load_dotenv')
        self.addCleanup(patcher_env.stop)
        patcher_env.start()
        # APIキー取得もモック
        patcher_getenv = patch('claude_tk.claude_tk_app_multi_image.os.getenv', return_value='dummy-key')
        self.addCleanup(patcher_getenv.stop)
        patcher_getenv.start()
        self.app = ClaudeChatApp(self.root)

    def test_markdown_to_text_basic(self):
        md = '# Title\n\n- item1\n- item2\n**bold** and *italic*\n[link](http://a)'
        text = self.app.markdown_to_text(md)
        self.assertIn('Title', text)
        self.assertIn('item1', text)
        self.assertIn('bold', text)
        self.assertIn('italic', text)
        self.assertNotIn('[link]', text)

    def test_get_mime_type(self):
        self.assertEqual(self.app.get_mime_type('a.jpg'), 'image/jpeg')
        self.assertEqual(self.app.get_mime_type('a.jpeg'), 'image/jpeg')
        self.assertEqual(self.app.get_mime_type('a.png'), 'image/png')
        self.assertEqual(self.app.get_mime_type('a.bmp'), 'image/bmp')
        self.assertEqual(self.app.get_mime_type('a.gif'), 'image/gif')
        self.assertEqual(self.app.get_mime_type('a.unknown'), 'application/octet-stream')

    @patch('tkinter.filedialog.asksaveasfilename', return_value=None)
    def test_save_conversation_history_empty(self, mock_save):
        self.app.conversation_history = []
        self.assertFalse(self.app.save_conversation_history())

    def test_update_history_display_no_error(self):
        # 履歴が空でもエラーにならない
        self.app.conversation_history = []
        self.app.history_text = MagicMock()
        self.app.history_images = []
        self.app.history_text.config = MagicMock()
        self.app.history_text.delete = MagicMock()
        self.app.history_text.insert = MagicMock()
        self.app.history_text.tag_config = MagicMock()
        self.app.history_text.see = MagicMock()
        self.app.update_history_display()

    def test_prompt_save_conversation_cancel(self):
        self.app.conversation_history = [{'role': 'user', 'content': 'dummy'}]  # 履歴が空でない場合
        with patch('tkinter.messagebox.askyesnocancel', return_value=None):
            self.assertFalse(self.app.prompt_save_conversation('テスト'))

    def test_prompt_save_conversation_yes(self):
        with patch('tkinter.messagebox.askyesnocancel', return_value=True), \
             patch.object(self.app, 'save_conversation_history', return_value=True):
            self.assertTrue(self.app.prompt_save_conversation('テスト'))

    def test_prompt_save_conversation_no(self):
        with patch('tkinter.messagebox.askyesnocancel', return_value=False):
            self.assertTrue(self.app.prompt_save_conversation('テスト'))

    def test_resume_conversation_json_import(self):
        # ZIPファイルの内容を一時作成してテスト
        with tempfile.TemporaryDirectory() as tmpdir:
            json_data = {
                'conversation': [
                    {'role': 'user', 'content': 'Q1'},
                    {'role': 'assistant', 'content': 'A1'}
                ]
            }
            json_path = os.path.join(tmpdir, 'test.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f)
            zip_path = os.path.join(tmpdir, 'test.zip')
            import zipfile
            with zipfile.ZipFile(zip_path, 'w') as z:
                z.write(json_path, arcname='test.json')
            # filedialog.askopenfilenameをモック
            with patch('tkinter.filedialog.askopenfilename', return_value=zip_path), \
                 patch('tkinter.messagebox.showinfo'), \
                 patch('tkinter.messagebox.showerror'):
                self.app.update_history_display = MagicMock()
                self.app.resume_conversation()
                self.assertEqual(len(self.app.conversation_history), 2)
                self.assertEqual(self.app.conversation_history[0]['role'], 'user')
                self.assertEqual(self.app.conversation_history[1]['role'], 'assistant')

    def test_ask_save_format_ok(self):
        # ask_save_formatのOK動作をテスト
        with patch('tkinter.Toplevel'), \
             patch('tkinter.StringVar', return_value=MagicMock(get=lambda: 'markdown')):
            # win.wait_window()を即returnに
            with patch('tkinter.Toplevel.wait_window', return_value=None):
                self.assertIn(self.app.ask_save_format(), ['markdown', 'zip', 'both', None])

    def test_attach_image_cancel(self):
        with patch('tkinter.filedialog.askopenfilename', return_value=''):
            self.app.attach_image()
            self.assertIsNone(self.app.attached_image_path)

    def test_attach_image_error(self):
        with patch('tkinter.filedialog.askopenfilename', return_value='dummy.png'), \
             patch('PIL.Image.open', side_effect=OSError('bad image')), \
             patch('tkinter.messagebox.showerror') as mock_err:
            self.app.attach_image()
            self.assertIsNone(self.app.attached_image_path)
            mock_err.assert_called()

    def test_remove_image(self):
        self.app.attached_image_path = 'dummy.png'
        self.app.image_preview_label = MagicMock()
        self.app.remove_image_button = MagicMock()
        self.app.remove_image()
        self.assertIsNone(self.app.attached_image_path)

    def test_clear_conversation_empty(self):
        self.app.conversation_history = []
        with patch.object(self.app, 'prompt_save_conversation', return_value=True), \
             patch('tkinter.messagebox.askyesno', return_value=True):
            self.app.history_text = MagicMock()
            self.app.question_text = MagicMock()
            self.app.remove_image = MagicMock()
            self.app.update_history_display = MagicMock()
            self.app.clear_conversation()
            self.app.update_history_display.assert_called()

    def test_clear_conversation_confirm_yes(self):
        self.app.conversation_history = [{'role': 'user', 'content': 'a'}]
        with patch.object(self.app, 'prompt_save_conversation', return_value=True), \
             patch('tkinter.messagebox.askyesno', return_value=True):
            self.app.history_text = MagicMock()
            self.app.question_text = MagicMock()
            self.app.remove_image = MagicMock()
            self.app.update_history_display = MagicMock()
            self.app.clear_conversation()
            self.app.update_history_display.assert_called()

    def test_clear_conversation_confirm_no(self):
        self.app.conversation_history = [{'role': 'user', 'content': 'a'}]
        with patch.object(self.app, 'prompt_save_conversation', return_value=True), \
             patch('tkinter.messagebox.askyesno', return_value=False):
            self.app.history_text = MagicMock()
            self.app.question_text = MagicMock()
            self.app.remove_image = MagicMock()
            self.app.update_history_display = MagicMock()
            self.app.clear_conversation()
            self.app.update_history_display.assert_not_called()

    def test_update_history_display_image_error(self):
        self.app.conversation_history = [
            {'role': 'user', 'content': 'q', 'image_path': 'bad.png'}
        ]
        self.app.history_text = MagicMock()
        self.app.history_images = []
        with patch('PIL.Image.open', side_effect=OSError('bad image')):
            self.app.update_history_display()
        # エラー時も例外にならないこと

    def test_send_question_empty(self):
        self.app.question_text = MagicMock(get=MagicMock(return_value='\n'))
        with patch('tkinter.messagebox.showwarning') as mock_warn:
            self.app.send_question()
            mock_warn.assert_called()

    def test_send_question_api_error(self):
        self.app.question_text = MagicMock(get=MagicMock(return_value='test'))
        self.app.send_button = MagicMock()
        self.app.root = MagicMock()
        self.app.remove_image = MagicMock()
        self.app.update_history_display = MagicMock()
        self.app.conversation_history = []
        self.app.client.messages.create = MagicMock(side_effect=Exception('api error'))
        with patch('tkinter.messagebox.showerror') as mock_err:
            self.app.send_question()
            mock_err.assert_called()

    def test_resume_conversation_no_json(self):
        import zipfile
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, 'test.zip')
            with zipfile.ZipFile(zip_path, 'w') as z:
                z.writestr('dummy.txt', 'no json')
            with patch('tkinter.filedialog.askopenfilename', return_value=zip_path), \
                 patch('tkinter.messagebox.showerror') as mock_err:
                self.app.resume_conversation()
                mock_err.assert_called()

    def test_resume_conversation_invalid_conversation(self):
        import zipfile
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, 'test.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({'conversation': {}}, f)
            zip_path = os.path.join(tmpdir, 'test.zip')
            with zipfile.ZipFile(zip_path, 'w') as z:
                z.write(json_path, arcname='test.json')
            with patch('tkinter.filedialog.askopenfilename', return_value=zip_path), \
                 patch('tkinter.messagebox.showerror') as mock_err:
                self.app.resume_conversation()
                mock_err.assert_called()

    def test_resume_conversation_invalid_message(self):
        import zipfile
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, 'test.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({'conversation': [{'role': 'user'}]}, f)
            zip_path = os.path.join(tmpdir, 'test.zip')
            with zipfile.ZipFile(zip_path, 'w') as z:
                z.write(json_path, arcname='test.json')
            with patch('tkinter.filedialog.askopenfilename', return_value=zip_path), \
                 patch('tkinter.messagebox.showerror') as mock_err:
                self.app.resume_conversation()
                mock_err.assert_called()

    def test_save_conversation_history_json(self):
        self.app.conversation_history = [
            {"role": "user", "content": "Q", "image_path": __file__},
            {"role": "assistant", "content": "A", "markdown": "A_md"}
        ]
        with patch.object(self.app, 'ask_save_format', return_value="json"), \
             patch('tkinter.filedialog.asksaveasfilename', return_value="/tmp/test.zip"), \
             patch('tempfile.TemporaryDirectory') as mock_tmpdir, \
             patch('shutil.copy2'), \
             patch('zipfile.ZipFile') as mock_zip, \
             patch('builtins.open', mock_open()), \
             patch('tkinter.messagebox.showinfo'):
            mock_tmpdir.return_value.__enter__.return_value = "/tmp/tmpdir"
            mock_tmpdir.return_value.__exit__.return_value = False
            self.assertTrue(self.app.save_conversation_history())
            mock_zip.assert_called()

    def test_save_conversation_history_markdown(self):
        self.app.conversation_history = [
            {"role": "user", "content": "Q", "image_path": __file__},
            {"role": "assistant", "content": "A", "markdown": "A_md"}
        ]
        with patch.object(self.app, 'ask_save_format', return_value="markdown"), \
             patch('tkinter.filedialog.asksaveasfilename', return_value="/tmp/test.zip"), \
             patch('tempfile.TemporaryDirectory') as mock_tmpdir, \
             patch('shutil.copy2'), \
             patch('zipfile.ZipFile') as mock_zip, \
             patch('builtins.open', mock_open()), \
             patch('tkinter.messagebox.showinfo'):
            mock_tmpdir.return_value.__enter__.return_value = "/tmp/tmpdir"
            mock_tmpdir.return_value.__exit__.return_value = False
            self.assertTrue(self.app.save_conversation_history())
            mock_zip.assert_called()

    def test_save_conversation_history_both(self):
        self.app.conversation_history = [
            {"role": "user", "content": "Q", "image_path": __file__},
            {"role": "assistant", "content": "A", "markdown": "A_md"}
        ]
        with patch.object(self.app, 'ask_save_format', return_value="both"), \
             patch('tkinter.filedialog.asksaveasfilename', side_effect=["/tmp/test1.zip", "/tmp/test2.zip"]), \
             patch('tempfile.TemporaryDirectory') as mock_tmpdir, \
             patch('shutil.copy2'), \
             patch('zipfile.ZipFile') as mock_zip, \
             patch('builtins.open', mock_open()), \
             patch('tkinter.messagebox.showinfo'):
            mock_tmpdir.return_value.__enter__.return_value = "/tmp/tmpdir"
            mock_tmpdir.return_value.__exit__.return_value = False
            self.assertTrue(self.app.save_conversation_history())
            self.assertGreaterEqual(mock_zip.call_count, 2)

    def test_save_conversation_history_save_type_none(self):
        self.app.conversation_history = [{"role": "user", "content": "Q"}]
        with patch.object(self.app, 'ask_save_format', return_value=None):
            self.assertFalse(self.app.save_conversation_history())

    def test_save_conversation_history_no_conversation(self):
        self.app.conversation_history = []
        self.assertFalse(self.app.save_conversation_history())

    def test_ask_save_format_options(self):
        # ask_save_formatの選択肢("markdown", "json", "both")をテスト
        for val in ["markdown", "json", "both", None]:
            with patch('tkinter.Toplevel'), \
                 patch('tkinter.StringVar', return_value=MagicMock(get=lambda: val)):
                with patch('tkinter.Toplevel.wait_window', return_value=None):
                    self.assertIn(self.app.ask_save_format(), ["markdown", "json", "both", None])

    def test_save_conversation_history_zip_error(self):
        self.app.conversation_history = [{"role": "user", "content": "Q", "image_path": __file__}]
        with patch.object(self.app, 'ask_save_format', return_value="json"), \
             patch('tkinter.filedialog.asksaveasfilename', return_value="/tmp/test.zip"), \
             patch('tempfile.TemporaryDirectory') as mock_tmpdir, \
             patch('shutil.copy2'), \
             patch('zipfile.ZipFile', side_effect=OSError("zip error")), \
             patch('builtins.open', mock_open()), \
             patch('tkinter.messagebox.showerror') as mock_err:
            mock_tmpdir.return_value.__enter__.return_value = "/tmp/tmpdir"
            mock_tmpdir.return_value.__exit__.return_value = False
            self.assertFalse(self.app.save_conversation_history())
            mock_err.assert_called()

    def test_save_conversation_history_markdown_error(self):
        self.app.conversation_history = [{"role": "user", "content": "Q", "image_path": __file__}]
        with patch.object(self.app, 'ask_save_format', return_value="markdown"), \
             patch('tkinter.filedialog.asksaveasfilename', return_value="/tmp/test.zip"), \
             patch('tempfile.TemporaryDirectory') as mock_tmpdir, \
             patch('shutil.copy2'), \
             patch('zipfile.ZipFile', side_effect=OSError("zip error")), \
             patch('builtins.open', mock_open()), \
             patch('tkinter.messagebox.showerror') as mock_err:
            mock_tmpdir.return_value.__enter__.return_value = "/tmp/tmpdir"
            mock_tmpdir.return_value.__exit__.return_value = False
            self.assertFalse(self.app.save_conversation_history())
            mock_err.assert_called()

if __name__ == '__main__':
    unittest.main() 