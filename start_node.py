import subprocess
import psutil
import argparse
from hashlib import sha1

def node_already_running(node_arg):
    for process in psutil.process_iter(['pid', 'cmdline']):
        if node_arg in process.info['cmdline']:
            return True


def start_node_in_background(node_name: str):
    try:
        node_arg = f"{node_name}_{sha1(node_name.encode('utf-8')).hexdigest()}" 
        if node_already_running(node_arg):
            print(f"{node_name} is already running")
            return

        command = f"python3 src/node.py {node_arg}"
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"Error starting node {node_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start node's to participate in the blockchain")
    parser.add_argument("node_name")
    args = parser.parse_args()
    
    start_node_in_background(args.node_name)
