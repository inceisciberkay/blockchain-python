from hashlib import sha256

class Block:
    def __init__(self, index, previous_hash, nonce, transactions):
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

    def hash(self):
        transactions_str = ""
        for transaction in self.transactions:
            print(transaction)
            transactions_str += transaction.to_str()

        concatenated_str = (str(self.index) 
                            + str(self.previous_hash) 
                            + str(self.nonce) 
                            + transactions_str)

        return sha256(concatenated_str.encode('utf-8')).hexdigest()


