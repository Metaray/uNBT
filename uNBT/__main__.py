from .nbt import read_nbt_file
from .util import fancy_tag_format
import os
import sys

def print_usage():
	print('Usage: uNBT.py <command> <file>')
	print('Commands:')
	print('    print - Print tag with formatting')

if len(sys.argv) != 3:
	print_usage()
	exit(1)

else:
	cmd = sys.argv[1].lower()
	path = sys.argv[2]

	if cmd not in ['print']:
		print('Unknown command: {}'.format(cmd))
		print_usage()
		exit(2)

	if not os.path.exists(path):
		print('File {} does not exist'.format(path))
		exit(3)
	
	root, root_name = read_nbt_file(path, with_name=True)
	if cmd == 'print':
		print('Root name:', repr(root_name))
		print(fancy_tag_format(root))
