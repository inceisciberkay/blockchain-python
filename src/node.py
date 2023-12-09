import argparse
import time
import sys
import signal
import os
import toml
from key_generator import *

def create_wallet():
    # Generate key pair
    private_key, public_key = generate_key_pair()

    # Convert public key to address
    address = public_key_to_address(public_key)

    return {
        'wallet': {
            'private_key': private_key.to_string().hex(),
            'public_key': public_key.to_string().hex(),
            'address': address
        }
    }

def create_genesis():
    pass
    

class Node():
    def __init__(self, name):
        self.name = name
        # check if the node already exists
        node_config_dir_path = os.path.join('local_configs', name)
        node_config_file_path = os.path.join(node_config_dir_path, 'config.toml')
        if not os.path.exists(node_config_dir_path):
            os.makedirs(node_config_dir_path)
            # create configuration: wallet (private-public key pair), ledger, etc.
            wallet_dict = create_wallet()
            with open(node_config_file_path, 'w+') as f:
                toml.dump(wallet_dict, f)


        # read configuration
        config = toml.load(node_config_file_path)
        self.wallet = config['wallet']

def signal_handler(signum, frame):
    # do something
    sys.exit(0)

def background_task(process_id: str):
    # register signal
    signal.signal(signal.SIGTERM, signal_handler)

    # create node
    node_name = process_id.split('_')[0]
    node = Node(node_name)

    while True: 
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a background task with a specific process ID.")
    parser.add_argument("process_id", help="The process ID for the background task.")
    args = parser.parse_args()
    
    background_task(args.process_id)
