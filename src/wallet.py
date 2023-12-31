import os
import toml
import socket
import pickle
import time
from src.definitions import WALLET_PORT

class Wallet():
    def __init__(self, node_name):
        self.node_name = node_name
        self.ip_address = f"192.168.100.{int(node_name[4:])}"  # Assuming the node name is in the format "nodeX"
        # check if the node already exists
        node_config_dir_path = os.path.join('local_configs', node_name)
        node_wallet_config_file_path = os.path.join(node_config_dir_path, 'wallet.toml')
        if os.path.exists(node_config_dir_path):
            # read configuration
            wallet_config = toml.load(node_wallet_config_file_path)['wallet']
            self.private_key = wallet_config['private_key']
            self.public_key = wallet_config['public_key']
            self.address = wallet_config['address']
        else:
            raise Exception

    def get_balance(self):
        wallet_addr = (self.ip_address, WALLET_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wallet_socket:
            wallet_socket.connect(wallet_addr)
            # send balance request to node
            msg = {
                'type': 'balance_request',
            }
            wallet_socket.send(pickle.dumps(msg))
            data = wallet_socket.recv(1024)
            balance = pickle.loads(data)
        return balance

    def get_address(self):
        return self.address
    
    def create_transaction(self, receiver_addr, amount):
        wallet_addr = (self.ip_address, WALLET_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wallet_socket:
            wallet_socket.connect(wallet_addr)
            # send transaction to the node holding the wallet
            # transaction will be propagated through its node
            msg = {
                'type': 'create_transaction',
                'sender_addr': self.address,
                'receiver_addr': receiver_addr,
                'amount': amount
            }
            wallet_socket.send(pickle.dumps(msg))
        
        time.sleep(0.01)
        return self.get_balance()
