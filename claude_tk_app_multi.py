import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import anthropic
import markdown
import re
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
        self.model = "claude-sonnet-4-20250514"
        
        # 会話履歴を保持
        self.conversation_history = []
        
        self.setup_ui()
        self.center_window()
    
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
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)
        
        # 質問入力欄（左半分）
        input_frame = ttk.LabelFrame(main_frame, text="新しい質問", padding="5")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
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
        latest_answer_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5), pady=(5, 0))
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
        history_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
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
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
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
        
        self.exit_button = ttk.Button(
            button_frame, 
            text="終了する", 
            command=self.root.destroy
        )
        self.exit_button.pack(side=tk.LEFT)
        
        # Enterキーで質問送信
        self.question_text.bind('<Control-Return>', lambda e: self.send_question())
    
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
        
        # ボタンを無効化
        self.send_button.config(state=tk.DISABLED)
        self.root.config(cursor="wait")
        
        try:
            # 会話履歴に質問を追加
            self.conversation_history.append({"role": "user", "content": question})
            
            # APIリクエスト用のメッセージリストを作成
            messages = []
            for msg in self.conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
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
            
            # 会話履歴に回答を追加
            self.conversation_history.append({"role": "assistant", "content": plain_text})
            
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
        finally:
            # ボタンを再有効化
            self.send_button.config(state=tk.NORMAL)
            self.root.config(cursor="")
    
    def clear_conversation(self):
        """会話履歴をクリア"""
        if messagebox.askyesno("確認", "会話履歴をクリアしますか？"):
            self.conversation_history = []
            self.update_history_display()
            self.question_text.delete("1.0", tk.END)
            self.latest_answer_text.config(state=tk.NORMAL)
            self.latest_answer_text.delete("1.0", tk.END)
            self.latest_answer_text.config(state=tk.DISABLED)
            self.latest_answer_text.master.grid_remove()

def main():
    root = tk.Tk()
    app = ClaudeChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 