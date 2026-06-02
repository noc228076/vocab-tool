#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for the vocabulary learning application
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import pystray
        print("  [OK] pystray")
    except ImportError:
        print("  [FAIL] pystray - not installed")
        return False

    try:
        from PIL import Image
        print("  [OK] Pillow")
    except ImportError:
        print("  [FAIL] Pillow - not installed")
        return False

    try:
        import tkinter
        print("  [OK] tkinter")
    except ImportError:
        print("  [FAIL] tkinter - not installed")
        return False

    return True

def test_word_loading():
    """Test if words can be loaded from JSON"""
    print("\nTesting word loading...")
    try:
        import json
        words_file = Path(__file__).parent.parent / "data" / "words.json"

        if not words_file.exists():
            print(f"  [FAIL] words.json not found")
            return False

        with open(words_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cet4_count = len(data.get('cet4', []))
        cet6_count = len(data.get('cet6', []))

        print(f"  [OK] CET-4 words: {cet4_count}")
        print(f"  [OK] CET-6 words: {cet6_count}")
        print(f"  [OK] Total words: {cet4_count + cet6_count}")

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def test_database():
    """Test if database can be created and accessed"""
    print("\nTesting database...")
    try:
        import sqlite3
        import tempfile

        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name

        # Test database operations
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                word TEXT
            )
        ''')

        cursor.execute("INSERT INTO test (word) VALUES (?)", ("test",))
        conn.commit()

        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()

        conn.close()

        # Clean up
        os.unlink(tmp_path)

        if result:
            print("  [OK] Database operations work")
            return True
        else:
            print("  [FAIL] Database operations failed")
            return False

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def test_word_manager():
    """Test Words class"""
    print("\nTesting Words...")
    try:
        from vocab_app import Words

        words_file = Path(__file__).parent.parent / "data" / "words.json"
        wm = Words(str(words_file))

        # Test getting a random word
        word = wm.rand('cet4')
        if word:
            word_data = wm.get(word)
            print(f"  [OK] Random word: {word}")
            print(f"    Meaning: {word_data.get('meaning', 'N/A')}")
        else:
            print("  [FAIL] Could not get random word")
            return False

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def test_database_manager():
    """Test DB class"""
    print("\nTesting DB...")
    try:
        from vocab_app import DB
        import tempfile

        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name

        db = DB(tmp_path)

        # Test word progress
        db.progress("test", "cet4", True)
        stats = db.stats()

        if stats['total'] > 0:
            print("  [OK] Word progress tracking works")
        else:
            print("  [FAIL] Word progress tracking failed")
            return False

        # Test stats
        print(f"  [OK] Stats: {stats['total']} words learned")

        # Clean up
        os.unlink(tmp_path)

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def main():
    print("=" * 50)
    print("四六级背单词小工具 - 测试")
    print("=" * 50)

    tests = [
        test_imports,
        test_word_loading,
        test_database,
        test_word_manager,
        test_database_manager
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    if failed == 0:
        print("\nAll tests passed! The application can run normally.")
        print("\nHow to run:")
        print("  1. Double-click 'start.bat'")
        print("  2. Or run: python src/vocab_app.py")
        return 0
    else:
        print("\nSome tests failed. Please check dependencies and configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
