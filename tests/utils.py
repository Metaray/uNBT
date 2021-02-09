import uNBT as nbt
import os

# TODO: use addTypeEqualityFunc or add equality comparison to tags
def tags_equal(a, b):
    if type(a) != type(b):
        return False
    
    if type(a) is nbt.TagList:
        if a.item_cls.tagid != b.item_cls.tagid:
            return False
        return all(tags_equal(x, y) for x, y in zip(a, b))

    if type(a) is nbt.TagCompound:
        for key, value in a.items():
            if not (key in b and tags_equal(value, b[key])):
                return False
        return True
    
    return a.value == b.value

def read_test_data(name, binary=True):
    path = os.path.join(os.path.dirname(__file__), name)
    mode = 'rb' if binary else 'r'
    with open(path, mode) as f:
        return f.read()
