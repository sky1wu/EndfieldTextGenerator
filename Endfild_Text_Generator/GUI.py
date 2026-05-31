import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from PIL import Image, ImageTk, ImageDraw
from backend import generate_image

class TitleGeneratorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("终末地白色大字生成器")
        self.root.geometry("1280x720")
        self.root.minsize(1024, 600)
        self.set_icon()

        # 变量
        self.background_path = tk.StringVar()
        self.width = tk.IntVar(value=1920)
        self.height = tk.IntVar(value=1080)
        self.main_text = tk.StringVar(value="主标题")
        self.second_line = tk.StringVar(value="")
        self.sub_text_enabled = tk.BooleanVar(value=False)
        self.shadow_enabled = tk.BooleanVar(value=False)
        self.shadow_opacity = tk.DoubleVar(value=0.15)

        self.preview_photo = None
        self.update_job = None
        self.preview_img_cache = None
        self.checkerboard_photo = None
        self.scale_label = None

        self.setup_styles()
        self.create_widgets()
        self.bind_events()
        self.update_preview()

    def set_icon(self):
        try:
            import os
            if os.path.exists("assets/icon.ico"):
                self.root.iconbitmap("assets/icon.ico")
            elif os.path.exists("assets/icon.png"):
                img = ImageTk.PhotoImage(file="assets/icon.png")
                self.root.iconphoto(True, img)
        except:
            pass

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        bg_color = '#f0f0f0'
        style.configure('TLabel', font=('Segoe UI', 10), background=bg_color)
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TEntry', font=('Segoe UI', 10), fieldbackground='white')
        style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'), background=bg_color)
        style.configure('TLabelframe', background=bg_color)
        style.configure('TFrame', background=bg_color)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_frame, width=380)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        left_panel.pack_propagate(False)

        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ----- 画布设置 -----
        canvas_frame = ttk.LabelFrame(left_panel, text="画布设置")
        canvas_frame.pack(fill=tk.X, pady=(0,15))
        canvas_inner = ttk.Frame(canvas_frame)
        canvas_inner.pack(fill=tk.X, padx=15, pady=15)

        canvas_inner.columnconfigure(0, weight=0)
        canvas_inner.columnconfigure(1, weight=1)
        canvas_inner.columnconfigure(2, weight=0)
        canvas_inner.columnconfigure(3, weight=0)

        # 背景图片行
        ttk.Label(canvas_inner, text="背景图片:", width=10, anchor='e').grid(row=0, column=0, sticky='e', pady=5)
        bg_entry = ttk.Entry(canvas_inner, textvariable=self.background_path)
        bg_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(canvas_inner, text="浏览", command=self.select_background, width=6).grid(row=0, column=2, padx=2, pady=5)
        ttk.Button(canvas_inner, text="清除", command=self.clear_background, width=6).grid(row=0, column=3, pady=5)

        # 宽度行
        ttk.Label(canvas_inner, text="宽度:", width=10, anchor='e').grid(row=1, column=0, sticky='e', pady=5)
        self.width_entry = ttk.Entry(canvas_inner, textvariable=self.width)
        self.width_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        ttk.Label(canvas_inner, text="").grid(row=1, column=2)
        ttk.Label(canvas_inner, text="").grid(row=1, column=3)

        # 高度行
        ttk.Label(canvas_inner, text="高度:", width=10, anchor='e').grid(row=2, column=0, sticky='e', pady=5)
        self.height_entry = ttk.Entry(canvas_inner, textvariable=self.height)
        self.height_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        ttk.Label(canvas_inner, text="").grid(row=2, column=2)
        ttk.Label(canvas_inner, text="").grid(row=2, column=3)

        # ----- 文字设置 -----
        text_frame = ttk.LabelFrame(left_panel, text="文字设置")
        text_frame.pack(fill=tk.X, pady=(0,15))
        text_inner = ttk.Frame(text_frame)
        text_inner.pack(fill=tk.X, padx=15, pady=15)

        main_row = ttk.Frame(text_inner)
        main_row.pack(fill=tk.X, pady=5)
        ttk.Label(main_row, text="主标题:", width=10, anchor='e').pack(side=tk.LEFT)
        ttk.Entry(main_row, textvariable=self.main_text).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        second_row = ttk.Frame(text_inner)
        second_row.pack(fill=tk.X, pady=5)
        ttk.Label(second_row, text="第二行:", width=10, anchor='e').pack(side=tk.LEFT)
        ttk.Entry(second_row, textvariable=self.second_line).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.sub_check = tk.Checkbutton(text_inner, text="添加萨卡兹文副标题（内容为标题的五笔）", variable=self.sub_text_enabled,
                                        bg='#f0f0f0', activebackground='#f0f0f0', selectcolor='#f0f0f0')
        self.sub_check.pack(anchor='w', pady=10, padx=5)

        # ----- 底影效果 -----
        shadow_frame = ttk.LabelFrame(left_panel, text="底影效果")
        shadow_frame.pack(fill=tk.X, pady=(0,15))
        shadow_inner = ttk.Frame(shadow_frame)
        shadow_inner.pack(fill=tk.X, padx=15, pady=15)

        self.shadow_check = tk.Checkbutton(shadow_inner, text="启用底影", variable=self.shadow_enabled,
                                           command=self.toggle_shadow_slider,
                                           bg='#f0f0f0', activebackground='#f0f0f0', selectcolor='#f0f0f0')
        self.shadow_check.pack(anchor='w')

        opacity_row = ttk.Frame(shadow_inner)
        opacity_row.pack(fill=tk.X, pady=(10,0))
        ttk.Label(opacity_row, text="不透明度:", width=12).pack(side=tk.LEFT)
        self.shadow_slider = tk.Scale(opacity_row, from_=0.0, to=1.0, variable=self.shadow_opacity,
                                      orient=tk.HORIZONTAL, resolution=0.01, bg='#f0f0f0', troughcolor='#c0c0c0')
        self.shadow_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.shadow_opacity_label = ttk.Label(opacity_row, text=f"{self.shadow_opacity.get():.2f}", width=5)
        self.shadow_opacity_label.pack(side=tk.LEFT)

        if not self.shadow_enabled.get():
            self.shadow_slider.config(state='disabled')

        # ----- 操作按钮 -----
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X, pady=10)
        self.save_btn = ttk.Button(button_frame, text="保存图片", command=self.save_image)
        self.save_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.refresh_btn = ttk.Button(button_frame, text="刷新预览", command=self.update_preview)
        self.refresh_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.reset_btn = ttk.Button(button_frame, text="重置默认", command=self.reset_defaults)
        self.reset_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 版权声明
        copyright_label = ttk.Label(left_panel, text="作者：刃下狼血", font=('Segoe UI', 9), anchor='center')
        copyright_label.pack(side=tk.BOTTOM, pady=10)

        # ----- 预览区域 -----
        preview_frame = ttk.LabelFrame(right_panel, text="预览")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas = tk.Canvas(preview_frame, bg='#0a0a0a', highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_label = ttk.Label(self.preview_canvas, text="生成中...", font=("Segoe UI", 14))
        self.preview_label.place(relx=0.5, rely=0.5, anchor='center')

        self.scale_label = ttk.Label(self.preview_canvas, text="缩放: --%", font=('Segoe UI', 9), background='#0a0a0a', foreground='#ffffff')
        self.scale_label.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)

        self.preview_canvas.bind('<Configure>', self.on_canvas_resize)

        # 初始化宽高输入框状态
        self.update_width_height_state()

    def update_width_height_state(self):
        """根据背景图片是否有内容，冻结或解冻宽度高度输入框"""
        if self.background_path.get().strip():
            self.width_entry.config(state='disabled')
            self.height_entry.config(state='disabled')
        else:
            self.width_entry.config(state='normal')
            self.height_entry.config(state='normal')

    def create_checkerboard(self, width, height, square=20):
        img = Image.new('RGBA', (width, height), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        color1 = '#1b1b1b'
        color2 = '#151515'
        for y in range(0, height, square):
            for x in range(0, width, square):
                if (x//square + y//square) % 2 == 0:
                    draw.rectangle([x, y, x+square, y+square], fill=color1)
                else:
                    draw.rectangle([x, y, x+square, y+square], fill=color2)
        return img

    def on_canvas_resize(self, event):
        if self.preview_img_cache is not None:
            self._show_preview(self.preview_img_cache)

    def toggle_shadow_slider(self):
        if self.shadow_enabled.get():
            self.shadow_slider.config(state='normal')
        else:
            self.shadow_slider.config(state='disabled')

    def bind_events(self):
        self.main_text.trace_add('write', self.on_param_changed)
        self.second_line.trace_add('write', self.on_param_changed)
        self.sub_text_enabled.trace_add('write', self.on_param_changed)
        self.shadow_enabled.trace_add('write', self.on_param_changed)
        self.shadow_opacity.trace_add('write', self.on_shadow_opacity_changed)
        self.width.trace_add('write', self.on_param_changed)
        self.height.trace_add('write', self.on_param_changed)
        self.background_path.trace_add('write', self.on_param_changed)

    def on_shadow_opacity_changed(self, *args):
        self.shadow_opacity_label.config(text=f"{self.shadow_opacity.get():.2f}")
        self.on_param_changed()

    def on_param_changed(self, *args):
        self.update_width_height_state()
        if self.update_job:
            self.root.after_cancel(self.update_job)
        self.update_job = self.root.after(200, self.update_preview)

    def select_background(self):
        path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.background_path.set(path)
            try:
                with Image.open(path) as img:
                    self.width.set(img.width)
                    self.height.set(img.height)
            except:
                pass
            self.update_width_height_state()

    def clear_background(self):
        self.background_path.set("")
        self.update_width_height_state()

    def reset_defaults(self):
        self.background_path.set("")
        self.width.set(1920)
        self.height.set(1080)
        self.main_text.set("主标题")
        self.second_line.set("")
        self.sub_text_enabled.set(False)
        self.shadow_enabled.set(False)
        self.shadow_opacity.set(0.15)
        self.toggle_shadow_slider()
        self.update_width_height_state()
        self.update_preview()

    def update_preview(self):
        self.save_btn.config(state='disabled')
        self.refresh_btn.config(state='disabled')
        self.reset_btn.config(state='disabled')
        self.preview_label.config(text="生成中...")
        self.preview_label.place(relx=0.5, rely=0.5, anchor='center')
        thread = threading.Thread(target=self._generate_preview, daemon=True)
        thread.start()

    def _generate_preview(self):
        try:
            w = self.width.get()
            h = self.height.get()
            if w <= 0 or h <= 0:
                raise ValueError("宽高必须大于0")
            img = generate_image(
                width=w,
                height=h,
                main_text=self.main_text.get(),
                second_line=self.second_line.get(),
                sub_text_enabled=self.sub_text_enabled.get(),
                shadow_enabled=self.shadow_enabled.get(),
                shadow_opacity=self.shadow_opacity.get(),
                background_path=self.background_path.get() if self.background_path.get() else None
            )
            self.preview_img_cache = img
            self.root.after(0, self._show_preview, img)
        except Exception as e:
            self.root.after(0, self._show_error, str(e))

    def _show_preview(self, img):
        canvas_w = self.preview_canvas.winfo_width()
        canvas_h = self.preview_canvas.winfo_height()
        if canvas_w <= 1:
            canvas_w = 600
        if canvas_h <= 1:
            canvas_h = 400
        img_w, img_h = img.size
        scale = min(canvas_w / img_w, canvas_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        preview = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        self.scale_label.config(text=f"缩放: {scale*100:.1f}%")

        if self.checkerboard_photo is None or self.checkerboard_photo.width() != new_w or self.checkerboard_photo.height() != new_h:
            checker_img = self.create_checkerboard(new_w, new_h, 20)
            self.checkerboard_photo = ImageTk.PhotoImage(checker_img)

        self.preview_photo = ImageTk.PhotoImage(preview)

        self.preview_canvas.delete("all")
        x_offset = (canvas_w - new_w) // 2
        y_offset = (canvas_h - new_h) // 2

        self.preview_canvas.create_image(x_offset, y_offset, image=self.checkerboard_photo, anchor='nw')
        self.preview_canvas.create_image(x_offset, y_offset, image=self.preview_photo, anchor='nw')

        self.preview_label.place_forget()
        self.save_btn.config(state='normal')
        self.refresh_btn.config(state='normal')
        self.reset_btn.config(state='normal')

    def _show_error(self, err):
        self.preview_label.config(text=f"生成失败: {err}")
        self.preview_label.place(relx=0.5, rely=0.5, anchor='center')
        self.save_btn.config(state='normal')
        self.refresh_btn.config(state='normal')
        self.reset_btn.config(state='normal')
        messagebox.showerror("错误", f"生成图片失败:\n{err}")

    def save_image(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG图片", "*.png")])
        if path:
            try:
                if self.preview_img_cache is not None:
                    img = self.preview_img_cache
                else:
                    w = self.width.get()
                    h = self.height.get()
                    img = generate_image(
                        width=w,
                        height=h,
                        main_text=self.main_text.get(),
                        second_line=self.second_line.get(),
                        sub_text_enabled=self.sub_text_enabled.get(),
                        shadow_enabled=self.shadow_enabled.get(),
                        shadow_opacity=self.shadow_opacity.get(),
                        background_path=self.background_path.get() if self.background_path.get() else None
                    )
                img.save(path)
                messagebox.showinfo("成功", f"图片已保存到:\n{path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败:\n{e}")

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = TitleGeneratorGUI()
    app.run()