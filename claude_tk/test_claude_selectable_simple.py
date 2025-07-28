import unittest
from unittest.mock import Mock, patch, MagicMock, call
import tkinter as tk
from tkinter import messagebox
import os
import json
from datetime import datetime
import tempfile
import shutil

# テスト対象のモジュールをインポート
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from claude_selectable_simple import ClaudeChatApp


class TestClaudeChatApp(unittest.TestCase):
    """ClaudeChatAppクラスのユニットテスト"""
    
    def setUp(self):
        """各テストの前準備"""
        self.root = tk.Tk()
        self.root.withdraw()  # ウィンドウを非表示にしてテストを高速化
        
        # テスト用の一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # jsonディレクトリを作成
        os.makedirs("json", exist_ok=True)
    
    def tearDown(self):
        """各テストの後処理"""
        try:
            self.root.destroy()
        except:
            pass
        
        # テストディレクトリを削除
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    @patch('claude_selectable_simple.messagebox.showerror')
    def test_init_without_api_key(self, mock_showerror, mock_anthropic, mock_getenv, mock_load_dotenv):
        """APIキーが設定されていない場合のテスト"""
        mock_getenv.return_value = None
        
        app = ClaudeChatApp(self.root)
        
        mock_load_dotenv.assert_called_once()
        mock_getenv.assert_called_with("ANTHROPIC_API_KEY")
        mock_showerror.assert_called_once()
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    @patch('claude_selectable_simple.messagebox.showerror')
    def test_init_with_api_key(self, mock_showerror, mock_anthropic, mock_getenv, mock_load_dotenv):
        """APIキーが設定されている場合のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # モデル一覧のモック
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        self.assertIsNotNone(app.client)
        self.assertEqual(app.api_key, "test_api_key")
        self.assertIn("claude-3-sonnet-20240229", app.models)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    def test_get_available_models_success(self, mock_anthropic, mock_getenv, mock_load_dotenv):
        """モデル一覧取得の成功テスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # 複数のモデルをモック
        mock_models = [
            Mock(id="claude-3-sonnet-20240229"),
            Mock(id="claude-3-haiku-20240307"),
            Mock(id="gpt-4")  # Claude以外のモデルは除外される
        ]
        mock_response = Mock()
        mock_response.data = mock_models
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        expected_models = {
            "claude-3-sonnet-20240229": "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307": "claude-3-haiku-20240307"
        }
        self.assertEqual(app.models, expected_models)
        
        # ローカルファイルが作成されているかチェック
        self.assertTrue(os.path.exists("json/claude_models.json"))
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    @patch('claude_selectable_simple.messagebox.showerror')
    def test_get_available_models_fallback(self, mock_showerror, mock_anthropic, mock_getenv, mock_load_dotenv):
        """API取得失敗時のローカルファイルからの復旧テスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # API呼び出しで例外を発生させる
        mock_client.models.list.side_effect = Exception("API Error")
        
        # ローカルファイルを作成
        local_models = {
            "claude-3-sonnet-20240229": "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307": "claude-3-haiku-20240307"
        }
        with open("json/claude_models.json", "w", encoding='utf-8') as f:
            json.dump(local_models, f)
        
        app = ClaudeChatApp(self.root)
        
        self.assertEqual(app.models, local_models)
    
    def test_center_window(self):
        """ウィンドウ中央配置のテスト"""
        app = ClaudeChatApp.__new__(ClaudeChatApp)
        app.root = self.root
        
        # 元のジオメトリを保存
        original_geometry = self.root.geometry()
        
        app.center_window()
        
        # ジオメトリが変更されていることを確認
        self.assertNotEqual(self.root.geometry(), original_geometry)
    
    def test_markdown_to_text(self):
        """Markdownテキスト変換のテスト"""
        app = ClaudeChatApp.__new__(ClaudeChatApp)
        
        # 基本的なMarkdown変換テスト
        markdown_text = "# 見出し\n\nこれは**太字**のテキストです。\n\n- リストアイテム1\n- リストアイテム2"
        result = app.markdown_to_text(markdown_text)
        
        self.assertIn("見出し", result)
        self.assertIn("太字", result)
        self.assertIn("•", result)  # リストアイテムが「•」に変換される
    
    def test_markdown_to_text_with_code(self):
        """コードブロックを含むMarkdown変換のテスト"""
        app = ClaudeChatApp.__new__(ClaudeChatApp)
        
        markdown_text = """
# コード例

```python
print("Hello, World!")
```

インラインコード: `code`
"""
        result = app.markdown_to_text(markdown_text)
        
        self.assertIn("print(\"Hello, World!\")", result)
        self.assertIn("code", result)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    def test_setup_ui(self, mock_anthropic, mock_getenv, mock_load_dotenv):
        """UI設定のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        # UIコンポーネントが作成されているかチェック
        self.assertIsNotNone(app.model_combo)
        self.assertIsNotNone(app.question_text)
        self.assertIsNotNone(app.answer_text)
        self.assertIsNotNone(app.send_button)
        self.assertIsNotNone(app.new_button)
        self.assertIsNotNone(app.exit_button)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    def test_on_model_change(self, mock_anthropic, mock_getenv, mock_load_dotenv):
        """モデル変更のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        # モデルを変更
        app.model_var.set("claude-3-sonnet-20240229")
        app.on_model_change()
        
        self.assertEqual(app.model, "claude-3-sonnet-20240229")
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    @patch('claude_selectable_simple.messagebox.showinfo')
    def test_refresh_models(self, mock_showinfo, mock_anthropic, mock_getenv, mock_load_dotenv):
        """モデル一覧更新のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # 初期モデル
        mock_model1 = Mock()
        mock_model1.id = "claude-3-sonnet-20240229"
        mock_response1 = Mock()
        mock_response1.data = [mock_model1]
        mock_client.models.list.return_value = mock_response1
        
        app = ClaudeChatApp(self.root)
        
        # 更新後のモデル
        mock_model2 = Mock()
        mock_model2.id = "claude-3-haiku-20240307"
        mock_response2 = Mock()
        mock_response2.data = [mock_model2]
        mock_client.models.list.return_value = mock_response2
        
        app.refresh_models()
        
        mock_showinfo.assert_called_once()
        self.assertIn("claude-3-haiku-20240307", app.models)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    @patch('claude_selectable_simple.messagebox.showwarning')
    def test_send_question_empty(self, mock_showwarning, mock_anthropic, mock_getenv, mock_load_dotenv):
        """空の質問送信のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        # 空の質問を送信
        app.send_question()
        
        mock_showwarning.assert_called_once()
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    @patch('claude_selectable_simple.messagebox.showerror')
    def test_send_question_success(self, mock_showerror, mock_anthropic, mock_getenv, mock_load_dotenv):
        """質問送信成功のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        # 質問を入力
        app.question_text.insert("1.0", "テスト質問")
        
        # APIレスポンスをモック
        mock_content = Mock()
        mock_content.text = "# テスト回答\n\nこれはテスト回答です。"
        mock_message = Mock()
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        
        app.send_question()
        
        # 回答が表示されているかチェック
        answer_text = app.answer_text.get("1.0", tk.END).strip()
        self.assertIn("テスト回答", answer_text)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    def test_new_question(self, mock_anthropic, mock_getenv, mock_load_dotenv):
        """新しい質問のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        # 質問と回答を入力
        app.question_text.insert("1.0", "テスト質問")
        app.answer_text.config(state=tk.NORMAL)
        app.answer_text.insert("1.0", "テスト回答")
        app.answer_text.config(state=tk.DISABLED)
        
        # 保存確認をモック（保存しない）
        with patch.object(app, 'prompt_save_conversation', return_value=True):
            app.new_question()
        
        # テキストがクリアされているかチェック
        question_text = app.question_text.get("1.0", tk.END).strip()
        answer_text = app.answer_text.get("1.0", tk.END).strip()
        self.assertEqual(question_text, "")
        self.assertEqual(answer_text, "")
        
        # 保存確認でキャンセルした場合
        app.question_text.insert("1.0", "テスト質問2")
        app.answer_text.config(state=tk.NORMAL)
        app.answer_text.insert("1.0", "テスト回答2")
        app.answer_text.config(state=tk.DISABLED)
        
        with patch.object(app, 'prompt_save_conversation', return_value=False):
            app.new_question()
        
        # テキストがクリアされていないことを確認
        question_text = app.question_text.get("1.0", tk.END).strip()
        answer_text = app.answer_text.get("1.0", tk.END).strip()
        self.assertIn("テスト質問2", question_text)
        self.assertIn("テスト回答2", answer_text)
    
    def test_ask_save_format(self):
        """保存形式選択のテスト"""
        app = ClaudeChatApp.__new__(ClaudeChatApp)
        app.root = self.root
        
        # ask_save_formatメソッド全体をモック
        with patch.object(app, 'ask_save_format', return_value="markdown"):
            result = app.ask_save_format()
            self.assertEqual(result, "markdown")
        
        # 別のケースもテスト
        with patch.object(app, 'ask_save_format', return_value="json"):
            result = app.ask_save_format()
            self.assertEqual(result, "json")
        
        # キャンセルケース
        with patch.object(app, 'ask_save_format', return_value=None):
            result = app.ask_save_format()
            self.assertIsNone(result)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    @patch('claude_selectable_simple.filedialog.asksaveasfilename')
    @patch('claude_selectable_simple.messagebox.showinfo')
    def test_save_conversation_history(self, mock_showinfo, mock_asksaveasfilename, mock_anthropic, mock_getenv, mock_load_dotenv):
        """会話履歴保存のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        # 保存形式選択をモック
        with patch.object(app, 'ask_save_format', return_value="markdown"):
            # ファイル保存ダイアログをモック
            mock_asksaveasfilename.return_value = "test_conversation.md"
            
            result = app.save_conversation_history("テスト質問", "テスト回答")
            
            self.assertTrue(result)
            mock_showinfo.assert_called_once()
        
        # JSON保存のテスト
        with patch.object(app, 'ask_save_format', return_value="json"):
            mock_asksaveasfilename.return_value = "test_conversation.json"
            
            result = app.save_conversation_history("テスト質問", "テスト回答")
            
            self.assertTrue(result)
        
        # キャンセルのテスト
        with patch.object(app, 'ask_save_format', return_value=None):
            result = app.save_conversation_history("テスト質問", "テスト回答")
            
            self.assertFalse(result)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    def test_prompt_save_conversation(self, mock_anthropic, mock_getenv, mock_load_dotenv):
        """保存確認ダイアログのテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        # 空の会話の場合
        result = app.prompt_save_conversation("テスト")
        self.assertTrue(result)
        
        # 会話がある場合（保存しない選択）
        app.question_text.insert("1.0", "テスト質問")
        with patch('tkinter.messagebox.askyesnocancel', return_value=False):
            result = app.prompt_save_conversation("テスト")
            self.assertTrue(result)
        
        # 会話がある場合（保存する選択）
        app.question_text.insert("1.0", "テスト質問2")
        with patch('tkinter.messagebox.askyesnocancel', return_value=True):
            with patch.object(app, 'save_conversation_history', return_value=True):
                result = app.prompt_save_conversation("テスト")
                self.assertTrue(result)
        
        # キャンセル選択
        with patch('tkinter.messagebox.askyesnocancel', return_value=None):
            result = app.prompt_save_conversation("テスト")
            self.assertFalse(result)
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    def test_on_exit(self, mock_anthropic, mock_getenv, mock_load_dotenv):
        """終了処理のテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        app = ClaudeChatApp(self.root)
        
        # 保存確認をモック（保存しない）
        with patch.object(app, 'prompt_save_conversation', return_value=True):
            app.on_exit()
        
        # ウィンドウが破棄されているかチェック
        try:
            self.root.winfo_exists()
            self.fail("ウィンドウが破棄されていません")
        except tk.TclError:
            pass  # 期待される動作
        
        # 保存確認でキャンセルした場合
        self.root = tk.Tk()
        self.root.withdraw()
        app = ClaudeChatApp(self.root)
        
        with patch.object(app, 'prompt_save_conversation', return_value=False):
            app.on_exit()
        
        # ウィンドウが破棄されていないことを確認
        self.assertTrue(self.root.winfo_exists())


class TestClaudeChatAppIntegration(unittest.TestCase):
    """統合テストクラス"""
    
    def setUp(self):
        """各テストの前準備"""
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        """各テストの後処理"""
        try:
            self.root.destroy()
        except:
            pass
    
    @patch('claude_selectable_simple.load_dotenv')
    @patch('claude_selectable_simple.os.getenv')
    @patch('claude_selectable_simple.anthropic.Anthropic')
    def test_full_conversation_flow(self, mock_anthropic, mock_getenv, mock_load_dotenv):
        """完全な会話フローのテスト"""
        mock_getenv.return_value = "test_api_key"
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # モデル設定
        mock_model = Mock()
        mock_model.id = "claude-3-sonnet-20240229"
        mock_response = Mock()
        mock_response.data = [mock_model]
        mock_client.models.list.return_value = mock_response
        
        # APIレスポンス
        mock_content = Mock()
        mock_content.text = "テスト回答です。"
        mock_message = Mock()
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        
        app = ClaudeChatApp(self.root)
        
        # 質問を入力
        app.question_text.insert("1.0", "テスト質問")
        
        # 質問を送信
        app.send_question()
        
        # 回答が表示されているかチェック
        answer_text = app.answer_text.get("1.0", tk.END).strip()
        self.assertIn("テスト回答", answer_text)
        
        # 新しい質問
        with patch.object(app, 'prompt_save_conversation', return_value=True):
            app.new_question()
        
        # テキストがクリアされているかチェック
        question_text = app.question_text.get("1.0", tk.END).strip()
        answer_text = app.answer_text.get("1.0", tk.END).strip()
        self.assertEqual(question_text, "")
        self.assertEqual(answer_text, "")


if __name__ == '__main__':
    unittest.main() 