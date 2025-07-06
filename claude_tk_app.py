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
        self.root.title("Claude Chat App")
        self.root.geometry("800x600")
        
        # API設定
        load_dotenv()
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            messagebox.showerror("エラー", "ANTHROPIC_API_KEYが設定されていません。.envファイルを確認してください。")
            root.destroy()
            return
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        
        self.setup_ui()
    
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
        
        # 質問欄（左半分）
        question_frame = ttk.LabelFrame(main_frame, text="質問", padding="5")
        question_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
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
        answer_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
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
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
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
            command=self.root.destroy
        )
        self.exit_button.pack(side=tk.LEFT)
    
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
        # 質問欄と回答欄をリセット
        self.question_text.delete("1.0", tk.END)
        self.answer_text.config(state=tk.NORMAL)
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = ClaudeChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 