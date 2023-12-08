import argparse
import psutil
from hashlib import sha1

def stop_node_running_in_background(node_name: str):
    try:
        for process in psutil.process_iter(['pid', 'cmdline']):
            if f"{node_name}_{sha1(node_name.encode('utf-8')).hexdigest()}" in process.info['cmdline']:
                process.terminate()
                break
        else:
            print(f"No node running in the background found with name {node_name}")
    except Exception as e:
        print(f"Error terminating node {node_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stop node's participation in the blockchain")
    parser.add_argument("node_name")
    args = parser.parse_args()
    
    stop_node_running_in_background(args.node_name)
