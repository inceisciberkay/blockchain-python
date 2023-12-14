import argparse
import time
import sys
import signal
import os
import toml
import socket
import threading
import time
import pickle
from key_generator import *
from block import Block
from transaction import Transaction
from blockchain import Blockchain
from definitions import TRACKER_IP, TRACKER_PORT, WALLET_PORT, NODE_RECV_PORT, NODE_SEND_PORT

def create_wallet():
    # Generate key pair
    private_key, public_key = generate_key_pair()

    # Convert public key to address
    address = public_key_to_address(public_key)

    return {
        'private_key': private_key.to_string().hex(),
        'public_key': public_key.to_string().hex(),
        'address': address
    }

def create_initial_ledger():
    generation_transaction = Transaction(
        sender_addr="mine",
        receiver_addr="1DbmANxnphGoJ1H57EaYXQTb1yH4MEgH75", # satoshi's (node1) account
        amount=10
    )
    genesis = Block(
        index=0,
        previous_hash="000000000000000000000000000000000000000000000000000000000000000000000000", # base16
        nonce=0,
        transactions=[generation_transaction]
    )
    ledger = Blockchain(
        blocks=[genesis]
    )
    return ledger.to_list_of_dicts()

class Node():
    def __init__(self, name):
        self.name = name
        self.ip_address = f"192.168.100.{int(name[4:])}"  # Assuming the node name is in the format "nodeX"
        self.neighbors = []

        # check if the node already exists
        node_config_dir_path = os.path.join('local_configs', name)
        self.node_wallet_config_file_path = os.path.join(node_config_dir_path, 'wallet.toml')
        self.node_ledger_config_file_path = os.path.join(node_config_dir_path, 'ledger.toml')
        if not os.path.exists(node_config_dir_path):
            os.makedirs(node_config_dir_path)

            # create configuration: wallet (private-public key pair, address) and ledger
            wallet_dict = create_wallet()
            ledger_dict = create_initial_ledger()

            with open(self.node_wallet_config_file_path, 'w+') as f:
                toml.dump({
                    'wallet': wallet_dict
                }, f)

            with open(self.node_ledger_config_file_path, 'w+') as f:
                toml.dump({
                    'ledger': ledger_dict
                }, f)

        # read ledger configuration into object
        config = toml.load(self.node_ledger_config_file_path)
        self.ledger = Blockchain.create_from_list_of_block_dicts(config['ledger'])
        
        self.transaction_pool = []
    
    def mine(self):
        # clear transaction pool
        pass
    
    def run(self):
        wallet_listener= threading.Thread(target=self.listen_wallet)
        tracker_listener = threading.Thread(target=self.listen_tracker)
        neighbors_listener = threading.Thread(target=self.listen_neighbors)

        self.workers = (wallet_listener, tracker_listener, neighbors_listener)

        # start threads
        for worker in self.workers:
            worker.daemon = True
            worker.start()

        for worker in self.workers:
            worker.join()

    def handle_incoming_transaction(self, sender_name, transaction_dict):
        sender_addr = transaction_dict['sender_addr']
        receiver_addr = transaction_dict['receiver_addr']
        amount = transaction_dict['amount']
        print(f'{self.name} received transaction from {sender_name}: {sender_addr} {receiver_addr}, {amount}')

        # check the validity of transaction
        # todo

        # construct transaction object
        new_transaction = Transaction(sender_addr, receiver_addr, amount)

        # add transaction to the transaction pool
        exists = False
        # check if transaction already exists in the pool
        for transaction in self.transaction_pool:
            if transaction.get_hash() == new_transaction.get_hash():
                exists = True
                return  # if transaction already exists in the pool, do not forward to neighbors
        if not exists:
            self.transaction_pool.append(new_transaction)

        # propagate it through the network (by passing to neighbors)
        for neighbor_name in self.neighbors:
            if neighbor_name == sender_name: continue   # do not forward message to sender
            send_addr = (self.ip_address, NODE_SEND_PORT)
            neighbor_addr = (f"192.168.100.{int(neighbor_name[4:])}", NODE_RECV_PORT)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock:
                send_sock.bind(send_addr)
                # construct transaction message
                message = {'type': 'transaction', 'data': new_transaction.to_dict()}
                send_sock.sendto(pickle.dumps(message), neighbor_addr)

    
    def handle_incoming_block(self, sender_name, block_dict):
        pass

    def listen_wallet(self):
        wallet_addr = (self.ip_address, WALLET_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wallet_socket:
            wallet_socket.bind(wallet_addr)
            wallet_socket.listen(1) # one node have only one wallet

            while True:
                s, _ = wallet_socket.accept()
                sender_addr, receiver_addr, amount = s.recv(1024).decode('utf-8').split('_')
                self.handle_incoming_transaction(
                    self.name,
                    {
                    'sender_addr': sender_addr, 
                    'receiver_addr': receiver_addr, 
                    'amount': float(amount)
                    })

    def listen_neighbors(self):
        # neighbors can send transactions or blocks
        # communication between neighbors happens connectionless (UDP) 
        recv_addr = (self.ip_address, NODE_RECV_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as recv_socket:
            recv_socket.bind(recv_addr)
            recv_socket.setblocking(False)
            while True: 
                try:
                    data, sender_addr = recv_socket.recvfrom(1024)
                    sender_ip, _ = sender_addr
                    sender_name = f'node{sender_ip.split(".")[3]}'
                    message = pickle.loads(data)
                    if message['type'] == 'transaction':
                        # assume the message format is correct
                        self.handle_incoming_transaction(sender_name, message['data'])
                    elif message['type'] == 'block':
                        # assume the message format is correct
                        self.handle_incoming_block(sender_name, message['data'])
                    else:
                        print(f'Unsupported message type: {message["type"]}')

                except socket.error as e:
                    # no message is received from the socket
                    pass

                time.sleep(0.1)  # Add a short delay to avoid busy-waiting

    def listen_tracker(self):
        tracker_addr = (TRACKER_IP, TRACKER_PORT)  # Tracker's address
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tracker_socket:
            tracker_socket.connect(tracker_addr)
            # tell tracker that i am up and running
            tracker_socket.send(f"{self.name}_{self.ip_address}".encode('utf-8'))   

            while True:
                # Receive the list of neighbors from the tracker
                neighbors = tracker_socket.recv(1024).decode('utf-8')
                self.neighbors = eval(neighbors)  # Convert the string to a list

                print(f"Neighbors are updated: {self.neighbors}")


def signal_handler(signum, frame):
    # do something
    sys.exit(0)

def background_task(process_id: str):
    # register signal
    signal.signal(signal.SIGTERM, signal_handler)

    # create node
    node_name = process_id.split('_')[0]
    node = Node(node_name)

    # run node
    node.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a background task with a specific process ID.")
    parser.add_argument("process_id", help="The process ID for the background task.")
    args = parser.parse_args()
    
    background_task(args.process_id)
