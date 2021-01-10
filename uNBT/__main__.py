from .nbt import *
import os
import sys


def print_usage():
	print('Usage: python -m uNBT <command> [arguments]')
	print('Commands:')
	print('    print <file> [selectors] - Print file\'s nbt data with neat formatting')


def fancy_tag_format(tag, indent='  ', level=0):
	out = ''
	tag_name = tag.__class__.__name__
	if tag.tagid in (TagByteArray.tagid, TagIntArray.tagid, TagLongArray.tagid):
		out += '{} {}'.format(tag_name, tag._value.tolist())
	elif tag.tagid == TagList.tagid:
		out += '{} [\n'.format(tag_name)
		for x in tag._value:
			out += '{}{}\n'.format(indent * (level + 1), fancy_tag_format(x, indent, level + 1))
		out += indent * level + ']'
	elif tag.tagid == TagCompound.tagid:
		out += 'TagCompound {\n'
		for name in tag._value:
			out += '{}{}: {}\n'.format(indent * (level + 1), name, fancy_tag_format(tag._value[name], indent, level + 1))
		out += indent * level + '}'
	elif tag.tagid == TagString.tagid:
		out += repr(tag)
	else:
		out += '{}({})'.format(tag_name, tag._value)
	return out


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
					print('No entry "{}" in tag {}'.format(selector, str(root)))
					exit(4)
			
			elif isinstance(root, TagList):
				try:
					root = root[int(selector)]
				except ValueError:
					print('Non-numerical selector "{}" for tag {}'.format(selector, str(root)))
					exit(4)
				except IndexError:
					print('Index {} out of range for tag {}'.format(selector, str(root)))
					exit(4)
			
			else:
				print('Cannot select "{}" from tag {}'.format(selector, str(root)))
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
