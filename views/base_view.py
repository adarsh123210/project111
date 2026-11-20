"""
Base Frame and Container View with Modern Sidebar
"""

import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS


def add_treeview_scrollbars(tree):
    """Attach vertical and horizontal scrollbars to a Treeview."""
    for column in tree["columns"]:
        tree.column(column, width=150, minwidth=80, stretch=True)

    vertical_scrollbar = ttk.Scrollbar(
        tree.master, orient="vertical", command=tree.yview
    )
    horizontal_scrollbar = ttk.Scrollbar(
        tree.master, orient="horizontal", command=tree.xview
    )
    tree.configure(
        yscrollcommand=vertical_scrollbar.set,
        xscrollcommand=horizontal_scrollbar.set,
    )
    vertical_scrollbar.pack(side="right", fill="y")
    horizontal_scrollbar.pack(side="bottom", fill="x")


class BaseWindow(tk.Toplevel):
    """Base window containing a modern sidebar and a dynamic main content frame."""

    def __init__(self, title, user_session, on_logout):
        super().__init__()
        self.user_session = user_session
        self.on_logout = on_logout
        self.title(f"{title} - Logged in as: {user_session['username']} ({user_session['role'].capitalize()})")
        self.geometry("1200x750")
        self.minsize(1050, 650)
        self.configure(bg=COLORS["bg"])

        # Make window responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.nav_buttons = {}
        self.current_page = None
        self.active_nav_btn = None
        self._configure_styles()
        self._setup_layout()

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            rowheight=34,
            font=FONTS["body"],
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["primary_soft"],
            foreground=COLORS["text"],
            font=FONTS["body_bold"],
            relief="flat",
            padding=(8, 8),
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["primary_soft"])],
            foreground=[("selected", COLORS["primary"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            padding=(8, 7),
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            padding=(8, 6),
        )
        style.configure(
            "TNotebook",
            background=COLORS["background"],
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
            padding=(16, 9),
            font=FONTS["body_bold"],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["primary_soft"])],
            foreground=[("selected", COLORS["primary"])],
        )

    def _setup_layout(self):
        # Master container - use grid for responsiveness
        self.main_container = tk.Frame(self, bg=COLORS["bg"])
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)

        # Sidebar frame
        self.sidebar = tk.Frame(self.main_container, bg=COLORS["sidebar_bg"], width=230)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(2, weight=1)  # nav menu expands

        # Content Area
        self.content_area = tk.Frame(self.main_container, bg=COLORS["bg"])
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=25)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # App Brand Header
        brand_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"], pady=20)
        brand_frame.grid(row=0, column=0, sticky="ew", padx=8)
        tk.Label(
            brand_frame,
            text="CMS",
            font=("Arial", 22, "bold"),
            bg=COLORS["sidebar_bg"],
            fg=COLORS["primary"],
            anchor="center",
        ).pack(fill="x", padx=4)

        # User Badge
        user_badge = tk.Frame(self.sidebar, bg=COLORS["primary_soft"], pady=10, padx=12)
        user_badge.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 15))
        user_badge.grid_columnconfigure(0, weight=1)
        tk.Label(
            user_badge,
            text=f"👤 {self.user_session['username']}",
            font=FONTS["body_bold"],
            bg=COLORS["primary_soft"],
            fg=COLORS["text"],
        ).pack(anchor="w")
        tk.Label(
            user_badge,
            text=f"Role: {self.user_session['role'].upper()}",
            font=FONTS["small"],
            bg=COLORS["primary_soft"],
            fg=COLORS["muted"],
        ).pack(anchor="w")

        # Nav Buttons Frame - expands to fill space
        self.nav_menu_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        self.nav_menu_frame.grid(row=2, column=0, sticky="new", padx=8)

        # Logout at bottom
        logout_btn = tk.Button(
            self.sidebar,
            text="Logout",
            font=FONTS["sidebar_bold"],
            bg=COLORS["danger"],
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            pady=8,
            command=self._handle_logout,
        )
        logout_btn.grid(row=3, column=0, sticky="ew", padx=10, pady=20)

    def add_nav_item(self, text, page_creator_fn):
        """Add a navigation button to the sidebar."""
        btn = tk.Button(
            self.nav_menu_frame,
            text=text,
            font=FONTS["sidebar"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["sidebar_fg"],
            activebackground=COLORS["sidebar_hover"],
            activeforeground="#ffffff",
            relief="flat",
            anchor="w",
            padx=12,
            pady=10,
            height=2,
            wraplength=190,
            cursor="hand2",
            command=lambda: self.switch_page(text, page_creator_fn),
        )
        btn.pack(fill="x", pady=2, padx=8)
        self.nav_buttons[text] = btn
        btn.bind("<Enter>", lambda event, item=btn: self._nav_hover(item, True))
        btn.bind("<Leave>", lambda event, item=btn: self._nav_hover(item, False))

    def _nav_hover(self, button, entering):
        if button is self.active_nav_btn:
            return
        if entering:
            button.configure(bg=COLORS["primary_soft"], fg=COLORS["primary"])
        else:
            button.configure(bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_fg"])

    def switch_page(self, title, page_creator_fn):
        """Switch current content view."""
        for name, btn in self.nav_buttons.items():
            if name == title:
                btn.configure(
                    bg=COLORS["primary_soft"],
                    fg=COLORS["primary"],
                    font=FONTS["sidebar_bold"],
                )
            else:
                btn.configure(
                    bg=COLORS["sidebar_bg"],
                    fg=COLORS["sidebar_fg"],
                    font=FONTS["sidebar"],
                )

        for widget in self.content_area.winfo_children():
            widget.destroy()

        self.current_page = page_creator_fn(self.content_area)
        if self.current_page:
            self.current_page.pack(fill="both", expand=True)
        self.active_nav_btn = self.nav_buttons.get(title)
        self._bind_button_highlights(self.content_area)

    def _bind_button_highlights(self, root):
        """Apply consistent card, border, hover, and active colors to content views."""
        for widget in root.winfo_children():
            if isinstance(widget, tk.LabelFrame):
                widget.configure(
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    fg=COLORS["text_primary"],
                )
            elif isinstance(widget, tk.Frame):
                try:
                    if widget.cget("relief") == "solid":
                        widget.configure(relief="flat", bd=0, highlightthickness=0)
                except tk.TclError:
                    pass

            if isinstance(widget, tk.Button):
                default_bg = widget.cget("bg")
                default_fg = widget.cget("fg")
                default_active_bg = widget.cget("activebackground")

                if default_bg == COLORS["accent"] or default_bg == COLORS["accent_dark"]:
                    hover_bg = COLORS["primary_hover"]
                elif default_bg == COLORS["success"]:
                    hover_bg = "#238b55"
                elif default_bg == COLORS["danger"]:
                    hover_bg = "#b91c1c"
                elif default_bg == COLORS["warning"]:
                    hover_bg = "#d97706"
                elif default_bg in (COLORS["neutral"], "#64748b", "#e5e5e5"):
                    hover_bg = COLORS["neutral_hover"]
                else:
                    hover_bg = COLORS["primary_soft"]

                hover_fg = "#ffffff" if default_bg not in (
                    COLORS["neutral"],
                    "#64748b",
                    "#e5e5e5",
                ) else COLORS["text_primary"]

                if default_active_bg == "SystemButtonFace":
                    widget.configure(activebackground=hover_bg)
                    widget.configure(activeforeground=hover_fg)

                widget.bind(
                    "<Enter>",
                    lambda event, button=widget, bg=hover_bg, fg=hover_fg:
                        button.configure(bg=bg, fg=fg),
                )
                widget.bind(
                    "<Leave>",
                    lambda event, button=widget, bg=default_bg, fg=default_fg:
                        button.configure(bg=bg, fg=fg),
                )
            self._bind_button_highlights(widget)

    def _handle_logout(self):
        self.destroy()
        if self.on_logout:
            self.on_logout()
