"""
Courier Management System - Configuration
Application-wide constants, colors, fonts, and settings.
"""

import os

# Application Info
APP_NAME = "Courier Management System"
APP_VERSION = "1.0.0"

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "courier_management.db")

# Window Dimensions
LOGIN_WINDOW_SIZE = "1000x600"
MAIN_WINDOW_SIZE = "1200x750"

# RecallBox-inspired visual tokens
COLORS = {
    "background": "#F7F7FC",
    "surface": "#FFFFFF",
    "primary": "#6957D8",
    "primary_soft": "#EEEAFE",
    "text": "#25243A",
    "muted": "#85849A",
    "primary_hover": "#5544C7",
    "soft_hover": "#DCD4FF",
    "neutral": "#E5E5E5",
    "neutral_hover": "#D5D5D5",
    "success": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "border": "#E6E5EF",
    "table_stripe": "#F9F9FD",
    # Compatibility names used throughout the existing views
    "sidebar_bg": "#FFFFFF",
    "sidebar_fg": "#85849A",
    "sidebar_active": "#EEEAFE",
    "sidebar_hover": "#EEEAFE",
    "accent": "#6957D8",
    "accent_dark": "#5544C7",
    "bg": "#F7F7FC",
    "card_bg": "#FFFFFF",
    "text_primary": "#25243A",
    "text_secondary": "#85849A",
}

# Fonts
FONTS = {
    "heading": ("Arial", 28, "bold"),
    "subheading": ("Arial", 20, "bold"),
    "body": ("Arial", 13),
    "body_bold": ("Arial", 13, "bold"),
    "small": ("Arial", 11),
    "sidebar": ("Arial", 13),
    "sidebar_bold": ("Arial", 13, "bold"),
    "button": ("Arial", 13, "bold"),
    "entry": ("Arial", 13),
}

# User Roles
ROLES = {
    "admin": "Admin",
    "staff": "Staff",
}

# Parcel Types
PARCEL_TYPES = ["Document", "Package", "Fragile", "Heavy"]

# Parcel Statuses
PARCEL_STATUSES = [
    "Booked",
    "Picked Up",
    "In Transit",
    "At Branch",
    "Out for Delivery",
    "Delivered",
    "Failed",
    "Returned to Sender",
    "Cancelled",
]

# Payment Methods
PAYMENT_METHODS = ["Cash", "Card", "UPI", "Online"]

# Payment Statuses
PAYMENT_STATUSES = ["Paid", "Unpaid", "Partial"]

# Vehicle Types
VEHICLE_TYPES = ["Bike", "Van", "Truck"]

# Courier Availability Statuses
COURIER_STATUSES = ["Available", "On Delivery", "Off Duty"]

# Transfer Statuses
TRANSFER_STATUSES = ["Initiated", "In Transit", "Received"]

# Failed Delivery Reasons
FAILED_REASONS = [
    "Recipient not available",
    "Wrong address",
    "Refused by recipient",
    "Damaged in transit",
    "Incomplete address",
    "Other",
]

# Tracking Number Prefix
TRACKING_PREFIX = "CMS"
