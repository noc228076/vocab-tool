#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test the thread-safe auto-show mechanism
"""

import threading
import queue
import time

def test_queue_mechanism():
    """Test that the queue-based approach works correctly"""
    print("Testing queue-based auto-show mechanism...")

    # Create a queue
    q = queue.Queue()

    # Simulate the auto-show loop putting signals in the queue
    def auto_show_loop():
        for i in range(3):
            q.put(f"show_word_{i}")
            time.sleep(0.1)

    # Simulate the main thread checking the queue
    results = []
    def check_queue():
        try:
            while True:
                item = q.get_nowait()
                results.append(item)
        except queue.Empty:
            pass

    # Start the auto-show thread
    thread = threading.Thread(target=auto_show_loop, daemon=True)
    thread.start()

    # Wait for the thread to finish
    time.sleep(0.5)

    # Check the queue
    check_queue()

    print(f"Received {len(results)} signals: {results}")

    if len(results) == 3:
        print("Test passed!")
        return True
    else:
        print("Test failed!")
        return False

if __name__ == "__main__":
    test_queue_mechanism()
