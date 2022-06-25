import struct
import gzip
from array import array
from collections import abc
import sys
from io import BytesIO

__all__ = [
	'NbtError',
	'NbtUnpackError',
	'NbtInvalidOperation',
	'Tag',
	'TagByte',
	'TagShort',
	'TagInt',
	'TagLong',
	'TagFloat',
	'TagDouble',
	'TagByteArray',
	'TagString',
	'TagList',
	'TagCompound',
	'TagIntArray',
	'TagLongArray',
	'read_nbt_file',
	'write_nbt_file',
]


_do_byteswap = sys.byteorder == 'little'

_struct_byte = struct.Struct('>b')
_struct_short = struct.Struct('>h')
_struct_int = struct.Struct('>i')

def _compound_read_name(stream):
	size, = _struct_short.unpack(stream.read(2))
	return stream.read(size).decode('utf-8')

def _compound_write_name(stream, name):
	raw = name.encode('utf-8')
	stream.write(_struct_short.pack(len(raw)))
	stream.write(raw)


class NbtError(Exception):
	"""Base exception of errors occuring during operations with NBT tags."""

class NbtUnpackError(NbtError):
	"""Error occured during NBT deserialization."""

class NbtInvalidOperation(NbtError):
	"""Error occured when performing some operation on NBT tags."""


class Tag:
	"""Abstract base class for all NBT tags."""
	__slots__ = ('_value',)
	
	tagid = 0
	"""int: Numerical id of a this tag type."""
	
	def __init__(self):
		raise NotImplementedError('Cannot create instances of base Tag')
	
	def __repr__(self):
		return '{}({!r})'.format(self.__class__.__name__, self._value)
	
	def __eq__(self, other):
		if type(self) is not type(other):
			return False
		return self._value == other._value
	
	__hash__ = None
	
	@property
	def value(self):
		"""Get stored tag value."""
		return self._value
	
	@classmethod
	def read(cls, stream):
		"""Read this tag from a provided stream.

		Note:
			Doesn't include preceesing name or tag id present in some cases.
			Doesn't check if all bytes have been read.

		Args:
			stream (file-like): Stream to read a tag from.
		
		Returns:
			Tag: Tag read from `stream`.
		
		Raises:
			NbtUnpackError: If some unknown tag is encountered.
		"""
		raise NotImplementedError('Cannot read instances of Tag')
	
	def write(self, stream):
		"""Write this tag to a provided stream.

		Args:
			stream (file-like): Stream to write this tag to.
		"""
		raise NotImplementedError('Cannot write instances of Tag')

	@classmethod
	def from_bytes(cls, bytes):
		"""Read this tag from provided bytes.

		Note:
			Helper method that calls `read`.

		Args:
			bytes (bytes): Bytes to read a tag from.
		
		Returns:
			Tag: Tag read from `bytes`.
		
		Raises:
			NbtUnpackError: If some unknown tag is encountered.
		"""
		return cls.read(BytesIO(bytes))

	def to_bytes(self):
		"""Serialize this tag to bytes.

		Note:
			Helper method that calls `write`.

		Returns:
			bytes: Bytes of serialized tag.
		"""
		buffer = BytesIO()
		self.write(buffer)
		return buffer.getvalue()


class _TagNumber(Tag):
	def __init__(self, value=0):
		"""Create new integer number tag.

		Args:
			value: Any object convertable to int. Defaults to 0.
		"""
		value = int(value) % self._mod
		if value < self._mod >> 1:
			self._value = value
		else:
			self._value = value - self._mod
	
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
	_fmt = struct.Struct('>i')

class TagLong(_TagNumber):
	__slots__ = ()
	tagid = 4
	_mod = 2 ** 64
	_fmt = struct.Struct('>q')


class TagDouble(_TagNumber):
	__slots__ = ()
	tagid = 6
	_fmt = struct.Struct('>d')
	
	def __init__(self, value=0.0):
		"""Create new floating point number tag.

		Args:
			value: Any object convertable to float. Defaults to 0.0
		"""
		self._value = float(value)

class TagFloat(TagDouble):
	__slots__ = ()
	tagid = 5
	_fmt = struct.Struct('>f')


class _TagNumberArray(Tag):
	def __init__(self, numbers):
		"""Create new number array tag.

		Args:
			numbers (array-like): Any array of integers in correct range.
		"""
		self._value = array(self._itype, numbers)
	
	def __str__(self):
		return '{}(len={})'.format(self.__class__.__name__, len(self._value))
	
	@classmethod
	def read(cls, stream):
		length, = _struct_int.unpack(stream.read(4))
		values = array(cls._itype)
		values.frombytes(stream.read(length * values.itemsize))
		if _do_byteswap:
			values.byteswap()
		return cls(values)
	
	def write(self, stream):
		stream.write(_struct_int.pack(len(self._value)))
		if _do_byteswap:
			out = array(self._itype, self._value)
			out.byteswap()
			out.tofile(stream)
		else:
			self._value.tofile(stream)

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
		"""Create new string tag.

		Args:
			value (str): Value of this tag.
		"""
		if not isinstance(value, str):
			raise ValueError('Value must have type str')
		self._value = value
	
	def __str__(self):
		return self._value
	
	@classmethod
	def read(cls, stream):
		size, = _struct_short.unpack(stream.read(2))
		return cls(stream.read(size).decode('utf-8'))

	def write(self, stream):
		raw = self._value.encode('utf-8')
		stream.write(_struct_short.pack(len(raw)))
		stream.write(raw)


class TagList(Tag, abc.MutableSequence):
	__slots__ = ('item_cls',)
	tagid = 9
	
	def __init__(self, item_cls, items=None):
		"""Create new list tag.

		Args:
			item_cls (Tag): The tag type this list holds.
			items (iterable of Tag): Starting contents of this tag. Default is empty list.
		
		Raises:
			NbtInvalidOperation: If `item_cls` is not a tag class
				or some tag in `items` doesn't match `item_cls`.
		"""
		if not issubclass(item_cls, Tag):
			raise NbtInvalidOperation('Item class must be some Tag')
		self.item_cls = item_cls
		if items is not None:
			items = list(items)
			if not all(type(item) is item_cls for item in items):
				raise NbtInvalidOperation('All list elements must be same Tag')
			self._value = items
		else:
			self._value = []

	def __eq__(self, other):
		if type(self) is not type(other):
			return False
		return self.item_cls == other.item_cls and self._value == other._value

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
		return 'TagList({}, {})'.format(self.item_cls.__name__, self._value)

	def __str__(self):
		return 'TagList({}, len={})'.format(self.item_cls.__name__, len(self._value))
	
	@classmethod
	def read(cls, stream):
		itemid = stream.read(1)[0]
		if itemid not in _tagid_class_mapping:
			raise NbtUnpackError('Unknown list item tag id {}'.format(itemid))
		itemcls = _tagid_class_mapping[itemid]
		itemcls_read = itemcls.read
		
		size, = _struct_int.unpack(stream.read(4))
		tags = [itemcls_read(stream) for _ in range(size)]
		
		thislist = cls(itemcls)
		thislist._value = tags
		return thislist

	def write(self, stream):
		stream.write(_struct_byte.pack(self.item_cls.tagid))
		stream.write(_struct_int.pack(len(self._value)))
		for tag in self._value:
			tag.write(stream)


class TagCompound(Tag, abc.MutableMapping):
	__slots__ = ()
	tagid = 10

	def __init__(self, mapping=None):
		"""Create new compound tag.

		Args:
			mapping (dict): Starting contents of this tag. String to Tag mapping.
				Default is empty dict.
		
		Raises:
			NbtInvalidOperation: If some `mapping` values are not NBT tags
				or some keys are not strings.
		"""
		if mapping is not None:
			if any(not isinstance(item, Tag) for item in mapping.values()):
				raise NbtInvalidOperation('Not all mapping elements are Tags')
			if any(type(key) is not str for key in mapping.keys()):
				raise NbtInvalidOperation('Not all mapping keys are strings')
			self._value = mapping.copy()
		else:
			self._value = {}
	
	def __str__(self):
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
		tagdict = {}
		stream_read = stream.read

		while True:
			tagid = stream_read(1)[0]
			if not tagid:
				break
			if tagid not in _tagid_class_mapping:
				raise NbtUnpackError('Unknown tag id {} in compound'.format(tagid))
			name = _compound_read_name(stream)
			tag = _tagid_class_mapping[tagid].read(stream)
			tagdict[name] = tag
		
		thistag = cls()
		thistag._value = tagdict
		return thistag
	
	def write(self, stream):
		for name, tag in self._value.items():
			stream.write(_struct_byte.pack(tag.tagid))
			_compound_write_name(stream, name)
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


def read_nbt_file(file, *, with_name=False):
	"""Read file containing NBT data.

	Expects to read compound root tag.
	Compressed files are unpacked automatically.

	Args:
		file (str or file-like): Path to file or file-like object to read from.
		with_name (bool): Return root tag name as well. Default is False.
	
	Returns:
		Tag: Root tag read from file.
		(or if with_name is True)
		tuple(Tag, str): Root tag and it's name.
	
	Raises:
		NbtUnpackError: If root tag is not TagCompound or some unknown tag is found.
	"""
	file_handle = None
	try:
		if type(file) is str:
			file_handle = file = open(file, 'rb')
		
		gz_magic = file.read(2)
		file.seek(-2, 1)
		if gz_magic == b'\x1f\x8b':
			file = gzip.open(file, 'rb')
		
		if file.read(1)[0] != TagCompound.tagid:
			raise NbtUnpackError('Invalid base tag')
		root_name = _compound_read_name(file)
		root = TagCompound.read(file)
		if with_name:
			return root, root_name
		else:
			return root
	
	finally:
		if file_handle is not None:
			file_handle.close()


def write_nbt_file(file, root, *, root_name='', compress=True):
	"""Write NBT storing file.

	Args:
		file (str or file-like): Path to file or file-like object to write to.
		root (TagCompound): Root tag to write.
		root_name (str): Name of root tag. Default is empty string.
		compress (bool): Compress the data. Default is True.
	
	Raises:
		NbtInvalidOperation: If root is not TagCompound.
	"""
	if type(root) is not TagCompound:
		raise NbtInvalidOperation('Root must be a TagCompound')

	file_handle = None
	try:
		if type(file) is str:
			file_handle = file = open(file, 'wb')
		
		if compress:
			file_handle = file = gzip.open(file, 'wb')
		
		file.write(b'\x0a')
		_compound_write_name(file, root_name)
		root.write(file)

	finally:
		if file_handle is not None:
			file_handle.close()
