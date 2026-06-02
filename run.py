#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Launch the vocabulary learning application
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main entry point"""
    print("=" * 50)
    print("CET 4/6 Vocabulary Tool")
    print("=" * 50)
    print()
    print("Starting application...")
    print()

    try:
        # Import and run the application
        from vocab_app import App
        app = App()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication exited")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nPlease check dependencies:")
        print("  pip install pystray Pillow")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
