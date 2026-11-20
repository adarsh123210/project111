"""
Staff & Branch Management Views: Customers, Parcel Booking, Charge Calculation, Transfers
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS, PARCEL_TYPES, PAYMENT_METHODS
from models.db_models import (
    get_all_customers, add_customer,
    get_all_branches, get_all_charges,
    create_parcel, get_all_parcels, transfer_parcel_branch
)
from views.base_view import add_treeview_scrollbars
from utils.helpers import calculate_delivery_cost


class StaffDashboardView(tk.Frame):
    def __init__(self, parent, user_session):
        super().__init__(parent, bg=COLORS["bg"])
        self.user_session = user_session
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 15))
        tk.Label(header, text="📋 Staff & Branch Operations Hub", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(anchor="w")

        info_box = tk.Frame(self, bg=COLORS["primary_soft"], padx=20, pady=20, relief="flat", bd=0,
                            highlightthickness=0)
        info_box.pack(fill="x", pady=10)
        tk.Label(info_box, text=f"Welcome, {self.user_session['username']}!", font=FONTS["subheading"], bg=COLORS["card_bg"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(info_box, text="Quick Actions Available:", font=FONTS["body_bold"], bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(anchor="w", pady=(10, 5))
        tk.Label(info_box, text="• Book parcels for walk-in customers with instant automated charge calculation\n• Register new sender and receiver customer profiles\n• Coordinate branch-to-branch parcel transfers\n• Search and track active shipments", font=FONTS["body"], bg=COLORS["card_bg"], justify="left").pack(anchor="w")


class CustomerManagementView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="👤 Customer Directory", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")
        tk.Button(header, text="➕ Add New Customer", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", padx=12, pady=5, relief="flat", command=self._open_add_dialog).pack(side="right")

        tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "name", "phone", "email", "city", "address", "pincode")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.tree)
        self.tree.heading("id", text="Cust ID")
        self.tree.heading("name", text="Full Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("email", text="Email")
        self.tree.heading("city", text="City")
        self.tree.heading("address", text="Address")
        self.tree.heading("pincode", text="Pincode")
        self.tree.column("id", width=50, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for c in get_all_customers():
            self.tree.insert("", "end", values=(
                c["id"], c["name"], c["phone"], c["email"] or "-",
                c["city"] or "-", c["address"] or "-", c["pincode"] or "-"
            ))

    def _open_add_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Register New Customer")
        dlg.geometry("450x450")
        dlg.configure(bg="#ffffff")
        dlg.transient(self)
        dlg.grab_set()

        fields = [
            ("Full Name:", "name"),
            ("Phone Number:", "phone"),
            ("Email Address:", "email"),
            ("Street Address:", "address"),
            ("City:", "city"),
            ("State:", "state"),
            ("Pincode:", "pincode"),
        ]
        entries = {}

        for i, (label, key) in enumerate(fields):
            tk.Label(dlg, text=label, font=FONTS["body"], bg="#ffffff").grid(row=i, column=0, padx=15, pady=6, sticky="w")
            ent = ttk.Entry(dlg, width=28)
            ent.grid(row=i, column=1, padx=15, pady=6, sticky="w")
            entries[key] = ent

        def save():
            name = entries["name"].get().strip()
            phone = entries["phone"].get().strip()
            email = entries["email"].get().strip()
            addr = entries["address"].get().strip()
            city = entries["city"].get().strip()
            state = entries["state"].get().strip()
            pin = entries["pincode"].get().strip()

            if not name or not phone:
                messagebox.showerror("Error", "Customer name and phone are required!")
                return

            res, err = add_customer(name, phone, email, addr, city, state, pin)
            if err:
                messagebox.showerror("Error", err)
            else:
                messagebox.showinfo("Success", "Customer profile created!")
                dlg.destroy()
                self._refresh()

        tk.Button(dlg, text="Save Customer", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", command=save, padx=15, pady=5).grid(row=len(fields), column=0, columnspan=2, pady=15)


class ParcelBookingView(tk.Frame):
    def __init__(self, parent, user_session):
        super().__init__(parent, bg=COLORS["bg"])
        self.user_session = user_session
        self.customers = get_all_customers()
        self.cust_map = {f"{c['name']} ({c['phone']})": c["id"] for c in self.customers}
        self.branches = get_all_branches(active_only=True)
        self.branch_map = {b["name"]: b["id"] for b in self.branches}
        self.charge_rules = get_all_charges()

        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="📦 Book New Parcel & Calculate Delivery Charges", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(anchor="w")

        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True)

        # Left Column: Sender & Receiver Details
        left_col = tk.LabelFrame(container, text="1. Parties Information", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=15, pady=10)

        tk.Label(left_col, text="Sender Customer:", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        self.sender_cb = ttk.Combobox(left_col, values=list(self.cust_map.keys()), width=35)
        if self.cust_map:
            self.sender_cb.current(0)
        self.sender_cb.pack(anchor="w", pady=(0, 10))

        tk.Label(left_col, text="Receiver Customer:", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        self.receiver_cb = ttk.Combobox(left_col, values=list(self.cust_map.keys()), width=35)
        if len(self.cust_map) > 1:
            self.receiver_cb.current(1)
        elif self.cust_map:
            self.receiver_cb.current(0)
        self.receiver_cb.pack(anchor="w", pady=(0, 10))

        tk.Label(left_col, text="Source Branch (Origin):", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        self.source_cb = ttk.Combobox(left_col, values=list(self.branch_map.keys()), state="readonly", width=35)
        if self.branch_map:
            self.source_cb.current(0)
        self.source_cb.pack(anchor="w", pady=(0, 10))

        tk.Label(left_col, text="Destination Branch:", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        self.dest_cb = ttk.Combobox(left_col, values=list(self.branch_map.keys()), state="readonly", width=35)
        if len(self.branch_map) > 1:
            self.dest_cb.current(1)
        elif self.branch_map:
            self.dest_cb.current(0)
        self.dest_cb.pack(anchor="w", pady=(0, 10))

        # Middle Column: Specifications
        mid_col = tk.LabelFrame(container, text="2. Parcel Specifications", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=15, pady=10)

        tk.Label(mid_col, text="Parcel Type:", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        self.type_cb = ttk.Combobox(mid_col, values=PARCEL_TYPES, state="readonly", width=30)
        self.type_cb.current(1)
        self.type_cb.pack(anchor="w", pady=(0, 8))

        tk.Label(mid_col, text="Weight (kg):", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        self.weight_ent = ttk.Entry(mid_col, width=32)
        self.weight_ent.insert(0, "1.5")
        self.weight_ent.pack(anchor="w", pady=(0, 8))

        tk.Label(mid_col, text="Dimensions L x W x H (cm):", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        dim_f = tk.Frame(mid_col, bg=COLORS["card_bg"])
        dim_f.pack(anchor="w", pady=(0, 8))
        self.len_ent = ttk.Entry(dim_f, width=8)
        self.len_ent.insert(0, "20")
        self.len_ent.pack(side="left", padx=(0, 4))
        self.wid_ent = ttk.Entry(dim_f, width=8)
        self.wid_ent.insert(0, "15")
        self.wid_ent.pack(side="left", padx=4)
        self.hgt_ent = ttk.Entry(dim_f, width=8)
        self.hgt_ent.insert(0, "10")
        self.hgt_ent.pack(side="left", padx=4)

        self.is_express_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(mid_col, text="⚡ Express Delivery", variable=self.is_express_var).pack(anchor="w", pady=(5, 8))

        tk.Label(mid_col, text="Description of Contents:", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        self.desc_ent = ttk.Entry(mid_col, width=32)
        self.desc_ent.insert(0, "Documents / Electronics")
        self.desc_ent.pack(anchor="w", pady=(0, 8))

        # Right Column: Calculation & Payment
        right_col = tk.LabelFrame(container, text="3. Charge & Payment", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=15, pady=10)

        tk.Button(right_col, text="🔄 Calculate Charge", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", command=self._compute_charge).pack(fill="x", pady=(5, 10))

        self.charge_summary_lbl = tk.Label(
            right_col,
            text="Base: ₹0.00\nWeight Cost: ₹0.00\nDistance Est: ₹0.00\nSurcharge: ₹0.00\n\nTOTAL: ₹0.00",
            font=FONTS["body_bold"],
            bg=COLORS["bg"],
            justify="left",
            padx=10,
            pady=10,
            relief="flat",
            bd=0
        )
        self.charge_summary_lbl.pack(fill="x", pady=(0, 10))

        tk.Label(right_col, text="Payment Method:", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(anchor="w", pady=(5, 2))
        self.pay_cb = ttk.Combobox(right_col, values=PAYMENT_METHODS, state="readonly", width=30)
        self.pay_cb.current(0)
        self.pay_cb.pack(anchor="w", pady=(0, 15))

        self.total_charge_val = 0.0

        tk.Button(
            right_col,
            text="✅ Confirm & Book Parcel",
            font=("Arial", 13, "bold"),
            bg=COLORS["success"],
            fg="#fff",
            pady=8,
            command=self._confirm_booking
        ).pack(fill="x")

        self._compute_charge()
        self.booking_columns = (left_col, mid_col, right_col)
        self._layout_booking_columns(container, container.winfo_width())
        container.bind(
            "<Configure>",
            lambda event: self._layout_booking_columns(container, event.width),
        )

    def _layout_booking_columns(self, container, available_width):
        if available_width >= 900:
            for column in range(3):
                container.grid_columnconfigure(column, weight=1)
            self.booking_columns[0].grid(
                row=0, column=0, sticky="nsew", padx=(0, 10)
            )
            self.booking_columns[1].grid(
                row=0, column=1, sticky="nsew", padx=(0, 10)
            )
            self.booking_columns[2].grid(row=0, column=2, sticky="nsew")
        else:
            for column in range(3):
                container.grid_columnconfigure(column, weight=1 if column < 2 else 0)
            self.booking_columns[0].grid(
                row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10)
            )
            self.booking_columns[1].grid(
                row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 10)
            )
            self.booking_columns[2].grid(
                row=1, column=0, columnspan=2, sticky="nsew"
            )

    def _compute_charge(self):
        try:
            ptype = self.type_cb.get()
            weight = float(self.weight_ent.get().strip() or 0)
            express = self.is_express_var.get()
            calc = calculate_delivery_cost(ptype, weight, express, distance_km=60.0, charge_rules=self.charge_rules)
            self.total_charge_val = calc["total"]

            text = (
                f"Base Charge: ₹{calc['base_charge']:.2f}\n"
                f"Weight Cost: ₹{calc['weight_cost']:.2f}\n"
                f"Distance Cost: ₹{calc['distance_cost']:.2f}\n"
                f"Express Surcharge: ₹{calc['express_surcharge']:.2f}\n\n"
                f"TOTAL CHARGE: ₹{calc['total']:.2f}"
            )
            self.charge_summary_lbl.config(text=text)
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Invalid input values: {e}")

    def _confirm_booking(self):
        self._compute_charge()
        sender_txt = self.sender_cb.get()
        recv_txt = self.receiver_cb.get()

        sender_id = self.cust_map.get(sender_txt)
        recv_id = self.cust_map.get(recv_txt)
        s_branch_id = self.branch_map.get(self.source_cb.get())
        d_branch_id = self.branch_map.get(self.dest_cb.get())

        if not sender_id or not recv_id or not s_branch_id or not d_branch_id:
            messagebox.showerror("Error", "Please select valid Sender, Receiver, and Branches!")
            return

        ptype = self.type_cb.get()
        weight = float(self.weight_ent.get().strip() or 0)
        l = float(self.len_ent.get().strip() or 0)
        w = float(self.wid_ent.get().strip() or 0)
        h = float(self.hgt_ent.get().strip() or 0)
        desc = self.desc_ent.get().strip()
        pay_method = self.pay_cb.get()

        pid, tracking_no, err = create_parcel(
            sender_id, recv_id, ptype, weight, l, w, h, desc, 0, "",
            s_branch_id, d_branch_id, self.total_charge_val, self.user_session["id"], pay_method
        )

        if err:
            messagebox.showerror("Booking Failed", err)
        else:
            self._show_booking_success_dialog(tracking_no, self.total_charge_val)

    def _show_booking_success_dialog(self, tracking_no, total_amt):
        dlg = tk.Toplevel(self)
        dlg.title("Booking Confirmed")
        dlg.geometry("420x260")
        dlg.configure(bg="#ffffff")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="🎉 Parcel Booked Successfully!", font=FONTS["subheading"], bg="#ffffff", fg=COLORS["success"]).pack(pady=(15, 5))
        tk.Label(dlg, text="Parcel Unique ID / Tracking Number:", font=FONTS["body"], bg="#ffffff", fg=COLORS["text_secondary"]).pack()

        # Standard selectable Entry widget for native Ctrl+C / right-click copy
        uid_ent = tk.Entry(dlg, font=("Consolas", 14, "bold"), justify="center", bd=1, relief="solid", bg="#f8fafc", fg=COLORS["accent"])
        uid_ent.insert(0, tracking_no)
        uid_ent.pack(fill="x", padx=30, pady=10)
        uid_ent.focus_set()
        uid_ent.select_range(0, "end")

        tk.Label(dlg, text=f"Total Amount Collected: ₹{total_amt:.2f}", font=FONTS["body_bold"], bg="#ffffff", fg=COLORS["text_primary"]).pack(pady=4)

        tk.Button(
            dlg,
            text="Done",
            font=FONTS["body_bold"],
            bg=COLORS["neutral"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["neutral_hover"],
            activeforeground=COLORS["text_primary"],
            padx=20,
            pady=4,
            relief="flat",
            command=dlg.destroy
        ).pack(pady=(12, 0))




class BranchTransferView(tk.Frame):
    def __init__(self, parent, user_session):
        super().__init__(parent, bg=COLORS["bg"])
        self.user_session = user_session
        self.branches = get_all_branches(active_only=True)
        self.branch_map = {b["name"]: b["id"] for b in self.branches}
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="🚚 Branch-to-Branch Transfer Dispatch", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")

        # Transfer Operation Panel
        ctrl_frame = tk.LabelFrame(self, text="Dispatch Parcel to Another Branch", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=15, pady=10)
        ctrl_frame.pack(fill="x", pady=(0, 10))

        ctrl_frame.grid_columnconfigure(1, weight=1)
        ctrl_frame.grid_columnconfigure(3, weight=1)
        tk.Label(ctrl_frame, text="Select Destination Branch:", font=FONTS["body"], bg=COLORS["card_bg"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.dest_cb = ttk.Combobox(ctrl_frame, values=list(self.branch_map.keys()), state="readonly", width=25)
        if self.branch_map:
            self.dest_cb.current(0)
        self.dest_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(ctrl_frame, text="Transfer Remarks:", font=FONTS["body"], bg=COLORS["card_bg"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.rem_ent = ttk.Entry(ctrl_frame, width=30)
        self.rem_ent.insert(0, "Inter-branch transfer via route transport")
        self.rem_ent.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        tk.Button(ctrl_frame, text="🚀 Dispatch Selected Parcel", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", command=self._dispatch_transfer).grid(row=1, column=0, columnspan=4, padx=5, pady=(5, 0), sticky="e")

        # Treeview of parcels
        tree_frame = tk.Frame(self, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "tracking", "sender", "receiver", "type", "current_branch", "dest_branch", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        add_treeview_scrollbars(self.tree)
        self.tree.heading("id", text="ID")
        self.tree.heading("tracking", text="Tracking #")
        self.tree.heading("sender", text="Sender")
        self.tree.heading("receiver", text="Receiver")
        self.tree.heading("type", text="Type")
        self.tree.heading("current_branch", text="Current Location")
        self.tree.heading("dest_branch", text="Final Destination")
        self.tree.heading("status", text="Status")
        self.tree.column("id", width=35, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for p in get_all_parcels():
            self.tree.insert("", "end", values=(
                p["id"], p["tracking_number"], p["sender_name"], p["receiver_name"],
                p["parcel_type"], p["source_branch_name"], p["dest_branch_name"], p["status"]
            ))

    def _dispatch_transfer(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a parcel from list to dispatch!")
            return
        vals = self.tree.item(sel[0], "values")
        parcel_id = vals[0]
        to_branch_id = self.branch_map.get(self.dest_cb.get())
        remarks = self.rem_ent.get().strip()

        ok, err = transfer_parcel_branch(parcel_id, 1, to_branch_id, self.user_session["id"], remarks)
        if ok:
            messagebox.showinfo("Success", "Parcel dispatched to destination branch!")
            self._refresh()
        else:
            messagebox.showerror("Error", err)