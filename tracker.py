import threading
import sys
import signal
import socket
from src.definitions import TRACKER_IP, TRACKER_PORT, MAX_NUMBER_OF_NODES

class Tracker:
    def __init__(self):
        self.up_and_running_nodes = {}  # key: node_name, value: socket

    def update_neighbors(self):
        # Send the list of active nodes to the newly connected node
        for node_name, socket in self.up_and_running_nodes.items():
            active_nodes = [name for name, _ in self.up_and_running_nodes.items() if name != node_name]
            socket.send(str(active_nodes).encode('utf-8'))

    def handle_node_connection(self, node_socket):
        node_name, node_ip_addr = node_socket.recv(1024).decode('utf-8').split('_')
        self.up_and_running_nodes[node_name] = node_socket
        print(f"Node {node_name} connected from {node_ip_addr}")
        self.update_neighbors()

    def listen_nodes(self):
        tracker_addr = (TRACKER_IP, TRACKER_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tracker_socket:
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
