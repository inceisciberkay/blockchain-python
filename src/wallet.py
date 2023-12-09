class Wallet():
    def __init__(self, wallet: dict):
        self.private_key = wallet['private_key']
        self.public_key = wallet['public_key']
        self.address = wallet['address']

    def calculateUTXO(self):
        pass

    