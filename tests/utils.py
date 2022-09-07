from pathlib import Path
import struct


def read_test_data(name, binary=True):
    path = Path(__file__).parent / name
    if binary:
        return path.read_bytes()
    else:
        return path.read_text()


def round_f32(x):
    return struct.unpack('f', struct.pack('f', x))[0]
