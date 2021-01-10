from .nbt import TagByteArray, TagIntArray, TagList, TagCompound, TagString
import os
import re
from collections import namedtuple

__all__ = [
	'fancy_tag_format',
	'RegionFileInfo',
	'region_pos_from_path',
	'enumerate_region_files',
	'enumerate_world',
]


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

def region_pos_from_path(path):
	name = os.path.basename(path)
	m = re.match(r'^r\.(-?\d+)\.(-?\d+)\.mc[ar]$', name)
	if m:
		return (int(m.group(1)), int(m.group(2)))
	return None

def enumerate_region_files(path, fmt='anvil'):
	'Enumerate .mcr or .mca files in provided directory'
	if fmt == 'anvil':
		ext = 'mca'
	elif fmt == 'region':
		ext = 'mcr'
	else:
		raise ValueError('Unknown format')
	files = []
	for name in os.listdir(path):
		fullpath = os.path.join(path, name)
		rxz = region_pos_from_path(name)
		if rxz and name.endswith(ext) and os.path.isfile(fullpath):
			files.append(RegionFileInfo(fullpath, rxz[0], rxz[1]))
	return files

def enumerate_world(path, fmt='anvil'):
	'Enumerate dimensions in provieded world directory'
	dims = {}
	for name in os.listdir(path):
		fullpath = os.path.join(path, name)
		if not os.path.isdir(fullpath):
			continue
		if name == 'region':
			dims[0] = enumerate_region_files(fullpath, fmt)
		else:
			m = re.match(r'DIM(-?\d+)$', name)
			if m:
				regpath = os.path.join(fullpath, 'region')
				if os.path.isdir(regpath):
					dims[int(m.group(1))] = enumerate_region_files(regpath, fmt)
	return dims
