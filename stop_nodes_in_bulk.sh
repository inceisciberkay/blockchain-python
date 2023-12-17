#!/bin/bash

for i in {1..10}; do
    node_name="node$i"
    echo "Stopping $node_name..."
    python3 stop_node.py $node_name
    sleep 0.1
done

echo "All nodes stopped."