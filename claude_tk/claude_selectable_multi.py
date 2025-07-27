import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import anthropic
import markdown
import re
import json
from datetime import datetime
from dotenv import load_dotenv

class ClaudeChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Chat App - Multi Turn")
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
        
        # 会話履歴を保持
        self.conversation_history = []
        
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
    
    def refresh_models(self):
        """モデル一覧を更新"""
        try:
            self.models = self.get_available_models()
            if self.models:
                # コンボボックスの値を更新
                self.model_combo['values'] = list(self.models.keys())
                # 現在選択されているモデルが新しい一覧にない場合は最初のモデルを選択
                if self.model not in self.models:
                    self.model = list(self.models.keys())[0]
                    self.model_var.set(self.model)
                messagebox.showinfo("更新完了", "モデル一覧を更新しました。")
            else:
                messagebox.showerror("エラー", "モデル一覧の更新に失敗しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"モデル一覧の更新に失敗しました: {str(e)}")
    
    def on_model_change(self, event=None):
        """モデルが変更された時の処理"""
        # 会話履歴がある場合は変更を無効化
        if self.conversation_history:
            # 元のモデルに戻す
            self.model_var.set(self.model)
            messagebox.showwarning("警告", "会話が始まっているため、モデルを変更できません。\n「会話をクリア」ボタンを押してからモデルを変更してください。")
            return
    
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
        
        # 質問入力欄（左半分）
        input_frame = ttk.LabelFrame(main_frame, text="新しい質問", padding="5")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.question_text = scrolledtext.ScrolledText(
            input_frame, 
            wrap=tk.WORD, 
            width=40, 
            height=15,
            font=("Arial", 10)
        )
        self.question_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)
        
        # 最新回答表示欄（左半分の下部）
        latest_answer_frame = ttk.LabelFrame(main_frame, text="最新の回答", padding="5")
        latest_answer_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5), pady=(5, 0))
        latest_answer_frame.grid_remove()  # 最初は非表示
        
        self.latest_answer_text = scrolledtext.ScrolledText(
            latest_answer_frame, 
            wrap=tk.WORD, 
            width=40, 
            height=10,
            font=("Arial", 9),
            state=tk.DISABLED
        )
        self.latest_answer_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        latest_answer_frame.columnconfigure(0, weight=1)
        latest_answer_frame.rowconfigure(0, weight=1)
        
        # 会話履歴表示欄（右半分）
        history_frame = ttk.LabelFrame(main_frame, text="会話履歴", padding="5")
        history_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        self.history_text = scrolledtext.ScrolledText(
            history_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=25,
            font=("Arial", 9),
            state=tk.DISABLED
        )
        self.history_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
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
        
        self.clear_button = ttk.Button(
            button_frame, 
            text="会話をクリア", 
            command=self.clear_conversation
        )
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))

        # 「会話を再開」ボタン
        self.resume_button = ttk.Button(
            button_frame,
            text="会話を再開",
            command=self.resume_conversation
        )
        self.resume_button.pack(side=tk.LEFT, padx=(0, 10))

        self.exit_button = ttk.Button(
            button_frame, 
            text="終了する", 
            command=self.exit_application
        )
        self.exit_button.pack(side=tk.LEFT)
        
        # Enterキーで質問送信
        self.question_text.bind('<Control-Return>', lambda e: self.send_question() or "break")
    
    def update_history_display(self):
        """会話履歴の表示を更新"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        
        pair_num = 0
        for msg in self.conversation_history:
            if msg["role"] == "user":
                pair_num += 1
                self.history_text.insert(tk.END, f"【質問 {pair_num}】\n", "user")
                self.history_text.insert(tk.END, f"{msg['content']}\n\n", "user_content")
            else:
                self.history_text.insert(tk.END, f"【回答 {pair_num}】\n", "assistant")
                self.history_text.insert(tk.END, f"{msg['content']}\n\n", "assistant_content")
        
        # タグの設定
        self.history_text.tag_config("user", foreground="blue", font=("Arial", 9, "bold"))
        self.history_text.tag_config("user_content", foreground="black", font=("Arial", 9))
        self.history_text.tag_config("assistant", foreground="green", font=("Arial", 9, "bold"))
        self.history_text.tag_config("assistant_content", foreground="black", font=("Arial", 9))
        
        # 最新の位置にスクロール
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)
    
    def send_question(self):
        question = self.question_text.get("1.0", tk.END).strip()
        if not question:
            messagebox.showwarning("警告", "質問を入力してください。")
            return
        
        # 現在選択されているモデルを取得
        self.model = self.model_var.get()
        
        # ボタンを無効化
        self.send_button.config(state=tk.DISABLED)
        self.root.config(cursor="wait")
        
        try:
            # 会話履歴に質問を追加
            self.conversation_history.append({"role": "user", "content": question})
            
            # 会話が始まったらモデル選択を無効化
            if len(self.conversation_history) == 1:
                self.model_combo.config(state="disabled")
            
            # APIリクエスト用のメッセージリストを作成
            messages = []
            for msg in self.conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"] if msg["role"] == "user" else msg.get("markdown", msg["content"])
                })
            
            # APIリクエスト
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=messages
            )
            
            answer = message.content[0].text
            
            # Markdownをプレーンテキストに変換
            plain_text = self.markdown_to_text(answer)
            
            # 会話履歴に回答を追加（plain_textとmarkdown両方保持）
            self.conversation_history.append({"role": "assistant", "content": plain_text, "markdown": answer})
            
            # 履歴表示を更新
            self.update_history_display()
            
            # 最新回答を表示
            self.latest_answer_text.config(state=tk.NORMAL)
            self.latest_answer_text.delete("1.0", tk.END)
            self.latest_answer_text.insert("1.0", plain_text)
            self.latest_answer_text.config(state=tk.DISABLED)
            
            # 最新回答欄を表示
            self.latest_answer_text.master.grid()
            
            # 質問欄をクリア
            self.question_text.delete("1.0", tk.END)
                
        except Exception as e:
            messagebox.showerror("エラー", f"通信エラー: {str(e)}")
            # エラーが発生した場合は質問を履歴から削除
            if self.conversation_history and self.conversation_history[-1]["role"] == "user":
                self.conversation_history.pop()
                # 会話履歴が空になったらモデル選択を再有効化
                if not self.conversation_history:
                    self.model_combo.config(state="readonly")
        finally:
            # ボタンを再有効化
            self.send_button.config(state=tk.NORMAL)
            self.root.config(cursor="")
    
    def clear_conversation(self):
        """会話履歴をクリア"""
        if not self.prompt_save_conversation("会話クリア"):
            return
        
        if messagebox.askyesno("確認", "会話履歴をクリアしますか？"):
            self.conversation_history = []
            self.update_history_display()
            self.question_text.delete("1.0", tk.END)
            self.latest_answer_text.config(state=tk.NORMAL)
            self.latest_answer_text.delete("1.0", tk.END)
            self.latest_answer_text.config(state=tk.DISABLED)
            self.latest_answer_text.master.grid_remove()
            # 会話履歴をクリアしたらモデル選択を再有効化
            self.model_combo.config(state="readonly")

    def save_conversation_history(self):
        """会話履歴をファイルに保存（Markdown/JSON/両方選択可）"""
        if not self.conversation_history:
            return False

        # 保存形式を選択
        save_type = self.ask_save_format()
        if save_type is None:
            return False  # キャンセル

        # デフォルトのファイル名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_json = f"claude_conversation_{timestamp}.json"
        default_md = f"claude_conversation_{timestamp}.md"

        result = True
        if save_type in ("json", "both"):
            file_path = filedialog.asksaveasfilename(
                title="会話履歴をJSONで保存",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=default_json
            )
            if file_path:
                try:
                    # JSON用: assistantはMarkdownのまま
                    save_data = {
                        "metadata": {
                            "created_at": datetime.now().isoformat(),
                            "model": self.model,
                            "total_messages": len(self.conversation_history)
                        },
                        "conversation": [
                            dict(msg) if msg["role"] == "user" else {
                                "role": "assistant",
                                "content": msg.get("markdown", msg["content"])
                            }
                            for msg in self.conversation_history
                        ]
                    }
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(save_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    messagebox.showerror("保存エラー", f"JSON保存に失敗しました:\n{str(e)}")
                    result = False
            elif save_type == "json":
                return False  # キャンセル

        if save_type in ("markdown", "both"):
            file_path = filedialog.asksaveasfilename(
                title="会話履歴をMarkdownで保存",
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
                initialfile=default_md
            )
            if file_path:
                try:
                    # Markdown用: 質問・回答ペアで整形
                    md_lines = []
                    pair_num = 0
                    for msg in self.conversation_history:
                        if msg["role"] == "user":
                            pair_num += 1
                            md_lines.append(f"## 質問{pair_num}\n{msg['content']}\n")
                        else:
                            md = msg.get("markdown", msg["content"])
                            md_lines.append(f"## 回答{pair_num}\n{md}\n")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(md_lines))
                except Exception as e:
                    messagebox.showerror("保存エラー", f"Markdown保存に失敗しました:\n{str(e)}")
                    result = False
            elif save_type == "markdown":
                return False  # キャンセル

        if result:
            messagebox.showinfo("保存完了", "会話履歴を保存しました。")
        return result

    def ask_save_format(self):
        """保存形式を選択するダイアログ"""
        win = tk.Toplevel(self.root)
        win.title("保存形式の選択")
        win.grab_set()
        win.geometry("320x160")
        # 画面中央に配置
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"320x160+{x}+{y}")
        label = ttk.Label(win, text="会話履歴の保存形式を選択してください:")
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

    def prompt_save_conversation(self, action_name):
        """会話履歴の保存を確認"""
        if not self.conversation_history:
            return True  # 履歴がない場合はそのまま実行
        
        # 保存するかどうかを確認
        result = messagebox.askyesnocancel(
            "会話履歴の保存",
            f"{action_name}前に会話履歴を保存しますか？\n\n"
            f"「はい」: 保存してから{action_name}\n"
            f"「いいえ」: 保存せずに{action_name}\n"
            f"「キャンセル」: {action_name}をキャンセル"
        )
        
        if result is None:  # キャンセル
            return False
        elif result:  # はい（保存する）
            return self.save_conversation_history()
        else:  # いいえ（保存しない）
            return True

    def exit_application(self):
        """アプリケーションを終了"""
        if not self.prompt_save_conversation("終了"):
            return
        
        self.root.destroy()

    def resume_conversation(self):
        """JSONファイルから会話履歴をインポートして再開"""
        file_path = filedialog.askopenfilename(
            title="会話履歴ファイル（JSON）を選択してください",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return  # キャンセル
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # モデル情報を取得（metadataから）
            if "metadata" in data and "model" in data["metadata"]:
                saved_model = data["metadata"]["model"]
                # 保存されたモデルが利用可能なモデルリストに含まれているかチェック
                if saved_model in self.models:
                    self.model = saved_model
                    self.model_var.set(self.model)
                else:
                    messagebox.showwarning("警告", f"保存されたモデル '{saved_model}' が現在利用できません。\n現在選択されているモデルを使用します。")
            
            # conversationキーがあればそれを使う
            conversation = data.get("conversation", data)
            # conversationはリストであることを確認
            if not isinstance(conversation, list):
                raise ValueError("不正な会話履歴ファイルです（conversationがリストではありません）")
            # 各メッセージのroleとcontent/markdownを検証
            new_history = []
            for msg in conversation:
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    raise ValueError("不正な会話履歴ファイルです（メッセージ形式エラー）")
                # assistantの場合はmarkdownも保持
                if msg["role"] == "assistant":
                    new_history.append({
                        "role": "assistant",
                        "content": self.markdown_to_text(msg.get("content", "")),
                        "markdown": msg.get("content", "")
                    })
                else:
                    new_history.append({
                        "role": "user",
                        "content": msg["content"]
                    })
            
            self.conversation_history = new_history
            self.update_history_display()
            
            # 会話履歴がある場合はモデル選択を無効化
            if self.conversation_history:
                self.model_combo.config(state="disabled")
            
            # 最新回答欄も更新
            last_assistant = next((m for m in reversed(self.conversation_history) if m["role"] == "assistant"), None)
            if last_assistant:
                self.latest_answer_text.config(state=tk.NORMAL)
                self.latest_answer_text.delete("1.0", tk.END)
                self.latest_answer_text.insert("1.0", last_assistant["content"])
                self.latest_answer_text.config(state=tk.DISABLED)
                self.latest_answer_text.master.grid()
            else:
                self.latest_answer_text.config(state=tk.NORMAL)
                self.latest_answer_text.delete("1.0", tk.END)
                self.latest_answer_text.config(state=tk.DISABLED)
                self.latest_answer_text.master.grid_remove()
            
            messagebox.showinfo("インポート完了", "会話履歴を再開しました。")
        except Exception as e:
            messagebox.showerror("インポートエラー", f"会話履歴のインポートに失敗しました:\n{str(e)}")

def main():
    root = tk.Tk()
    app = ClaudeChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 