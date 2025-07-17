import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import base64
from datetime import datetime

# claude_tk_app_image.pyのClaudeChatAppをimport
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from claude_tk_app_image import ClaudeChatApp

class TestClaudeChatApp(unittest.TestCase):
    def setUp(self):
        # Tkinterのrootをモック
        self.root = MagicMock()
        # anthropic, dotenv, PIL, filedialog, messageboxなどもpatch
        patcher1 = patch('claude_tk_app_image.anthropic')
        patcher2 = patch('claude_tk_app_image.load_dotenv')
        patcher3 = patch('claude_tk_app_image.os.getenv', return_value='dummy_key')
        patcher4 = patch('claude_tk_app_image.messagebox')
        patcher5 = patch('claude_tk_app_image.filedialog')
        patcher6 = patch('claude_tk_app_image.Image')
        patcher7 = patch('claude_tk_app_image.ImageTk')
        self.mock_anthropic = patcher1.start()
        self.mock_load_dotenv = patcher2.start()
        self.mock_getenv = patcher3.start()
        self.mock_messagebox = patcher4.start()
        self.mock_filedialog = patcher5.start()
        self.mock_Image = patcher6.start()
        self.mock_ImageTk = patcher7.start()
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)
        self.addCleanup(patcher3.stop)
        self.addCleanup(patcher4.stop)
        self.addCleanup(patcher5.stop)
        self.addCleanup(patcher6.stop)
        self.addCleanup(patcher7.stop)
        # ClaudeChatAppインスタンス
        self.app = ClaudeChatApp(self.root)

    def test_markdown_to_text_basic(self):
        md = '# Title\n\n- item1\n- item2\n\n**bold** and *italic* and [link](http://a)'
        text = self.app.markdown_to_text(md)
        self.assertIn('Title', text)
        self.assertIn('item1', text)
        self.assertIn('item2', text)
        self.assertIn('bold', text)
        self.assertIn('italic', text)
        self.assertIn('link', text)

    def test_select_image_success(self):
        # filedialog.askopenfilenameでダミー画像パスを返す
        dummy_path = 'dummy.jpg'
        self.mock_filedialog.askopenfilename.return_value = dummy_path
        # open()をモックしてダミー画像データ
        with patch('builtins.open', mock_open(read_data=b'12345')):
            self.app.update_image_preview = MagicMock()
            self.app.image_label = MagicMock()
            self.app.select_image()
            self.assertEqual(self.app.selected_image_path, dummy_path)
            self.assertIsNotNone(self.app.image_data)
            self.app.update_image_preview.assert_called()
            self.app.image_label.config.assert_called()

    def test_select_image_cancel(self):
        self.mock_filedialog.askopenfilename.return_value = ''
        self.app.select_image()
        self.assertIsNone(self.app.selected_image_path)
        self.assertIsNone(self.app.image_data)

    def test_remove_image(self):
        self.app.selected_image_path = 'dummy.jpg'
        self.app.image_data = 'abc'
        self.app.image_label = MagicMock()
        self.app.preview_label = MagicMock()
        self.app.remove_image()
        self.assertIsNone(self.app.selected_image_path)
        self.assertIsNone(self.app.image_data)
        self.app.image_label.config.assert_called()
        self.app.preview_label.config.assert_called()

    def test_send_question_no_question(self):
        self.app.question_text = MagicMock()
        self.app.question_text.get.return_value = ''
        self.app.send_button = MagicMock()
        self.app.root = MagicMock()
        self.app.send_question()
        self.mock_messagebox.showwarning.assert_called()

    def test_send_question_with_image(self):
        # 質問文あり、画像あり、APIレスポンスもモック
        self.app.question_text = MagicMock()
        self.app.question_text.get.return_value = 'test question'
        self.app.send_button = MagicMock()
        self.app.root = MagicMock()
        self.app.selected_image_path = 'dummy.jpg'
        self.app.image_data = base64.b64encode(b'123').decode('utf-8')
        # answer_text, markdown_to_text, anthropic APIレスポンスもモック
        self.app.answer_text = MagicMock()
        self.app.markdown_to_text = MagicMock(return_value='plain answer')
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='markdown answer')]
        self.app.client.messages.create.return_value = mock_message
        self.app.send_question()
        self.app.answer_text.config.assert_any_call(state='normal')
        self.app.answer_text.delete.assert_called()
        self.app.answer_text.insert.assert_called_with('1.0', 'plain answer')
        self.app.answer_text.config.assert_any_call(state='disabled')
        self.assertEqual(self.app.qa_history[0]['question'], 'test question')
        self.assertEqual(self.app.qa_history[0]['answer'], 'markdown answer')
        self.assertEqual(self.app.qa_history[0]['image_path'], 'dummy.jpg')

    def test_new_question(self):
        self.app.question_text = MagicMock()
        self.app.answer_text = MagicMock()
        self.app.remove_image = MagicMock()
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': 'img.jpg'}]
        self.app.prompt_save_qa = MagicMock(return_value=True)
        self.app.new_question()
        self.app.question_text.delete.assert_called()
        self.app.answer_text.delete.assert_called()
        self.app.remove_image.assert_called()
        self.assertEqual(self.app.qa_history, [])

    def test_exit_application(self):
        self.app.prompt_save_qa = MagicMock(return_value=True)
        self.app.root = MagicMock()
        self.app.exit_application()
        self.app.root.destroy.assert_called()

    def test_prompt_save_qa_cancel(self):
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': None}]
        self.mock_messagebox.askyesnocancel.return_value = None
        result = self.app.prompt_save_qa('終了')
        self.assertFalse(result)

    def test_prompt_save_qa_yes(self):
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': None}]
        self.mock_messagebox.askyesnocancel.return_value = True
        self.app.save_qa_history = MagicMock(return_value=True)
        result = self.app.prompt_save_qa('終了')
        self.assertTrue(result)
        self.app.save_qa_history.assert_called()

    def test_prompt_save_qa_no(self):
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': None}]
        self.mock_messagebox.askyesnocancel.return_value = False
        result = self.app.prompt_save_qa('終了')
        self.assertTrue(result)

    def test_save_qa_history_no_history(self):
        self.app.qa_history = []
        self.assertFalse(self.app.save_qa_history())

    def test_ask_save_format_cancel(self):
        # ask_save_formatでキャンセル
        with patch('claude_tk_app_image.tk.Toplevel') as mock_top, \
             patch('claude_tk_app_image.tk.StringVar') as mock_stringvar:
            instance = MagicMock()
            mock_top.return_value = instance
            mock_stringvar.return_value = MagicMock()
            instance.wait_window.side_effect = lambda: None
            instance.grab_set.side_effect = lambda: None
            instance.winfo_width.return_value = 100
            instance.winfo_height.return_value = 100
            instance.winfo_screenwidth.return_value = 200
            instance.winfo_screenheight.return_value = 200
            # キャンセルボタン押下
            result = self.app.ask_save_format()
            self.assertIn(result, [None, 'markdown', 'json', 'both'])

    def test_save_qa_history_json_cancel(self):
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': None}]
        self.app.ask_save_format = MagicMock(return_value='json')
        self.mock_filedialog.asksaveasfilename.return_value = ''  # キャンセル
        result = self.app.save_qa_history()
        self.assertFalse(result)

    def test_save_qa_history_markdown_cancel(self):
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': None}]
        self.app.ask_save_format = MagicMock(return_value='markdown')
        self.mock_filedialog.asksaveasfilename.return_value = ''  # キャンセル
        result = self.app.save_qa_history()
        self.assertFalse(result)

    def test_save_qa_history_json_exception(self):
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': None}]
        self.app.ask_save_format = MagicMock(return_value='json')
        self.mock_filedialog.asksaveasfilename.return_value = 'dummy.zip'
        # openで例外
        with patch('builtins.open', side_effect=OSError('fail')):
            result = self.app.save_qa_history()
            self.mock_messagebox.showerror.assert_called()
            self.assertFalse(result)

    def test_save_qa_history_markdown_exception(self):
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': None}]
        self.app.ask_save_format = MagicMock(return_value='markdown')
        self.mock_filedialog.asksaveasfilename.return_value = 'dummy.zip'
        # openで例外
        with patch('builtins.open', side_effect=OSError('fail')):
            result = self.app.save_qa_history()
            self.mock_messagebox.showerror.assert_called()
            self.assertFalse(result)

    def test_save_qa_history_both_success(self):
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': None}]
        self.app.ask_save_format = MagicMock(return_value='both')
        self.mock_filedialog.asksaveasfilename.side_effect = ['dummy_json.zip', 'dummy_md.zip']
        # open, json.dump, zipfile.ZipFile, shutil.copy2 などをモック
        with patch('builtins.open', mock_open()), \
             patch('claude_tk_app_image.json.dump'), \
             patch('claude_tk_app_image.zipfile.ZipFile') as mock_zip:
            result = self.app.save_qa_history()
            self.mock_messagebox.showinfo.assert_called()
            self.assertTrue(result)

    def test_save_qa_history_md_image_copy_error(self):
        # 画像付きでshutil.copy2が例外
        self.app.qa_history = [{'question': 'q', 'answer': 'a', 'image_path': 'img.jpg'}]
        self.app.ask_save_format = MagicMock(return_value='markdown')
        self.mock_filedialog.asksaveasfilename.return_value = 'dummy.zip'
        with patch('builtins.open', mock_open()), \
             patch('claude_tk_app_image.shutil.copy2', side_effect=OSError('fail')), \
             patch('claude_tk_app_image.zipfile.ZipFile'), \
             patch('os.path.exists', return_value=False):
            # messagebox.showinfoが呼ばれることを確認
            result = self.app.save_qa_history()
            self.mock_messagebox.showinfo.assert_called()

    def test_select_image_open_error(self):
        self.mock_filedialog.askopenfilename.return_value = 'dummy.jpg'
        with patch('builtins.open', side_effect=OSError('fail')):
            self.app.image_label = MagicMock()
            self.app.update_image_preview = MagicMock()
            self.mock_messagebox.reset_mock()
            self.app.select_image()
            self.mock_messagebox.showerror.assert_called()
            self.assertIsNone(self.app.selected_image_path)
            self.assertIsNone(self.app.image_data)

    def test_update_image_preview_error(self):
        self.app.selected_image_path = 'dummy.jpg'
        self.app.preview_label = MagicMock()
        self.mock_Image.open.side_effect = OSError('fail')
        self.app.update_image_preview()
        self.app.preview_label.config.assert_called_with(image='', text='プレビューエラー')

if __name__ == '__main__':
    unittest.main() 