"""レストラン注文システム（tkinter）"""

import tkinter as tk
from tkinter import messagebox, ttk

from menu import ALLERGENS, CATEGORIES, MENU_BY_ID, STORE_NAME, items_in
from order import MAX_QUANTITY, Order
from recommend import GENDERS, MOODS, parse_age, recommend

FONT = "Yu Gothic UI"
ACCENT = "#b5542d"
BG = "#fbf6ef"


def yen(amount):
    sign = "-" if amount < 0 else ""
    return f"{sign}¥{abs(amount):,}"


class OrderApp:
    def __init__(self, root):
        self.root = root
        self.order = Order()
        self.category = None  # None = すべて
        self.recommended = []

        root.title(f"{STORE_NAME} 注文システム")
        root.geometry("1240x780")
        root.minsize(1080, 700)
        root.configure(bg=BG)
        self._setup_style()
        self._build_header()

        body = ttk.Frame(root, padding=(12, 0, 12, 12))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=3)
        body.columnconfigure(2, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_menu_panel(body).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._build_order_panel(body).grid(row=0, column=1, sticky="nsew", padx=8)
        right = ttk.Frame(body)
        right.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        self._build_allergy_panel(right).pack(fill="x", pady=(0, 10))
        self._build_recommend_panel(right).pack(fill="both", expand=True)

        self.select_category(None)
        self.refresh_order()

    # ---------- 見た目 ----------
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=(FONT, 11), background=BG)
        style.configure("TFrame", background=BG)
        style.configure("TLabelframe", background=BG)
        style.configure("TLabelframe.Label", font=(FONT, 12, "bold"), foreground=ACCENT, background=BG)
        style.configure("TLabel", background=BG)
        style.configure("Treeview", font=(FONT, 11), rowheight=28)
        style.configure("Treeview.Heading", font=(FONT, 11, "bold"))
        style.configure("Cat.TButton", padding=(8, 4))
        style.configure("CatOn.TButton", padding=(8, 4), background=ACCENT, foreground="white")
        style.map("CatOn.TButton", background=[("active", "#9a4524")])
        style.configure("Accent.TButton", font=(FONT, 13, "bold"), padding=(10, 8),
                        background=ACCENT, foreground="white")
        style.map("Accent.TButton", background=[("active", "#9a4524")])
        style.configure("Total.TLabel", font=(FONT, 16, "bold"), foreground=ACCENT)

    def _build_header(self):
        header = tk.Frame(self.root, bg=ACCENT)
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text=STORE_NAME, font=(FONT, 24, "bold"),
                 bg=ACCENT, fg="white").pack(side="left", padx=20, pady=10)
        tk.Button(header, text="注文履歴", font=(FONT, 11, "bold"), bg="white", fg=ACCENT,
                  relief="flat", padx=12, cursor="hand2",
                  command=self.show_history).pack(side="right", padx=(0, 20))
        self.slip_label = tk.Label(header, font=(FONT, 12), bg=ACCENT, fg="white")
        self.slip_label.pack(side="right", padx=20)

    # ---------- メニュー ----------
    def _build_menu_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="メニュー", padding=10)

        cats = ttk.Frame(frame)
        cats.pack(fill="x", pady=(0, 8))
        self.cat_buttons = {}
        for i, cat in enumerate([None] + CATEGORIES):
            btn = ttk.Button(cats, text=cat or "すべて", style="Cat.TButton",
                             command=lambda c=cat: self.select_category(c))
            btn.grid(row=i // 3, column=i % 3, sticky="ew", padx=2, pady=2)
            cats.columnconfigure(i % 3, weight=1)
            self.cat_buttons[cat] = btn

        self.menu_tree = ttk.Treeview(frame, columns=("price", "allergen"), show="tree headings",
                                      selectmode="browse")
        self.menu_tree.heading("#0", text="品名")
        self.menu_tree.heading("price", text="価格(税込)")
        self.menu_tree.heading("allergen", text="アレルゲン")
        self.menu_tree.column("#0", width=220)
        self.menu_tree.column("price", width=80, anchor="e")
        self.menu_tree.column("allergen", width=120)
        self.menu_tree.tag_configure("allergy", foreground="#c0392b")
        self.menu_tree.pack(fill="both", expand=True)
        self.menu_tree.bind("<Double-1>", lambda e: self.add_selected())

        qty_row = ttk.Frame(frame)
        qty_row.pack(fill="x", pady=(8, 0))
        ttk.Label(qty_row, text="数量").pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        ttk.Spinbox(qty_row, from_=1, to=MAX_QUANTITY, width=5, textvariable=self.qty_var,
                    font=(FONT, 12)).pack(side="left", padx=6)
        ttk.Button(qty_row, text="注文する", style="Accent.TButton",
                   command=self.add_selected).pack(side="right")
        return frame

    def select_category(self, category):
        self.category = category
        for cat, btn in self.cat_buttons.items():
            btn.configure(style="CatOn.TButton" if cat == category else "Cat.TButton")
        self.menu_tree.delete(*self.menu_tree.get_children())
        avoid = self.avoid
        for item in items_in(category, avoid if self.hide_allergy_var.get() else ()):
            hit = item.allergens_in(avoid)
            self.menu_tree.insert("", "end", iid=str(item.id),
                                  text=f"⚠ {item.name}" if hit else item.name,
                                  values=(yen(item.price), item.allergen_text),
                                  tags=("allergy",) if hit else ())

    def _confirm_allergy(self, items):
        """アレルゲンを含む料理があれば確認する。注文してよければ True。"""
        warnings = [f"・{item.name}（{'・'.join(item.allergens_in(self.avoid))}）"
                    for item in items if item.allergens_in(self.avoid)]
        if not warnings:
            return True
        return messagebox.askyesno(
            "アレルギーの確認",
            "次の料理には、お客様のアレルギー食材が含まれています。\n\n"
            + "\n".join(warnings) + "\n\nそれでも注文しますか？",
            icon="warning", default="no")

    def _read_quantity(self):
        text = self.qty_var.get().strip().translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        try:
            qty = int(text)
        except ValueError:
            qty = None
        if qty is None or not 1 <= qty <= MAX_QUANTITY:
            messagebox.showwarning("数量エラー", f"数量は 1〜{MAX_QUANTITY} の整数で入力してください。")
            self.qty_var.set("1")
            return None
        return qty

    def add_selected(self):
        selected = self.menu_tree.selection()
        if not selected:
            messagebox.showinfo("注文", "メニューから料理を選んでください。")
            return
        qty = self._read_quantity()
        if qty is None:
            return
        item = MENU_BY_ID[int(selected[0])]
        if not self._confirm_allergy([item]):
            return
        self.order.add(item, qty)
        self.qty_var.set("1")
        self.refresh_order()

    # ---------- 注文 ----------
    def _build_order_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="ご注文内容", padding=10)

        self.order_tree = ttk.Treeview(frame, columns=("price", "qty", "sub"), show="tree headings",
                                       selectmode="extended")
        self.order_tree.heading("#0", text="品名")
        self.order_tree.heading("price", text="単価")
        self.order_tree.heading("qty", text="数量")
        self.order_tree.heading("sub", text="金額")
        self.order_tree.column("#0", width=200)
        self.order_tree.column("price", width=70, anchor="e")
        self.order_tree.column("qty", width=50, anchor="center")
        self.order_tree.column("sub", width=80, anchor="e")
        self.order_tree.tag_configure("allergy", foreground="#c0392b")
        self.order_tree.pack(fill="both", expand=True)
        self.order_tree.bind("<Delete>", lambda e: self.cancel_selected())

        ttk.Button(frame, text="選択した注文を取り消す",
                   command=self.cancel_selected).pack(fill="x", pady=(8, 0))

        total_row = ttk.Frame(frame)
        total_row.pack(fill="x", pady=(12, 6))
        ttk.Label(total_row, text="現在の小計", font=(FONT, 12)).pack(side="left")
        self.total_label = ttk.Label(total_row, style="Total.TLabel")
        self.total_label.pack(side="right")

        ttk.Button(frame, text="お会計", style="Accent.TButton",
                   command=self.checkout).pack(fill="x")
        return frame

    def refresh_order(self):
        self.order_tree.delete(*self.order_tree.get_children())
        for line in self.order.lines:
            hit = line.item.allergens_in(self.avoid)
            self.order_tree.insert("", "end", iid=str(line.line_no),
                                   text=f"⚠ {line.item.name}" if hit else line.item.name,
                                   values=(yen(line.item.price), line.quantity, yen(line.subtotal)),
                                   tags=("allergy",) if hit else ())
        self.total_label.configure(text=yen(self.order.total))
        self.slip_label.configure(text=f"伝票番号 No.{self.order.slip_no:04d}")

    def cancel_selected(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showinfo("取消", "取り消す注文を選んでください。")
            return
        names = "\n".join(f"・{self.order_tree.item(iid, 'text')}" for iid in selected)
        if not messagebox.askyesno("取消の確認", f"次の注文を取り消しますか？\n\n{names}"):
            return
        for iid in selected:
            self.order.cancel(int(iid))
        self.refresh_order()

    def checkout(self):
        if not self.order.lines:
            messagebox.showinfo("お会計", "まだ注文がありません。")
            return
        detail = "\n".join(f"{line.item.name} × {line.quantity}　{yen(line.subtotal)}"
                           for line in self.order.lines)
        message = f"{detail}\n\n────────────\n合計金額（税込）　{yen(self.order.total)}"
        if not messagebox.askyesno("お会計", f"{message}\n\nこの内容でお会計しますか？"):
            return
        total = self.order.checkout()
        messagebox.showinfo("お会計完了",
                            f"伝票番号 No.{self.order.slip_no:04d}\n\n"
                            f"合計金額（税込）　{yen(total)}\n\n"
                            f"ご来店ありがとうございました！\n{STORE_NAME}")
        self.order = Order()
        self.clear_allergies()  # アレルギー設定はお客様ごとなので次の伝票ではリセット

    # ---------- アレルギー ----------
    def _build_allergy_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="アレルギー", padding=10)
        ttk.Label(frame, text="お客様のアレルギー食材を選んでください").grid(
            row=0, column=0, columnspan=4, sticky="w")

        self.allergy_vars = {}
        for i, allergen in enumerate(ALLERGENS):
            var = tk.BooleanVar()
            ttk.Checkbutton(frame, text=allergen, variable=var,
                            command=self.on_allergy_change).grid(
                row=1 + i // 4, column=i % 4, sticky="w", padx=(0, 6), pady=2)
            self.allergy_vars[allergen] = var

        self.hide_allergy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="該当する料理をメニューに表示しない",
                        variable=self.hide_allergy_var,
                        command=self.on_allergy_change).grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ttk.Button(frame, text="クリア", command=self.clear_allergies).grid(
            row=4, column=3, sticky="e", pady=(4, 0))
        ttk.Label(frame, text="※特定原材料 8 品目を表示しています。\n※同じ調理器具を使うため、"
                  "微量が混入する場合があります。", foreground="#666", font=(FONT, 9)).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(4, 0))
        return frame

    @property
    def avoid(self):
        """選択中のアレルギー食材"""
        return {a for a, var in self.allergy_vars.items() if var.get()}

    def on_allergy_change(self):
        self.select_category(self.category)
        self.refresh_order()
        if self.recommended:
            # 古いおすすめにアレルゲンが残らないよう選び直してもらう
            self.recommended = []
            self.rec_tree.delete(*self.rec_tree.get_children())
            self.rec_note.configure(text="アレルギーの設定が変わりました。もう一度「おすすめを見る」を押してください。")

    def clear_allergies(self):
        for var in self.allergy_vars.values():
            var.set(False)
        self.hide_allergy_var.set(False)
        self.on_allergy_change()

    # ---------- 履歴 ----------
    def show_history(self):
        HistoryWindow(self.root, self.order.logger)

    # ---------- おすすめ ----------
    def _build_recommend_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="おすすめ診断", padding=10)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="年齢").grid(row=0, column=0, sticky="w", pady=4)
        self.age_var = tk.StringVar()
        age_entry = ttk.Entry(frame, textvariable=self.age_var, font=(FONT, 12))
        age_entry.grid(row=0, column=1, sticky="ew", pady=4)
        age_entry.bind("<Return>", lambda e: self.show_recommend())

        ttk.Label(frame, text="性別").grid(row=1, column=0, sticky="w", pady=4)
        self.gender_var = tk.StringVar(value=GENDERS[0])
        ttk.Combobox(frame, textvariable=self.gender_var, values=GENDERS,
                     state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="気分").grid(row=2, column=0, sticky="w", pady=4)
        self.mood_var = tk.StringVar(value=MOODS[0])
        ttk.Combobox(frame, textvariable=self.mood_var, values=MOODS,
                     state="readonly").grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Button(frame, text="おすすめを見る", command=self.show_recommend).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(8, 8))

        self.rec_tree = ttk.Treeview(frame, columns=("price",), show="tree headings",
                                     height=6, selectmode="extended")
        self.rec_tree.heading("#0", text="おすすめ")
        self.rec_tree.heading("price", text="価格")
        self.rec_tree.column("#0", width=190)
        self.rec_tree.column("price", width=70, anchor="e")
        self.rec_tree.grid(row=4, column=0, columnspan=2, sticky="nsew")
        frame.rowconfigure(4, weight=1)

        self.rec_note = ttk.Label(frame, text="年齢などを入力してください。",
                                  wraplength=250, foreground="#666")
        self.rec_note.grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))

        ttk.Button(frame, text="選んだおすすめを注文（各1つ）", command=self.add_recommended).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        return frame

    def show_recommend(self):
        age, error = parse_age(self.age_var.get())
        if error:
            # 不正な入力でも停止せず、メッセージを出して入力し直してもらう
            messagebox.showwarning("入力エラー", error)
            self.age_var.set("")
            return
        avoid = self.avoid
        self.recommended = recommend(age, self.gender_var.get(), self.mood_var.get(), avoid)
        self.rec_tree.delete(*self.rec_tree.get_children())
        for slot, item, reason in self.recommended:
            self.rec_tree.insert("", "end", iid=str(item.id), text=f"【{slot}】{item.name}",
                                 values=(yen(item.price),))
        self.rec_tree.selection_set(self.rec_tree.get_children())
        reasons = " / ".join(f"{item.name}：{reason}" for _, item, reason in self.recommended)
        note = f"{age}歳の方へのおすすめ　{reasons}"
        if avoid:
            note += f"\n（{'・'.join(a for a in ALLERGENS if a in avoid)} を含む料理は除いています）"
        if len(self.recommended) < 4:
            note += "\n※アレルギー条件に合う料理が無い分類は表示していません。"
        self.rec_note.configure(text=note)

    def add_recommended(self):
        selected = self.rec_tree.selection()
        if not selected:
            messagebox.showinfo("おすすめ", "先に「おすすめを見る」を押して、料理を選んでください。")
            return
        items = [MENU_BY_ID[int(iid)] for iid in selected]
        if not self._confirm_allergy(items):
            return
        for item in items:
            self.order.add(item, 1)
        self.refresh_order()


class HistoryWindow:
    """order_log.csv の記録を伝票ごとに一覧表示する"""

    def __init__(self, root, logger):
        self.logger = logger
        self.win = tk.Toplevel(root)
        self.win.title(f"{STORE_NAME} 注文履歴")
        self.win.geometry("980x560")
        self.win.configure(bg=BG)
        self.win.transient(root)

        body = ttk.Frame(self.win, padding=12)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(body, text="伝票一覧（新しい順）", padding=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.slip_tree = ttk.Treeview(left, columns=("time", "status", "total"),
                                      show="tree headings", selectmode="browse")
        self.slip_tree.heading("#0", text="伝票")
        self.slip_tree.heading("time", text="日時")
        self.slip_tree.heading("status", text="状態")
        self.slip_tree.heading("total", text="金額")
        self.slip_tree.column("#0", width=80)
        self.slip_tree.column("time", width=150)
        self.slip_tree.column("status", width=70, anchor="center")
        self.slip_tree.column("total", width=80, anchor="e")
        self.slip_tree.tag_configure("unpaid", foreground="#999")
        self.slip_tree.pack(fill="both", expand=True)
        self.slip_tree.bind("<<TreeviewSelect>>", lambda e: self.show_detail())

        right = ttk.LabelFrame(body, text="明細", padding=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.detail_tree = ttk.Treeview(right, columns=("action", "price", "qty", "amount"),
                                        show="tree headings", selectmode="none")
        self.detail_tree.heading("#0", text="日時")
        self.detail_tree.heading("action", text="操作")
        self.detail_tree.heading("price", text="単価")
        self.detail_tree.heading("qty", text="数量")
        self.detail_tree.heading("amount", text="金額")
        self.detail_tree.column("#0", width=150)
        self.detail_tree.column("action", width=230)
        self.detail_tree.column("price", width=70, anchor="e")
        self.detail_tree.column("qty", width=50, anchor="center")
        self.detail_tree.column("amount", width=80, anchor="e")
        self.detail_tree.tag_configure("cancel", foreground="#c0392b")
        self.detail_tree.tag_configure("checkout", font=(FONT, 11, "bold"))
        self.detail_tree.pack(fill="both", expand=True)

        bottom = ttk.Frame(body)
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.summary = ttk.Label(bottom, style="Total.TLabel")
        self.summary.pack(side="left")
        ttk.Button(bottom, text="閉じる", command=self.win.destroy).pack(side="right")
        ttk.Button(bottom, text="更新", command=self.reload).pack(side="right", padx=8)

        self.reload()

    def reload(self):
        try:
            self.slips = {slip.slip_no: slip for slip in self.logger.history()}
        except (OSError, UnicodeDecodeError) as e:
            messagebox.showerror("履歴", f"履歴ファイルを読み込めませんでした。\n{e}", parent=self.win)
            self.slips = {}
        self.slip_tree.delete(*self.slip_tree.get_children())
        self.detail_tree.delete(*self.detail_tree.get_children())
        for slip in self.slips.values():
            if slip.paid:
                time, status, tags = slip.checkout_row["日時"], "会計済", ()
            else:
                time, status, tags = slip.started_at, "未会計", ("unpaid",)
            self.slip_tree.insert("", "end", iid=str(slip.slip_no), text=f"No.{slip.slip_no:04d}",
                                  values=(time, status, yen(slip.total)), tags=tags)
        paid = [s for s in self.slips.values() if s.paid]
        self.summary.configure(
            text=f"会計済 {len(paid)} 件　売上合計 {yen(sum(s.total for s in paid))}")
        if self.slips:
            first = self.slip_tree.get_children()[0]
            self.slip_tree.selection_set(first)
        else:
            self.detail_tree.insert("", "end", text="まだ履歴がありません。", values=("", "", "", ""))

    def show_detail(self):
        selected = self.slip_tree.selection()
        if not selected:
            return
        self.detail_tree.delete(*self.detail_tree.get_children())
        for row in self.slips[int(selected[0])].rows:
            action = row.get("操作", "")
            if action == "会計":
                label, tags = "お会計", ("checkout",)
            else:
                label = f"{action}：{row.get('品名', '')}"
                tags = ("cancel",) if action == "取消" else ()
            price = row.get("単価") or ""
            amount = row.get("金額") or ""
            self.detail_tree.insert("", "end", text=row.get("日時", ""), tags=tags, values=(
                label,
                yen(int(price)) if price.lstrip("-").isdigit() else price,
                row.get("数量", ""),
                yen(int(amount)) if amount.lstrip("-").isdigit() else amount,
            ))


def show_splash(root):
    """起動時に店名を表示するスプラッシュ画面"""
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    w, h = 520, 220
    x = (splash.winfo_screenwidth() - w) // 2
    y = (splash.winfo_screenheight() - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")
    splash.configure(bg=ACCENT)
    tk.Label(splash, text="いらっしゃいませ", font=(FONT, 14), bg=ACCENT, fg="white").pack(pady=(40, 6))
    tk.Label(splash, text=STORE_NAME, font=(FONT, 26, "bold"), bg=ACCENT, fg="white").pack()
    return splash


def main():
    root = tk.Tk()
    root.withdraw()
    splash = show_splash(root)

    def start():
        splash.destroy()
        OrderApp(root)
        root.deiconify()

    root.after(1800, start)
    root.mainloop()


if __name__ == "__main__":
    main()
