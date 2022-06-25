import os


def read_test_data(name, binary=True):
    path = os.path.join(os.path.dirname(__file__), name)
    mode = 'rb' if binary else 'r'
    with open(path, mode) as f:
        return f.read()
