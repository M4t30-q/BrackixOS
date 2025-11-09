import sys
import math
import ast
import operator
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QGridLayout, QHBoxLayout
)
from PySide6.QtCore import Qt


class EvalExpr(ast.NodeVisitor):
    ENABLED_FUNCS = {
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'log': lambda x: math.log10(x), 'ln': math.log,
        'sqrt': math.sqrt, 'abs': abs, 'exp': math.exp,
        'factorial': math.factorial, 'asin': math.asin,
        'acos': math.acos, 'atan': math.atan, 'sinh': math.sinh,
        'cosh': math.cosh, 'tanh': math.tanh,
    }
    ENABLED_CONSTS = {'pi': math.pi, 'e': math.e}
    ENABLED_OPERATORS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
    }

    def __init__(self, use_degrees=False):
        self.use_degrees = use_degrees

    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise ValueError("Unsupported constant")
        elif isinstance(node, ast.BinOp):
            op_func = self.ENABLED_OPERATORS.get(type(node.op))
            if op_func is None:
                raise ValueError("Unsupported operator")
            return op_func(self.visit(node.left), self.visit(node.right))
        elif isinstance(node, ast.UnaryOp):
            op_func = self.ENABLED_OPERATORS.get(type(node.op))
            if op_func is None:
                raise ValueError("Unsupported unary operator")
            return op_func(self.visit(node.operand))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                func = self.ENABLED_FUNCS.get(func_name)
                if func is None:
                    raise ValueError(f"Unsupported function '{func_name}'")
                args = [self.visit(arg) for arg in node.args]
                # Convert degrees to radians if needed for trig functions
                if func_name in ('sin', 'cos', 'tan') and self.use_degrees:
                    args = [math.radians(arg) for arg in args]
                if func_name in ('asin', 'acos', 'atan') and self.use_degrees:
                    res = func(*args)
                    return math.degrees(res)
                return func(*args)
            else:
                raise ValueError("Invalid function call")
        elif isinstance(node, ast.Name):
            if node.id in self.ENABLED_CONSTS:
                return self.ENABLED_CONSTS[node.id]
            else:
                raise ValueError(f"Unknown identifier: {node.id}")
        else:
            raise ValueError("Unsupported expression")


class Calc(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calc 🧮✨ - Scientific Calculator")
        self.setGeometry(400, 200, 480, 660)
        self.use_degrees = True
        self.create_ui()
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d30;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #f0f0f0;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-size: 26px;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #444;
            }
            QPushButton {
                background-color: #3a3a3e;
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
                border: none;
                transition: background-color 0.3s;
            }
            QPushButton:hover {
                background-color: #505055;
                cursor: pointer;
            }
            QPushButton:pressed {
                background-color: #2e2e2e;
            }
            QPushButton#modeBtn {
                background-color: #F96060;
                font-weight: bold;
            }
        """)

    def create_ui(self):
        layout = QVBoxLayout()

        self.display = QLineEdit()
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        layout.addWidget(self.display)

        mode_layout = QHBoxLayout()
        self.mode_btn = QPushButton("Degrees")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(True)
        self.mode_btn.setObjectName("modeBtn")
        self.mode_btn.clicked.connect(self.toggle_mode)
        mode_layout.addWidget(self.mode_btn)
        layout.addLayout(mode_layout)

        grid = QGridLayout()

        buttons = [
            ['7', '8', '9', '/', 'sin', 'asin', 'pi'],
            ['4', '5', '6', '*', 'cos', 'acos', 'e'],
            ['1', '2', '3', '-', 'tan', 'atan', '√'],
            ['0', '.', '(', ')', '^', 'log', 'ln'],
            ['C', 'DEL', 'abs', 'exp', 'mod', 'fact', '='],
        ]

        for r, row in enumerate(buttons):
            for c, text in enumerate(row):
                btn = QPushButton(text)
                btn.setFixedSize(70, 60)
                btn.clicked.connect(lambda _, t=text: self.on_click(t))
                grid.addWidget(btn, r, c)

        layout.addLayout(grid)
        self.setLayout(layout)

    def toggle_mode(self):
        self.use_degrees = self.mode_btn.isChecked()
        self.mode_btn.setText("Degrees" if self.use_degrees else "Radians")

    def insert_text(self, text):
        self.display.setText(self.display.text() + text)

    def on_click(self, text):
        current = self.display.text()
        if text == 'C':
            self.display.clear()
        elif text == 'DEL':
            self.display.setText(current[:-1])
        elif text == '=':
            try:
                expr = self.preprocess_expression(current)
                tree = ast.parse(expr, mode='eval')
                evaluator = EvalExpr(use_degrees=self.use_degrees)
                result = evaluator.visit(tree)
                self.display.setText(str(result))
            except Exception:
                self.display.setText("Error")
        else:
            mapping = {
                '√': 'sqrt(',
                '^': '**',
                'ln': 'ln(',
                'log': 'log(',
                'sin': 'sin(',
                'cos': 'cos(',
                'tan': 'tan(',
                'asin': 'asin(',
                'acos': 'acos(',
                'atan': 'atan(',
                'abs': 'abs(',
                'exp': 'exp(',
                'mod': '%',
                'fact': 'factorial(',
                'pi': 'pi',
                'e': 'e',
            }
            to_insert = mapping.get(text, text)
            self.insert_text(to_insert)

    def preprocess_expression(self, expr):
        if expr.count('(') != expr.count(')'):
            raise ValueError("Unbalanced parentheses")
        return expr


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Calc()
    win.show()
    sys.exit(app.exec())
