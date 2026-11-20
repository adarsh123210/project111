"""
Courier Management System - Login Window and Session Router
"""

import ctypes
import os
import sys

# Draw the window at the monitor's real resolution so Windows
# does not stretch the whole UI and soften text and artwork.
if sys.platform == "win32":
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

import tkinter as tk
from tkinter import ttk, messagebox
from config import APP_NAME, BASE_DIR, COLORS, FONTS, LOGIN_WINDOW_SIZE
from models.db_models import authenticate_user
from views.base_view import BaseWindow

# PIL for JPG support
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Admin views
from views.admin.admin_views import (
    AdminDashboardView, StaffManagementView,
    BranchManagementView, ParcelOversightView, TransactionsView,
    ChargeConfigView, UserManagementView, ReportView
)

# Staff views
from views.staff.staff_views import (
    StaffDashboardView, CustomerManagementView,
    ParcelBookingView, BranchTransferView
)
from views.tracking_view import ParcelTrackingView

class LoginWindow(tk.Tk):
    """Initial Login Window."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Authentication")
        self.resizable(True, True)
        self.configure(bg=COLORS["bg"])
        self.minsize(800, 500)

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        width, height = (int(part) for part in LOGIN_WINDOW_SIZE.split("x"))
        x = max((self.winfo_screenwidth() - width) // 2, 0)
        y = max((self.winfo_screenheight() - height) // 2, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        # Main container - centered card that doesn't stretch full width
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Outer wrapper to center the card
        outer = tk.Frame(self, bg=COLORS["bg"])
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        # Card - fixed max width, centered
        card = tk.Frame(
            outer,
            bg=COLORS["card_bg"],
            highlightthickness=0,
        )
        card.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)

        # Configure card grid - left panel fixed, form centered
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=0)  # left panel doesn't expand
        card.grid_columnconfigure(1, weight=1)  # form area expands

        # Left panel with poster image - fixed width
        art_panel = tk.Frame(card, bg=COLORS["card_bg"], width=380)
        art_panel.grid(row=0, column=0, sticky="ns", padx=(20, 10), pady=20)
        art_panel.grid_propagate(False)  # keep fixed width
        art_panel.grid_rowconfigure(0, weight=1)
        art_panel.grid_columnconfigure(0, weight=1)

        # Load JPG poster using PIL
        poster_path = os.path.join(BASE_DIR, "assets", "international courier services near me.jpg")
        if HAS_PIL and os.path.exists(poster_path):
            try:
                img = Image.open(poster_path)
                self._original_poster = img
                self._poster_label = tk.Label(art_panel, bg=COLORS["card_bg"], bd=0)
                self._poster_label.grid(row=0, column=0, sticky="nsew")
                art_panel.bind("<Configure>", self._resize_poster)
            except Exception:
                tk.Label(art_panel, text="📦", font=("Arial", 48), bg=COLORS["card_bg"]).grid(row=0, column=0, sticky="nsew")
        else:
            tk.Label(art_panel, text="📦", font=("Arial", 48), bg=COLORS["card_bg"]).grid(row=0, column=0, sticky="nsew")

        # Vertical separator
        tk.Frame(card, bg=COLORS["border"], width=1).grid(row=0, column=1, sticky="ns", padx=10, pady=28)

        # Right form panel - centered in available space
        form_container = tk.Frame(card, bg=COLORS["card_bg"])
        form_container.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        form_container.grid_rowconfigure(0, weight=1)
        form_container.grid_columnconfigure(0, weight=1)

        # Form inner - centered with max width
        form_inner = tk.Frame(form_container, bg=COLORS["card_bg"])
        form_inner.grid(row=0, column=0, sticky="nsew")
        form_inner.grid_columnconfigure(0, weight=1)

        # Limit form width to keep it centered and readable
        form_frame = tk.Frame(form_inner, bg=COLORS["card_bg"])
        form_frame.grid(row=0, column=0, sticky="nsew")
        for column in range(2):
            form_frame.grid_columnconfigure(column, weight=1)
        self.selected_role = None
        self.role_buttons = {}

        tk.Label(
            form_frame,
            text="Courier Office CMS",
            font=("Arial", 28, "bold"),
            bg=COLORS["card_bg"],
            fg=COLORS["text_primary"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(30, 0))

        tk.Label(
            form_frame,
            text="Sign in to continue",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 16))

        tk.Label(
            form_frame, text="Sign in as", font=FONTS["body_bold"],
            bg=COLORS["card_bg"], fg=COLORS["text_primary"],
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 6))

        for column, (role, label, icon) in enumerate((
            ("admin", "Admin", "👑"),
            ("staff", "Staff", "🧑‍💼"),
        )):
            button = tk.Button(
                form_frame,
                text=f"{icon}  {label}",
                font=FONTS["body_bold"],
                bg=COLORS["bg"],
                fg=COLORS["text_primary"],
                activebackground=COLORS["accent_dark"],
                activeforeground="#ffffff",
                relief="flat",
                cursor="hand2",
                pady=9,
                command=lambda selected_role=role: self._select_role(selected_role),
            )
            button.grid(row=3, column=column, sticky="ew", padx=(0 if column == 0 else 4, 0 if column == 1 else 4))
            self.role_buttons[role] = button

        tk.Label(
            form_frame, text="Username", font=FONTS["body_bold"],
            bg=COLORS["card_bg"], fg=COLORS["text_primary"],
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 0))
        self.username_ent = ttk.Entry(form_frame, font=FONTS["entry"])
        self.username_ent.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(6, 12), ipady=5)

        tk.Label(
            form_frame, text="Password", font=FONTS["body_bold"],
            bg=COLORS["card_bg"], fg=COLORS["text_primary"],
        ).grid(row=6, column=0, columnspan=2, sticky="w")
        self.password_ent = ttk.Entry(form_frame, font=FONTS["entry"], show="*")
        self.password_ent.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 12), ipady=5)

        login_btn = tk.Button(
            form_frame,
            text="Sign In",
            font=FONTS["button"],
            bg=COLORS["accent"],
            fg="#ffffff",
            activebackground=COLORS["accent_dark"],
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            pady=10,
            command=self._handle_login,
        )
        login_btn.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(8, 20))

        self.bind("<Return>", lambda event: self._handle_login())
        self.username_ent.focus_set()

    def _select_role(self, role):
        self.selected_role = role
        for button_role, button in self.role_buttons.items():
            selected = button_role == role
            button.configure(
                bg=COLORS["accent"] if selected else COLORS["bg"],
                fg="#ffffff" if selected else COLORS["text_primary"],
            )

    def _resize_poster(self, event):
        """Dynamically resize poster image to fit panel."""
        if not hasattr(self, '_original_poster') or not self._original_poster:
            return
        # Get panel size
        w = event.width
        h = event.height
        if w <= 1 or h <= 1:
            return
        # Calculate new size maintaining aspect ratio
        img = self._original_poster
        img_ratio = img.height / img.width
        panel_ratio = h / w
        if img_ratio > panel_ratio:
            # Image is taller - fit to height
            new_h = h - 40
            new_w = int(new_h / img_ratio)
        else:
            # Image is wider - fit to width
            new_w = w - 20
            new_h = int(new_w * img_ratio)
        new_w = max(new_w, 50)
        new_h = max(new_h, 50)
        try:
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self._poster_img = ImageTk.PhotoImage(resized)
            self._poster_label.configure(image=self._poster_img)
        except Exception:
            pass

    def _handle_login(self):
        if not self.selected_role:
            messagebox.showwarning("Select Account Type", "Please choose Admin or Staff before signing in.")
            return

        username = self.username_ent.get().strip()
        password = self.password_ent.get().strip()

        if not username or not password:
            messagebox.showwarning("Incomplete Form", "Please enter both username and password!")
            return

        user = authenticate_user(username, password, expected_role=self.selected_role)
        if not user:
            messagebox.showerror("Access Denied", "Invalid username or password!")
            return

        # Hide login window and launch appropriate module
        self.withdraw()
        self._launch_user_module(user)

    def _launch_user_module(self, user):
        role = user["role"]

        if role == "admin":
            win = BaseWindow("Admin & Management Control Panel", user, on_logout=self._on_logout)
            win.add_nav_item("Dashboard", lambda parent: AdminDashboardView(parent))
            win.add_nav_item("Staff Management", lambda parent: StaffManagementView(parent))
            win.add_nav_item("Branches", lambda parent: BranchManagementView(parent))
            win.add_nav_item("Parcels Oversight", lambda parent: ParcelOversightView(parent, user))
            win.add_nav_item("Track Shipment", lambda parent: ParcelTrackingView(parent))
            win.add_nav_item("Transactions", lambda parent: TransactionsView(parent))
            win.add_nav_item("Delivery Charges", lambda parent: ChargeConfigView(parent))
            win.add_nav_item("User Accounts", lambda parent: UserManagementView(parent))
            win.add_nav_item("Reports", lambda parent: ReportView(parent))
            win.switch_page("Dashboard", lambda parent: AdminDashboardView(parent))

        elif role == "staff":
            win = BaseWindow("Staff & Branch Management Portal", user, on_logout=self._on_logout)
            win.add_nav_item("Dashboard", lambda parent: StaffDashboardView(parent, user))
            win.add_nav_item("Book New Parcel", lambda parent: ParcelBookingView(parent, user))
            win.add_nav_item("Customers", lambda parent: CustomerManagementView(parent))
            win.add_nav_item("Branch Transfers", lambda parent: BranchTransferView(parent, user))
            win.add_nav_item("Track Consignment", lambda parent: ParcelTrackingView(parent))
            win.switch_page("Dashboard", lambda parent: StaffDashboardView(parent, user))

    def _on_logout(self):
        self.deiconify()
        self.password_ent.delete(0, "end")