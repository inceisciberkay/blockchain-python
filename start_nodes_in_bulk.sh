#!/bin/bash

for i in {1..10}; do
    node_name="node$i"
    echo "Starting $node_name..."
    python3 start_node.py $node_name
    sleep 0.3
done

echo "All nodes started."