import zlib
import struct
from io import BytesIO
from .nbt import read_nbt_file
from .util import region_pos_from_path
import os


class Chunk:
    def __init__(self, chunk_nbt):
        self._chunk_nbt = chunk_nbt
    
    @property
    def nbt(self):
        return self._chunk_nbt


class Region:
    CHUNKS_WIDTH = 32

    def __init__(self):
        # Non-generated chunks are stored as None
        # When first read chunks are stored as compressed bytes
        # Getting a chunk automatically decompresses bytes and parses NBT
        # Parsed chunks are stored as Chunk
        self._chunks = [[None] * self.CHUNKS_WIDTH for _ in range(self.CHUNKS_WIDTH)]
    
    @classmethod
    def from_file(cls, path):
        region = cls()
        rxz = region_pos_from_path(path)
        
        with open(path, 'rb') as rflie:
            chunk_locations = []
            for z in range(cls.CHUNKS_WIDTH):
                for x in range(cls.CHUNKS_WIDTH):
                    # big endian, [0..2] offset in 4KiB sectors, [3] length in 4KiB sectors rounded up
                    try:
                        loc_info, = struct.unpack('>I', rflie.read(4))
                    except struct.error:
                        return region # empty or invalid file
                    
                    if loc_info == 0:
                        continue # chunk not present
                    
                    sector_count = loc_info & 255
                    chunk_locations.append(((loc_info >> 8) * 4096, x, z))
            
            # Sort by offset for read performance
            for offset, x, z in sorted(chunk_locations):
                rflie.seek(offset)
                length, compression = struct.unpack('>IB', rflie.read(5))
                
                # 1 - Gzip (unused), 2 - Zlib, 3 - uncompressed
                # If high bit is set - chunk is in external file c.[x].[z].mcc
                if (compression & 127) != 2:
                    # raise NotImplementedError('Unsupported compression format {}'.format(compression))
                    print('Warning: skipping chunk with unsupported compression')
                    continue
                
                if compression & 128:
                    if rxz is None:
                        raise ValueError('Found external chunk, but no region position available')
                    cx, cz = x + rxz[0] * 32, z + rxz[1] * 32
                    cname = 'c.{}.{}.mcc'.format(cx, cz)
                    with open(os.path.join(os.path.dirname(path), cname), 'rb') as cfile:
                        data = cfile.read()
                else:
                    data = rflie.read(length)
                region._chunks[z][x] = data

        return region

    def get_chunk(self, x, z):
        data = self._chunks[z][x]
        if type(data) is not bytes:
            return data
        data = zlib.decompress(data)
        chunk_nbt = Chunk(read_nbt_file(BytesIO(data)))
        self._chunks[z][x] = chunk_nbt
        return chunk_nbt
    
    def iter_nonempty(self):
        for z in range(self.CHUNKS_WIDTH):
            for x in range(self.CHUNKS_WIDTH):
                chunk = self.get_chunk(x, z)
                if chunk:
                    yield chunk
