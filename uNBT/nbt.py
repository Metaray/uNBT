from pathlib import PurePath
import struct
import gzip
from array import array
from collections.abc import MutableSequence, MutableMapping
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


_struct_byte = struct.Struct('>b')
_struct_short = struct.Struct('>h')
_struct_int = struct.Struct('>i')
_struct_float = struct.Struct('>f')


def _compound_read_name(stream):
	size, = _struct_short.unpack(stream.read(2))
	return stream.read(size).decode('utf-8')


def _compound_write_name(stream, name):
	raw = name.encode('utf-8')
	stream.write(_struct_short.pack(len(raw)))
	stream.write(raw)


def _array_exact_for(itype):
	return array(itype).itemsize == struct.calcsize(itype)


class NbtError(Exception):
	"""Some error occurred during operations with NBT tags."""

class NbtUnpackError(NbtError):
	"""Error occurred during NBT deserialization."""

class NbtInvalidOperation(NbtError):
	"""Error occurred when performing some operation on NBT tags."""


class Tag:
	"""Abstract base class of NBT tags."""
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
	
	@classmethod
	def read(cls, stream):
		"""Read this tag from a provided stream.

		Note:
			Doesn't read preceding tag name.
			Doesn't check if all bytes have been read.

		Args:
			stream (file-like): Stream to read a tag from.
		
		Returns:
			Tag: Tag read from `stream`.
		
		Raises:
			NbtUnpackError: If some unknown tag is encountered.
		"""
		raise NotImplementedError('Cannot read instances of base Tag')
	
	def write(self, stream):
		"""Write this tag to a provided stream.

		Args:
			stream (file-like): Stream to write this tag to.
		"""
		raise NotImplementedError('Cannot write instances of base Tag')

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
	__slots__ = ()

	def __init__(self, value=0):
		"""Initialize new integer number tag.

		Args:
			value (int): Value of tag. Default is 0.
		"""
		if not isinstance(value, int):
			raise ValueError('Tag value must be an int')
		mod = self._mod
		value = int(value) % mod
		if value < (mod >> 1):
			self._value = value
		else:
			self._value = value - mod
	
	@property
	def value(self):
		"""Get stored tag value."""
		return self._value
	
	@value.setter
	def value(self, new_value):
		"""Set tag value (equivalent to re-initialization)"""
		self.__init__(new_value)

	def __int__(self):
		return int(self._value)
	
	def __float__(self):
		return float(self._value)
	
	@classmethod
	def read(cls, stream):
		fmt = cls._fmt
		x, = fmt.unpack(stream.read(fmt.size))
		return cls(x)
	
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
		"""Initialize new floating point number tag.

		Args:
			value (float): Value of tag. Default is 0.0
		"""
		if not isinstance(value, float):
			raise ValueError('Tag value must be a float')
		self._value = value

class TagFloat(_TagNumber):
	__slots__ = ()
	tagid = 5
	_fmt = struct.Struct('>f')

	def __init__(self, value=0.0):
		"""Initialize new floating point number tag.
		
		Note:
			Value is truncated to 32-bit (single) precision.

		Args:
			value (float): Value of tag. Default is 0.0
		"""
		if not isinstance(value, float):
			raise ValueError('Tag value must be a float')
		self._value, = _struct_float.unpack(_struct_float.pack(value))


class _TagNumberArray(Tag, MutableSequence):
	__slots__ = ()
	
	def __init__(self, numbers=None):
		"""Initialize new number array tag.

		Args:
			numbers (iterable of int): Starting value of array. Default is empty.
		"""
		if numbers is not None:
			self._value = array(self._itype, numbers)
		else:
			self._value = array(self._itype)
	
	@property
	def value(self):
		"""Get internal array buffer"""
		return self._value

	def __str__(self):
		return '{}(len={})'.format(self.__class__.__name__, len(self._value))
	
	def __len__(self):
		return len(self._value)
	
	def __getitem__(self, index):
		return self._value[index]
	
	def __setitem__(self, index, value):
		self._value[index] = value
	
	def __delitem__(self, index):
		del self._value[index]
	
	def insert(self, index, value):
		self._value.insert(index, value)
	
	@classmethod
	def _read_s(cls, stream):
		length, = _struct_int.unpack(stream.read(4))
		fmt = struct.Struct('>{}{}'.format(length, cls._itype))
		return cls(fmt.unpack(stream.read(fmt.size)))
	
	def _write_s(self, stream):
		length = len(self._value)
		fmt = struct.Struct('>{}{}'.format(length, self._itype))
		stream.write(_struct_int.pack(length))
		stream.write(fmt.pack(*self._value))
	
	@classmethod
	def read(cls, stream):
		length, = _struct_int.unpack(stream.read(4))
		tag = cls()
		values = tag._value
		values.fromfile(stream, length)
		values.byteswap()
		return tag

	def write(self, stream):
		stream.write(_struct_int.pack(len(self._value)))
		out = array(self._itype, self._value)
		out.byteswap()
		out.tofile(stream)


class TagByteArray(_TagNumberArray):
	__slots__ = ()
	tagid = 7
	_itype = 'b'
	if not _array_exact_for(_itype):
		read, write = _TagNumberArray._read_s, _TagNumberArray._write_s


class TagIntArray(_TagNumberArray):
	__slots__ = ()
	tagid = 11
	_itype = 'i'
	if not _array_exact_for(_itype):
		read, write = _TagNumberArray._read_s, _TagNumberArray._write_s


class TagLongArray(_TagNumberArray):
	__slots__ = ()
	tagid = 12
	_itype = 'q'
	if not _array_exact_for(_itype):
		read, write = _TagNumberArray._read_s, _TagNumberArray._write_s


class TagString(Tag):
	__slots__ = ()
	tagid = 8
	
	def __init__(self, value=''):
		"""Initialize new string tag.

		Args:
			value (str): Value of this tag. Default is empty string.
		"""
		if not isinstance(value, str):
			raise ValueError('Value must have type str')
		self._value = value
	
	@property
	def value(self):
		"""Get stored tag value."""
		return self._value
	
	@value.setter
	def value(self, new_value):
		"""Set tag value (equivalent to re-initialization)"""
		self.__init__(new_value)

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


class TagList(Tag, MutableSequence):
	__slots__ = ('item_cls',)
	tagid = 9
	
	def __init__(self, item_cls, items=None):
		"""Initialize new list tag.

		Args:
			item_cls (Tag): The tag type this list holds.
			items (iterable of Tag): Starting contents of the list. Default is empty.
		
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
		if not isinstance(other, TagList):
			return False
		return self.item_cls == other.item_cls and self._value == other._value

	def __len__(self):
		return len(self._value)
	
	def __getitem__(self, index):
		return self._value[index]
	
	def __setitem__(self, index, item):
		if isinstance(index, int):
			if not isinstance(item, self.item_cls):
				raise NbtInvalidOperation('Setting wrong tag type for this list')
			self._value[index] = item
		
		elif isinstance(index, slice):
			items = list(item)
			if self.item_cls is Tag:
				if items:
					new_cls = type(items[0])
					if not issubclass(new_cls, Tag):
						raise NbtInvalidOperation('Item class must be some Tag')
					if not all(isinstance(it, new_cls) for it in items):
						raise NbtInvalidOperation('Conflicting tag types in values')
					self._value[index] = items
					self.item_cls = new_cls
			else:
				this_tag = self.item_cls
				if not all(isinstance(it, this_tag) for it in items):
					raise NbtInvalidOperation('Setting wrong tag type for this list')
				self._value[index] = items
		
		else:
			raise NbtInvalidOperation('Unsupported index type')
	
	def __delitem__(self, index):
		del self._value[index]
	
	def insert(self, index, tag):
		if type(tag) is not self.item_cls:
			if self.item_cls is Tag:
				new_cls = type(tag)
				if not issubclass(new_cls, Tag):
					raise NbtInvalidOperation('Item class must be some Tag')
				self._value.insert(index, tag)
				self.item_cls = new_cls
				return
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


class TagCompound(Tag, MutableMapping):
	__slots__ = ()
	tagid = 10

	def __init__(self, mapping=None):
		"""Initialize new compound tag.

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
			if any(not isinstance(key, str) for key in mapping.keys()):
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
		if not isinstance(key, str):
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

	Note:
		Compressed files are unpacked automatically.

	Args:
		file (str, Path, or file-like): Path to file or file-like object to read from.
		with_name (bool): Return root tag name as well. Default is False.
	
	Returns:
		Tag: Root tag read from file.
		(or if with_name is True)
		tuple(Tag, str): Root tag and it's name.
	
	Raises:
		NbtUnpackError: If unknown tag is found.
	"""
	file_handle = None
	try:
		if isinstance(file, (str, PurePath)):
			file_handle = file = open(file, 'rb')
		
		gz_magic = file.read(2)
		file.seek(-2, 1)
		if gz_magic == b'\x1f\x8b':
			file = gzip.open(file, 'rb')
		
		tagid = file.read(1)[0]
		if tagid == 0 or tagid not in _tagid_class_mapping:
			raise NbtUnpackError('Invalid base tag')
		
		root_name = _compound_read_name(file)
		root = _tagid_class_mapping[tagid].read(file)
		
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
		file (str, Path or file-like): Path to file or file-like object to write to.
		root (Tag): Tag to write.
		root_name (str): Name of root tag. Default is empty string.
		compress (bool): Compress the data. Default is True.
	
	Raises:
		NbtInvalidOperation: If root is not Tag.
	"""
	if not isinstance(root, Tag):
		raise NbtInvalidOperation('Root must be a Tag')

	file_handle = None
	try:
		if isinstance(file, (str, PurePath)):
			file_handle = file = open(file, 'wb')
		
		if compress:
			file_handle = file = gzip.open(file, 'wb')
		
		file.write(_struct_byte.pack(root.tagid))
		_compound_write_name(file, root_name)
		root.write(file)

	finally:
		if file_handle is not None:
			file_handle.close()
