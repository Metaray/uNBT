import struct
import gzip
import array
from collections import OrderedDict, abc
import sys

_do_byteswap = sys.byteorder == 'little'

class NbtError(Exception):
	pass
class NbtUnpackError(NbtError):
	pass
class NbtInvalidOperation(NbtError):
	pass


class Tag:
	__slots__ = ('_value',)
	tagid = 0
	
	def __init__(self):
		raise NotImplementedError('Cannot create instances of base Tag')
	
	def __repr__(self):
		return '{}({})'.format(self.__class__.__name__, self._value)
	
	@property
	def value(self):
		return self._value
	
	@classmethod
	def read(cls, stream):
		raise NotImplementedError('Cannot read instances of Tag')
	
	def write(self, stream):
		raise NotImplementedError('Cannot write instances of Tag')


class _TagNumber(Tag):
	def __init__(self, value=0):
		self._value = self._normalize(value)
	
	@classmethod
	def _normalize(cls, value):
		value = int(value) % cls._mod
		if value >= cls._mod >> 1:
			value -= cls._mod
		return value
	
	def __int__(self):
		return int(self._value)
	
	def __float__(self):
		return float(self._value)
	
	@classmethod
	def read(cls, stream):
		rawnum = stream.read(cls._fmt.size)
		return cls(cls._fmt.unpack(rawnum)[0])
	
	def write(self, stream):
		stream.write(self._fmt.pack(self._value))

class TagByte(_TagNumber):
	__slots__ = ()
	tagid = 1
	_mod = 2 ** 8
	_fmt = struct.Struct('>b')

class TagShort(_TagNumber):
	__slots__ = ()
	tagid = 2
	_mod = 2 ** 16
	_fmt = struct.Struct('>h')

class TagInt(_TagNumber):
	__slots__ = ()
	tagid = 3
	_mod = 2 ** 32
	_fmt = struct.Struct('>l')

class TagLong(_TagNumber):
	__slots__ = ()
	tagid = 4
	_mod = 2 ** 64
	_fmt = struct.Struct('>q')


class TagDouble(_TagNumber):
	__slots__ = ()
	tagid = 6
	_fmt = struct.Struct('>d')
	
	@classmethod
	def _normalize(cls, value):
		return float(value)

class TagFloat(TagDouble):
	__slots__ = ()
	tagid = 5
	_fmt = struct.Struct('>f')


class _TagNumberArray(Tag):
	def __init__(self, numbers):
		self._value = array.array(self._itype, numbers)
	
	def __repr__(self):
		return '{}(len={})'.format(self.__class__.__name__, len(self._value))
	
	@classmethod
	def read(cls, stream):
		length, = TagInt._fmt.unpack(stream.read(4))
		values = array.array(cls._itype)
		values.frombytes(stream.read(length * values.itemsize))
		if _do_byteswap:
			values.byteswap()
		return cls(values)
	
	def write(self, stream):
		stream.write(TagInt._fmt.pack(len(self._value)))
		if _do_byteswap:
			out = array.array(self._itype, self._value)
			out.byteswap()
			out.tofile(stream)

class TagByteArray(_TagNumberArray):
	__slots__ = ()
	tagid = 7
	_itype = 'b'

class TagIntArray(_TagNumberArray):
	__slots__ = ()
	tagid = 11
	_itype = 'l'

class TagLongArray(_TagNumberArray):
	__slots__ = ()
	tagid = 12
	_itype = 'q'


class TagString(Tag):
	__slots__ = ()
	tagid = 8
	
	def __init__(self, value):
		if not isinstance(value, str):
			raise ValueError('Value must have type str')
		self._value = value
	
	def __str__(self):
		return self._value
	
	def __repr__(self):
		return 'TagString({})'.format(repr(self._value))
	
	@classmethod
	def read(cls, stream):
		size, = TagShort._fmt.unpack(stream.read(2))
		return cls(stream.read(size).decode('utf-8'))

	def write(self, stream):
		raw = self._value.encode('utf-8')
		stream.write(TagShort._fmt.pack(len(raw)))
		stream.write(raw)


class TagList(Tag, abc.MutableSequence):
	__slots__ = ('item_cls',)
	tagid = 9
	
	def __init__(self, item_cls, items=None):
		if not issubclass(item_cls, Tag):
			raise NbtInvalidOperation('Item class must be some Tag')
		self.item_cls = item_cls
		if items is not None:
			if not all(type(item) is item_cls for item in items):
				raise NbtInvalidOperation('All list elements must be same Tag')
			self._value = list(items)
		else:
			self._value = []

	def __len__(self):
		return len(self._value)
	
	def __getitem__(self, index):
		return self._value[index]
	
	def __setitem__(self, index, tag):
		if type(tag) is not self.item_cls:
			raise NbtInvalidOperation('Setting wrong tag type for this list')
		self._value[index] = tag
	
	def __delitem__(self, index):
		del self._value[index]
	
	def insert(self, index, tag):
		if type(tag) is not self.item_cls:
			raise NbtInvalidOperation('Inserting wrong tag type for this list')
		self._value.insert(index, tag)
	
	def __repr__(self):
		return 'TagList(type={}, len={})'.format(self.item_cls.__name__, len(self._value))
	
	@classmethod
	def read(cls, stream):
		itemid = stream.read(1)[0]
		if itemid not in _tagid_class_mapping:
			raise NbtUnpackError('Unknown list item tag id {}'.format(itemid))
		itemcls = _tagid_class_mapping[itemid]
		itemcls_read = itemcls.read
		
		size, = TagInt._fmt.unpack(stream.read(4))
		tags = [itemcls_read(stream) for _ in range(size)]
		
		thislist = cls(itemcls)
		thislist._value = tags
		return thislist

	def write(self, stream):
		stream.write(TagByte._fmt.pack(self.item_cls.tagid))
		stream.write(TagInt._fmt.pack(len(self._value)))
		for tag in self._value:
			tag.write(stream)


class TagCompound(Tag, abc.MutableMapping):
	__slots__ = ()
	tagid = 10

	def __init__(self, mapping=None):
		if mapping is not None:
			if any(not isinstance(item, Tag) for item in mapping.values()):
				raise NbtInvalidOperation('Not all mapping elements are Tags')
			if any(type(key) is not str for key in mapping.keys()):
				raise NbtInvalidOperation('Not all mapping keys are strings')
			self._value = mapping.copy()
		else:
			self._value = {}
	
	def __repr__(self):
		return 'TagCompound(len={})'.format(len(self._value))
	
	def __len__(self):
		return len(self._value)
	
	def __getitem__(self, key):
		return self._value[key]
	
	def __setitem__(self, key, tag):
		if type(key) is not str:
			raise NbtInvalidOperation('Mapping key is not string')
		if not isinstance(tag, Tag):
			raise NbtInvalidOperation('Mapping value is not instance of Tag')
		self._value[key] = tag
	
	def __delitem__(self, key):
		del self._value[key]
	
	def __iter__(self):
		return iter(self._value)

	@classmethod
	def read(cls, stream):
		tagdict = OrderedDict()
		# tagdict = {}
		stream_read = stream.read

		while True:
			tagid = stream_read(1)[0]
			if not tagid:
				break
			if tagid not in _tagid_class_mapping:
				raise NbtUnpackError('Unknown tag id {} in compound'.format(tagid))
			name = TagString.read(stream).value
			tag = _tagid_class_mapping[tagid].read(stream)
			tagdict[name] = tag
		
		thistag = cls()
		thistag._value = tagdict
		return thistag
	
	def write(self, stream):
		for name, tag in self._value.items():
			stream.write(TagByte._fmt.pack(tag.tagid))
			TagString(name).write(stream)
			tag.write(stream)
		stream.write(b'\x00')


_tagid_class_mapping = {
	0: Tag,
	1: TagByte,
	2: TagShort,
	3: TagInt,
	4: TagLong,
	5: TagFloat,
	6: TagDouble,
	7: TagByteArray,
	8: TagString,
	9: TagList,
	10: TagCompound,
	11: TagIntArray,
	12: TagLongArray,
}


def read_root_tag(stream):
	if stream.read(1) != b'\x0a':
		raise NbtUnpackError('Invalid base tag')
	root_name = TagString.read(stream)
	return TagCompound.read(stream)

def read_nbt_file(file):
	file_handle = None
	try:
		if type(file) is str:
			file_handle = file = open(file, 'rb')
		magic = file.read(2)
		file.seek(0)
		if magic == b'\x1f\x8b':
			file = gzip.open(file, 'rb')
		return read_root_tag(file)
	finally:
		if file_handle is not None:
			file_handle.close()

def write_nbt_file(file, root, compress=True):
	file_handle = None
	try:
		if compress:
			file_handle = gzip.open(file, 'wb')
		else:
			file_handle = open(file, 'wb')
		file_handle.write(b'\x0a\x00\x00')
		root.write(file_handle)
	finally:
		if file_handle is not None:
			file_handle.close()

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


if __name__ == '__main__':
	import os

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
		
		root = read_nbt_file(path)
		if cmd == 'print':
			print(fancy_tag_format(root))
