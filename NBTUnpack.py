import struct
import gzip

class NBTError(Exception):
	pass
class NBTUnpackError(NBTError):
	pass
class NBTInvalidOperation(NBTError):
	pass

def make_reader(name):
	reader = struct.Struct(name)
	size = reader.size
	def read_func(stream):
		bytes = stream.read(size)
		if len(bytes) != size:
			raise NBTUnpackError('Unpacking {}: expected {} got {}'.format(name, size, len(bytes)))
		return reader.unpack(bytes)[0]
	return read_func

read_byte = make_reader('>b')
read_ubyte = make_reader('>B')
read_short = make_reader('>h')
read_ushort = make_reader('>H')
read_int = make_reader('>l')
read_long = make_reader('>q')
read_float = make_reader('>f')
read_double = make_reader('>d')

def ReadTagByte(stream):
	return read_byte(stream)

def ReadTagShort(stream):
	return read_short(stream)

def ReadTagInt(stream):
	return read_int(stream)

def ReadTagLong(stream):
	return read_long(stream)

def ReadTagFloat(stream):
	return read_float(stream)

def ReadTagDouble(stream):
	return read_double(stream)

def ReadTagByteArray(stream):
	size = read_int(stream)
	data = []
	for i in range(size):
		data.append(read_byte(stream))
	return data

def ReadTagString(stream):
	size = read_ushort(stream)
	encoded = stream.read(size)
	if len(encoded) != size:
		raise NBTUnpackError('String too short')
	return encoded.decode('utf-8')

def ReadTagList(stream):
	tagid = read_byte(stream)
	if tagid not in TagReaders:
		raise NBTUnpackError('Unknown tag id')
	read_item = TagReaders[tagid]
	size = read_int(stream)
	data = []
	for i in range(size):
		data.append(read_item(stream))
	return data

def ReadTagCompound(stream):
	tagdict = {}
	while True:
		tagid = read_ubyte(stream)
		if tagid == 0:
			break
		if tagid not in TagReaders:
			raise NBTUnpackError('Unknown tag id')
		
		namelen = read_ushort(stream)
		tagnameraw = stream.read(namelen)
		if len(tagnameraw) != namelen:
			raise NBTUnpackError('Name too short')
		tagname = tagnameraw.decode('utf-8')
		
		tagdata = TagReaders[tagid](stream)
		
		#tagdict[tagname] = (tagid, tagdata)
		tagdict[tagname] = tagdata
	return tagdict

def ReadTagIntArray(stream):
	size = read_int(stream)
	data = []
	for i in xrange(size):
		data.append(read_int(stream))
	return data

def ReadBaseTag(stream):
	tagid = read_ubyte(stream)
	if tagid != 10:
		raise NBTUnpackError('Invalid base tag')
	# Should always be zero so no name bytes
	read_ushort(stream)
	return ReadTagCompound(stream)

TagReaders = {
	0: lambda x: None,
	1: ReadTagByte,
	2: ReadTagShort,
	3: ReadTagInt,
	4: ReadTagLong,
	5: ReadTagFloat,
	6: ReadTagDouble,
	7: ReadTagByteArray,
	8: ReadTagString,
	9: ReadTagList,
	10: ReadTagCompound,
	11: ReadTagIntArray
}

def ReadNBTFile(path):
	file = open(path, 'rb')

	magic = file.read(2)
	if magic == b'\x1f\x8b':
		file.close()
		file = gzip.open(path, 'rb')
	else:
		file.seek(0)
	
	#roottag = (10, ReadBaseTag(file))
	roottag = ReadBaseTag(file)

	file.close()
	return roottag


if __name__ == '__main__':
	import os
	fname = input('Enter file name: ')
	if not os.path.exists(fname):
		print('No such file exists')
		exit(0)
	
	filetags = ReadNBTFile(fname)
	
	open('UnpackedData.txt', 'w').write(str(filetags))
