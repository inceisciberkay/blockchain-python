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
from definitions import TRACKER_IP, TRACKER_PORT, WALLET_PORT, NODE_RECV_PORT, \
    NODE_SEND_TRANSACTION_PORT, NODE_PROPAGATE_BLOCK_PORT, NODE_SEND_MINED_BLOCK_PORT, \
    SEED_PORT, MAX_NUMBER_OF_NODES 

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
        amount=10.0
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
        ledger_config = toml.load(self.node_ledger_config_file_path)
        self.ledger = Blockchain.create_from_list_of_block_dicts(ledger_config['ledger'])

        # read address from wallet config which will be used for mining transactions
        self.address = toml.load(self.node_wallet_config_file_path)['wallet']['address']
        
        self.alternative_top = None
        self.transaction_pool = []

        self.synchronize_ledger()

    def synchronize_ledger(self):
        tracker_addr = (TRACKER_IP, TRACKER_PORT)  # Tracker's address
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tracker_socket:
            tracker_socket.connect(tracker_addr)
            # tell tracker that i am up and running, and need some seed nodes to synchronize
            msg = {
                'type': 'seed'
            }
            tracker_socket.send(pickle.dumps(msg))   
            seeder = tracker_socket.recv(1024).decode('utf-8')
        
        if seeder == 'None':
            print('No currently running active node')
            return

        print(f'My seeder: {seeder}')

        # establish connection to seeder node
        seeder_addr = (f"192.168.100.{int(seeder[4:])}", SEED_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as seeder_socket:
            seeder_socket.connect(seeder_addr)
            msg = {
                'start_from': self.ledger.get_length()
            }
            seeder_socket.send(pickle.dumps(msg))
            while True:
                # Receive blocks one by one from a currently running node that has full copy of blockchain
                msg = pickle.loads(seeder_socket.recv(1024))
                if msg['type'] == 'finish':
                    break
                # TODO: validate the block
                block = Block.create_from_block_dict(msg['block'])
                self.ledger.append_block(block)

                # Write the updated ledger to the config file for demonstration
                with open(self.node_ledger_config_file_path, 'w+') as f:
                    toml.dump({
                        'ledger': self.ledger.to_list_of_dicts()
                    }, f)

            # TODO: handle disconnection case

    
    def listen_seed(self):
        seed_addr = (self.ip_address, SEED_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as seed_socket:
            seed_socket.bind(seed_addr)
            seed_socket.listen(MAX_NUMBER_OF_NODES)

            while True:
                s, _ = seed_socket.accept()
                msg = pickle.loads(s.recv(1024))
                start_from = int(msg['start_from'])
                for block in self.ledger.blocks[start_from:]:
                    s.send(pickle.dumps({
                        'type': 'block',
                        'block': block.to_dict()
                    }))
                    time.sleep(0.01)
                s.send(pickle.dumps({
                    'type': 'finish',
                }))
    
    def mine(self):
        while True:
            self.lost_round = False
            # create new block (including special mine transaction)
            mine_transaction = Transaction(
                sender_addr="mine",
                receiver_addr=self.address,
                amount=10.0
            )
            included_transactions = [mine_transaction, *(self.transaction_pool)]
            new_block = Block(
                previous_hash=self.ledger.get_top().hash(),
                index=self.ledger.get_top().index + 1,
                nonce=0,
                transactions = included_transactions
            )

            while not self.lost_round and not self.ledger.is_valid_proof(new_block):
                new_block.nonce += 1

            if not self.lost_round:
                # won the round, append the block and multicast to neighbors
                print(f'Mined the block: {new_block.to_dict()}')
                self.ledger.append_block(new_block)
                for neighbor_name in self.neighbors:
                    send_addr = (self.ip_address, NODE_SEND_MINED_BLOCK_PORT)
                    neighbor_addr = (f"192.168.100.{int(neighbor_name[4:])}", NODE_RECV_PORT)
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock:
                        send_sock.bind(send_addr)
                        # Construct block message
                        message = {'type': 'block', 'data': new_block.to_dict(), 'followed_route': [self.name]}
                        send_sock.sendto(pickle.dumps(message), neighbor_addr)
            
                # Write the updated ledger to the config file for later reuse
                with open(self.node_ledger_config_file_path, 'w+') as f:
                    toml.dump({
                        'ledger': self.ledger.to_list_of_dicts()
                    }, f)

                # remove included transactions from the transaction pool
                self.update_transaction_pool(included_transactions)
    
    def run(self):
        miner = threading.Thread(target=self.mine)
        seed_listener = threading.Thread(target=self.listen_seed)
        wallet_listener= threading.Thread(target=self.listen_wallet)
        tracker_listener = threading.Thread(target=self.listen_tracker)
        neighbors_listener = threading.Thread(target=self.listen_neighbors)

        self.workers = (miner, seed_listener, wallet_listener, tracker_listener, neighbors_listener)

        # start threads
        for worker in self.workers:
            worker.daemon = True
            worker.start()

        for worker in self.workers:
            worker.join()

    def update_transaction_pool(self, included_transactions):
        included_transaction_hashes = [transaction.hash() for transaction in included_transactions]
        new_transaction_pool = []
        for transaction in self.transaction_pool:
            if transaction.hash() not in included_transaction_hashes:
                new_transaction_pool.append(transaction)

        self.transaction_pool = new_transaction_pool

    def handle_incoming_transaction(self, sender_name, transaction_dict, followed_route):
        print(f'{self.name} received transaction from {sender_name}, route {followed_route}: {transaction_dict}')

        # check the validity of transaction
        sender_addr = transaction_dict['sender_addr']
        amount = transaction_dict['amount']
        if amount > self.calculate_UTXO(sender_addr):
            print(f'Invalid transaction (balance is not sufficient): {transaction_dict}')
            return

        # construct transaction object
        new_transaction = Transaction.create_from_transaction_dict(transaction_dict)

        # add transaction to the transaction pool
        # check if transaction already exists in the pool
        for transaction in self.transaction_pool:
            if transaction.hash() == new_transaction.hash():
                return  # if transaction already exists in the pool, do not forward to neighbors

        self.transaction_pool.append(new_transaction)

        # propagate it through the network (by passing to neighbors)
        for neighbor_name in self.neighbors:
            if neighbor_name in followed_route: continue   # do not forward message to if already received
            send_addr = (self.ip_address, NODE_SEND_TRANSACTION_PORT)
            neighbor_addr = (f"192.168.100.{int(neighbor_name[4:])}", NODE_RECV_PORT)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock:
                send_sock.bind(send_addr)
                # construct transaction message
                message = {
                    'type': 'transaction',
                    'data': new_transaction.to_dict(),
                    'followed_route': [*followed_route, self.name]
                }
                send_sock.sendto(pickle.dumps(message), neighbor_addr)
    
    def handle_incoming_block(self, sender_name, block_dict, followed_route):
        print(f'{self.name} received block from {sender_name}, route: {followed_route}: {block_dict}')

        # if block is valid construct block object
        new_block = Block.create_from_block_dict(block_dict)

        if self.alternative_top != None:
            if new_block.hash() == self.alternative_top.hash():
                return  # already handled
            elif new_block.previous_hash == self.alternative_top.hash():    # new block is on top of the fork
                # restructure ledger
                self.ledger.remove_top_block()
                self.ledger.append_block(self.alternative_top)
                self.update_transaction_pool(self.alternative_top.transactions)
                self.alternative_top = None
            
        if new_block.hash() == self.ledger.get_top().hash():
            return  # already handled
        elif new_block.previous_hash == self.ledger.get_top().hash():
            if self.alternative_top != None:
                print(f'Fork is discarded {self.alternative_top.to_dict()}')
                self.alternative_top = None     # fork loses battle

            # add block to the local ledger
            # for now no need to check if the block is already received since in that case received block would be on top
            self.ledger.append_block(new_block)

            # refine transaction pool based on incoming block: remove included transactions from the transaction pool
            self.update_transaction_pool(new_block.transactions)

            # if block is valid, signal to stop mining
            self.lost_round = True  # python assignments are atomic
        elif new_block.previous_hash == self.ledger.get_second_top().hash():
            print(f'Fork block is received: {new_block.to_dict()}')
            self.alternative_top = new_block
        else:
            return  # prevent attack

        # propagate block through network by passing to neighbors
        for neighbor_name in self.neighbors:
            if neighbor_name in followed_route: continue   # do not forward message if already received
            send_addr = (self.ip_address, NODE_PROPAGATE_BLOCK_PORT)
            neighbor_addr = (f"192.168.100.{int(neighbor_name[4:])}", NODE_RECV_PORT)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock:
                send_sock.bind(send_addr)
                # construct block message
                message = {
                    'type': 'block',
                    'data': new_block.to_dict(),
                    'followed_route': [*followed_route, self.name]
                }
                send_sock.sendto(pickle.dumps(message), neighbor_addr)

        # write new ledger to config file for later reuse
        with open(self.node_ledger_config_file_path, 'w+') as f:
            toml.dump({
                'ledger': self.ledger.to_list_of_dicts()
            }, f)
        
    def calculate_UTXO(self, address):
        balance = 0.0
        # iterate through entire blockchain
        for block in self.ledger.blocks:
            for transaction in block.transactions:
                if transaction.receiver_addr == address:
                    balance += transaction.amount
                elif transaction.sender_addr == address:
                    balance -= transaction.amount
        # iterate through transaction pool
        for transaction in self.transaction_pool:
            if transaction.receiver_addr == address:
                balance += transaction.amount
            elif transaction.sender_addr == address:
                balance -= transaction.amount

        return balance

    def listen_wallet(self):
        wallet_addr = (self.ip_address, WALLET_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wallet_socket:
            wallet_socket.bind(wallet_addr)
            wallet_socket.listen(1) # one node have only one wallet

            while True:
                s, _ = wallet_socket.accept()
                data = s.recv(1024)
                message = pickle.loads(data)
                if message['type'] == 'balance_request':
                    balance = self.calculate_UTXO(self.address)
                    s.send(pickle.dumps(balance))
                else:
                    self.handle_incoming_transaction(
                        self.name,
                        {
                            'sender_addr': message['sender_addr'],
                            'receiver_addr': message['receiver_addr'],
                            'amount': message['amount']
                        },
                        [self.name]
                    )

    def listen_neighbors(self):
        # neighbors can send transactions or blocks
        # communication between neighbors happens connectionless (UDP) 
        # channels are unidirectional
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
                        self.handle_incoming_transaction(sender_name, message['data'], message['followed_route'])
                    elif message['type'] == 'block':
                        # assume the message format is correct
                        self.handle_incoming_block(sender_name, message['data'], message['followed_route'])
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
            # tell tracker that i am ready to get neighbor updates
            msg = {
                'type': 'update',
                'node_name': self.name
            }
            tracker_socket.send(pickle.dumps(msg))   

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
