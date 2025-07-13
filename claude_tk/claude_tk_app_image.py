import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import anthropic
import markdown
import re
import base64
from dotenv import load_dotenv
from PIL import Image, ImageTk
import io

class ClaudeChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Chat App with Image Support")
        self.root.geometry("1000x700")
        
        # API設定
        load_dotenv()
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            messagebox.showerror("エラー", "ANTHROPIC_API_KEYが設定されていません。.envファイルを確認してください。")
            root.destroy()
            return
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # 画像対応モデル
        
        # 画像関連の変数
        self.selected_image_path = None
        self.image_data = None
        
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
    
    def select_image(self):
        """画像を選択する"""
        file_path = filedialog.askopenfilename(
            title="画像を選択",
            filetypes=[
                ("画像ファイル", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 画像を読み込み
                with open(file_path, "rb") as image_file:
                    self.image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
                self.selected_image_path = file_path
                
                # プレビューを更新
                self.update_image_preview()
                
                # ファイル名を表示
                filename = os.path.basename(file_path)
                self.image_label.config(text=f"選択された画像: {filename}")
                
            except Exception as e:
                messagebox.showerror("エラー", f"画像の読み込みに失敗しました: {str(e)}")
    
    def update_image_preview(self):
        """画像プレビューを更新する"""
        if self.selected_image_path:
            try:
                # 画像を読み込み、リサイズ
                image = Image.open(self.selected_image_path)
                
                # プレビュー用にリサイズ（最大200x200）
                image.thumbnail((200, 200), Image.Resampling.LANCZOS)
                
                # PhotoImageに変換
                photo = ImageTk.PhotoImage(image)
                
                # プレビューラベルに表示
                self.preview_label.config(image=photo, text="")
                self.preview_label.image = photo  # 参照を保持
                
            except Exception as e:
                self.preview_label.config(image="", text="プレビューエラー")
    
    def remove_image(self):
        """選択された画像を削除する"""
        self.selected_image_path = None
        self.image_data = None
        self.image_label.config(text="画像が選択されていません")
        self.preview_label.config(image="", text="画像プレビュー")
    
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
        
        # 画像選択フレーム
        image_frame = ttk.Frame(question_frame)
        image_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(
            image_frame, 
            text="画像を選択", 
            command=self.select_image
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            image_frame, 
            text="画像を削除", 
            command=self.remove_image
        ).pack(side=tk.LEFT)
        
        # 画像情報ラベル
        self.image_label = ttk.Label(image_frame, text="画像が選択されていません")
        self.image_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 画像プレビューフレーム
        preview_frame = ttk.LabelFrame(question_frame, text="画像プレビュー", padding="5")
        preview_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.preview_label = ttk.Label(preview_frame, text="画像プレビュー", width=30)
        self.preview_label.pack()
        
        # 質問テキストエリア
        self.question_text = scrolledtext.ScrolledText(
            question_frame, 
            wrap=tk.WORD, 
            width=40, 
            height=15,
            font=("Arial", 10)
        )
        self.question_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        question_frame.columnconfigure(0, weight=1)
        question_frame.rowconfigure(2, weight=1)
        
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
        
        # Ctrl+Enterで質問送信
        self.question_text.bind('<Control-Return>', lambda e: self.send_question() or "break")
    
    def send_question(self):
        question = self.question_text.get("1.0", tk.END).strip()
        if not question:
            messagebox.showwarning("警告", "質問を入力してください。")
            return
        
        # ボタンを無効化
        self.send_button.config(state=tk.DISABLED)
        self.root.config(cursor="wait")
        
        try:
            # メッセージの内容を構築
            content = [{"type": "text", "text": question}]
            
            # 画像がある場合は追加
            if self.image_data:
                # 画像のMIMEタイプを判定
                file_extension = os.path.splitext(self.selected_image_path)[1].lower()
                mime_type_map = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.bmp': 'image/bmp',
                    '.webp': 'image/webp'
                }
                mime_type = mime_type_map.get(file_extension, 'image/jpeg')
                
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": self.image_data
                    }
                })
            
            # APIリクエスト
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": content
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
        
        # 画像もリセット
        self.remove_image()

def main():
    root = tk.Tk()
    app = ClaudeChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 