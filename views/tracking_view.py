import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.db_models import get_parcel_by_tracking, get_tracking_events
from views.base_view import add_treeview_scrollbars


class ParcelTrackingView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="🔍 Comprehensive Parcel Tracking Journey", font=FONTS["heading"], bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(anchor="w")

        search_bar = tk.Frame(self, bg=COLORS["card_bg"], padx=15, pady=12, relief="flat", bd=0,
                              highlightthickness=0)
        search_bar.pack(fill="x", pady=(0, 15))

        tk.Label(search_bar, text="Enter Tracking Number (e.g. CMS-YYYY-XXXXXX):", font=FONTS["body_bold"], bg=COLORS["card_bg"]).pack(side="left", padx=5)
        self.track_ent = ttk.Entry(search_bar, width=28)
        self.track_ent.pack(side="left", padx=8)

        tk.Button(search_bar, text="Track Shipment", font=FONTS["button"], bg=COLORS["accent"], fg="#fff", padx=12, pady=4, command=self._do_track).pack(side="left", padx=5)

        self.result_container = tk.Frame(self, bg=COLORS["bg"])
        self.result_container.pack(fill="both", expand=True)

    def _do_track(self):
        tno = self.track_ent.get().strip()
        if not tno:
            messagebox.showwarning("Warning", "Please enter a tracking number!")
            return

        for widget in self.result_container.winfo_children():
            widget.destroy()

        parcel = get_parcel_by_tracking(tno)
        if not parcel:
            tk.Label(self.result_container, text=f"❌ No consignment found matching: {tno}", font=FONTS["subheading"], bg=COLORS["bg"], fg=COLORS["danger"]).pack(pady=20)
            return

        overview = tk.Frame(self.result_container, bg=COLORS["card_bg"], padx=15, pady=12, relief="flat", bd=0,
                            highlightthickness=0)
        overview.pack(fill="x", pady=(0, 10))

        top_row = tk.Frame(overview, bg=COLORS["card_bg"])
        top_row.pack(fill="x")

        tk.Label(top_row, text="Shipment UID:", font=FONTS["subheading"], bg=COLORS["card_bg"], fg=COLORS["accent"]).pack(side="left")

        uid_display = tk.Entry(top_row, font=("Consolas", 12, "bold"), width=22, bd=1, relief="solid", fg=COLORS["accent"])
        uid_display.insert(0, parcel["tracking_number"])
        uid_display.pack(side="left", padx=10)

        tk.Label(top_row, text=f"Status: {parcel['status'].upper()}", font=FONTS["body_bold"], bg=COLORS["card_bg"], fg=COLORS["text_primary"]).pack(side="right")

        tk.Label(
            overview,
            text=f"Sender: {parcel['sender_name']} ({parcel['sender_phone']})  ➔  Receiver: {parcel['receiver_name']} ({parcel['receiver_phone']})\n"
                 f"Route: {parcel['source_branch_name']} ➔ {parcel['dest_branch_name']} | Type: {parcel['parcel_type']} | Weight: {parcel['weight_kg']} kg",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            justify="left"
        ).pack(anchor="w", pady=(5, 0))

        events_frame = tk.LabelFrame(self.result_container, text="Checkpoint History Timeline", font=FONTS["subheading"], bg=COLORS["card_bg"], padx=10, pady=10)
        events_frame.pack(fill="both", expand=True)

        columns = ("timestamp", "status", "location", "remarks", "updated_by")
        tree = ttk.Treeview(events_frame, columns=columns, show="headings")
        add_treeview_scrollbars(tree)
        tree.heading("timestamp", text="Timestamp")
        tree.heading("status", text="Status Event")
        tree.heading("location", text="Location")
        tree.heading("remarks", text="Remarks")
        tree.heading("updated_by", text="Operator")

        tree.column("timestamp", width=140, anchor="center")
        tree.column("status", width=120, anchor="center")
        tree.pack(fill="both", expand=True)

        for event in get_tracking_events(parcel["id"]):
            tree.insert("", "end", values=(
                event["timestamp"], event["status"], event["location"] or "-",
                event["remarks"] or "-", event["username"] or "System"
            ))
