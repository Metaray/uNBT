import os

def load_tests(loader, suite, pattern):
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(
        start_dir=this_dir,
        pattern='test_*.py',
        top_level_dir=os.path.split(this_dir)[0],
    )
    suite.addTests(package_tests)
    return suite
