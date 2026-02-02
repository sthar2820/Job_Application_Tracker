"""
Sample test runner for all tests.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tests.test_extract import run_all_tests as run_extract_tests
from app.tests.test_classify import run_all_tests as run_classify_tests


def main():
    """Run all test suites."""
    print("\n" + "=" * 60)
    print("JOB APPLICATION TRACKER - TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        # Run extract tests
        run_extract_tests()
        print()
        
        # Run classify tests
        run_classify_tests()
        print()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
