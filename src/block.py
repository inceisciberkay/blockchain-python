from hashlib import sha256
from transaction import Transaction

class Block:
    def __init__(self, previous_hash, index, nonce, transactions):
        self.previous_hash = previous_hash
        self.index = index
        self.nonce = nonce
        self.transactions = transactions    # list of transactions

    def to_dict(self):
        # convert list of transactions to list of dictionaries
        transactions = []
        for transaction in self.transactions:
            transactions.append(transaction.to_dict())

        return {
            'hash': self.hash(),
            'previous_hash': self.previous_hash,
            'index': self.index,
            'nonce': self.nonce,
            'transactions': transactions
        }
    
    @classmethod
    def create_from_block_dict(cls, block_dict: dict):
        # create list of transactions from a list of dictionaries
        transactions = []
        for transaction_dict in block_dict['transactions']:
            transaction = Transaction.create_from_transaction_dict(transaction_dict)
            transactions.append(transaction)

        return Block(
            previous_hash=block_dict['previous_hash'],
            index=block_dict['index'],
            nonce=block_dict['nonce'],
            transactions=transactions
        )

    def hash(self):
        transactions_str = ""
        for transaction in self.transactions:
            transactions_str += transaction.to_str()

        concatenated_str = (str(self.index) 
                            + str(self.previous_hash) 
                            + str(self.nonce) 
                            + transactions_str)

        return sha256(concatenated_str.encode('utf-8')).hexdigest()


