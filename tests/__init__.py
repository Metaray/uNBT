from pathlib import Path

def load_tests(loader, suite, pattern):
    this_dir = Path(__file__).parent
    package_tests = loader.discover(
        start_dir=str(this_dir),
        pattern='test_*.py',
        top_level_dir=str(this_dir.parent),
    )
    suite.addTests(package_tests)
    return suite
