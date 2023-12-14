#!/bin/python3

import sys
import argparse
from PySide6.QtWidgets import QApplication, QMainWindow, QLineEdit, QPushButton, QLabel, QFormLayout, QWidget
from PySide6.QtGui import QFont
from src.wallet import Wallet


class WalletWindow(QMainWindow):
    def __init__(self, node_name):
        super(WalletWindow, self).__init__()
        self.setMinimumSize(500, 200)
        self.setWindowTitle(f"Wallet Client of {node_name}")

        try:
            self.wallet = Wallet(node_name)
        except Exception:
            print("Node does not exist")    # no local config file can be found for node
            exit(1)

        self.recipient_address = None
        self.amount = None

        self.init_UI_elements()
        self.init_design()
    
    def init_UI_elements(self):
        # wallet address field
        self.walletAddressLabel = QLabel("Wallet Address:")
        self.walletAddressTextField = QLabel(self.wallet.get_address())

        # balance field
        self.balanceLabel = QLabel("Balance:")
        self.balanceTextField = QLabel(str(self.wallet.get_balance()))

        # recipient address field
        self.recipientAddressLabel = QLabel("Recipient Address:")
        self.recipientAddressInput = QLineEdit()
        self.recipientAddressInput.textChanged.connect(self.update_recipient_address)

        # amount field
        self.amountLabel = QLabel("Amount:")
        self.amountInput = QLineEdit()
        self.amountInput.textChanged.connect(self.update_amount)

        # payment button
        self.paymentButton = QPushButton("Send", self)
        self.paymentButton.clicked.connect(self.handle_click_payment)

    def init_design(self):
        central_widget = QWidget(self)
        layout = QFormLayout()
        central_widget.setLayout(layout)

        layout.addRow(self.walletAddressLabel, self.walletAddressTextField)
        layout.addRow(self.balanceLabel, self.balanceTextField)
        layout.addRow(QLabel(""), QLabel(""))
        layout.addRow(self.recipientAddressLabel, self.recipientAddressInput)
        layout.addRow(self.amountLabel, self.amountInput)
        layout.addWidget(self.paymentButton)
        self.setCentralWidget(central_widget)

        font = QFont()
        font.setBold(True)
        self.balanceTextField.setFont(font)
        self.paymentButton.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px 20px; font-size: 16px; border: none; border-radius: 5px;"
        )
        
    def update_recipient_address(self):
        self.recipient_address = self.recipientAddressInput.text()

    def update_amount(self):
        self.amount = self.amountInput.text()

    def handle_click_payment(self):
        try:
            assert(self.recipient_address is not None)
            assert(self.amount is not None)
            amount = float(self.amount)
            self.wallet.create_transaction(self.recipient_address, amount)
            self.reset_fields()

        except AssertionError:
            print('Recipient Address and Amount must be specified')
        except ValueError:
            print('Amount should be a floating point number')

    def reset_fields(self):
        self.recipientAddressInput.clear()
        self.amountInput.clear()
        self.recipient_address = None
        self.amount = None


def window(node_name: str):
    app = QApplication(sys.argv)
    win = WalletWindow(node_name)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Which node's wallet you want to open")
    parser.add_argument("node_name")
    args = parser.parse_args()
    
    window(args.node_name)
