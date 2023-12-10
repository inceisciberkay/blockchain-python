import argparse
import time
import sys
import signal
import os
import toml
from key_generator import *
from block import Block
from transaction import Transaction
from blockchain import Blockchain

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
        receiver_addr="1MMietQo1TdZ5pwWTE16WghZpn5uuKNGdV", # satoshi's (node1) account
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

        # check if the node already exists
        node_config_dir_path = os.path.join('local_configs', name)
        self.node_config_file_path = os.path.join(node_config_dir_path, 'config.toml')
        if not os.path.exists(node_config_dir_path):
            os.makedirs(node_config_dir_path)
            # create configuration: wallet (private-public key pair), ledger, etc.
            wallet_dict = create_wallet()
            ledger_dict = create_initial_ledger()

            with open(self.node_config_file_path, 'w+') as f:
                toml.dump({
                    'wallet': wallet_dict,
                    'block': ledger_dict,   # it is actually ledger, named as 'block' for readability of config file
                }, f)

        # read configuration
        config = toml.load(self.node_config_file_path)
        self.wallet = config['wallet']
        self.ledger = config['ledger']
    
    def run(self):
        while True: 
            with open(self.node_config_file_path, 'a'):
                time.sleep(1)

def signal_handler(signum, frame):
    # do something
    sys.exit(0)

def background_task(process_id: str):
    # register signal
    signal.signal(signal.SIGTERM, signal_handler)

    # create node
    node_name = process_id.split('_')[0]
    node = Node(node_name)
    node.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a background task with a specific process ID.")
    parser.add_argument("process_id", help="The process ID for the background task.")
    args = parser.parse_args()
    
    background_task(args.process_id)
