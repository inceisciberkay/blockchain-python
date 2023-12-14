from hashlib import sha256

class Transaction:
    def __init__(self, sender_addr, receiver_addr, amount):
        self.sender_addr = sender_addr
        self.receiver_addr = receiver_addr
        self.amount = amount

    def to_dict(self):
        return {
            'sender_addr': self.sender_addr,
            'receiver_addr': self.receiver_addr,
            'amount': self.amount
        }
    
    @classmethod
    def create_from_transaction_dict(cls, transaction_dict: dict):
        return Transaction(
            sender_addr=transaction_dict['sender_addr'],
            receiver_addr=transaction_dict['receiver_addr'],
            amount=transaction_dict['amount']
        )
    
    def to_str(self):
        return f"{self.sender_addr}{self.receiver_addr}{self.amount}"
    
    def get_hash(self):
        # todo: include timestamp field for uniqueness of transactions
        return sha256(self.to_str().encode('utf-8')).hexdigest()