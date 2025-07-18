import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import anthropic
import markdown
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageTk  # 画像表示用
import base64
import shutil
import tempfile
import zipfile

class ClaudeChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Chat App - Multi Turn and Image")
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
        self.attached_image_path = None
        self.attached_image_preview = None
        self.history_images = []  # 履歴欄の画像参照保持用
        self._imported_tempdir = None  # zip復元用一時ディレクトリ参照
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def markdown_to_text(self, markdown_text):
        html = markdown.markdown(markdown_text)
        html = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', r'\1\n', html, flags=re.DOTALL)
        html = re.sub(r'<p>(.*?)</p>', r'\1\n\n', html, flags=re.DOTALL)
        html = re.sub(r'<li>(.*?)</li>', r'• \1\n', html, flags=re.DOTALL)
        html = re.sub(r'<pre><code>(.*?)</code></pre>', r'\1', html, flags=re.DOTALL)
        html = re.sub(r'<code>(.*?)</code>', r'\1', html)
        html = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', html)
        html = re.sub(r'<(strong|b)>(.*?)</(strong|b)>', r'\2', html)
        html = re.sub(r'<(em|i)>(.*?)</(em|i)>', r'\2', html)
        html = re.sub(r'<[^>]+>', '', html)
        html = html.replace('&amp;', '&')
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&quot;', '"')
        html = html.replace('&#39;', "'")
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
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
        
        # 質問欄（左半分）
        question_frame = ttk.LabelFrame(main_frame, text="質問", padding="5")
        question_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # 画像選択フレーム
        image_frame = ttk.Frame(question_frame)
        image_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.attach_image_button = ttk.Button(
            image_frame, text="画像を選択", command=self.attach_image
        )
        self.attach_image_button.pack(side=tk.LEFT, padx=(0, 5))
        self.remove_image_button = ttk.Button(
            image_frame, text="画像を削除", command=self.remove_image, state=tk.DISABLED
        )
        self.remove_image_button.pack(side=tk.LEFT)
        self.image_label = ttk.Label(image_frame, text="画像が選択されていません")
        self.image_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 画像プレビューフレーム
        preview_frame = ttk.LabelFrame(question_frame, text="画像プレビュー", padding="5")
        preview_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.image_preview_label = ttk.Label(preview_frame, text="画像プレビュー", width=30)
        self.image_preview_label.pack()
        
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
        self.send_button = ttk.Button(
            button_frame, text="質問を送信する", command=self.send_question
        )
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        self.clear_button = ttk.Button(
            button_frame, text="会話をクリア", command=self.clear_conversation
        )
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        self.resume_button = ttk.Button(
            button_frame, text="会話を再開", command=self.resume_conversation
        )
        self.resume_button.pack(side=tk.LEFT, padx=(0, 10))
        self.exit_button = ttk.Button(
            button_frame, text="終了する", command=self.exit_application
        )
        self.exit_button.pack(side=tk.LEFT)
        self.question_text.bind('<Control-Return>', lambda e: self.send_question() or "break")

    def attach_image(self):
        file_path = filedialog.askopenfilename(
            title="画像ファイルを選択", filetypes=[("画像ファイル", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("すべてのファイル", "*.*")]
        )
        if not file_path:
            return
        self.attached_image_path = file_path
        # プレビュー表示
        try:
            img = Image.open(file_path)
            img.thumbnail((180, 180))
            self.attached_image_preview = ImageTk.PhotoImage(img)
            self.image_preview_label.config(image=self.attached_image_preview, text="")
            self.remove_image_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("画像エラー", f"画像の読み込みに失敗しました: {str(e)}")
            self.attached_image_path = None
            self.image_preview_label.config(image="", text="")
            self.remove_image_button.config(state=tk.DISABLED)

    def remove_image(self):
        self.attached_image_path = None
        self.image_preview_label.config(image="", text="")
        self.remove_image_button.config(state=tk.DISABLED)

    def update_history_display(self):
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        self.history_images.clear()  # 画像参照をクリア
        pair_num = 0
        for msg in self.conversation_history:
            if msg["role"] == "user":
                pair_num += 1
                self.history_text.insert(tk.END, f"【質問 {pair_num}】\n", "user")
                self.history_text.insert(tk.END, f"{msg['content']}\n", "user_content")
                if msg.get("image_path"):
                    try:
                        img = Image.open(msg["image_path"])
                        img.thumbnail((200, 200))
                        photo = ImageTk.PhotoImage(img)
                        self.history_images.append(photo)  # 参照保持
                        self.history_text.image_create(tk.END, image=photo)
                        self.history_text.insert(tk.END, "\n", "user_image")
                    except Exception as e:
                        self.history_text.insert(tk.END, f"[画像表示エラー: {os.path.basename(msg['image_path'])}]\n", "user_image")
                self.history_text.insert(tk.END, "\n")
            else:
                self.history_text.insert(tk.END, f"【回答 {pair_num}】\n", "assistant")
                self.history_text.insert(tk.END, f"{msg['content']}\n\n", "assistant_content")
        self.history_text.tag_config("user", foreground="blue", font=("Arial", 9, "bold"))
        self.history_text.tag_config("user_content", foreground="black", font=("Arial", 9))
        self.history_text.tag_config("user_image", foreground="purple", font=("Arial", 8, "italic"))
        self.history_text.tag_config("assistant", foreground="green", font=("Arial", 9, "bold"))
        self.history_text.tag_config("assistant_content", foreground="black", font=("Arial", 9))
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)

    def send_question(self):
        question = self.question_text.get("1.0", tk.END).strip()
        if not question:
            messagebox.showwarning("警告", "質問を入力してください。")
            return
        self.send_button.config(state=tk.DISABLED)
        self.root.config(cursor="wait")
        try:
            # 会話履歴に質問を追加
            user_msg = {"role": "user", "content": question}
            if self.attached_image_path:
                user_msg["image_path"] = self.attached_image_path
            self.conversation_history.append(user_msg)
            # APIリクエスト用メッセージリスト
            messages = []
            for i, msg in enumerate(self.conversation_history):
                if msg["role"] == "user":
                    # 最新のuserメッセージだけ画像付き
                    if i == len(self.conversation_history) - 1 and msg.get("image_path"):
                        with open(msg["image_path"], "rb") as f:
                            img_bytes = f.read()
                        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                        mime_type = self.get_mime_type(msg["image_path"])
                        messages.append({
                            "role": "user",
                            "content": [
                                {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": img_b64}},
                                {"type": "text", "text": msg["content"]}
                            ]
                        })
                    else:
                        # 過去のuserメッセージはテキストのみ
                        messages.append({"role": "user", "content": msg["content"]})
                else:
                    messages.append({
                        "role": "assistant",
                        "content": msg.get("markdown", msg["content"])
                    })
            # APIリクエスト
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=messages
            )
            answer = message.content[0].text
            plain_text = self.markdown_to_text(answer)
            self.conversation_history.append({"role": "assistant", "content": plain_text, "markdown": answer})
            self.update_history_display()
            self.question_text.delete("1.0", tk.END)
            self.remove_image()
        except Exception as e:
            messagebox.showerror("エラー", f"通信エラー: {str(e)}")
            if self.conversation_history and self.conversation_history[-1]["role"] == "user":
                self.conversation_history.pop()
        finally:
            self.send_button.config(state=tk.NORMAL)
            self.root.config(cursor="")

    def get_mime_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            return "image/jpeg"
        elif ext == ".png":
            return "image/png"
        elif ext == ".bmp":
            return "image/bmp"
        elif ext == ".gif":
            return "image/gif"
        return "application/octet-stream"

    def clear_conversation(self):
        if not self.prompt_save_conversation("会話クリア"):
            return
        if messagebox.askyesno("確認", "会話履歴をクリアしますか？"):
            self.conversation_history = []
            self.update_history_display()
            self.question_text.delete("1.0", tk.END)
            self.history_text.config(state=tk.NORMAL)
            self.history_text.delete("1.0", tk.END)
            self.history_text.config(state=tk.DISABLED)
            self.remove_image()

    def save_conversation_history(self):
        if not self.conversation_history:
            return False
        save_type = self.ask_save_format()
        if save_type is None:
            return False
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_json = f"claude_conversation_{timestamp}.json"
        default_md = f"claude_conversation_{timestamp}.md"
        default_json_zip = f"claude_conversation_{timestamp}_json.zip"
        default_md_zip = f"claude_conversation_{timestamp}_md.zip"
        result = True
        if save_type in ("json", "both"):
            file_path = filedialog.asksaveasfilename(
                title="会話履歴をZIPで保存",
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
                initialfile=default_json_zip
            )
            if file_path:
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        img_dir = os.path.join(tmpdir, "img")
                        os.makedirs(img_dir, exist_ok=True)
                        # JSONデータ作成
                        save_data = {
                            "metadata": {
                                "created_at": datetime.now().isoformat(),
                                "model": self.model,
                                "total_messages": len(self.conversation_history)
                            },
                            "conversation": []
                        }
                        for msg in self.conversation_history:
                            if msg["role"] == "user" and msg.get("image_path"):
                                img_filename = os.path.basename(msg["image_path"])
                                img_dst = os.path.join(img_dir, img_filename)
                                shutil.copy2(msg["image_path"], img_dst)
                                msg_copy = dict(msg)
                                msg_copy["image_path"] = f"img/{img_filename}"
                                save_data["conversation"].append(msg_copy)
                            elif msg["role"] == "assistant":
                                save_data["conversation"].append({
                                    "role": "assistant",
                                    "content": msg.get("markdown", msg["content"])
                                })
                            else:
                                save_data["conversation"].append(dict(msg))
                        json_path = os.path.join(tmpdir, default_json)
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(save_data, f, ensure_ascii=False, indent=2)
                        # zip作成
                        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            zipf.write(json_path, arcname=default_json)
                            for root, _, files in os.walk(img_dir):
                                for fname in files:
                                    fpath = os.path.join(root, fname)
                                    arcname = os.path.relpath(fpath, tmpdir)
                                    zipf.write(fpath, arcname=arcname)
                except Exception as e:
                    messagebox.showerror("保存エラー", f"ZIP保存に失敗しました:\n{str(e)}")
                    result = False
            elif save_type == "json":
                return False
        if save_type in ("markdown", "both"):
            file_path = filedialog.asksaveasfilename(
                title="会話履歴をMarkdown ZIPで保存",
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
                initialfile=default_md_zip
            )
            if file_path:
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        md_name = os.path.splitext(os.path.basename(file_path))[0] + ".md"
                        md_path = os.path.join(tmpdir, md_name)
                        img_dir = os.path.join(tmpdir, "img")
                        os.makedirs(img_dir, exist_ok=True)
                        md_lines = []
                        pair_num = 0
                        for msg in self.conversation_history:
                            if msg["role"] == "user":
                                pair_num += 1
                                md_lines.append(f"## 質問{pair_num}\n{msg['content']}")
                                if msg.get("image_path"):
                                    img_filename = os.path.basename(msg["image_path"])
                                    img_dst = os.path.join(img_dir, img_filename)
                                    try:
                                        if not os.path.exists(img_dst):
                                            shutil.copy2(msg["image_path"], img_dst)
                                        md_lines.append(f"![添付画像](img/{img_filename})")
                                    except Exception as e:
                                        md_lines.append(f"[画像保存エラー: {img_filename}]")
                            else:
                                md = msg.get("markdown", msg["content"])
                                md_lines.append(f"## 回答{pair_num}\n{md}")
                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(md_lines))
                        # zip化
                        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            zipf.write(md_path, arcname=md_name)
                            for root, _, files in os.walk(img_dir):
                                for fname in files:
                                    fpath = os.path.join(root, fname)
                                    arcname = os.path.relpath(fpath, tmpdir)
                                    zipf.write(fpath, arcname=arcname)
                except Exception as e:
                    messagebox.showerror("保存エラー", f"Markdown ZIP保存に失敗しました:\n{str(e)}")
                    result = False
            elif save_type == "markdown":
                return False
        if result:
            messagebox.showinfo("保存完了", "会話履歴を保存しました。")
        return result

    def ask_save_format(self):
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
        label = ttk.Label(win, text="会話履歴の保存形式を選択してください:")
        label.pack(pady=10)
        var = tk.StringVar(value="markdown")
        rb1 = ttk.Radiobutton(win, text="Markdown形式で保存", variable=var, value="markdown")
        rb2 = ttk.Radiobutton(win, text="ZIP形式で保存", variable=var, value="zip")
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
        if not self.conversation_history:
            return True
        result = messagebox.askyesnocancel(
            "会話履歴の保存",
            f"{action_name}前に会話履歴を保存しますか？\n\n"
            f"「はい」: 保存してから{action_name}\n"
            f"「いいえ」: 保存せずに{action_name}\n"
            f"「キャンセル」: {action_name}をキャンセル"
        )
        if result is None:
            return False
        elif result:
            return self.save_conversation_history()
        else:
            return True

    def exit_application(self):
        if not self.prompt_save_conversation("終了"):
            return
        self.root.destroy()

    def resume_conversation(self):
        file_path = filedialog.askopenfilename(
            title="会話履歴ファイル（ZIP）を選択してください",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # 既存の一時ディレクトリがあればクリーンアップ
                if self._imported_tempdir is not None:
                    self._imported_tempdir.cleanup()
                self._imported_tempdir = tempfile.TemporaryDirectory()
                tmpdir_name = self._imported_tempdir.name
                zipf.extractall(tmpdir_name)
                # JSONファイル名を自動検出
                json_name = None
                for name in zipf.namelist():
                    if name.endswith('.json') and not name.startswith('img/'):
                        json_name = name
                        break
                if not json_name:
                    raise ValueError("ZIP内にJSONファイルが見つかりません")
                json_path = os.path.join(tmpdir_name, json_name)
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                conversation = data.get("conversation", data)
                if not isinstance(conversation, list):
                    raise ValueError("不正な会話履歴ファイルです（conversationがリストではありません）")
                new_history = []
                for msg in conversation:
                    if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                        raise ValueError("不正な会話履歴ファイルです（メッセージ形式エラー）")
                    if msg["role"] == "assistant":
                        new_history.append({
                            "role": "assistant",
                            "content": self.markdown_to_text(msg.get("content", "")),
                            "markdown": msg.get("content", "")
                        })
                    else:
                        user_msg = {"role": "user", "content": msg["content"]}
                        if "image_path" in msg:
                            # img/パスを絶対パスに変換
                            img_rel = msg["image_path"]
                            img_abs = os.path.join(tmpdir_name, img_rel)
                            user_msg["image_path"] = img_abs
                        new_history.append(user_msg)
                self.conversation_history = new_history
                self.update_history_display()
                messagebox.showinfo("インポート完了", "会話履歴を再開しました。")
        except Exception as e:
            messagebox.showerror("インポートエラー", f"会話履歴のインポートに失敗しました:\n{str(e)}")

def main():
    root = tk.Tk()
    app = ClaudeChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 