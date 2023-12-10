import os
import toml

class Wallet():
    def __init__(self, node_name):
        self.node_name = node_name
        # get wallet configuration from the file

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

    def calculate_UTXO(self):
        pass

    def get_balance(self):
        return 1243124

    def get_address(self):
        return self.address
