"""
Admin and Management Module Views
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from config import COLORS, FONTS, ROLES
from views.base_view import add_treeview_scrollbars
from models.db_models import (
    get_dashboard_stats, get_all_staff, add_staff, update_staff,
    get_all_branches, add_branch, update_branch,
    get_all_parcels, update_parcel_status,
    get_all_transactions, get_all_charges, update_charge_rule,
    get_all_users, update_user_status, reset_user_password, create_user,
    get_transactions_by_date_range, get_parcels_by_date_range, get_report_summary
)


class AdminDashboardView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        stats = get_dashboard_stats()

        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        page_scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        page = tk.Frame(canvas, bg=COLORS["bg"])
        page_window = canvas.create_window((0, 0), window=page, anchor="nw")
        canvas.configure(yscrollcommand=page_scrollbar.set)
        page.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(page_window, width=event.width),
        )
        canvas.pack(side="left", fill="both", expand=True)
        page_scrollbar.pack(side="right", fill="y")

        # Header
        header = tk.Frame(page, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 15))
        title_label = tk.Label(
            header,
            text="📊 Admin & Management Dashboard",
            font=FONTS["heading"],
            bg=COLORS["bg"],
            fg=COLORS["text_primary"],
            justify="left",
        )
        title_label.pack(anchor="w")
        header.bind(
            "<Configure>",
            lambda event: title_label.configure(wraplength=max(event.width, 1)),
        )

        # KPI Stats Cards Grid
        cards_frame = tk.Frame(page, bg=COLORS["bg"])
        cards_frame.pack(fill="x", pady=10)

        card_data = [
            ("Total Parcels", stats["total_parcels"], COLORS["accent"]),
            ("Pending / Processing", stats["pending"], COLORS["warning"]),
            ("In Transit", stats["in_transit"], "#8b5cf6"),
            ("Out for Delivery", stats["out_for_delivery"], "#06b6d4"),
            ("Delivered Successfully", stats["delivered"], COLORS["success"]),
            ("Delivery Failed", stats["failed"], COLORS["danger"]),
            ("Active Staff", stats["active_staff"], "#475569"),
            ("Total Revenue (INR)", f"₹{stats['total_revenue']:,.2f}", COLORS["success"]),
        ]

        self.stat_cards = []
        for stat_title, val, color in card_data:
            card = tk.Frame(cards_frame, bg=COLORS["card_bg"], padx=15, pady=15, relief="flat", bd=0,
                            highlightthickness=0)
            tk.Label(card, text=stat_title, font=FONTS["small"], bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(anchor="w")
            tk.Label(card, text=str(val), font=("Arial", 27, "bold"), bg=COLORS["card_bg"], fg=color).pack(anchor="w", pady=(5, 0))
            self.stat_cards.append(card)

        self._layout_stat_cards(cards_frame, cards_frame.winfo_width())
        cards_frame.bind(
            "<Configure>",
            lambda event: self._layout_stat_cards(cards_frame, event.width),
        )

        # Recent Parcels Preview Table
        recent_frame = tk.LabelFrame(
            page,
            text="Recent Parcels Activity",
            font=FONTS["subheading"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_primary"],
            padx=10,
            pady=10,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        recent_frame.pack(fill="both", expand=True, pady=10)

        cols = ("tracking", "sender", "receiver", "type", "charge", "status", "date")
        tree = ttk.Treeview(recent_frame, columns=cols, show="headings", height=8)
        add_treeview_scrollbars(tree)
        tree.heading("tracking", text="Tracking #")
        tree.heading("sender", text="Sender")
        tree.heading("receiver", text="Receiver")
        tree.heading("type", text="Type")
        tree.heading("charge", text="Charge (₹)")
        tree.heading("status", text="Status")
        tree.heading("date", text="Booked Date")

        for col in cols:
            tree.column(col, anchor="center")

        tree.pack(fill="both", expand=True)

        for p in get_all_parcels()[:15]:
            tree.insert("", "end", values=(
                p["tracking_number"],
                p["sender_name"],
                p["receiver_name"],
                p["parcel_type"],
                f"₹{p['total_charge']:.2f}",
                p["status"],
                p["booked_at"]
            ))

    def _layout_stat_cards(self, cards_frame, available_width):
        columns = max(1, min(3, available_width // 220))
        for column in range(3):
            cards_frame.grid_columnconfigure(
                column,
                weight=1 if column < columns else 0,
                uniform="stat_card",
            )
        for index, card in enumerate(self.stat_cards):
            card.grid(
                row=index // columns,
                column=index % columns,
                padx=8,
                pady=8,
                sticky="nsew",
            )


class StaffManagementView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.branches = get_all_branches(active_only=True)
        self.branch_map = {b["name"]: b["id"] for b in self.branches}
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="👥 Staff Management", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")
        tk.Button(header, text="➕ Add New Staff", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", padx=12, pady=5, relief="flat", command=self._open_add_dialog).pack(side="right")

        # Treeview
        tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "emp_id", "name", "phone", "email", "branch", "username", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.tree)
        self.tree.heading("id", text="ID")
        self.tree.heading("emp_id", text="Emp ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("email", text="Email")
        self.tree.heading("branch", text="Assigned Branch")
        self.tree.heading("username", text="Username")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("emp_id", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in get_all_staff():
            self.tree.insert("", "end", values=(
                s["id"], s["employee_id"], s["name"], s["phone"], s["email"] or "-",
                s["branch_name"] or "None", s["username"], "Active" if s["is_active"] else "Inactive"
            ))

    def _open_add_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Staff Member")
        dlg.geometry("450x480")
        dlg.configure(bg="#ffffff")
        dlg.transient(self)
        dlg.grab_set()

        fields = [
            ("Full Name:", "name"),
            ("Employee ID:", "emp_id"),
            ("Phone:", "phone"),
            ("Email:", "email"),
            ("Username:", "username"),
            ("Password:", "password"),
        ]
        entries = {}

        for i, (label, key) in enumerate(fields):
            tk.Label(dlg, text=label, font=FONTS["body"], bg="#ffffff").grid(row=i, column=0, padx=15, pady=8, sticky="w")
            ent = ttk.Entry(dlg, width=28, show="*" if key == "password" else "")
            ent.grid(row=i, column=1, padx=15, pady=8, sticky="w")
            entries[key] = ent

        tk.Label(dlg, text="Assigned Branch:", font=FONTS["body"], bg="#ffffff").grid(row=len(fields), column=0, padx=15, pady=8, sticky="w")
        branch_cb = ttk.Combobox(dlg, values=list(self.branch_map.keys()), state="readonly", width=26)
        if self.branch_map:
            branch_cb.current(0)
        branch_cb.grid(row=len(fields), column=1, padx=15, pady=8, sticky="w")

        def save():
            name = entries["name"].get().strip()
            emp_id = entries["emp_id"].get().strip()
            phone = entries["phone"].get().strip()
            email = entries["email"].get().strip()
            uname = entries["username"].get().strip()
            pwd = entries["password"].get().strip()
            branch_name = branch_cb.get()

            if not all([name, emp_id, phone, uname, pwd]):
                messagebox.showerror("Error", "Please fill in all required fields!")
                return

            branch_id = self.branch_map.get(branch_name)
            res, err = add_staff(name, phone, email, branch_id, emp_id, uname, pwd)
            if err:
                messagebox.showerror("Error", err)
            else:
                messagebox.showinfo("Success", "Staff member created successfully!")
                dlg.destroy()
                self._refresh()

        tk.Button(dlg, text="Save Staff", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", command=save, padx=15, pady=5).grid(row=len(fields)+1, column=0, columnspan=2, pady=20)


class BranchManagementView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="🏢 Branch Management", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")
        tk.Button(header, text="➕ Add New Branch", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", padx=12, pady=5, relief="flat", command=self._open_add_dialog).pack(side="right")

        tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "code", "name", "city", "state", "pincode", "phone", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.tree)
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Branch Code")
        self.tree.heading("name", text="Name")
        self.tree.heading("city", text="City")
        self.tree.heading("state", text="State")
        self.tree.heading("pincode", text="Pincode")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("status", text="Status")
        self.tree.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for b in get_all_branches():
            self.tree.insert("", "end", values=(
                b["id"], b["branch_code"], b["name"], b["city"], b["state"],
                b["pincode"], b["phone"], "Active" if b["is_active"] else "Inactive"
            ))

    def _open_add_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add New Branch")
        dlg.geometry("450x450")
        dlg.configure(bg="#ffffff")
        dlg.transient(self)
        dlg.grab_set()

        fields = [
            ("Branch Code:", "code"),
            ("Branch Name:", "name"),
            ("Address:", "address"),
            ("City:", "city"),
            ("State:", "state"),
            ("Pincode:", "pincode"),
            ("Phone:", "phone"),
        ]
        entries = {}

        for i, (label, key) in enumerate(fields):
            tk.Label(dlg, text=label, font=FONTS["body"], bg="#ffffff").grid(row=i, column=0, padx=15, pady=6, sticky="w")
            ent = ttk.Entry(dlg, width=28)
            ent.grid(row=i, column=1, padx=15, pady=6, sticky="w")
            entries[key] = ent

        def save():
            code = entries["code"].get().strip()
            name = entries["name"].get().strip()
            addr = entries["address"].get().strip()
            city = entries["city"].get().strip()
            state = entries["state"].get().strip()
            pin = entries["pincode"].get().strip()
            phone = entries["phone"].get().strip()

            if not code or not name:
                messagebox.showerror("Error", "Branch code and name are required!")
                return

            res, err = add_branch(code, name, addr, city, state, pin, phone)
            if err:
                messagebox.showerror("Error", err)
            else:
                messagebox.showinfo("Success", "Branch created successfully!")
                dlg.destroy()
                self._refresh()

        tk.Button(dlg, text="Save Branch", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", command=save, padx=15, pady=5).grid(row=len(fields), column=0, columnspan=2, pady=15)


class ParcelOversightView(tk.Frame):
    def __init__(self, parent, user_session):
        super().__init__(parent, bg=COLORS["bg"])
        self.user_session = user_session
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="📦 All Parcels Oversight", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")

        # Search filter bar
        filter_bar = tk.Frame(self, bg=COLORS["card_bg"], padx=10, pady=8)
        filter_bar.pack(fill="x", pady=(0, 10))

        tk.Label(filter_bar, text="Search Tracking/Sender/Receiver:", font=FONTS["body"], bg=COLORS["card_bg"]).pack(side="left", padx=5)
        self.search_ent = ttk.Entry(filter_bar, width=25)
        self.search_ent.pack(side="left", padx=5)

        tk.Button(filter_bar, text="🔍 Search", font=FONTS["small"], bg=COLORS["accent"], fg="#fff", command=self._refresh).pack(side="left", padx=5)
        tk.Button(filter_bar, text="Clear", font=FONTS["small"], bg=COLORS["neutral"], fg=COLORS["text_primary"], activebackground=COLORS["neutral_hover"], activeforeground=COLORS["text_primary"], command=lambda: [self.search_ent.delete(0, "end"), self._refresh()]).pack(side="left", padx=5)

        # Treeview
        tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "tracking", "sender", "receiver", "route", "type", "weight", "charge", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.tree)
        self.tree.heading("id", text="ID")
        self.tree.heading("tracking", text="Tracking #")
        self.tree.heading("sender", text="Sender")
        self.tree.heading("receiver", text="Receiver")
        self.tree.heading("route", text="Route")
        self.tree.heading("type", text="Type")
        self.tree.heading("weight", text="Weight (kg)")
        self.tree.heading("charge", text="Charge (₹)")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=35, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Admin Action controls
        action_bar = tk.Frame(self, bg=COLORS["card_bg"], padx=10, pady=8)
        action_bar.pack(fill="x", pady=10)
        tk.Button(action_bar, text="✏️ Override Parcel Status", font=FONTS["button"], bg=COLORS["warning"], fg="#fff", command=self._override_status).pack(side="left", padx=5)

        # Allow user to click any row and select tracking number text directly in an entry box
        tk.Label(action_bar, text="Selected UID:", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(side="left", padx=(20, 5))
        self.selected_uid_ent = tk.Entry(action_bar, font=("Consolas", 11, "bold"), width=22, bd=1, relief="solid")
        self.selected_uid_ent.pack(side="left", padx=5)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Control-c>", self._on_tree_copy)

        self._refresh()

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0], "values")
            if len(vals) > 1:
                self.selected_uid_ent.delete(0, "end")
                self.selected_uid_ent.insert(0, vals[1])

    def _on_tree_copy(self, event):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0], "values")
            if len(vals) > 1:
                self.clipboard_clear()
                self.clipboard_append(vals[1])
                self.update()


    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        q = self.search_ent.get().strip()
        for p in get_all_parcels(search_query=q):
            self.tree.insert("", "end", values=(
                p["id"], p["tracking_number"], p["sender_name"], p["receiver_name"],
                f"{p['source_branch_name']} -> {p['dest_branch_name']}",
                p["parcel_type"], p["weight_kg"], f"₹{p['total_charge']:.2f}",
                p["status"]
            ))

    def _override_status(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a parcel from table first!")
            return
        vals = self.tree.item(sel[0], "values")
        parcel_id = vals[0]
        tracking_no = vals[1]

        dlg = tk.Toplevel(self)
        dlg.title(f"Override Status - {tracking_no}")
        dlg.geometry("380x250")
        dlg.configure(bg="#ffffff")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Select New Status:", font=FONTS["body"], bg="#ffffff").pack(pady=(15, 5))
        from config import PARCEL_STATUSES
        st_cb = ttk.Combobox(dlg, values=PARCEL_STATUSES, state="readonly", width=25)
        st_cb.current(0)
        st_cb.pack(pady=5)

        tk.Label(dlg, text="Remarks / Reason:", font=FONTS["body"], bg="#ffffff").pack(pady=(10, 5))
        rem_ent = ttk.Entry(dlg, width=30)
        rem_ent.pack(pady=5)

        def save():
            new_st = st_cb.get()
            rem = rem_ent.get().strip() or "Status updated by administrator"
            update_parcel_status(parcel_id, new_st, "Admin Center", self.user_session["id"], rem)
            messagebox.showinfo("Success", "Status updated successfully!")
            dlg.destroy()
            self._refresh()

        tk.Button(dlg, text="Save Status", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", command=save, padx=15, pady=5).pack(pady=15)


class TransactionsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="💳 Transactions & Payment Records", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")

        tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "tracking", "amount", "method", "status", "date", "recorded_by")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.tree)
        self.tree.heading("id", text="Txn ID")
        self.tree.heading("tracking", text="Parcel Tracking #")
        self.tree.heading("amount", text="Amount (₹)")
        self.tree.heading("method", text="Payment Method")
        self.tree.heading("status", text="Payment Status")
        self.tree.heading("date", text="Date")
        self.tree.heading("recorded_by", text="Recorded By")
        self.tree.pack(fill="both", expand=True)

        for t in get_all_transactions():
            self.tree.insert("", "end", values=(
                t["id"], t["tracking_number"], f"₹{t['amount']:.2f}",
                t["payment_method"], t["payment_status"], t["payment_date"],
                t["recorded_by_user"] or "System"
            ))


class ChargeConfigView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="⚙️ Delivery Charges Configuration", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")

        tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "name", "type", "base", "per_kg", "per_km", "express")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.tree)
        self.tree.heading("id", text="Rule ID")
        self.tree.heading("name", text="Rule Name")
        self.tree.heading("type", text="Parcel Type")
        self.tree.heading("base", text="Base Charge (₹)")
        self.tree.heading("per_kg", text="Rate / kg (₹)")
        self.tree.heading("per_km", text="Rate / km (₹)")
        self.tree.heading("express", text="Express Multiplier")
        self.tree.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in get_all_charges():
            self.tree.insert("", "end", values=(
                r["id"], r["name"], r["parcel_type"],
                f"₹{r['base_charge']:.2f}", f"₹{r['per_kg_rate']:.2f}",
                f"₹{r['per_km_rate']:.2f}", f"{r['express_multiplier']}x"
            ))


class UserManagementView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="🔐 User Accounts & Permissions", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")

        tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "username", "role", "status", "created_at")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.tree)
        self.tree.heading("id", text="User ID")
        self.tree.heading("username", text="Username")
        self.tree.heading("role", text="System Role")
        self.tree.heading("status", text="Account Status")
        self.tree.heading("created_at", text="Registered On")
        self.tree.pack(fill="both", expand=True)

        for u in get_all_users():
            self.tree.insert("", "end", values=(
                u["id"], u["username"], u["role"].capitalize(),
                "Active" if u["is_active"] else "Deactivated", u["created_at"]
            ))


class ReportView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 15))
        tk.Label(header, text="📋 Reports & Analytics", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(anchor="w")

        # Date Range Filter
        filter_frame = tk.LabelFrame(self, text="Date Range Filter", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=15, pady=10)
        filter_frame.pack(fill="x", pady=(0, 10))

        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1)
        tk.Label(filter_frame, text="From Date:", font=FONTS["body"], bg=COLORS["card_bg"]).grid(row=0, column=0, padx=5, pady=4, sticky="w")
        self.from_date = ttk.Entry(filter_frame, width=15, font=FONTS["entry"])
        self.from_date.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
        self.from_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(filter_frame, text="To Date:", font=FONTS["body"], bg=COLORS["card_bg"]).grid(row=0, column=2, padx=5, pady=4, sticky="w")
        self.to_date = ttk.Entry(filter_frame, width=15, font=FONTS["entry"])
        self.to_date.grid(row=0, column=3, padx=5, pady=4, sticky="ew")
        self.to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        actions_frame = tk.Frame(filter_frame, bg=COLORS["card_bg"])
        actions_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 0))
        tk.Button(actions_frame, text="🔍 Generate Report", font=FONTS["button"], bg=COLORS["accent"], fg="#fff",
                  command=self._generate_report).pack(side="left", padx=(0, 8))
        tk.Button(actions_frame, text="🖨️ Print Report", font=FONTS["button"], bg=COLORS["success"], fg="#fff",
                  command=self._print_report).pack(side="left", padx=5)
        tk.Button(actions_frame, text="📊 Quick Stats", font=FONTS["button"], bg=COLORS["warning"], fg="#fff",
                  command=self._show_summary).pack(side="left", padx=5)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Summary Tab
        self.summary_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.summary_frame, text="📊 Summary")

        # Transactions Tab
        self.trans_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.trans_frame, text="💳 Transactions")

        # Parcels Tab
        self.parcels_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.parcels_frame, text="📦 Parcels")

        self._build_summary_tab()
        self._build_transactions_tab()
        self._build_parcels_tab()

    def _build_summary_tab(self):
        # Summary cards
        self.summary_cards_frame = tk.Frame(self.summary_frame, bg=COLORS["bg"])
        self.summary_cards_frame.pack(fill="x", padx=10, pady=10)

        # Breakdown tables
        breakdown_frame = tk.Frame(self.summary_frame, bg=COLORS["bg"])
        breakdown_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Status breakdown
        status_frame = tk.LabelFrame(breakdown_frame, text="Parcels by Status", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=10, pady=10)
        status_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.status_tree = ttk.Treeview(status_frame, columns=("status", "count"), show="headings", height=8)
        add_treeview_scrollbars(self.status_tree)
        self.status_tree.heading("status", text="Status")
        self.status_tree.heading("count", text="Count")
        self.status_tree.column("status", width=150)
        self.status_tree.column("count", width=80, anchor="center")
        self.status_tree.pack(fill="both", expand=True)

        # Type breakdown
        type_frame = tk.LabelFrame(breakdown_frame, text="Parcels by Type", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=10, pady=10)
        type_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.type_tree = ttk.Treeview(type_frame, columns=("type", "count"), show="headings", height=8)
        add_treeview_scrollbars(self.type_tree)
        self.type_tree.heading("type", text="Parcel Type")
        self.type_tree.heading("count", text="Count")
        self.type_tree.column("type", width=150)
        self.type_tree.column("count", width=80, anchor="center")
        self.type_tree.pack(fill="both", expand=True)

        # Payment breakdown
        payment_frame = tk.LabelFrame(breakdown_frame, text="Payments by Method", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=10, pady=10)
        payment_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.payment_tree = ttk.Treeview(payment_frame, columns=("method", "count", "total"), show="headings", height=8)
        add_treeview_scrollbars(self.payment_tree)
        self.payment_tree.heading("method", text="Method")
        self.payment_tree.heading("count", text="Count")
        self.payment_tree.heading("total", text="Total (₹)")
        self.payment_tree.column("method", width=100)
        self.payment_tree.column("count", width=80, anchor="center")
        self.payment_tree.column("total", width=100, anchor="e")
        self.payment_tree.pack(fill="both", expand=True)

    def _build_transactions_tab(self):
        # Toolbar
        toolbar = tk.Frame(self.trans_frame, bg=COLORS["card_bg"], padx=10, pady=5)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="Transactions", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(side="left")

        # Treeview
        tree_frame = tk.Frame(self.trans_frame, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "date", "tracking", "sender", "receiver", "type", "weight", "amount", "method", "status")
        self.trans_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.trans_tree)
        self.trans_tree.heading("id", text="ID")
        self.trans_tree.heading("date", text="Date")
        self.trans_tree.heading("tracking", text="Tracking #")
        self.trans_tree.heading("sender", text="Sender")
        self.trans_tree.heading("receiver", text="Receiver")
        self.trans_tree.heading("type", text="Type")
        self.trans_tree.heading("weight", text="Weight (kg)")
        self.trans_tree.heading("amount", text="Amount (₹)")
        self.trans_tree.heading("method", text="Method")
        self.trans_tree.heading("status", text="Payment Status")
        self.trans_tree.column("id", width=40, anchor="center")
        self.trans_tree.column("date", width=120, anchor="center")
        self.trans_tree.column("tracking", width=130, anchor="center")
        self.trans_tree.column("amount", width=100, anchor="e")
        self.trans_tree.pack(fill="both", expand=True)

    def _build_parcels_tab(self):
        # Toolbar
        toolbar = tk.Frame(self.parcels_frame, bg=COLORS["card_bg"], padx=10, pady=5)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="Parcels", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(side="left")

        # Treeview
        tree_frame = tk.Frame(self.parcels_frame, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "date", "tracking", "sender", "receiver", "route", "type", "weight", "status", "payment")
        self.parcels_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.parcels_tree)
        self.parcels_tree.heading("id", text="ID")
        self.parcels_tree.heading("date", text="Booked Date")
        self.parcels_tree.heading("tracking", text="Tracking #")
        self.parcels_tree.heading("sender", text="Sender")
        self.parcels_tree.heading("receiver", text="Receiver")
        self.parcels_tree.heading("route", text="Route")
        self.parcels_tree.heading("type", text="Type")
        self.parcels_tree.heading("weight", text="Weight (kg)")
        self.parcels_tree.heading("status", text="Status")
        self.parcels_tree.heading("payment", text="Payment")
        self.parcels_tree.column("id", width=40, anchor="center")
        self.parcels_tree.column("date", width=120, anchor="center")
        self.parcels_tree.column("tracking", width=130, anchor="center")
        self.parcels_tree.pack(fill="both", expand=True)

    def _generate_report(self):
        from_date = self.from_date.get().strip()
        to_date = self.to_date.get().strip()

        if not from_date or not to_date:
            messagebox.showwarning("Warning", "Please enter both From and To dates!")
            return

        try:
            # Validate date format
            datetime.strptime(from_date, "%Y-%m-%d")
            datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
            return

        # Fetch data
        self.transactions = get_transactions_by_date_range(from_date, to_date)
        self.parcels = get_parcels_by_date_range(from_date, to_date)
        self.summary = get_report_summary(from_date, to_date)

        self._update_summary_cards()
        self._update_summary_tables()
        self._update_transactions_table()
        self._update_parcels_table()

        messagebox.showinfo("Success", f"Report generated for {from_date} to {to_date}")

    def _update_summary_cards(self):
        for widget in self.summary_cards_frame.winfo_children():
            widget.destroy()

        cards = [
            ("Total Parcels", str(self.summary["total_parcels"]), COLORS["accent"]),
            ("Total Revenue", f"₹{self.summary['total_revenue']:,.2f}", COLORS["success"]),
        ]
        for i, (title, val, color) in enumerate(cards):
            card = tk.Frame(self.summary_cards_frame, bg=COLORS["card_bg"], padx=20, pady=15, relief="flat", bd=0)
            card.grid(row=0, column=i, padx=10, sticky="ew")
            self.summary_cards_frame.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=title, font=FONTS["small"], bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack()
            tk.Label(card, text=val, font=("Arial", 27, "bold"), bg=COLORS["card_bg"], fg=color).pack()

    def _update_summary_tables(self):
        # Status breakdown
        for item in self.status_tree.get_children():
            self.status_tree.delete(item)
        for status, count in self.summary["status_breakdown"].items():
            self.status_tree.insert("", "end", values=(status, count))

        # Type breakdown
        for item in self.type_tree.get_children():
            self.type_tree.delete(item)
        for ptype, count in self.summary["type_breakdown"].items():
            self.type_tree.insert("", "end", values=(ptype, count))

        # Payment breakdown
        for item in self.payment_tree.get_children():
            self.payment_tree.delete(item)
        for method, data in self.summary["payment_breakdown"].items():
            self.payment_tree.insert("", "end", values=(method, data["count"], f"₹{data['total']:,.2f}"))

    def _update_transactions_table(self):
        for item in self.trans_tree.get_children():
            self.trans_tree.delete(item)
        for t in self.transactions:
            self.trans_tree.insert("", "end", values=(
                t["id"], t["payment_date"], t["tracking_number"],
                t["sender_name"], t["receiver_name"], t["parcel_type"],
                t["weight_kg"], f"₹{t['amount']:.2f}", t["payment_method"], t["payment_status"]
            ))

    def _update_parcels_table(self):
        for item in self.parcels_tree.get_children():
            self.parcels_tree.delete(item)
        for p in self.parcels:
            route = f"{p['source_branch_name']} → {p['dest_branch_name']}"
            payment = f"{p['payment_method']} ({p['payment_status']})"
            self.parcels_tree.insert("", "end", values=(
                p["id"], p["booked_at"], p["tracking_number"],
                p["sender_name"], p["receiver_name"], route,
                p["parcel_type"], p["weight_kg"], p["status"], payment
            ))

    def _show_summary(self):
        """Switch to summary tab"""
        self.notebook.select(self.summary_frame)

    def _print_report(self):
        """Generate printable HTML report and open print dialog"""
        if not hasattr(self, 'summary') or not self.summary:
            messagebox.showwarning("Warning", "Please generate a report first!")
            return

        from_date = self.from_date.get().strip()
        to_date = self.to_date.get().strip()

        html = self._generate_html_report(from_date, to_date)

        # Save to temp file and open in browser for printing
        import tempfile
        import webbrowser
        import os

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html)
                temp_path = f.name
            
            # Open in default browser for printing
            webbrowser.open(f'file://{os.path.abspath(temp_path)}')
            messagebox.showinfo("Print", "Report opened in browser. Use Ctrl+P to print.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate print: {e}")

    def _generate_html_report(self, from_date, to_date):
        """Generate HTML report for printing"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Courier Management Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; color: #25243A; background: #F7F7FC; }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #6957D8; padding-bottom: 15px; }}
        .header h1 {{ margin: 0; color: #25243A; }}
        .header p {{ margin: 5px 0; color: #85849A; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #6957D8; border-bottom: 1px solid #E6E5EF; padding-bottom: 5px; }}
        .summary-cards {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .card {{ flex: 1; padding: 15px; background: #FFFFFF; border: 0; border-radius: 12px; text-align: center; }}
        .card-title {{ font-size: 12px; color: #85849A; text-transform: uppercase; letter-spacing: 0.5px; }}
        .card-value {{ font-size: 27px; font-weight: bold; color: #6957D8; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #E6E5EF; }}
        th {{ background: #EEEAFE; font-weight: 600; color: #25243A; }}
        tr:nth-child(even) {{ background: #F9F9FD; }}
        .text-right {{ text-align: right; }}
        .text-center {{ text-align: center; }}
        @media print {{
            .no-print {{ display: none; }}
            body {{ margin: 0; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📦 Courier Management System</h1>
        <p>Report Period: {from_date} to {to_date}</p>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <div class="section">
        <h2>📊 Summary</h2>
        <div class="summary-cards">
            <div class="card">
                <div class="card-title">Total Parcels</div>
                <div class="card-value">{self.summary['total_parcels']}</div>
            </div>
            <div class="card">
                <div class="card-title">Total Revenue</div>
                <div class="card-value">₹{self.summary['total_revenue']:,.2f}</div>
            </div>
        </div>

        <h3>Parcels by Status</h3>
        <table>
            <thead><tr><th>Status</th><th class="text-center">Count</th></tr></thead>
            <tbody>"""

        for status, count in self.summary["status_breakdown"].items():
            html += f"<tr><td>{status}</td><td class='text-center'>{count}</td></tr>"

        html += """</tbody></table>

        <h3>Parcels by Type</h3>
        <table>
            <thead><tr><th>Type</th><th class="text-center">Count</th></tr></thead>
            <tbody>"""

        for ptype, count in self.summary["type_breakdown"].items():
            html += f"<tr><td>{ptype}</td><td class='text-center'>{count}</td></tr>"

        html += """</tbody></table>

        <h3>Payments by Method</h3>
        <table>
            <thead><tr><th>Method</th><th class="text-center">Count</th><th class="text-right">Total (₹)</th></tr></thead>
            <tbody>"""

        for method, data in self.summary["payment_breakdown"].items():
            html += f"<tr><td>{method}</td><td class='text-center'>{data['count']}</td><td class='text-right'>₹{data['total']:,.2f}</td></tr>"

        html += """</tbody></table>
    </div>

    <div class="section">
        <h2>💳 Transactions</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Date</th><th>Tracking #</th>
                    <th>Sender</th><th>Receiver</th><th>Type</th>
                    <th class="text-center">Weight (kg)</th>
                    <th class="text-right">Amount (₹)</th>
                    <th>Method</th><th>Status</th>
                </tr>
            </thead>
            <tbody>"""

        for t in self.transactions:
            html += f"""<tr>
                <td>{t['id']}</td><td>{t['payment_date']}</td><td>{t['tracking_number']}</td>
                <td>{t['sender_name']}</td><td>{t['receiver_name']}</td><td>{t['parcel_type']}</td>
                <td class="text-center">{t['weight_kg']}</td><td class="text-right">₹{t['amount']:.2f}</td>
                <td>{t['payment_method']}</td><td>{t['payment_status']}</td>
            </tr>"""

        html += """</tbody></table>
    </div>

    <div class="section">
        <h2>📦 Parcels</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Booked Date</th><th>Tracking #</th>
                    <th>Sender</th><th>Receiver</th><th>Route</th>
                    <th>Type</th><th class="text-center">Weight (kg)</th>
                    <th>Status</th><th>Payment</th>
                </tr>
            </thead>
            <tbody>"""

        for p in self.parcels:
            route = f"{p['source_branch_name']} → {p['dest_branch_name']}"
            payment = f"{p['payment_method']} ({p['payment_status']})"
            html += f"""<tr>
                <td>{p['id']}</td><td>{p['booked_at']}</td><td>{p['tracking_number']}</td>
                <td>{p['sender_name']}</td><td>{p['receiver_name']}</td><td>{route}</td>
                <td>{p['parcel_type']}</td><td class="text-center">{p['weight_kg']}</td>
                <td>{p['status']}</td><td>{payment}</td>
            </tr>"""

        html += """</tbody></table>
    </div>

    <div class="section no-print" style="margin-top: 40px; text-align: center; color: #85849A; font-size: 12px;">
        <p>Generated by Courier Management System</p>
    </div>
</body>
</html>"""
        return html