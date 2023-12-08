import subprocess
import argparse
from hashlib import sha1

def start_node_in_background(node_name: str):
    try:
        command = f"python3 src/node.py {node_name}_{sha1(node_name.encode('utf-8')).hexdigest()}"
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"Error starting node {node_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start node's to participate in the blockchain")
    parser.add_argument("node_name")
    args = parser.parse_args()
    
    start_node_in_background(args.node_name)
