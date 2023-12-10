class Transaction:
    def __init__(self, sender_addr, receiver_addr, amount):
        self.sender_addr = sender_addr
        self.receiver_addr = receiver_addr
        self.amount = amount

    def to_dict(self):
        return {
            'sender': self.sender_addr,
            'receiver': self.receiver_addr,
            'amount': self.amount
        }
    
    def to_str(self):
        return f"{self.sender_addr}{self.receiver_addr}{self.amount}"