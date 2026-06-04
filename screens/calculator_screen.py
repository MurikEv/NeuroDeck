from PyQt6.QtCore import Qt

class Calculator:
    def __init__(self, window):
        self.window = window

        self.expression = ""

        self.connect_buttons()
        self.update_display()

    def connect_buttons(self):
        self.window.btn0.clicked.connect(lambda: self.append_input("0"))
        self.window.btn1.clicked.connect(lambda: self.append_input("1"))
        self.window.btn2.clicked.connect(lambda: self.append_input("2"))
        self.window.btn3.clicked.connect(lambda: self.append_input("3"))
        self.window.btn4.clicked.connect(lambda: self.append_input("4"))
        self.window.btn5.clicked.connect(lambda: self.append_input("5"))
        self.window.btn6.clicked.connect(lambda: self.append_input("6"))
        self.window.btn7.clicked.connect(lambda: self.append_input("7"))
        self.window.btn8.clicked.connect(lambda: self.append_input("8"))
        self.window.btn9.clicked.connect(lambda: self.append_input("9"))
        self.window.btnDot.clicked.connect(lambda: self.append_input("."))
        self.window.btnPlus.clicked.connect(lambda: self.append_input("+"))
        self.window.btnMinus.clicked.connect(lambda: self.append_input("-"))
        self.window.btnDivide.clicked.connect(lambda: self.append_input("/"))
        self.window.btnMultiply.clicked.connect(lambda: self.append_input("*"))
        # self.window.btnPercent.clicked.connect(lambda: self.append_input("%"))
        self.window.btnRParenthesis.clicked.connect(lambda: self.append_input(")"))
        self.window.btnLParenthesis.clicked.connect(lambda: self.append_input("("))
        self.window.btnBackspace.clicked.connect(self.backspace)
        self.window.btnClear.clicked.connect(self.clear)
        self.window.btnEquals.clicked.connect(self.calculate)

    def append_input(self, value: str):
        self.expression += value
        self.update_display()

    def backspace(self):
        self.expression = self.expression[:-1]
        self.update_display()

    def clear(self):
        self.expression = ""
        self.update_display()

    def calculate(self):
        try:
            self.expression = str(eval(self.expression))
            self.update_display()
        except:
            self.expression = "Error"
            self.update_display()
            self.expression = ""

    def update_display(self):
        if self.expression:
            self.window.display.setText(self.expression)
        else:
            self.window.display.setText("0")
        
    def handle_key(self, event):
        pass
