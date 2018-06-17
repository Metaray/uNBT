import struct
import gzip
import array
from collections import OrderedDict, abc
import sys

_do_byteswap = sys.byteorder == 'little'

class NBTError(Exception):
	pass
class NBTUnpackError(NBTError):
	pass
class NBTInvalidOperation(NBTError):
	pass


class Tag:
	__slots__ = ('_value',)
	tagid = 0
	
	def __init__(self, value):
		self.value = value
	
	def __str__(self):
		return '{}({})'.format(self.__class__.__name__, self._value)
	
	def __repr__(self):
		return self.__str__()
	
	@classmethod
	def _normalize(cls, value):
		raise NBTInvalidOperation('Cannot create or use instances of Tag')
	
	@property
	def value(self):
		return self._value
	
	@value.setter
	def value(self, newval):
		self._value = self._normalize(newval)


class _TagNumber(Tag):
	def __init__(self, value=0):
		super().__init__(value)
	
	@classmethod
	def _normalize(cls, value):
		value = int(value) % cls._mod
		if value >= cls._mod // 2:
			value -= cls._mod
		return value
	
	@classmethod
	def read(cls, stream):
		bytes = stream.read(cls._fmt.size)
		if len(bytes) != cls._fmt.size:
			raise NBTUnpackError('Reading {} EOF reached'.format(cls))
		return cls(cls._fmt.unpack(bytes)[0])
	
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
		if isinstance(numbers, array.array) and numbers.typecode == self._itype:
			# Internal type matches, just copy
			self._value = array.array(self._itype, numbers)
		else:
			# Else do normalization
			self.value = numbers

	@classmethod
	def _normalize(cls, value):
		newarray = array.array(cls._itype)
		for x in value:
			newarray.append(cls._itemnorm(x))
		return newarray
	
	def __str__(self):
		return '{}(size={})'.format(self.__class__.__name__, len(self._value))
	
	@classmethod
	def read(cls, stream):
		length = TagInt._fmt.unpack(stream.read(4))[0]
		values = array.array(cls._itype)
		values.frombytes(stream.read(length * values.itemsize))
		if _do_byteswap:
			values.byteswap()
		return cls(values)
	
	def write(self, stream):
		stream.write(TagInt._fmt.pack(len(self._value)))
		packer = struct.Struct('>{}'.format(self._itype))
		for x in self._value:
			stream.write(packer.pack(x))

class TagByteArray(_TagNumberArray):
	__slots__ = ()
	tagid = 7
	_itype = 'b'
	_itemnorm = TagByte._normalize

class TagIntArray(_TagNumberArray):
	__slots__ = ()
	tagid = 11
	_itype = 'l'
	_itemnorm = TagInt._normalize


class TagString(Tag):
	__slots__ = ()
	tagid = 8
	
	@classmethod
	def _normalize(cls, value):
		return str(value)
	
	def __str__(self):
		return 'TagString("{}")'.format(self._value)
	
	@classmethod
	def read(cls, stream):
		size = TagShort._fmt.unpack(stream.read(2))[0]
		encoded = stream.read(size)
		if len(encoded) != size:
			raise NBTUnpackError('String too short')
		return cls(encoded.decode('utf-8'))

	def write(self, stream):
		raw = self._value.encode('utf-8')
		stream.write(TagShort._fmt.pack(len(raw)))
		stream.write(raw)


class TagList(Tag, abc.Sequence):
	__slots__ = ('itemid',)
	tagid = 9
	
	def __init__(self, items, id):
		self.itemid = id
		super().__init__(items)

	@classmethod
	def _normalize(cls, value):
		newarray = []
		for tag in value:
			if not isinstance(tag, Tag):
				raise NBTInvalidOperation('Array element is not a Tag')
			#if tag.id != cls.itemid ????
			#	raise NBTInvalidOperation('All elements must be the same tag')
			newarray.append(tag)
		return newarray

	def __len__(self):
		return len(self.value)
	
	def __getitem__(self, key):
		return self.value[key]
	
	def __str__(self):
		return 'TagList(type={}, size={})'.format(TagReaders[self.itemid].__name__, len(self._value))
	
	@classmethod
	def read(cls, stream):
		itemid = TagByte._fmt.unpack(stream.read(1))[0]
		if itemid not in TagReaders:
			raise NBTUnpackError('Unknown tag id')
		itemcls = TagReaders[itemid]
		size = TagInt._fmt.unpack(stream.read(4))[0]
		tags = []
		for i in range(size):
			tags.append(itemcls.read(stream))
		return cls(tags, itemid)

	def write(self, stream):
		stream.write(TagByte._fmt.pack(self.itemid))
		stream.write(TagInt._fmt.pack(len(self._value)))
		for tag in self._value:
			tag.write(stream)


class TagCompound(Tag, abc.Mapping):
	__slots__ = ()
	tagid = 10
	
	@classmethod
	def _normalize(cls, value):
		newdict = OrderedDict()
		for name, tag in value.items():
			if not isinstance(tag, Tag):
				raise NBTInvalidOperation('Dict element is not a Tag')
			newdict[name] = tag
		return newdict
	
	def __str__(self):
		return 'TagCompound(size={})'.format(len(self._value))
	
	def __len__(self):
		return len(self.value)
	
	def __getitem__(self, key):
		return self.value[key]
	
	def __iter__(self):
		return iter(self.value)

	@classmethod
	def read(cls, stream):
		tagdict = OrderedDict()
		while True:
			tagid = TagByte._fmt.unpack(stream.read(1))[0]
			if tagid == 0:
				break
			if tagid not in TagReaders:
				raise NBTUnpackError('Unknown tag id')
			name = TagString.read(stream).value
			tag = TagReaders[tagid].read(stream)
			tagdict[name] = tag
		return cls(tagdict)
	
	def write(self, stream):
		for name in self._value:
			tag = self._value[name]
			stream.write(TagByte._fmt.pack(tag.tagid))
			TagString(name).write(stream)
			tag.write(stream)
		stream.write(b'\x00')


def ReadBaseTag(stream):
	tagid = ord(stream.read(1))
	if tagid != TagCompound.tagid:
		raise NBTUnpackError('Invalid base tag')
	# Should always be zero, so no name bytes
	stream.read(2)
	return TagCompound.read(stream)

TagReaders = {
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
	11: TagIntArray
}

def ReadNBTFile(path):
	try:
		file = open(path, 'rb')
		magic = file.read(2)
		if magic == b'\x1f\x8b':
			file.close()
			file = gzip.open(path, 'rb')
		else:
			file.seek(0)
		roottag = ReadBaseTag(file)
	finally:
		file.close()
	return roottag

def WriteNBTFile(path, root, compress=True):
	try:
		if compress:
			file = gzip.open(path, 'wb')
		else:
			file = open(path, 'wb')
		file.write(b'\x0a\x00\x00')
		root.write(file)
	finally:
		file.close()

def fancy_tag_format(tag, indent='  ', level=0):
	out = ''
	tag_name = tag.__class__.__name__
	if tag.tagid in (TagByteArray.tagid, TagIntArray.tagid):
		out += '{} [\n'.format(tag_name)
		for x in tag._value:
			out += '{}, '.format(x)
		out += ']'
	elif tag.tagid == TagList.tagid:
		out += '{} [\n'.format(tag_name)
		for x in tag._value:
			out += '{}{}\n'.format(indent * (level+1), fancy_tag_format(x, indent, level + 1))
		out += indent * level + ']'
	elif tag.tagid == TagCompound.tagid:
		out += 'TagCompound {\n'
		for name in tag._value:
			out += '{}{}: {}\n'.format(indent * (level+1), name, fancy_tag_format(tag._value[name], indent, level+1))
		out += indent * level + '}'
	elif tag.tagid == TagString.tagid:
		out += 'TagString("{}")'.format(tag._value)
	else:
		out += '{}({})'.format(tag_name, tag._value)
	return out


if __name__ == '__main__':
	import os
	fname = input('Enter file name: ')
	if not os.path.exists(fname):
		print('No such file exists')
		exit(0)
	
	filetags = ReadNBTFile(fname)
	
	open('UnpackedData.txt', 'w').write(fancy_tag_format(filetags))
	
	WriteNBTFile('UnpackedResaved.dat', filetags)