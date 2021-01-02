from .nbt import *
from .util import fancy_tag_format
import os
import sys


def print_usage():
	print('Usage: python -m uNBT <command> [arguments]')
	print('Commands:')
	print('    print <file> [selectors] - Print file\'s nbt data with neat formatting')


def op_print(args):
	if len(args) not in (1, 2):
		print_usage()
		exit(3)
	
	path = args[0]
	if not os.path.exists(path):
		print('File {} does not exist'.format(path))
		exit(3)
	
	root, root_name = read_nbt_file(path, with_name=True)

	if len(args) == 2:
		for selector in args[1].split('.'):
			if isinstance(root, TagCompound):
				try:
					root = root[selector]
				except KeyError:
					print('No entry {} in tag {}'.format(selector, str(root)))
					exit(4)
			
			elif isinstance(root, TagList):
				try:
					root = root[int(selector)]
				except ValueError:
					print('Non-numerical selector {} for tag {}'.format(selector, str(root)))
					exit(4)
				except IndexError:
					print('Index {} out of range for tag {}'.format(selector, str(root)))
					exit(4)
			
			else:
				print('Cannot select {} from tag {}'.format(selector, str(root)))
				exit(4)
	else:
		print('Root tag name:', repr(root_name))

	print(fancy_tag_format(root))


if len(sys.argv) < 2:
	print_usage()
	exit(1)

cmd = sys.argv[1].lower()
cmd_args = sys.argv[2:]

if cmd == 'print':
	op_print(cmd_args)
else:
	print('Unknown command: {}'.format(cmd))
	print_usage()
	exit(2)
