import unittest
import uNBT as nbt


class TestTagReadOperations(unittest.TestCase):
    def run_integer_tests(self, tag_cls, x, mod):
        self.assertIs(type(int(tag_cls(x))), int)
        self.assertEqual(int(tag_cls(x)), x)

        y = max(-2**53 + 1, min(2**53 - 1, x))
        self.assertIs(type(float(tag_cls(y))), float)
        self.assertEqual(float(tag_cls(y)), y)

    def test_tag_byte(self):
        self.run_integer_tests(nbt.TagByte, 123, 2**8)

    def test_tag_short(self):
        self.run_integer_tests(nbt.TagShort, 12345, 2**16)

    def test_tag_int(self):
        self.run_integer_tests(nbt.TagInt, 1234567890, 2**32)

    def test_tag_long(self):
        self.run_integer_tests(nbt.TagLong, 1234567890123456789, 2**64)


    def run_float_tests(self, tag_cls):
        v = 1.2345

        self.assertIs(type(int(tag_cls(v))), int)
        self.assertEqual(int(tag_cls(v)), int(v))

        self.assertIs(type(float(tag_cls(v))), float)
        self.assertEqual(float(tag_cls(v)), v)

    def test_tag_float(self):
        self.run_float_tests(nbt.TagFloat)

    def test_tag_double(self):
        self.run_float_tests(nbt.TagDouble)


    def test_tag_string(self):
        s = 'Hello, tests!'
        self.assertEqual(str(nbt.TagString(s)), s)


    def test_tag_list(self):
        a = [nbt.TagInt(1), nbt.TagInt(3), nbt.TagInt(37)]
        b = nbt.TagList(nbt.TagInt, a)
        
        self.assertEqual(len(a), len(b))
        
        for x, y in zip(iter(a), iter(b)):
            self.assertEqual(x, y, msg='Failed comparison by iteration')

        for i in range(len(a)):
            self.assertEqual(a[i], b[i], msg='Failed comparison by indexing')


    def test_tag_compound(self):
        a = {
            'key': nbt.TagString('value'),
            'other': nbt.TagFloat(12.34),
        }
        b = nbt.TagCompound(a)

        self.assertEqual(len(a), len(b))

        self.assertEqual(a['key'], b['key'])

        self.assertEqual(set(a.keys()), set(b.keys()))
        for key in b:
            self.assertEqual(a[key], b[key], msg='Failed dict comparison')
