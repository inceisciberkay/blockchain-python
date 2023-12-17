import threading
import sys
import signal
import socket
import pickle
import random
from src.definitions import TRACKER_IP, TRACKER_PORT, MAX_NUMBER_OF_NODES

class Tracker:
    def __init__(self):
        self.up_and_running_nodes = {}  # key: node_name, value: socket

    # TODO: below is terrible
    def update_neighbors(self):
        for node_name, socket in self.up_and_running_nodes.items():
            neighbors = [name for name, _ in self.up_and_running_nodes.items() if name != node_name and random.randint(0,1) == 1]
            if len(neighbors) == 0: # give at least one neighbor
                neighbors = [name for name, _ in self.up_and_running_nodes.items() if name != node_name]
            socket.send(str(neighbors).encode('utf-8'))

    def handle_node_connection(self, node_socket):
        msg = pickle.loads(node_socket.recv(1024))
        if msg['type'] == 'seed':
            # choose one node from up and running nodes
            key_list = list(self.up_and_running_nodes.keys())
            if len(key_list) == 0:
                seed = 'None'
            else:
                seed = random.choice(key_list)
            node_socket.send(seed.encode('utf-8'))
            node_socket.close()
            return

        # else, msg type is update
        node_name = msg['node_name']
        self.up_and_running_nodes[node_name] = node_socket
        print(f"Node {node_name} is connected")
        self.update_neighbors()
    # TODO: remove from active nodes if inactive for some time

    def listen_nodes(self):
        tracker_addr = (TRACKER_IP, TRACKER_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tracker_socket:
            tracker_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tracker_socket.bind(tracker_addr)
            tracker_socket.listen(MAX_NUMBER_OF_NODES)

            while True:
                node_socket, _ = tracker_socket.accept()
                self.handle_node_connection(node_socket)

    def run(self):
        node_listener = threading.Thread(target=self.listen_nodes)
        node_listener.daemon = True
        node_listener.start()
        node_listener.join()

def signal_handler(signum, frame):
    # do something
    sys.exit(0)

def main():
    # register signal
    signal.signal(signal.SIGTERM, signal_handler)

    # create tracker node
    tracker = Tracker()
    tracker.run()

if __name__ == "__main__":
    main()
