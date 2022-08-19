from array import array
import unittest
from .utils import round_f32
import uNBT as nbt


class TestTagModifyOperations(unittest.TestCase):
    def set_test(self, tag, value):
        tag.value = value
        self.assertEqual(tag.value, value)
    
    def set_list_test(self, tag, values):
        tag[:] = values
        self.assertSequenceEqual(tag, values)

    def set_key_test(self, tag, key, value):
        tag[key] = value
        self.assertEqual(tag[key], value)
    

    def run_integer_tests(self, tag_cls, x, mod):
        self.set_test(tag_cls(), x)

    def test_tag_byte(self):
        self.run_integer_tests(nbt.TagByte, 123, 2**8)

    def test_tag_short(self):
        self.run_integer_tests(nbt.TagShort, 12345, 2**16)

    def test_tag_int(self):
        self.run_integer_tests(nbt.TagInt, 1234567890, 2**32)

    def test_tag_long(self):
        self.run_integer_tests(nbt.TagLong, 1234567890123456789, 2**64)


    def run_float_tests(self, tag_cls, v):
        self.set_test(tag_cls(), v)

    def test_tag_float(self):
        self.run_float_tests(nbt.TagFloat, round_f32(1.23456))

    def test_tag_double(self):
        self.run_float_tests(nbt.TagDouble, 1.23456)


    def test_tag_byte_array(self):
        a = array('b', [i for i in range(-128, 128)])
        self.set_list_test(nbt.TagByteArray(), a)

    def test_tag_int_array(self):
        a = array('i', [i * 2**24 for i in range(-128, 128)])
        self.set_list_test(nbt.TagIntArray(), a)

    def test_tag_long_array(self):
        a = array('q', [i * 2**56 for i in range(-128, 128)])
        self.set_list_test(nbt.TagLongArray(), a)


    def test_tag_string(self):
        self.set_test(nbt.TagString('-'), 'Hello, tests!')


    def test_tag_list(self):
        tag = nbt.TagList(nbt.TagInt)

        with self.assertRaises(nbt.NbtInvalidOperation):
            self.set_list_test(tag, [nbt.TagString('not TagInt')])

        a = [nbt.TagInt(x) for x in [1, 33, 7, 0]]
        self.set_list_test(tag, a)

        self.set_list_test(tag, [])

        with self.assertRaises(nbt.NbtInvalidOperation):
            tag[0] = nbt.TagString('not TagInt')
        
        with self.assertRaises(nbt.NbtInvalidOperation):
            tag[:] = [nbt.TagInt(10), nbt.TagString('not TagInt')]
        
        tag[:] = a
        self.set_key_test(tag, 0, nbt.TagInt(42))

        b = [nbt.TagInt(3), nbt.TagInt(4)]
        tag[:] = a
        tag[0:2] = b
        self.assertSequenceEqual(tag, b + a[2:])

        x = nbt.TagInt(123)
        tag.append(x)
        self.assertEqual(tag[-1], x)


    def test_tag_compound(self):
        tag = nbt.TagCompound()

        with self.assertRaises(nbt.NbtInvalidOperation):
            tag[nbt.TagString('u')] = nbt.TagLong()
        
        with self.assertRaises(nbt.NbtInvalidOperation):
            tag['v'] = 123

        self.set_key_test(tag, 'test key', nbt.TagString('test value'))

        d = {
            'key': nbt.TagString('value'),
            'other': nbt.TagFloat(12.34),
        }
        tag = nbt.TagCompound(d)
        k = 'key'
        self.assertTrue(k in tag)
        del tag[k]
        self.assertTrue(k not in tag)
        self.assertTrue('other' in tag)
