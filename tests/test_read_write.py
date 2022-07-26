import unittest
from .utils import read_test_data
import uNBT as nbt
from io import BytesIO
import sys

class TestReadWrite(unittest.TestCase):
    def test_save_load_cycle(self):
        self.run_save_load_for('bigtest.nbt')
        self.run_save_load_for('bigtest2.nbt')


    def run_save_load_for(self, filename):
        test_file = BytesIO(read_test_data(filename))
        tag, name = nbt.read_nbt_file(test_file, with_name=True)
        self.assertEqual(test_file.tell(), len(test_file.getvalue()), 'Unread data remaining')
        self.check_save_load(tag, name)


    def check_save_load(self, tag, name):
        # Save
        mock_file = BytesIO()
        nbt.write_nbt_file(mock_file, tag, root_name=name, compress=False)

        # Load back
        mock_file.seek(0)
        tag2, name2 = nbt.read_nbt_file(mock_file, with_name=True)

        # Test that save-load cycle didn't lose data
        self.assertEqual(name, name2, "Root tag names aren't equal")
        self.assertEqual(tag, tag2, 'Saved then read tag is different')


    # In newer python versions dictionary order is guaranteed so we can test for exact resave
    # This test guarantees we don't lose any data when reading
    @unittest.skipIf(sys.version_info < (3, 7), 'Not guaranteed on this python version')
    def test_exact_resave(self):
        self.run_exact_resave_for('bigtest.nbt')
        self.run_exact_resave_for('bigtest2.nbt')


    def run_exact_resave_for(self, filename):
        source_file = BytesIO(read_test_data(filename))
        tag, name = nbt.read_nbt_file(source_file, with_name=True)
        
        mock_file = BytesIO()
        nbt.write_nbt_file(mock_file, tag, root_name=name, compress=False)

        self.assertEqual(mock_file.getvalue(), source_file.getvalue(), 'Inexact NBT file resave')
