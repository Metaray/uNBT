import unittest
import uNBT as nbt


class TestTagCreation(unittest.TestCase):
    def run_integer_tests(self, tag_cls, x, mod):
        self.assertEqual(tag_cls().value, 0)
        self.assertEqual(tag_cls(x).value, x)
        self.assertEqual(tag_cls(str(x)).value, x)
        self.assertEqual(tag_cls(x + 5 * mod).value, x)
        self.assertEqual(tag_cls(-x).value, -x)
        self.assertEqual(tag_cls(-x + 8 * mod).value, -x)

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
        self.assertEqual(tag_cls().value, 0.0)
        self.assertEqual(tag_cls(v).value, v)
        self.assertEqual(tag_cls(str(v)).value, v)

    def test_tag_float(self):
        self.run_float_tests(nbt.TagFloat)

    def test_tag_double(self):
        self.run_float_tests(nbt.TagDouble)


    def test_tag_byte_array(self):
        a = [i for i in range(-128, 128)]
        self.assertEqual(list(nbt.TagByteArray(a).value), a)

    def test_tag_int_array(self):
        a = [i * 2**24 for i in range(-128, 128)]
        self.assertEqual(list(nbt.TagIntArray(a).value), a)

    def test_tag_long_array(self):
        a = [i * 2**56 for i in range(-128, 128)]
        self.assertEqual(list(nbt.TagLongArray(a).value), a)


    def test_tag_string(self):
        s = 'Hello, tests!'
        self.assertEqual(nbt.TagString(s).value, s)


    def test_tag_list(self):
        with self.assertRaises(nbt.NbtInvalidOperation):
            nbt.TagList(int)
        
        with self.assertRaises(nbt.NbtInvalidOperation):
            nbt.TagList(nbt.TagInt, [1, 2, 3])
        
        with self.assertRaises(nbt.NbtInvalidOperation):
            nbt.TagList(nbt.TagInt, [nbt.TagLong()])
        
        self.assertListEqual(nbt.TagList(nbt.TagLong).value, [])

        a = [nbt.TagInt(1), nbt.TagInt(3), nbt.TagInt(37)]
        self.assertListEqual(nbt.TagList(nbt.TagInt, a).value, a)

        b = iter(a)
        self.assertListEqual(nbt.TagList(nbt.TagInt, b).value, a)


    def test_tag_compound(self):
        self.assertDictEqual(nbt.TagCompound().value, {})

        with self.assertRaises(nbt.NbtInvalidOperation):
            nbt.TagCompound({123: 456})
        
        with self.assertRaises(nbt.NbtInvalidOperation):
            nbt.TagCompound({'key': 456})
        
        d = {
            'key': nbt.TagString('value'),
            'other': nbt.TagFloat(12.34),
        }
        self.assertDictEqual(nbt.TagCompound(d).value, d)
