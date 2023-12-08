import argparse
import time

def background_task(process_id: str):
    # do something
    time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a background task with a specific process ID.")
    parser.add_argument("process_id", help="The process ID for the background task.")
    args = parser.parse_args()
    
    background_task(args.process_id)
