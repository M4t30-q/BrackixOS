import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, 
    QMessageBox, QFontDialog, QColorDialog, QInputDialog
)
from PySide6.QtGui import QAction, QFont, QTextCursor
from PySide6.QtCore import Qt


class NtPad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.is_modified = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("NtPad 📝✨")
        self.setGeometry(300, 150, 900, 650)

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 12))
        self.text_edit.textChanged.connect(self.text_changed)
        self.setCentralWidget(self.text_edit)

        # Create menu bar
        self.create_menu_bar()

        # Apply styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d30;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                selection-background-color: #264f78;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #f0f0f0;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 12px;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #f0f0f0;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QMessageBox {
                background-color: #2d2d30;
                color: #f0f0f0;
            }
        """)

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.text_edit.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.text_edit.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.text_edit.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.text_edit.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.text_edit.paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.text_edit.selectAll)
        edit_menu.addAction(select_all_action)

        find_action = QAction("Find...", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.find_text)
        edit_menu.addAction(find_action)

        # Format Menu
        format_menu = menubar.addMenu("Format")

        font_action = QAction("Font...", self)
        font_action.triggered.connect(self.change_font)
        format_menu.addAction(font_action)

        color_action = QAction("Text Color...", self)
        color_action.triggered.connect(self.change_text_color)
        format_menu.addAction(color_action)

        # View Menu
        view_menu = menubar.addMenu("View")

        word_wrap_action = QAction("Word Wrap", self)
        word_wrap_action.setCheckable(True)
        word_wrap_action.setChecked(True)
        word_wrap_action.triggered.connect(self.toggle_word_wrap)
        view_menu.addAction(word_wrap_action)

    def text_changed(self):
        self.is_modified = True
        self.update_title()

    def update_title(self):
        title = "NtPad 📝✨"
        if self.current_file:
            title = f"{self.current_file} - {title}"
        if self.is_modified:
            title = f"*{title}"
        self.setWindowTitle(title)

    def new_file(self):
        if self.check_save():
            self.text_edit.clear()
            self.current_file = None
            self.is_modified = False
            self.update_title()

    def open_file(self):
        if self.check_save():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open File", "", "Text Files (*.txt);;All Files (*)"
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        self.text_edit.setPlainText(file.read())
                    self.current_file = file_path
                    self.is_modified = False
                    self.update_title()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")

    def save_file(self):
        if self.current_file:
            return self.save_to_file(self.current_file)
        else:
            return self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            return self.save_to_file(file_path)
        return False

    def save_to_file(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.text_edit.toPlainText())
            self.current_file = file_path
            self.is_modified = False
            self.update_title()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{e}")
            return False

    def check_save(self):
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Save Changes?",
                "Do you want to save changes to this document?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                return self.save_file()
            elif reply == QMessageBox.Cancel:
                return False
        return True

    def closeEvent(self, event):
        if self.check_save():
            event.accept()
        else:
            event.ignore()

    def change_font(self):
        font, ok = QFontDialog.getFont(self.text_edit.font(), self)
        if ok:
            self.text_edit.setFont(font)

    def change_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_edit.setTextColor(color)

    def toggle_word_wrap(self, checked):
        if checked:
            self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.text_edit.setLineWrapMode(QTextEdit.NoWrap)

    def find_text(self):
        search_text, ok = QInputDialog.getText(self, "Find", "Enter text to find:")
        if ok and search_text:
            cursor = self.text_edit.textCursor()
            cursor.setPosition(0)
            self.text_edit.setTextCursor(cursor)
            
            if not self.text_edit.find(search_text):
                QMessageBox.information(self, "Find", "Text not found.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NtPad()
    window.show()
    sys.exit(app.exec())
