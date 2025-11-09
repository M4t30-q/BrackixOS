# 
# BrackixOS v2.3: COMPLETE OS WITH 7 GAMES INTEGRATED
# Requirements: PySide6, PySide6-WebEngine, twincalc.py, twinntpad.py, assets/startup.wav, assets/wallpaper.jpg


import sys
import os
import time
import subprocess
import json
import random
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget,
    QHBoxLayout, QLineEdit, QProgressBar, QFrame, QTextEdit, QListWidget,
    QInputDialog, QMessageBox, QGridLayout, QScrollArea, QCheckBox, QSpinBox,
    QComboBox, QToolBar
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QUrl, QSize, QEasingCurve, Property, QRect
from PySide6.QtGui import QFont, QPalette, QBrush, QPixmap, QColor, QAction, QIcon, QPainter, QPen
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage


# Import calculator and notepad apps
try:
    from genericcalc import Calc
except ImportError:
    Calc = None

try:
    from genericnotepad import NtPad
except ImportError:
    NtPad = None


# ---------- User Manager for multi-user support ----------
class UserManager:
    def __init__(self):
        self.users_file = "assets/users.json"
        self.load_users()
    
    def load_users(self):
        os.makedirs("assets", exist_ok=True)
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            # Default admin user
            self.users = {
                "admin": {
                    "password": "admin",
                    "theme": "dark",
                    "wallpaper": "#1e1e2e"
                }
            }
            self.save_users()
    
    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)
    
    def authenticate(self, username, password):
        if username in self.users:
            return self.users[username]["password"] == password
        return False
    
    def create_user(self, username, password):
        if username not in self.users:
            self.users[username] = {
                "password": password,
                "theme": "dark",
                "wallpaper": "#1e1e2e"
            }
            self.save_users()
            return True
        return False
    
    def get_user_settings(self, username):
        return self.users.get(username, {})
    
    def update_user_settings(self, username, settings):
        if username in self.users:
            self.users[username].update(settings)
            self.save_users()


# ---------- Helper floating window class ----------
class AppWindow(QFrame):
    def __init__(self, title="App", size=(400, 300), parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(200, 150, *size)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 0.98);
                border: 2px solid #6c63ff;
                border-radius: 12px;
            }
        """)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.old_pos = None
        
        # Main layout for the window
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Title bar with close button
        self.create_title_bar(title)
        
        # Content container
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        
        self.main_layout.addWidget(self.content_widget)
        self.setLayout(self.main_layout)
    
    def create_title_bar(self, title):
        title_bar_widget = QWidget()
        title_bar_widget.setStyleSheet("background-color: #2d2d30; border-radius: 10px 10px 0 0;")
        title_bar = QHBoxLayout(title_bar_widget)
        title_bar.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        
        # Exit button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5555;
                color: white;
                border-radius: 14px;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #ff7777;
            }
            QPushButton:pressed {
                background-color: #dd3333;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_bar.addWidget(close_btn)
        
        self.main_layout.addWidget(title_bar_widget)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event):
        self.old_pos = None


# ---------- Boot Screen ----------
class BootScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        self.logo = QLabel("BrackixOS 💫")
        self.logo.setFont(QFont("Orbitron", 42, QFont.Bold))
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setStyleSheet("color: #6c63ff;")
        layout.addWidget(self.logo)
        
        version = QLabel("v2.3 Ultimate Edition")
        version.setFont(QFont("JetBrains Mono", 12))
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #888; margin-bottom: 20px;")
        layout.addWidget(version)
        
        self.status = QLabel("Initializing system...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: white; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(self.status)
        
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedWidth(400)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #222;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6c63ff, stop:1 #8a7fff);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.bar)
        
        self.setLayout(layout)
        
        self.progress = 0
        self.load_messages = [
            "Loading kernel modules...",
            "Initializing game engines...",
            "Starting desktop environment...",
            "Loading 7 awesome games...",
            "Configuring network...",
            "Almost ready..."
        ]
        self.message_index = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)
        
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start()
    
    def update_progress(self):
        self.progress += 1
        self.bar.setValue(self.progress)
        
        if self.progress % 17 == 0 and self.message_index < len(self.load_messages):
            self.status.setText(self.load_messages[self.message_index])
            self.message_index += 1
        
        if self.progress >= 100:
            self.timer.stop()
            self.status.setText("System ready!")
            QTimer.singleShot(350, self.switch_callback)


# ---------- Power Off Screen ----------
class PowerOffScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shutting down...")
        self.setStyleSheet("background-color: black; color: white;")
        self.setGeometry(300, 200, 600, 350)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel("⏻")
        icon.setFont(QFont("Segoe UI Emoji", 72))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("color: #6c63ff;")
        layout.addWidget(icon)
        
        label = QLabel("Powering off BrackixOS...")
        label.setFont(QFont("JetBrains Mono", 22, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        sub = QLabel("Goodbye, twin. 💫")
        sub.setFont(QFont("JetBrains Mono", 14))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #888; margin-top: 10px;")
        layout.addWidget(sub)
        
        self.dots = QLabel("")
        self.dots.setAlignment(Qt.AlignCenter)
        self.dots.setStyleSheet("font-size: 18px; color: #6c63ff;")
        layout.addWidget(self.dots)
        
        self.setLayout(layout)
        
        self.counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(400)
        
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(600)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
    
    def animate(self):
        self.counter = (self.counter + 1) % 4
        self.dots.setText("." * self.counter)


# ---------- Login Screen ----------
class LoginScreen(QWidget):
    def __init__(self, switch_callback, user_manager):
        super().__init__()
        self.switch_callback = switch_callback
        self.user_manager = user_manager
        self.current_user = None
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        logo = QLabel("BrackixOS")
        logo.setFont(QFont("Orbitron", 36, QFont.Bold))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")
        layout.addWidget(logo)
        
        self.title = QLabel("Welcome Back 👋")
        self.title.setFont(QFont("JetBrains Mono", 20, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: white; margin-bottom: 20px;")
        layout.addWidget(self.title)
        
        form_widget = QWidget()
        form_widget.setMaximumWidth(350)
        form_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(60, 60, 60, 0.5);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        form_layout = QVBoxLayout(form_widget)
        
        self.user_label = QLabel("Username:")
        self.user_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        form_layout.addWidget(self.user_label)
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter your username")
        self.username.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border-radius: 8px;
                background-color: #2d2d30;
                color: white;
                border: 2px solid #444;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #6c63ff;
            }
        """)
        form_layout.addWidget(self.username)
        
        self.pass_label = QLabel("Password:")
        self.pass_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; margin-top: 10px;")
        form_layout.addWidget(self.pass_label)
        
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Enter password")
        self.password.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border-radius: 8px;
                background-color: #2d2d30;
                color: white;
                border: 2px solid #444;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #6c63ff;
            }
        """)
        self.password.returnPressed.connect(self.login)
        form_layout.addWidget(self.password)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                border-radius: 10px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #7f74ff;
            }
            QPushButton:pressed {
                background-color: #5a52cc;
            }
        """)
        self.login_btn.clicked.connect(self.login)
        form_layout.addWidget(self.login_btn)
        
        self.create_btn = QPushButton("Create New Account")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6c63ff;
                font-size: 13px;
                padding: 8px;
                border: 2px solid #6c63ff;
                border-radius: 8px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: rgba(108, 99, 255, 0.1);
            }
        """)
        self.create_btn.clicked.connect(self.create_account)
        form_layout.addWidget(self.create_btn)
        
        layout.addWidget(form_widget)
        self.setLayout(layout)
        self.setStyleSheet("background-color: #1e1e2e; color: white;")
    
    def login(self):
        username = self.username.text().strip()
        password = self.password.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login", "Please enter both username and password.")
            return
        
        if self.user_manager.authenticate(username, password):
            self.current_user = username
            self.switch_callback(username)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            self.password.clear()
    
    def create_account(self):
        username, ok1 = QInputDialog.getText(self, "Create Account", "Enter new username:")
        if ok1 and username:
            password, ok2 = QInputDialog.getText(self, "Create Account", "Enter password:", QLineEdit.Password)
            if ok2 and password:
                if self.user_manager.create_user(username, password):
                    QMessageBox.information(self, "Success", f"Account '{username}' created successfully!")
                    self.username.setText(username)
                else:
                    QMessageBox.warning(self, "Error", "Username already exists.")


# ---------- Desktop ----------
class Desktop(QWidget):
    def __init__(self, root, user_manager):
        super().__init__()
        self.root = root
        self.user_manager = user_manager
        self.current_user = None
        self.setWindowTitle("BrackixOS Desktop")
        self.resize(1000, 700)
        
        self.using_image_wallpaper = False
        self.init_ui()
    
    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.create_taskbar()
        
        desktop_scroll = QScrollArea()
        desktop_scroll.setWidgetResizable(True)
        desktop_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        desktop_widget = QWidget()
        desktop_layout = QVBoxLayout(desktop_widget)
        desktop_layout.setContentsMargins(20, 20, 20, 20)
        
        self.create_app_grid(desktop_layout)
        self.create_color_swatches(desktop_layout)
        
        desktop_layout.addStretch()
        desktop_scroll.setWidget(desktop_widget)
        
        self.main_layout.addWidget(desktop_scroll)
        self.setLayout(self.main_layout)
        
        self.load_wallpaper()
        self.play_startup_sound()
        
        self.base_path = os.path.expanduser(os.path.join("~", "BrackixOS_Files"))
        os.makedirs(self.base_path, exist_ok=True)
    
    def create_taskbar(self):
        taskbar = QWidget()
        taskbar.setFixedHeight(50)
        taskbar.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 0.95);
                border-bottom: 2px solid #6c63ff;
            }
        """)
        
        taskbar_layout = QHBoxLayout(taskbar)
        taskbar_layout.setContentsMargins(15, 5, 15, 5)
        
        sys_label = QLabel("BrackixOS 💫")
        sys_label.setFont(QFont("Orbitron", 16, QFont.Bold))
        sys_label.setStyleSheet("color: #6c63ff;")
        taskbar_layout.addWidget(sys_label)
        
        taskbar_layout.addStretch()
        
        self.user_label = QLabel("")
        self.user_label.setStyleSheet("color: white; font-size: 13px; margin-right: 15px;")
        taskbar_layout.addWidget(self.user_label)
        
        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.clock.setFont(QFont("JetBrains Mono", 13, QFont.Bold))
        self.clock.setStyleSheet("color: white; background-color: rgba(108, 99, 255, 0.3); padding: 8px 15px; border-radius: 8px;")
        taskbar_layout.addWidget(self.clock)
        
        self.main_layout.addWidget(taskbar)
        self.update_clock()
    
    def create_app_grid(self, parent_layout):
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(20)
        
        apps = [
            ("🧮", "Calc", "Calculator", self.launch_calc),
            ("🖥️", "Terminal", "Command Line", self.launch_terminal),
            ("📁", "Files", "File Explorer", self.launch_files),
            ("📝", "NotePad", "Text Editor", self.launch_notepad),
            ("🌐", "Browser", "Web Browser", self.launch_browser),
            ("⚙️", "Settings", "System Settings", self.launch_settings),
            ("🎮", "Games", "Game Center", self.launch_games),
            ("⏻", "Power", "Shutdown", self.power_off)
        ]
        
        btn_style = """
            QPushButton {
                background-color: rgba(60, 60, 60, 0.7);
                color: white;
                border-radius: 15px;
                padding: 20px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background-color: rgba(108, 99, 255, 0.5);
                border: 2px solid #6c63ff;
            }
            QPushButton:pressed {
                background-color: rgba(108, 99, 255, 0.7);
            }
        """
        
        row, col = 0, 0
        max_cols = 4
        
        for icon, name, desc, callback in apps:
            btn_widget = QWidget()
            btn_layout = QVBoxLayout(btn_widget)
            btn_layout.setAlignment(Qt.AlignCenter)
            
            btn = QPushButton()
            btn.setFixedSize(140, 120)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(callback)
            
            btn_content = QVBoxLayout(btn)
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Segoe UI Emoji", 36))
            icon_label.setAlignment(Qt.AlignCenter)
            btn_content.addWidget(icon_label)
            
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
            btn_content.addWidget(name_label)
            
            btn_layout.addWidget(btn)
            grid.addWidget(btn_widget, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        parent_layout.addWidget(grid_widget)
    
    def create_color_swatches(self, parent_layout):
        swatch_label = QLabel("Quick Themes:")
        swatch_label.setStyleSheet("color: white; font-weight: bold; margin-top: 20px; margin-bottom: 10px;")
        parent_layout.addWidget(swatch_label)
        
        swatches_widget = QWidget()
        swatches = QHBoxLayout(swatches_widget)
        swatches.setSpacing(12)
        
        colors = {
            "🌌": ("#6c63ff", "Cosmic Purple"),
            "☁️": ("#5eb9ff", "Sky Blue"),
            "🌿": ("#6fffab", "Mint Green"),
            "🌙": ("#1e1e2e", "Dark Mode"),
            "☀️": ("#f5f5dc", "Light Mode"),
            "🔥": ("#ff6b6b", "Fire Red"),
            "🌊": ("#4ecdc4", "Ocean"),
            "🌸": ("#ff7eb3", "Sakura")
        }
        
        for emoji, (color, name) in colors.items():
            btn = QPushButton(emoji)
            btn.setFixedSize(50, 50)
            btn.setToolTip(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: 12px;
                    font-size: 20px;
                    border: 3px solid transparent;
                }}
                QPushButton:hover {{
                    border: 3px solid white;
                }}
            """)
            btn.clicked.connect(lambda _, c=color: self.set_wallpaper_color(c))
            swatches.addWidget(btn)
        
        swatches.addStretch()
        parent_layout.addWidget(swatches_widget)
    
    def set_current_user(self, username):
        self.current_user = username
        self.user_label.setText(f"👤 {username}")
        settings = self.user_manager.get_user_settings(username)
        if "wallpaper" in settings:
            self.set_wallpaper_color(settings["wallpaper"])
    
    def update_clock(self):
        now = datetime.now()
        self.clock.setText(now.strftime("%H:%M:%S • %b %d"))
        QTimer.singleShot(1000, self.update_clock)
    
    def load_wallpaper(self):
        wallpaper_path = "assets/wallpaper.jpg"
        if os.path.exists(wallpaper_path):
            palette = QPalette()
            wallpaper = QPixmap(wallpaper_path).scaled(
                QSize(1920, 1080), 
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            palette.setBrush(QPalette.Window, QBrush(wallpaper))
            self.setPalette(palette)
            self.setAutoFillBackground(True)
            self.using_image_wallpaper = True
        else:
            self.set_wallpaper_color("#1e1e2e")
    
    def set_wallpaper_color(self, color):
        self.setStyleSheet(f"background-color: {color};")
        self.using_image_wallpaper = False
        if self.current_user:
            self.user_manager.update_user_settings(self.current_user, {"wallpaper": color})
    
    def play_startup_sound(self):
        startup_wav = "assets/startup.wav"
        if os.path.exists(startup_wav):
            self.sound = QSoundEffect()
            self.sound.setSource(QUrl.fromLocalFile(startup_wav))
            self.sound.setVolume(0.5)
            QTimer.singleShot(300, self.sound.play)
    
    def launch_calc(self):
        if Calc:
            self.calc_window = Calc()
            self.calc_window.show()
        else:
            QMessageBox.warning(self, "Error", "Calculator app not found.")
    
    def launch_terminal(self):
        self.terminal = Terminal(self)
        self.terminal.show()
    
    def launch_files(self):
        self.files = FileExplorer(self)
        self.files.show()
    
    def launch_notepad(self):
        if NtPad:
            self.notepad = NtPad()
            self.notepad.show()
        else:
            QMessageBox.warning(self, "Error", "Notepad app not found.")
    
    def launch_browser(self):
        self.browser = Browser(self)
        self.browser.show()
    
    def launch_settings(self):
        self.settings_window = SettingsApp(self)
        self.settings_window.show()
    
    def launch_games(self):
        self.games = GameCenter(self)
        self.games.show()
    
    def logout(self):
        if self.root:
            self.root.show_login()
    
    def power_off(self):
        reply = QMessageBox.question(
            self, "Power Off",
            "Are you sure you want to shut down BrackixOS?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.power_screen = PowerOffScreen()
            self.power_screen.show()
            QTimer.singleShot(2000, QApplication.quit)


# ---------- WORKING BROWSER ----------
class Browser(AppWindow):
    def __init__(self, desktop):
        super().__init__("Generic Browser 🌐", size=(1100, 750), parent=desktop)
        
        nav_bar = QWidget()
        nav_bar.setStyleSheet("background-color: #2d2d30; padding: 5px;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(5, 5, 5, 5)
        
        back_btn = QPushButton("◀")
        back_btn.setFixedSize(35, 35)
        back_btn.setToolTip("Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3e;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6c63ff; }
        """)
        back_btn.clicked.connect(self.go_back)
        nav_layout.addWidget(back_btn)
        
        forward_btn = QPushButton("▶")
        forward_btn.setFixedSize(35, 35)
        forward_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3e;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6c63ff; }
        """)
        forward_btn.clicked.connect(self.go_forward)
        nav_layout.addWidget(forward_btn)
        
        reload_btn = QPushButton("🔄")
        reload_btn.setFixedSize(35, 35)
        reload_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3e;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #6c63ff; }
        """)
        reload_btn.clicked.connect(self.reload_page)
        nav_layout.addWidget(reload_btn)
        
        home_btn = QPushButton("🏠")
        home_btn.setFixedSize(35, 35)
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3e;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #6c63ff; }
        """)
        home_btn.clicked.connect(self.go_home)
        nav_layout.addWidget(home_btn)
        
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("🔍 Enter URL or search...")
        self.url_bar.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border-radius: 8px;
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #444;
            }
            QLineEdit:focus { border: 2px solid #6c63ff; }
        """)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_layout.addWidget(self.url_bar)
        
        go_btn = QPushButton("Go")
        go_btn.setFixedSize(50, 35)
        go_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7f74ff; }
        """)
        go_btn.clicked.connect(self.navigate_to_url)
        nav_layout.addWidget(go_btn)
        
        self.content_layout.addWidget(nav_bar)
        
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))
        self.browser.urlChanged.connect(self.update_url_bar)
        self.browser.loadFinished.connect(self.on_load_finished)
        
        self.content_layout.addWidget(self.browser)
        
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                color: #aaa;
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        self.content_layout.addWidget(self.status_bar)
        
        quick_links = QWidget()
        quick_links.setStyleSheet("background-color: #2d2d30; padding: 5px;")
        links_layout = QHBoxLayout(quick_links)
        links_layout.setContentsMargins(5, 3, 5, 3)
        
        links_label = QLabel("Quick:")
        links_label.setStyleSheet("color: #aaa; font-size: 11px;")
        links_layout.addWidget(links_label)
        
        bookmarks = [
            ("Google", "https://www.google.com"),
            ("YouTube", "https://www.youtube.com"),
            ("GitHub", "https://www.github.com"),
            ("Wikipedia", "https://www.wikipedia.org"),
            ("Reddit", "https://www.reddit.com"),
        ]
        
        for name, url in bookmarks:
            link_btn = QPushButton(name)
            link_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3e;
                    color: white;
                    padding: 4px 10px;
                    border-radius: 5px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #6c63ff; }
            """)
            link_btn.clicked.connect(lambda _, u=url: self.load_url(u))
            links_layout.addWidget(link_btn)
        
        links_layout.addStretch()
        self.content_layout.insertWidget(1, quick_links)
    
    def navigate_to_url(self):
        url = self.url_bar.text().strip()
        if not url:
            return
        
        if not url.startswith(('http://', 'https://')):
            if '.' in url and ' ' not in url:
                url = 'https://' + url
            else:
                url = 'https://www.google.com/search?q=' + url.replace(' ', '+')
        
        self.browser.setUrl(QUrl(url))
        self.status_bar.setText(f"Loading {url}...")
    
    def load_url(self, url):
        self.browser.setUrl(QUrl(url))
        self.url_bar.setText(url)
    
    def update_url_bar(self, url):
        self.url_bar.setText(url.toString())
    
    def on_load_finished(self, success):
        if success:
            self.status_bar.setText(f"Loaded: {self.browser.url().toString()}")
        else:
            self.status_bar.setText("Failed to load page")
    
    def go_back(self):
        self.browser.back()
    
    def go_forward(self):
        self.browser.forward()
    
    def reload_page(self):
        self.browser.reload()
    
    def go_home(self):
        self.browser.setUrl(QUrl("https://www.google.com"))


# ---------- Settings ----------
class SettingsApp(AppWindow):
    def __init__(self, desktop):
        super().__init__("Settings ⚙️", size=(480, 550), parent=desktop)
        self.desktop = desktop
        
        tab_layout = QHBoxLayout()
        self.appearance_btn = QPushButton("🎨 Appearance")
        self.system_btn = QPushButton("💻 System")
        self.about_btn = QPushButton("ℹ️ About")
        
        for btn in [self.appearance_btn, self.system_btn, self.about_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3e;
                    color: white;
                    padding: 10px;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #6c63ff; }
            """)
            tab_layout.addWidget(btn)
        
        self.content_layout.addLayout(tab_layout)
        
        self.content = QStackedWidget()
        self.content.addWidget(self.create_appearance_tab())
        self.content.addWidget(self.create_system_tab())
        self.content.addWidget(self.create_about_tab())
        
        self.content_layout.addWidget(self.content)
        
        self.appearance_btn.clicked.connect(lambda: self.content.setCurrentIndex(0))
        self.system_btn.clicked.connect(lambda: self.content.setCurrentIndex(1))
        self.about_btn.clicked.connect(lambda: self.content.setCurrentIndex(2))
    
    def create_appearance_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Choose Theme:")
        label.setStyleSheet("color: white; font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        themes = {
            "🌌 Cosmic Purple": "#6c63ff",
            "☁️ Sky Blue": "#5eb9ff",
            "🌿 Mint Green": "#6fffab",
            "🌙 Dark Mode": "#1e1e2e",
            "☀️ Light Mode": "#f5f5dc",
            "🔥 Fire Red": "#ff6b6b"
        }
        
        for name, color in themes.items():
            btn = QPushButton(name)
            text_color = "white" if color not in ["#f5f5dc"] else "black"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: {text_color};
                    border-radius: 10px;
                    padding: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ border: 2px solid white; }}
            """)
            btn.clicked.connect(lambda _, c=color: self.desktop.set_wallpaper_color(c))
            layout.addWidget(btn)
        
        layout.addStretch()
        return widget
    
    def create_system_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel(f"Current User: {self.desktop.current_user or 'Guest'}")
        info.setStyleSheet("color: white; font-size: 14px; margin-bottom: 15px;")
        layout.addWidget(info)
        
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ff8787; }
        """)
        logout_btn.clicked.connect(self.desktop.logout)
        layout.addWidget(logout_btn)
        
        layout.addStretch()
        return widget
    
    def create_about_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        about_text = QLabel(
            "BrackixOS v2.3\n\n"
            "A modern desktop environment\n"
            "built with PySide6\n\n"
            "Features:\n"
            "• Multi-user support\n"
            "• Custom themes\n"
            "• REAL Web Browser! 🌐\n"
            "• 7 Amazing Games! 🎮\n"
            "• Terminal & File Explorer\n\n"
            "Made with 💫 by Dev"
        )
        about_text.setStyleSheet("color: white; font-size: 13px;")
        about_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(about_text)
        
        layout.addStretch()
        return widget


# ---------- Terminal ----------
class Terminal(AppWindow):
    def __init__(self, desktop):
        super().__init__("Terminal 💻", size=(700, 500), parent=desktop)
        self.desktop = desktop
        
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 13px;
                border: none;
                padding: 10px;
            }
        """)
        self.content_layout.addWidget(self.output)
        
        input_layout = QHBoxLayout()
        prompt = QLabel("$")
        prompt.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
        input_layout.addWidget(prompt)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter command (type 'help')...")
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                border: none;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 13px;
                padding: 5px;
            }
        """)
        self.input.returnPressed.connect(self.run_command)
        input_layout.addWidget(self.input)
        
        self.content_layout.addLayout(input_layout)
        
        self.output.append("═══════════════════════════════════")
        self.output.append("  Shell v2.3")
        self.output.append("═══════════════════════════════════\n")
        self.output.append("Type 'help' for available commands.\n")
    
    def run_command(self):
        cmd = self.input.text().strip()
        self.input.clear()
        if not cmd:
            return
        
        self.output.append(f"<span style='color: #6c63ff;'>$ {cmd}</span>")
        
        if cmd == "help":
            self.output.append(
                "<span style='color: white;'>"
                "Available commands:\n"
                "  help, clear, ls, date, whoami, sysinfo\n"
                "  exec <app> - Launch apps\n"
                "  exit, logout, shutdown\n"
                "</span>"
            )
        elif cmd == "clear":
            self.output.clear()
        elif cmd == "ls":
            try:
                files = os.listdir(self.desktop.base_path)
                self.output.append("<span style='color: #5eb9ff;'>" + "\n".join(files) + "</span>")
            except Exception as e:
                self.output.append(f"<span style='color: #ff6b6b;'>Error: {e}</span>")
        elif cmd == "date":
            self.output.append(f"<span style='color: white;'>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>")
        elif cmd == "whoami":
            self.output.append(f"<span style='color: white;'>{self.desktop.current_user or 'guest'}</span>")
        elif cmd == "sysinfo":
            self.output.append(
                f"<span style='color: white;'>BrackixOS v2.3\nUser: {self.desktop.current_user or 'guest'}\n"
                f"Platform: {sys.platform}\nPython: {sys.version.split()[0]}</span>"
            )
        elif cmd.startswith("exec "):
            app = cmd.split(" ", 1)[1].strip().lower()
            self.launch_app(app)
        elif cmd == "exit":
            self.output.append("<span style='color: #ff6b6b;'>Closing...</span>")
            QTimer.singleShot(300, self.close)
        elif cmd == "logout":
            QTimer.singleShot(500, self.desktop.logout)
        elif cmd in ("shutdown", "poweroff"):
            QTimer.singleShot(500, self.desktop.power_off)
        else:
            self.output.append(f"<span style='color: #ff6b6b;'>Command not found: {cmd}</span>")
        
        self.output.append("")
    
    def launch_app(self, app):
        app_map = {
            "calc": self.desktop.launch_calc,
            "files": self.desktop.launch_files,
            "notepad": self.desktop.launch_notepad,
            "settings": self.desktop.launch_settings,
            "browser": self.desktop.launch_browser,
            "games": self.desktop.launch_games,
        }
        
        if app in app_map:
            app_map[app]()
            self.output.append(f"<span style='color: #6fffab;'>Launched {app}</span>")
        else:
            self.output.append(f"<span style='color: #ff6b6b;'>Unknown app: {app}</span>")


# ---------- File Explorer ----------
class FileExplorer(AppWindow):
    def __init__(self, desktop):
        super().__init__("Files 📁", size=(800, 550), parent=desktop)
        self.desktop = desktop
        
        path_bar = QHBoxLayout()
        self.path_label = QLabel("")
        self.path_label.setStyleSheet("color: white; font-weight: bold; padding: 8px; background-color: #2d2d30; border-radius: 5px;")
        path_bar.addWidget(self.path_label)
        
        up_btn = QPushButton("⬆️ Up")
        up_btn.setStyleSheet("padding: 8px; background-color: #3a3a3e; color: white; border-radius: 5px;")
        up_btn.clicked.connect(self.go_up)
        path_bar.addWidget(up_btn)
        
        self.content_layout.addLayout(path_bar)
        
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item { padding: 8px; border-radius: 4px; }
            QListWidget::item:hover { background-color: #3a3a3e; }
            QListWidget::item:selected { background-color: #6c63ff; }
        """)
        self.file_list.itemDoubleClicked.connect(self.open_item)
        self.content_layout.addWidget(self.file_list)
        
        btn_layout = QHBoxLayout()
        
        buttons = [
            ("🔄 Refresh", self.refresh_files),
            ("📄 New File", self.create_file),
            ("📁 New Folder", self.create_folder),
            ("🗑️ Delete", self.delete_item)
        ]
        
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3e;
                    color: white;
                    padding: 10px;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #6c63ff; }
            """)
            btn.clicked.connect(callback)
            btn_layout.addWidget(btn)
        
        self.content_layout.addLayout(btn_layout)
        
        self.base_path = desktop.base_path
        self.refresh_files()
    
    def refresh_files(self):
        self.file_list.clear()
        self.path_label.setText(f"📂 {self.base_path}")
        try:
            items = sorted(os.listdir(self.base_path))
            for item in items:
                full_path = os.path.join(self.base_path, item)
                icon = "📁" if os.path.isdir(full_path) else "📄"
                self.file_list.addItem(f"{icon} {item}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not read directory: {e}")
    
    def go_up(self):
        parent = os.path.dirname(self.base_path)
        if parent and os.path.exists(parent):
            self.base_path = parent
            self.refresh_files()
    
    def create_file(self):
        name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and name:
            try:
                open(os.path.join(self.base_path, name), "w").close()
                self.refresh_files()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def create_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            try:
                os.makedirs(os.path.join(self.base_path, name), exist_ok=True)
                self.refresh_files()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def delete_item(self):
        current = self.file_list.currentItem()
        if current:
            name = current.text().split(" ", 1)[1]
            path = os.path.join(self.base_path, name)
            reply = QMessageBox.question(self, "Delete", f"Delete '{name}'?")
            if reply == QMessageBox.Yes:
                try:
                    if os.path.isdir(path):
                        os.rmdir(path)
                    else:
                        os.remove(path)
                    self.refresh_files()
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
    
    def open_item(self, item):
        name = item.text().split(" ", 1)[1]
        path = os.path.join(self.base_path, name)
        if os.path.isdir(path):
            self.base_path = path
            self.refresh_files()


# ---------- GAME 1: Number Guess ----------
class NumberGuessGame(AppWindow):
    def __init__(self, parent=None):
        super().__init__("Number Guess 🎲", size=(400, 450), parent=parent)
        
        self.target = random.randint(1, 100)
        self.attempts = 0
        self.max_attempts = 10
        
        title = QLabel("🎲 Guess the Number!")
        title.setFont(QFont("Orbitron", 18, QFont.Bold))
        title.setStyleSheet("color: #6c63ff;")
        title.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(title)
        
        self.feedback = QLabel("")
        self.feedback.setFont(QFont("Arial", 14, QFont.Bold))
        self.feedback.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.feedback)
        
        self.attempts_label = QLabel(f"Attempts: {self.attempts}/{self.max_attempts}")
        self.attempts_label.setStyleSheet("color: white;")
        self.attempts_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.attempts_label)
        
        input_layout = QHBoxLayout()
        self.guess_input = QLineEdit()
        self.guess_input.setPlaceholderText("Enter guess...")
        self.guess_input.returnPressed.connect(self.check_guess)
        input_layout.addWidget(self.guess_input)
        
        guess_btn = QPushButton("Guess!")
        guess_btn.clicked.connect(self.check_guess)
        input_layout.addWidget(guess_btn)
        
        self.content_layout.addLayout(input_layout)
        
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setMaximumHeight(120)
        self.content_layout.addWidget(self.history)
        
        reset_btn = QPushButton("🔄 New Game")
        reset_btn.clicked.connect(self.reset_game)
        self.content_layout.addWidget(reset_btn)
    
    def check_guess(self):
        try:
            guess = int(self.guess_input.text())
            self.guess_input.clear()
            
            if guess < 1 or guess > 100:
                self.feedback.setText("Between 1 and 100!")
                self.feedback.setStyleSheet("color: #ff6b6b;")
                return
            
            self.attempts += 1
            self.attempts_label.setText(f"Attempts: {self.attempts}/{self.max_attempts}")
            self.history.append(f"Attempt {self.attempts}: {guess}")
            
            if guess == self.target:
                self.feedback.setText(f"🎉 Correct in {self.attempts} tries!")
                self.feedback.setStyleSheet("color: #6fffab;")
                self.guess_input.setEnabled(False)
            elif self.attempts >= self.max_attempts:
                self.feedback.setText(f"😢 Game Over! Was {self.target}")
                self.feedback.setStyleSheet("color: #ff6b6b;")
                self.guess_input.setEnabled(False)
            elif guess < self.target:
                self.feedback.setText("📈 Too low!")
                self.feedback.setStyleSheet("color: #5eb9ff;")
            else:
                self.feedback.setText("📉 Too high!")
                self.feedback.setStyleSheet("color: #ff9f43;")
        except:
            self.feedback.setText("Invalid number!")
            self.feedback.setStyleSheet("color: #ff6b6b;")
    
    def reset_game(self):
        self.target = random.randint(1, 100)
        self.attempts = 0
        self.attempts_label.setText(f"Attempts: {self.attempts}/{self.max_attempts}")
        self.feedback.setText("")
        self.history.clear()
        self.guess_input.setEnabled(True)


# ---------- GAME 2: Memory Match ----------
class MemoryMatchGame(AppWindow):
    def __init__(self, parent=None):
        super().__init__("Memory Match 🧩", size=(500, 550), parent=parent)
        
        self.cards = ["🍎", "🍊", "🍋", "🍌", "🍇", "🍓", "🍒", "🥝"] * 2
        random.shuffle(self.cards)
        self.revealed = []
        self.matched = []
        self.moves = 0
        
        title = QLabel("🧩 Memory Match")
        title.setFont(QFont("Orbitron", 18, QFont.Bold))
        title.setStyleSheet("color: #6c63ff;")
        title.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(title)
        
        self.moves_label = QLabel(f"Moves: {self.moves}")
        self.moves_label.setStyleSheet("color: white;")
        self.moves_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.moves_label)
        
        grid_widget = QWidget()
        self.grid = QGridLayout(grid_widget)
        self.grid.setSpacing(10)
        
        self.buttons = []
        for i in range(16):
            btn = QPushButton("?")
            btn.setFixedSize(80, 80)
            btn.setFont(QFont("Segoe UI Emoji", 24))
            btn.clicked.connect(lambda _, idx=i: self.flip_card(idx))
            self.buttons.append(btn)
            self.grid.addWidget(btn, i // 4, i % 4)
        
        self.content_layout.addWidget(grid_widget)
        
        reset_btn = QPushButton("🔄 New Game")
        reset_btn.clicked.connect(self.reset_game)
        self.content_layout.addWidget(reset_btn)
    
    def flip_card(self, idx):
        if idx in self.revealed or idx in self.matched or len(self.revealed) >= 2:
            return
        
        self.buttons[idx].setText(self.cards[idx])
        self.revealed.append(idx)
        
        if len(self.revealed) == 2:
            self.moves += 1
            self.moves_label.setText(f"Moves: {self.moves}")
            QTimer.singleShot(800, self.check_match)
    
    def check_match(self):
        idx1, idx2 = self.revealed
        
        if self.cards[idx1] == self.cards[idx2]:
            self.matched.extend([idx1, idx2])
            
            if len(self.matched) == 16:
                QMessageBox.information(self, "Victory!", f"🎉 You won in {self.moves} moves!")
        else:
            for idx in [idx1, idx2]:
                self.buttons[idx].setText("?")
        
        self.revealed.clear()
    
    def reset_game(self):
        self.cards = ["🍎", "🍊", "🍋", "🍌", "🍇", "🍓", "🍒", "🥝"] * 2
        random.shuffle(self.cards)
        self.revealed.clear()
        self.matched.clear()
        self.moves = 0
        self.moves_label.setText(f"Moves: {self.moves}")
        
        for btn in self.buttons:
            btn.setText("?")


# ---------- GAME 3: Click Speed ----------
class ClickSpeedGame(AppWindow):
    def __init__(self, parent=None):
        super().__init__("Click Speed 🎯", size=(450, 500), parent=parent)
        
        self.clicks = 0
        self.time_left = 10
        self.game_active = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        title = QLabel("🎯 Click Speed Test")
        title.setFont(QFont("Orbitron", 18, QFont.Bold))
        title.setStyleSheet("color: #6c63ff;")
        title.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(title)
        
        self.time_label = QLabel(f"Time: {self.time_left}s")
        self.time_label.setStyleSheet("color: #5eb9ff;")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.time_label)
        
        self.clicks_label = QLabel(f"Clicks: {self.clicks}")
        self.clicks_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.clicks_label.setStyleSheet("color: #6fffab;")
        self.clicks_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.clicks_label)
        
        self.click_btn = QPushButton("START!")
        self.click_btn.setFixedSize(200, 200)
        self.click_btn.setFont(QFont("Arial", 24, QFont.Bold))
        self.click_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                border-radius: 100px;
            }
        """)
        self.click_btn.clicked.connect(self.handle_click)
        
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        btn_layout.addWidget(self.click_btn)
        btn_layout.addStretch()
        self.content_layout.addWidget(btn_container)
        
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.result_label)
        
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self.reset_game)
        self.content_layout.addWidget(reset_btn)
    
    def handle_click(self):
        if not self.game_active:
            self.start_game()
        else:
            self.clicks += 1
            self.clicks_label.setText(f"Clicks: {self.clicks}")
    
    def start_game(self):
        self.game_active = True
        self.clicks = 0
        self.time_left = 10
        self.clicks_label.setText(f"Clicks: {self.clicks}")
        self.time_label.setText(f"Time: {self.time_left}s")
        self.result_label.setText("")
        self.click_btn.setText("CLICK!")
        self.timer.start(1000)
    
    def update_timer(self):
        self.time_left -= 1
        self.time_label.setText(f"Time: {self.time_left}s")
        
        if self.time_left <= 0:
            self.end_game()
    
    def end_game(self):
        self.timer.stop()
        self.game_active = False
        self.click_btn.setText("START!")
        
        cps = self.clicks / 10
        grade = "🏆 LEGENDARY!" if cps >= 10 else "⭐ EXCELLENT!" if cps >= 8 else "👍 GREAT!" if cps >= 6 else "👌 GOOD" if cps >= 4 else "🐌 KEEP TRYING!"
        
        self.result_label.setText(f"{grade}\n{self.clicks} clicks • {cps:.1f} cps")
    
    def reset_game(self):
        self.timer.stop()
        self.game_active = False
        self.clicks = 0
        self.time_left = 10
        self.clicks_label.setText(f"Clicks: {self.clicks}")
        self.time_label.setText(f"Time: {self.time_left}s")
        self.result_label.setText("")
        self.click_btn.setText("START!")


# ---------- GAME 4: TETRIS 🎮 ----------
class TetrisGame(AppWindow):
    def __init__(self, parent=None):
        super().__init__("Tetris 🎮", size=(400, 650), parent=parent)
        
        self.board_width = 10
        self.board_height = 20
        self.block_size = 25
        self.board = [[0] * self.board_width for _ in range(self.board_height)]
        
        self.shapes = [
            [[1, 1, 1, 1]],  # I
            [[1, 1], [1, 1]],  # O
            [[0, 1, 0], [1, 1, 1]],  # T
            [[1, 1, 0], [0, 1, 1]],  # S
            [[0, 1, 1], [1, 1, 0]],  # Z
            [[1, 0, 0], [1, 1, 1]],  # L
            [[0, 0, 1], [1, 1, 1]]   # J
        ]
        
        self.colors = ['#00ffff', '#ffff00', '#ff00ff', '#00ff00', '#ff0000', '#0000ff', '#ffa500']
        
        self.score = 0
        self.game_over = False
        
        info_layout = QHBoxLayout()
        
        self.score_label = QLabel(f"Score: {self.score}")
        self.score_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        info_layout.addWidget(self.score_label)
        
        info_layout.addStretch()
        
        self.content_layout.addLayout(info_layout)
        
        self.canvas = QWidget()
        self.canvas.setFixedSize(self.board_width * self.block_size, self.board_height * self.block_size)
        self.canvas.setStyleSheet("background-color: #0a0a0a; border: 2px solid #6c63ff;")
        self.content_layout.addWidget(self.canvas)
        
        btn_layout = QHBoxLayout()
        
        self.left_btn = QPushButton("◀")
        self.left_btn.clicked.connect(self.move_left)
        btn_layout.addWidget(self.left_btn)
        
        self.rotate_btn = QPushButton("🔄")
        self.rotate_btn.clicked.connect(self.rotate)
        btn_layout.addWidget(self.rotate_btn)
        
        self.right_btn = QPushButton("▶")
        self.right_btn.clicked.connect(self.move_right)
        btn_layout.addWidget(self.right_btn)
        
        self.down_btn = QPushButton("▼")
        self.down_btn.clicked.connect(self.move_down)
        btn_layout.addWidget(self.down_btn)
        
        for btn in [self.left_btn, self.rotate_btn, self.right_btn, self.down_btn]:
            btn.setFixedHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3e;
                    color: white;
                    font-size: 18px;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #6c63ff; }
            """)
        
        self.content_layout.addLayout(btn_layout)
        
        reset_btn = QPushButton("🔄 New Game")
        reset_btn.clicked.connect(self.reset_game)
        self.content_layout.addWidget(reset_btn)
        
        self.spawn_piece()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(500)
    
    def spawn_piece(self):
        idx = random.randint(0, len(self.shapes) - 1)
        self.current_shape = [row[:] for row in self.shapes[idx]]
        self.current_color = self.colors[idx]
        self.current_x = self.board_width // 2 - len(self.current_shape[0]) // 2
        self.current_y = 0
        
        if self.check_collision(self.current_shape, self.current_x, self.current_y):
            self.game_over = True
            self.timer.stop()
            QMessageBox.information(self, "Game Over", f"Final Score: {self.score}")
    
    def check_collision(self, shape, x, y):
        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    board_x = x + col_idx
                    board_y = y + row_idx
                    
                    if (board_x < 0 or board_x >= self.board_width or
                        board_y >= self.board_height or
                        (board_y >= 0 and self.board[board_y][board_x])):
                        return True
        return False
    
    def merge_piece(self):
        for row_idx, row in enumerate(self.current_shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    self.board[self.current_y + row_idx][self.current_x + col_idx] = self.current_color
    
    def clear_lines(self):
        lines_cleared = 0
        y = self.board_height - 1
        while y >= 0:
            if all(self.board[y]):
                del self.board[y]
                self.board.insert(0, [0] * self.board_width)
                lines_cleared += 1
            else:
                y -= 1
        
        if lines_cleared:
            self.score += lines_cleared * 100
            self.score_label.setText(f"Score: {self.score}")
    
    def move_left(self):
        if not self.game_over and not self.check_collision(self.current_shape, self.current_x - 1, self.current_y):
            self.current_x -= 1
            self.canvas.update()
    
    def move_right(self):
        if not self.game_over and not self.check_collision(self.current_shape, self.current_x + 1, self.current_y):
            self.current_x += 1
            self.canvas.update()
    
    def move_down(self):
        if not self.game_over:
            if not self.check_collision(self.current_shape, self.current_x, self.current_y + 1):
                self.current_y += 1
            else:
                self.merge_piece()
                self.clear_lines()
                self.spawn_piece()
            self.canvas.update()
    
    def rotate(self):
        if not self.game_over:
            rotated = [[self.current_shape[row][col] for row in range(len(self.current_shape) - 1, -1, -1)]
                      for col in range(len(self.current_shape[0]))]
            
            if not self.check_collision(rotated, self.current_x, self.current_y):
                self.current_shape = rotated
                self.canvas.update()
    
    def game_loop(self):
        self.move_down()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.canvas)
        
        # Draw board
        for y in range(self.board_height):
            for x in range(self.board_width):
                if self.board[y][x]:
                    painter.setBrush(QColor(self.board[y][x]))
                    painter.drawRect(x * self.block_size, y * self.block_size, self.block_size - 1, self.block_size - 1)
        
        # Draw current piece
        if not self.game_over:
            painter.setBrush(QColor(self.current_color))
            for row_idx, row in enumerate(self.current_shape):
                for col_idx, cell in enumerate(row):
                    if cell:
                        x = (self.current_x + col_idx) * self.block_size
                        y = (self.current_y + row_idx) * self.block_size
                        painter.drawRect(x, y, self.block_size - 1, self.block_size - 1)
    
    def reset_game(self):
        self.board = [[0] * self.board_width for _ in range(self.board_height)]
        self.score = 0
        self.score_label.setText(f"Score: {self.score}")
        self.game_over = False
        self.spawn_piece()
        self.timer.start(500)
        self.canvas.update()


# ---------- GAME 5: SNAKE 🐍 ----------
class SnakeGame(AppWindow):
    def __init__(self, parent=None):
        super().__init__("Snake 🐍", size=(500, 580), parent=parent)
        
        self.grid_size = 20
        self.cell_size = 20
        
        self.snake = [(10, 10), (10, 11), (10, 12)]
        self.direction = (-1, 0)  # up
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        
        self.score_label = QLabel(f"Score: {self.score}")
        self.score_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.score_label)
        
        self.canvas = QWidget()
        self.canvas.setFixedSize(self.grid_size * self.cell_size, self.grid_size * self.cell_size)
        self.canvas.setStyleSheet("background-color: #0a0a0a; border: 2px solid #6c63ff;")
        self.content_layout.addWidget(self.canvas)
        
        btn_layout = QGridLayout()
        
        up_btn = QPushButton("▲")
        up_btn.clicked.connect(lambda: self.change_direction((-1, 0)))
        btn_layout.addWidget(up_btn, 0, 1)
        
        left_btn = QPushButton("◀")
        left_btn.clicked.connect(lambda: self.change_direction((0, -1)))
        btn_layout.addWidget(left_btn, 1, 0)
        
        right_btn = QPushButton("▶")
        right_btn.clicked.connect(lambda: self.change_direction((0, 1)))
        btn_layout.addWidget(right_btn, 1, 2)
        
        down_btn = QPushButton("▼")
        down_btn.clicked.connect(lambda: self.change_direction((1, 0)))
        btn_layout.addWidget(down_btn, 2, 1)
        
        for btn in [up_btn, left_btn, right_btn, down_btn]:
            btn.setFixedSize(60, 60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3e;
                    color: white;
                    font-size: 20px;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #6c63ff; }
            """)
        
        self.content_layout.addLayout(btn_layout)
        
        reset_btn = QPushButton("🔄 New Game")
        reset_btn.clicked.connect(self.reset_game)
        self.content_layout.addWidget(reset_btn)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(150)
    
    def spawn_food(self):
        while True:
            food = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))
            if food not in self.snake:
                return food
    
    def change_direction(self, new_dir):
        # Prevent 180-degree turns
        if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
            self.direction = new_dir
    
    def game_loop(self):
        if self.game_over:
            return
        
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        
        # Check collision with walls
        if (new_head[0] < 0 or new_head[0] >= self.grid_size or
            new_head[1] < 0 or new_head[1] >= self.grid_size):
            self.game_over = True
            self.timer.stop()
            QMessageBox.information(self, "Game Over", f"Final Score: {self.score}")
            return
        
        # Check collision with self
        if new_head in self.snake:
            self.game_over = True
            self.timer.stop()
            QMessageBox.information(self, "Game Over", f"Final Score: {self.score}")
            return
        
        self.snake.insert(0, new_head)
        
        # Check if food eaten
        if new_head == self.food:
            self.score += 10
            self.score_label.setText(f"Score: {self.score}")
            self.food = self.spawn_food()
        else:
            self.snake.pop()
        
        self.canvas.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.canvas)
        
        # Draw food
        painter.setBrush(QColor('#ff0000'))
        painter.drawRect(self.food[1] * self.cell_size, self.food[0] * self.cell_size, 
                        self.cell_size - 1, self.cell_size - 1)
        
        # Draw snake
        for i, (row, col) in enumerate(self.snake):
            if i == 0:
                painter.setBrush(QColor('#00ff00'))
            else:
                painter.setBrush(QColor('#6fffab'))
            painter.drawRect(col * self.cell_size, row * self.cell_size, 
                           self.cell_size - 1, self.cell_size - 1)
    
    def reset_game(self):
        self.snake = [(10, 10), (10, 11), (10, 12)]
        self.direction = (-1, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.score_label.setText(f"Score: {self.score}")
        self.game_over = False
        self.timer.start(150)
        self.canvas.update()


# ---------- GAME 6: 2048 🎯 ----------
class Game2048(AppWindow):
    def __init__(self, parent=None):
        super().__init__("2048 🎯", size=(480, 600), parent=parent)
        
        self.grid_size = 4
        self.board = [[0] * self.grid_size for _ in range(self.grid_size)]
        self.score = 0
        
        self.score_label = QLabel(f"Score: {self.score}")
        self.score_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.score_label)
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        
        self.tiles = []
        for i in range(self.grid_size):
            row = []
            for j in range(self.grid_size):
                tile = QLabel("0")
                tile.setFixedSize(90, 90)
                tile.setAlignment(Qt.AlignCenter)
                tile.setStyleSheet("""
                    QLabel {
                        background-color: #3a3a3e;
                        color: white;
                        font-size: 24px;
                        font-weight: bold;
                        border-radius: 10px;
                    }
                """)
                self.grid_layout.addWidget(tile, i, j)
                row.append(tile)
            self.tiles.append(row)
        
        self.content_layout.addWidget(self.grid_widget)
        
        btn_layout = QGridLayout()
        
        up_btn = QPushButton("▲")
        up_btn.clicked.connect(lambda: self.move('up'))
        btn_layout.addWidget(up_btn, 0, 1)
        
        left_btn = QPushButton("◀")
        left_btn.clicked.connect(lambda: self.move('left'))
        btn_layout.addWidget(left_btn, 1, 0)
        
        right_btn = QPushButton("▶")
        right_btn.clicked.connect(lambda: self.move('right'))
        btn_layout.addWidget(right_btn, 1, 2)
        
        down_btn = QPushButton("▼")
        down_btn.clicked.connect(lambda: self.move('down'))
        btn_layout.addWidget(down_btn, 2, 1)
        
        for btn in [up_btn, left_btn, right_btn, down_btn]:
            btn.setFixedSize(80, 60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c63ff;
                    color: white;
                    font-size: 20px;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #7f74ff; }
            """)
        
        self.content_layout.addLayout(btn_layout)
        
        reset_btn = QPushButton("🔄 New Game")
        reset_btn.clicked.connect(self.reset_game)
        self.content_layout.addWidget(reset_btn)
        
        self.spawn_tile()
        self.spawn_tile()
        self.update_display()
    
    def spawn_tile(self):
        empty_cells = [(i, j) for i in range(self.grid_size) for j in range(self.grid_size) if self.board[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.board[i][j] = 2 if random.random() < 0.9 else 4
    
    def get_tile_color(self, value):
        colors = {
            0: "#3a3a3e",
            2: "#eee4da",
            4: "#ede0c8",
            8: "#f2b179",
            16: "#f59563",
            32: "#f67c5f",
            64: "#f65e3b",
            128: "#edcf72",
            256: "#edcc61",
            512: "#edc850",
            1024: "#edc53f",
            2048: "#edc22e"
        }
        return colors.get(value, "#3c3a32")
    
    def update_display(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                value = self.board[i][j]
                self.tiles[i][j].setText(str(value) if value else "")
                color = self.get_tile_color(value)
                text_color = "white" if value > 4 else "#776e65"
                self.tiles[i][j].setStyleSheet(f"""
                    QLabel {{
                        background-color: {color};
                        color: {text_color};
                        font-size: 24px;
                        font-weight: bold;
                        border-radius: 10px;
                    }}
                """)
    
    def compress(self, row):
        new_row = [i for i in row if i != 0]
        new_row += [0] * (len(row) - len(new_row))
        return new_row
    
    def merge(self, row):
        for i in range(len(row) - 1):
            if row[i] == row[i + 1] and row[i] != 0:
                row[i] *= 2
                row[i + 1] = 0
                self.score += row[i]
        return row
    
    def move(self, direction):
        original_board = [row[:] for row in self.board]
        
        if direction == 'left':
            for i in range(self.grid_size):
                self.board[i] = self.compress(self.board[i])
                self.board[i] = self.merge(self.board[i])
                self.board[i] = self.compress(self.board[i])
        
        elif direction == 'right':
            for i in range(self.grid_size):
                self.board[i] = self.compress(self.board[i][::-1])[::-1]
                self.board[i] = self.merge(self.board[i][::-1])[::-1]
                self.board[i] = self.compress(self.board[i][::-1])[::-1]
        
        elif direction == 'up':
            self.board = [[self.board[j][i] for j in range(self.grid_size)] for i in range(self.grid_size)]
            for i in range(self.grid_size):
                self.board[i] = self.compress(self.board[i])
                self.board[i] = self.merge(self.board[i])
                self.board[i] = self.compress(self.board[i])
            self.board = [[self.board[j][i] for j in range(self.grid_size)] for i in range(self.grid_size)]
        
        elif direction == 'down':
            self.board = [[self.board[j][i] for j in range(self.grid_size)] for i in range(self.grid_size)]
            for i in range(self.grid_size):
                self.board[i] = self.compress(self.board[i][::-1])[::-1]
                self.board[i] = self.merge(self.board[i][::-1])[::-1]
                self.board[i] = self.compress(self.board[i][::-1])[::-1]
            self.board = [[self.board[j][i] for j in range(self.grid_size)] for i in range(self.grid_size)]
        
        if self.board != original_board:
            self.spawn_tile()
            self.score_label.setText(f"Score: {self.score}")
            self.update_display()
            
            if self.check_game_over():
                QMessageBox.information(self, "Game Over", f"Final Score: {self.score}")
    
    def check_game_over(self):
        # Check if any moves possible
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.board[i][j] == 0:
                    return False
                if j < self.grid_size - 1 and self.board[i][j] == self.board[i][j + 1]:
                    return False
                if i < self.grid_size - 1 and self.board[i][j] == self.board[i + 1][j]:
                    return False
        return True
    
    def reset_game(self):
        self.board = [[0] * self.grid_size for _ in range(self.grid_size)]
        self.score = 0
        self.score_label.setText(f"Score: {self.score}")
        self.spawn_tile()
        self.spawn_tile()
        self.update_display()


# ---------- GAME 7: TIC TAC TOE ❌⭕ ----------
class TicTacToeGame(AppWindow):
    def __init__(self, parent=None):
        super().__init__("Tic Tac Toe ❌⭕", size=(450, 550), parent=parent)
        
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.game_over = False
        
        title = QLabel("Tic Tac Toe")
        title.setFont(QFont("Orbitron", 20, QFont.Bold))
        title.setStyleSheet("color: #6c63ff;")
        title.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(title)
        
        self.status_label = QLabel("Player X's turn")
        self.status_label.setStyleSheet("color: white; font-size: 16px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.status_label)
        
        grid_widget = QWidget()
        self.grid = QGridLayout(grid_widget)
        self.grid.setSpacing(10)
        
        self.buttons = []
        for i in range(3):
            row = []
            for j in range(3):
                btn = QPushButton("")
                btn.setFixedSize(110, 110)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3a3a3e;
                        color: white;
                        font-size: 48px;
                        font-weight: bold;
                        border-radius: 10px;
                    }
                    QPushButton:hover {
                        background-color: #505055;
                    }
                """)
                btn.clicked.connect(lambda _, r=i, c=j: self.make_move(r, c))
                self.grid.addWidget(btn, i, j)
                row.append(btn)
            self.buttons.append(row)
        
        self.content_layout.addWidget(grid_widget)
        
        reset_btn = QPushButton("🔄 New Game")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #7f74ff; }
        """)
        reset_btn.clicked.connect(self.reset_game)
        self.content_layout.addWidget(reset_btn)
    
    def make_move(self, row, col):
        if self.game_over or self.board[row][col] != '':
            return
        
        self.board[row][col] = self.current_player
        self.buttons[row][col].setText(self.current_player)
        
        if self.current_player == 'X':
            self.buttons[row][col].setStyleSheet("""
                QPushButton {
                    background-color: #ff6b6b;
                    color: white;
                    font-size: 48px;
                    font-weight: bold;
                    border-radius: 10px;
                }
            """)
        else:
            self.buttons[row][col].setStyleSheet("""
                QPushButton {
                    background-color: #6c63ff;
                    color: white;
                    font-size: 48px;
                    font-weight: bold;
                    border-radius: 10px;
                }
            """)
        
        if self.check_winner():
            self.status_label.setText(f"🎉 Player {self.current_player} wins!")
            self.status_label.setStyleSheet("color: #6fffab; font-size: 18px; font-weight: bold;")
            self.game_over = True
        elif self.check_draw():
            self.status_label.setText("🤝 It's a draw!")
            self.status_label.setStyleSheet("color: #ff9f43; font-size: 18px; font-weight: bold;")
            self.game_over = True
        else:
            self.current_player = 'O' if self.current_player == 'X' else 'X'
            self.status_label.setText(f"Player {self.current_player}'s turn")
    
    def check_winner(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != '':
                return True
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != '':
                return True
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != '':
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != '':
            return True
        
        return False
    
    def check_draw(self):
        for row in self.board:
            if '' in row:
                return False
        return True
    
    def reset_game(self):
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.game_over = False
        self.status_label.setText("Player X's turn")
        self.status_label.setStyleSheet("color: white; font-size: 16px;")
        
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].setText("")
                self.buttons[i][j].setStyleSheet("""
                    QPushButton {
                        background-color: #3a3a3e;
                        color: white;
                        font-size: 48px;
                        font-weight: bold;
                        border-radius: 10px;
                    }
                    QPushButton:hover {
                        background-color: #505055;
                    }
                """)


# ---------- GAME CENTER WITH ALL 7 GAMES! ----------
class GameCenter(AppWindow):
    def __init__(self, desktop):
        super().__init__("Game Center 🎮", size=(700, 650), parent=desktop)
        
        title = QLabel("Game Center")
        title.setFont(QFont("Orbitron", 24, QFont.Bold))
        title.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(title)
        
        subtitle = QLabel("7 Amazing Games to Play!")
        subtitle.setStyleSheet("color: #aaa; margin-bottom: 25px; font-size: 14px;")
        subtitle.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(subtitle)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        games = [
            ("🎲 Number Guess", "Guess the random number!", self.launch_number_guess),
            ("🧩 Memory Match", "Match all the pairs!", self.launch_memory),
            ("🎯 Click Speed", "How fast can you click?", self.launch_clicker),
            ("🎮 Tetris", "Classic block stacking game!", self.launch_tetris),
            ("🐍 Snake", "Eat and grow your snake!", self.launch_snake),
            ("🎯 2048", "Merge tiles to reach 2048!", self.launch_2048),
            ("❌⭕ Tic Tac Toe", "Beat your opponent!", self.launch_tictactoe)
        ]
        
        for name, desc, callback in games:
            btn = QPushButton(f"{name}\n{desc}")
            btn.setFixedHeight(80)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3e;
                    color: white;
                    border-radius: 12px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 15px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #6c63ff;
                    border: 2px solid #8a7fff;
                }
                QPushButton:pressed {
                    background-color: #5a52cc;
                }
            """)
            btn.clicked.connect(callback)
            scroll_layout.addWidget(btn)
        
        scroll.setWidget(scroll_widget)
        self.content_layout.addWidget(scroll)
    
    def launch_number_guess(self):
        self.number_game = NumberGuessGame(self)
        self.number_game.show()
    
    def launch_memory(self):
        self.memory_game = MemoryMatchGame(self)
        self.memory_game.show()
    
    def launch_clicker(self):
        self.clicker_game = ClickSpeedGame(self)
        self.clicker_game.show()
    
    def launch_tetris(self):
        self.tetris_game = TetrisGame(self)
        self.tetris_game.show()
    
    def launch_snake(self):
        self.snake_game = SnakeGame(self)
        self.snake_game.show()
    
    def launch_2048(self):
        self.game_2048 = Game2048(self)
        self.game_2048.show()
    
    def launch_tictactoe(self):
        self.tictactoe_game = TicTacToeGame(self)
        self.tictactoe_game.show()


# ---------- Main BrackixOS Manager ----------
class BrackixOS(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BrackixOS 💻✨")
        self.resize(1000, 700)
        
        self.user_manager = UserManager()
        
        self.stack = QStackedWidget()
        self.boot = BootScreen(self.show_login)
        self.login = LoginScreen(self.show_desktop, self.user_manager)
        self.desktop = Desktop(self, self.user_manager)
        
        self.stack.addWidget(self.boot)
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.desktop)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setLayout(layout)
    
    def show_login(self):
        self.stack.setCurrentWidget(self.login)
    
    def show_desktop(self, username):
        self.desktop.set_current_user(username)
        self.stack.setCurrentWidget(self.desktop)


# ---------- Entry point ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    
    window = BrackixOS()
    window.show()
    sys.exit(app.exec())
