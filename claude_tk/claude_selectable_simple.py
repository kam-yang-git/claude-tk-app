import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import os
import anthropic
import markdown
import re
from dotenv import load_dotenv
import json
from datetime import datetime

class ClaudeChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Chat App with Model Selection")
        self.root.geometry("1000x700")
        
        # API設定
        load_dotenv()
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            messagebox.showerror("エラー", "ANTHROPIC_API_KEYが設定されていません。.envファイルを確認してください。")
            root.destroy()
            return
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # モデル一覧を取得
        self.models = self.get_available_models()
        if not self.models:
            messagebox.showerror("エラー", "利用可能なモデルを取得できませんでした。")
            root.destroy()
            return
        
        # デフォルトモデルを設定
        self.model = list(self.models.keys())[0] if self.models else "claude-sonnet-4-20250514"
        
        self.setup_ui()
        self.center_window()
    
    def get_available_models(self):
        """利用可能なモデル一覧を取得"""
        try:
            # APIからモデル一覧を取得
            models_response = self.client.models.list()
            
            models_dict = {}
            for model in models_response.data:
                # Claudeモデルのみを対象とする
                if model.id.startswith("claude"):
                    models_dict[model.id] = model.id
            
            # ローカルファイルにも保存
            os.makedirs("json", exist_ok=True)
            with open("json/claude_models.json", "w", encoding='utf-8') as f:
                json.dump(models_dict, f, indent=4, ensure_ascii=False)
            
            return models_dict
            
        except Exception as e:
            # API取得に失敗した場合、ローカルファイルから読み込み
            try:
                with open("json/claude_models.json", "r", encoding='utf-8') as f:
                    return json.load(f)
            except:
                messagebox.showerror("エラー", f"モデル一覧の取得に失敗しました: {str(e)}")
                return {}
    
    def center_window(self):
        """ウィンドウを画面中央に配置する"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def markdown_to_text(self, markdown_text):
        """Markdownテキストをプレーンテキストに変換"""
        # HTMLに変換してからテキストを抽出
        html = markdown.markdown(markdown_text)
        
        # HTMLタグを削除してプレーンテキストに変換
        # 見出しタグを改行付きテキストに変換
        html = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', r'\1\n', html, flags=re.DOTALL)
        
        # 段落タグを改行付きテキストに変換
        html = re.sub(r'<p>(.*?)</p>', r'\1\n\n', html, flags=re.DOTALL)
        
        # リストアイテムを箇条書きに変換
        html = re.sub(r'<li>(.*?)</li>', r'• \1\n', html, flags=re.DOTALL)
        
        # コードブロックを処理
        html = re.sub(r'<pre><code>(.*?)</code></pre>', r'\1', html, flags=re.DOTALL)
        
        # インラインコードを処理
        html = re.sub(r'<code>(.*?)</code>', r'\1', html)
        
        # リンクを処理
        html = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', html)
        
        # 太字と斜体を処理
        html = re.sub(r'<(strong|b)>(.*?)</(strong|b)>', r'\2', html)
        html = re.sub(r'<(em|i)>(.*?)</(em|i)>', r'\2', html)
        
        # 残りのHTMLタグを削除
        html = re.sub(r'<[^>]+>', '', html)
        
        # HTMLエンティティをデコード
        html = html.replace('&amp;', '&')
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&quot;', '"')
        html = html.replace('&#39;', "'")
        
        # 余分な改行を整理
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', html)

        # 行頭の「- 」や「* 」を「・」に置換
        text = re.sub(r'^[\-\*]\s+', '・', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def setup_ui(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=0)
        
        # モデル選択フレーム（上部）
        model_frame = ttk.LabelFrame(main_frame, text="モデル選択", padding="3")
        model_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # モデル選択コンボボックス
        ttk.Label(model_frame, text="使用するモデル:").pack(side=tk.LEFT, padx=(0, 5))
        self.model_var = tk.StringVar(value=self.model)
        self.model_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.model_var,
            values=list(self.models.keys()),
            state="readonly",
            width=40
        )
        self.model_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.model_combo.bind('<<ComboboxSelected>>', self.on_model_change)
        
        # モデル一覧更新ボタン
        ttk.Button(
            model_frame,
            text="モデル一覧更新",
            command=self.refresh_models
        ).pack(side=tk.LEFT)
        
        # 質問欄（左半分）
        question_frame = ttk.LabelFrame(main_frame, text="質問", padding="5")
        question_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.question_text = scrolledtext.ScrolledText(
            question_frame, 
            wrap=tk.WORD, 
            width=40, 
            height=20,
            font=("Arial", 10)
        )
        self.question_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        question_frame.columnconfigure(0, weight=1)
        question_frame.rowconfigure(0, weight=1)
        
        # 回答欄（右半分）
        answer_frame = ttk.LabelFrame(main_frame, text="回答", padding="5")
        answer_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        self.answer_text = scrolledtext.ScrolledText(
            answer_frame, 
            wrap=tk.WORD, 
            width=40, 
            height=20,
            font=("Arial", 10),
            state=tk.DISABLED
        )
        self.answer_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        answer_frame.columnconfigure(0, weight=1)
        answer_frame.rowconfigure(0, weight=1)
        
        # ボタンフレーム（下部）
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # ボタン
        self.send_button = ttk.Button(
            button_frame, 
            text="質問を送信する", 
            command=self.send_question
        )
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.new_button = ttk.Button(
            button_frame, 
            text="新しい質問をする", 
            command=self.new_question
        )
        self.new_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.exit_button = ttk.Button(
            button_frame, 
            text="終了する", 
            command=self.on_exit
        )
        self.exit_button.pack(side=tk.LEFT)
        
        # Ctrl+Enterで質問送信
        self.question_text.bind('<Control-Return>', lambda e: self.send_question() or "break")
    
    def on_model_change(self, event=None):
        """モデルが変更された時の処理"""
        self.model = self.model_var.get()
    
    def refresh_models(self):
        """モデル一覧をAPIから更新"""
        try:
            # APIからモデル一覧を取得
            models_response = self.client.models.list()
            
            models_dict = {}
            for model in models_response.data:
                # Claudeモデルのみを対象とする
                if model.id.startswith("claude"):
                    models_dict[model.id] = model.id
            
            # ローカルファイルに保存
            os.makedirs("json", exist_ok=True)
            with open("json/claude_models.json", "w", encoding='utf-8') as f:
                json.dump(models_dict, f, indent=4, ensure_ascii=False)
            
            # モデル一覧を更新
            self.models = models_dict
            
            # 現在選択されているモデルが新しいリストに含まれているかチェック
            current_model = self.model_var.get()
            if current_model not in models_dict:
                # 含まれていない場合は、リストの最初のモデルを選択
                current_model = list(models_dict.keys())[0] if models_dict else "claude-sonnet-4-20250514"
                self.model_var.set(current_model)
                self.model = current_model
            
            # コンボボックスの値を更新
            self.model_combo['values'] = list(models_dict.keys())
            
            messagebox.showinfo("更新完了", "モデル一覧を更新しました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"モデル一覧の更新に失敗しました: {str(e)}")
    
    def send_question(self):
        question = self.question_text.get("1.0", tk.END).strip()
        if not question:
            messagebox.showwarning("警告", "質問を入力してください。")
            return
        
        # ボタンを無効化
        self.send_button.config(state=tk.DISABLED)
        self.root.config(cursor="wait")
        
        try:
            # APIリクエスト
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )
            
            answer = message.content[0].text
            
            # Markdownをプレーンテキストに変換
            plain_text = self.markdown_to_text(answer)
            
            # 回答を表示
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.delete("1.0", tk.END)
            self.answer_text.insert("1.0", plain_text)
            self.answer_text.config(state=tk.DISABLED)
                
        except Exception as e:
            messagebox.showerror("エラー", f"通信エラー: {str(e)}")
        finally:
            # ボタンを再有効化
            self.send_button.config(state=tk.NORMAL)
            self.root.config(cursor="")
    
    def new_question(self):
        # 質問欄と回答欄をリセット前に保存確認
        if not self.prompt_save_conversation("新しい質問"):
            return
        self.question_text.delete("1.0", tk.END)
        self.answer_text.config(state=tk.NORMAL)
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.config(state=tk.DISABLED)
    
    def ask_save_format(self):
        """保存形式を選択するダイアログ（multiと同じUI）"""
        win = tk.Toplevel(self.root)
        win.title("保存形式の選択")
        win.grab_set()
        win.geometry("320x160")
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"320x160+{x}+{y}")
        label = ttk.Label(win, text="保存形式を選択してください:")
        label.pack(pady=10)
        var = tk.StringVar(value="markdown")
        rb1 = ttk.Radiobutton(win, text="Markdown形式で保存", variable=var, value="markdown")
        rb2 = ttk.Radiobutton(win, text="JSON形式で保存", variable=var, value="json")
        rb3 = ttk.Radiobutton(win, text="両方保存", variable=var, value="both")
        rb1.pack(anchor=tk.W, padx=30)
        rb2.pack(anchor=tk.W, padx=30)
        rb3.pack(anchor=tk.W, padx=30)
        result = {"value": None}
        def ok():
            result["value"] = var.get()
            win.destroy()
        def cancel():
            result["value"] = None
            win.destroy()
        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="キャンセル", command=cancel).pack(side=tk.LEFT)
        win.wait_window()
        return result["value"]

    def save_conversation_history(self, question, answer):
        """質問・回答をファイルに保存（Markdown/JSON/両方選択可）"""
        if not question and not answer:
            return False
        save_type = self.ask_save_format()
        if save_type is None:
            return False
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_json = f"claude_selectable_{timestamp}.json"
        default_md = f"claude_selectable_{timestamp}.md"
        result = True
        if save_type in ("json", "both"):
            file_path = filedialog.asksaveasfilename(
                title="質問・回答をJSONで保存",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=default_json
            )
            if file_path:
                try:
                    save_data = {
                        "metadata": {
                            "created_at": datetime.now().isoformat(),
                            "model": self.model
                        },
                        "question": question,
                        "answer": answer
                    }
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(save_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    messagebox.showerror("保存エラー", f"JSON保存に失敗しました:\n{str(e)}")
                    result = False
            elif save_type == "json":
                return False
        if save_type in ("markdown", "both"):
            file_path = filedialog.asksaveasfilename(
                title="質問・回答をMarkdownで保存",
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
                initialfile=default_md
            )
            if file_path:
                try:
                    md_lines = [f"# 質問\n{question}\n\n# 回答\n{answer}\n"]
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(md_lines))
                except Exception as e:
                    messagebox.showerror("保存エラー", f"Markdown保存に失敗しました:\n{str(e)}")
                    result = False
            elif save_type == "markdown":
                return False
        if result:
            messagebox.showinfo("保存完了", "保存しました。")
        return result

    def prompt_save_conversation(self, action_name):
        """保存確認ダイアログ（multiと同じUI）"""
        question = self.question_text.get("1.0", tk.END).strip()
        answer = self.answer_text.get("1.0", tk.END).strip()
        if not question and not answer:
            return True
        result = messagebox.askyesnocancel(
            "保存確認",
            f"{action_name}前に質問・回答を保存しますか？\n\n"
            f"「はい」: 保存してから{action_name}\n"
            f"「いいえ」: 保存せずに{action_name}\n"
            f"「キャンセル」: {action_name}をキャンセル"
        )
        if result is None:
            return False
        elif result:
            return self.save_conversation_history(question, answer)
        else:
            return True
    
    def on_exit(self):
        if not self.prompt_save_conversation("終了"):
            return
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ClaudeChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 