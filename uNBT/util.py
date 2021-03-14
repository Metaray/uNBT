import os
import re
from collections import namedtuple

__all__ = [
	'RegionFileInfo',
	'region_pos_from_path',
	'enumerate_region_files',
	'enumerate_world',
]


RegionFileInfo = namedtuple('RegionFileInfo', ['path', 'x', 'z'])

def region_pos_from_path(path):
	"""Try to extract region coordinates from file name.

	Args:
		path (str): Path to region file.
	
	Returns:
		tuple, optional: (X,Z) tuple of integer coordinates of
			region file name or `None` if name is invalid.
	"""
	name = os.path.basename(path)
	m = re.match(r'^r\.(-?\d+)\.(-?\d+)\.mc[ar]$', name)
	if m:
		return (int(m.group(1)), int(m.group(2)))
	return None

def enumerate_region_files(path, fmt='anvil'):
	"""Enumerate .mcr or .mca region files in provided directory.

	Args:
		path (str): Path to ``region`` directory of a world.
		fmt (str): World save type. Supports:
			* anvil (default)
			* region

	Returns:
		list of RegionFileInfo: List of found potential region files.

	Raises:
		ValueError: If unknown `fmt` is passed in.
	"""
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
	"""Enumerate dimensions in provieded world directory.

	Args:
		path (str): Path to a world directory.
		fmt (str): World save type. Supports:
			* anvil (default)
			* region

	Returns:
		dict: Mapping from integer dimension ids to lists of 
			RegionFileInfo objects.

	Raises:
		ValueError: If unknown `fmt` is passed in.
	"""
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
