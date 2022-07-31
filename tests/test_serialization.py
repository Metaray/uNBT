import unittest
import uNBT as nbt
from io import BytesIO
from .utils import read_test_data, round_f32
import math


class TestSerialization(unittest.TestCase):
    def test_bigtest(self):
        ref = self.create_bigtest()
        tag = nbt.read_nbt_file(BytesIO(read_test_data('bigtest.nbt')))
        self.assertEqual(tag, ref)

    def test_bigtest2(self):
        ref = self.create_bigtest2()
        tag = nbt.read_nbt_file(BytesIO(read_test_data('bigtest2.nbt')))
        self.assertEqual(tag, ref)


    @staticmethod
    def create_bigtest():
        return nbt.TagCompound({
            'longTest': nbt.TagLong(9223372036854775807),
            'shortTest': nbt.TagShort(32767),
            'stringTest': nbt.TagString('HELLO WORLD THIS IS A TEST STRING ÅÄÖ!'),
            'floatTest': nbt.TagFloat(0.4982314705848694),
            'intTest': nbt.TagInt(2147483647),
            'nested compound test': nbt.TagCompound({
                'ham': nbt.TagCompound({
                    'name': nbt.TagString('Hampus'),
                    'value': nbt.TagFloat(0.75)
                }),
                'egg': nbt.TagCompound({
                    'name': nbt.TagString('Eggbert'),
                    'value': nbt.TagFloat(0.5)
                })
            }),
            'listTest (long)': nbt.TagList(nbt.TagLong, [nbt.TagLong(11), nbt.TagLong(12), nbt.TagLong(13), nbt.TagLong(14), nbt.TagLong(15)]),
            'listTest (compound)': nbt.TagList(nbt.TagCompound, [
                nbt.TagCompound({
                    'name': nbt.TagString('Compound tag #0'),
                    'created-on': nbt.TagLong(1264099775885)
                }),
                nbt.TagCompound({
                    'name': nbt.TagString('Compound tag #1'),
                    'created-on': nbt.TagLong(1264099775885)
                })
            ]),
            'byteTest': nbt.TagByte(127),
            'byteArrayTest (the first 1000 values of (n*n*255+n*7)%100, starting with n=0 (0, 62, 34, 16, 8, ...))': nbt.TagByteArray([
                (n*n*255+n*7)%100 for n in range(1000)
            ]),
            'doubleTest': nbt.TagDouble(0.4931287132182315),
        })


    @staticmethod
    def create_bigtest2():
        def make_rec_list(depth):
            if depth <= 1:
                return nbt.TagList(nbt.TagList)
            return nbt.TagList(nbt.TagList, [
                make_rec_list(1),
                make_rec_list(depth - 1),
            ])

        def make_rec_compound(depth):
            if depth <= 1:
                return nbt.TagCompound({
                    "Begin": nbt.TagByte(-128),
                    "end.": nbt.TagShort(2**15 - 1),
                })
            return nbt.TagCompound({
                'A': make_rec_compound(1),
                'B': make_rec_compound(depth - 1),
            })

        return nbt.TagCompound({
            'byte': nbt.TagByte(42),
            'short': nbt.TagShort(12345),
            'int': nbt.TagInt(1234567890),
            'long': nbt.TagLong(1234567890123456789),
            'float': nbt.TagFloat(round_f32((1 + 5**0.5) / 2)),
            'double': nbt.TagDouble(math.pi),
            'byte array': nbt.TagByteArray([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, -122, -23, 121, 98, -37, 61, 24, 85]),
            'string': nbt.TagString('Lorem ipsum\n\thello\tworld'),
            'tag list': make_rec_list(16),
            'compound': make_rec_compound(16),
            'int array': nbt.TagIntArray([x * 111111111 for x in range(-9, 10)]),
            'long array': nbt.TagLongArray([x * 1111111111111111111 for x in range(-8, 9)]),
        })
