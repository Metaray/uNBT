import unittest
from .utils import read_test_data
import uNBT as nbt
from io import BytesIO


class TestSnbt(unittest.TestCase):
    def test_serialize_cycle(self):
        self.run_cycle_for_file('bigtest.nbt')


    def run_cycle_for_file(self, filename):
        test_file = BytesIO(read_test_data(filename))
        tag = nbt.read_nbt_file(test_file)
        self.run_cycle_for_tag(tag)


    def run_cycle_for_tag(self, tag):
        # Test that serialize-parse cycle didn't lose data
        serialized = nbt.to_snbt(tag)
        parsed = nbt.parse_snbt(serialized)
        self.assertEqual(tag, parsed)


    def test_parseable(self):
        self.assertEqual(
            nbt.parse_snbt('123b'),
            nbt.TagByte(123)
        )
        self.assertEqual(
            nbt.parse_snbt('-12345s'),
            nbt.TagShort(-12345)
        )
        self.assertEqual(
            nbt.parse_snbt('+123456789'),
            nbt.TagInt(+123456789)
        )
        self.assertEqual(
            nbt.parse_snbt('123456789012l'),
            nbt.TagLong(123456789012)
        )

        self.assertEqual(
            nbt.parse_snbt('12.34f'),
            nbt.TagFloat(12.34)
        )
        self.assertEqual(
            nbt.parse_snbt('12.34d'),
            nbt.TagDouble(12.34)
        )
        self.assertEqual(
            nbt.parse_snbt('-12.34'),
            nbt.TagDouble(-12.34)
        )

        self.assertEqual(
            nbt.parse_snbt('false'),
            nbt.TagByte(0)
        )
        self.assertEqual(
            nbt.parse_snbt('true'),
            nbt.TagByte(1)
        )

        self.assertEqual(
            nbt.parse_snbt(r"'simple:string!'"),
            nbt.TagString(r'simple:string!')
        )
        self.assertEqual(
            nbt.parse_snbt(r'"a bc \'def\' ghi "'),
            nbt.TagString(r"a bc 'def' ghi ")
        )
        self.assertEqual(
            nbt.parse_snbt(r'"escaping test \" \\\\"'),
            nbt.TagString(r'escaping test " \\')
        )

        self.assertEqual(
            nbt.parse_snbt(r'[L; 1l, -2l, 3l]'),
            nbt.TagLongArray([1, -2, 3])
        )

        self.assertEqual(
            nbt.parse_snbt(r' [ [ 1 ], [ -2 ] ] '),
            nbt.TagList(
                nbt.TagList,
                [
                    nbt.TagList(nbt.TagInt, [nbt.TagInt(1)]),
                    nbt.TagList(nbt.TagInt, [nbt.TagInt(-2)])
                ]
            )
        )
        self.assertEqual(
            nbt.parse_snbt(r'["parse multiple", " quoted ", "strings"]'),
            nbt.TagList(
                nbt.TagString,
                [
                    nbt.TagString('parse multiple'),
                    nbt.TagString(' quoted '),
                    nbt.TagString('strings'),
                ]
            )
        )

        self.assertEqual(
            nbt.parse_snbt(r'{}'),
            nbt.TagCompound()
        )
        self.assertEqual(
            nbt.parse_snbt(r'{three:"3"}'),
            nbt.TagCompound({'three': nbt.TagString('3')})
        )
        self.assertEqual(
            nbt.parse_snbt(r'{"big key":{}}'),
            nbt.TagCompound({'big key': nbt.TagCompound()})
        )
        self.assertEqual(
            nbt.parse_snbt(r'{ spaces : 3 , everywhere : 7s }'),
            nbt.TagCompound({'spaces': nbt.TagInt(3), 'everywhere': nbt.TagShort(7)})
        )


    def test_unparseable(self):
        self.parse_expect_fail(r'')
        self.parse_expect_fail(r'123 "and more"')

        self.parse_expect_fail(r'"unclosed string')
        self.parse_expect_fail(r'"bad quote\"')
        
        self.parse_expect_fail(r'[[],[]')
        self.parse_expect_fail(r'[1,2,]')
        
        self.parse_expect_fail(r'[?;1,2,3]')
        self.parse_expect_fail(r'[I;1,2b]')
        self.parse_expect_fail(r'[I;1,"not an int"]')
        
        self.parse_expect_fail(r'{')
        self.parse_expect_fail(r'{bad key:"value"}')
        self.parse_expect_fail(r'{:"value"}')
        self.parse_expect_fail(r'{key:1,nocolon}')
        self.parse_expect_fail(r'{key:1,noval:}')


    def parse_expect_fail(self, s):
        with self.assertRaises(ValueError):
            tag = nbt.parse_snbt(s)
