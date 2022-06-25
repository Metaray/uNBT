import unittest
from .utils import tags_equal, read_test_data
import uNBT as nbt
from io import BytesIO
import sys

class TestReadWrite(unittest.TestCase):
    def test_save_load_cycle(self):
        self.run_save_load_for('bigtest.nbt')
    
    def run_save_load_for(self, filename):
        test_file = BytesIO(read_test_data(filename))
        tag, name = nbt.read_nbt_file(test_file, with_name=True)
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
        self.assertTrue(tags_equal(tag, tag2), 'Saved then read tag is different')


    # In newer python versions dictionary order is guaranteed so we can test for exact resave
    # This test guarantees we don't lose any data when reading
    @unittest.skipIf(sys.version_info < (3, 7), 'Not guaranteed on this python version')
    def test_exact_resave(self):
        source_file = BytesIO(read_test_data('bigtest.nbt'))
        tag, name = nbt.read_nbt_file(source_file, with_name=True)
        
        mock_file = BytesIO()
        nbt.write_nbt_file(mock_file, tag, root_name=name, compress=False)

        self.assertEqual(mock_file.getbuffer(), source_file.getbuffer())
