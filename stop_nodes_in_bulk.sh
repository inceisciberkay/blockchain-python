#!/bin/bash

for i in {1..42}; do
    node_name="node$i"
    echo "Stopping $node_name..."
    python3 stop_node.py $node_name
done

echo "All nodes stopped."