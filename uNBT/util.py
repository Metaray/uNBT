from .nbt import TagByteArray, TagIntArray, TagList, TagCompound, TagString
import os
import re
from collections import namedtuple


def fancy_tag_format(tag, indent='  ', level=0):
	out = ''
	tag_name = tag.__class__.__name__
	if tag.tagid in (TagByteArray.tagid, TagIntArray.tagid):
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


RegionFileInfo = namedtuple('RegionFileInfo', ['path', 'x', 'z'])

def enumerate_region_files(path):
	'Enumerate .mcr and .mca files in provided directory'
	files = []
	for name in os.listdir(path):
		m = re.match(r'r\.(-?\d+)\.(-?\d+)\.mc[ar]$', name)
		fullpath = os.path.join(path, name)
		if m and os.path.isfile(fullpath):
			files.append(RegionFileInfo(fullpath, int(m.group(1)), int(m.group(2))))
	return files

def enumerate_world(path):
	'Enumerate dimesions region files in provieded world directory'
	dims = {}
	for name in os.listdir(path):
		fullpath = os.path.join(path, name)
		if not os.path.isdir(fullpath):
			continue
		if name == 'region':
			dims[0] = enumerate_region_files(fullpath)
		else:
			m = re.match(r'DIM(-?\d+)$', name)
			if m:
				regpath = os.path.join(fullpath, 'region')
				if os.path.isdir(regpath):
					dims[int(m.group(1))] = enumerate_region_files(regpath)
	return dims
