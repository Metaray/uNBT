import zlib
import struct
from io import BytesIO
from .nbt import read_root_tag


class Chunk:
    def __init__(self, chunk_nbt):
        self._chunk_nbt = chunk_nbt
    
    @property
    def nbt(self):
        return self._chunk_nbt


class Region:
    CHUNKS_WIDTH = 32

    def __init__(self):
        self._chunks = [[None] * self.CHUNKS_WIDTH for _ in range(self.CHUNKS_WIDTH)]
    
    @classmethod
    def from_file(cls, path):
        region = cls()
        with open(path, 'rb') as rflie:
            chunk_locations = []
            for z in range(cls.CHUNKS_WIDTH):
                for x in range(cls.CHUNKS_WIDTH):
                    # big endian, [0..2] offset in 4KiB sectors, [3] length in 4KiB sectors runded up
                    loc_info, = struct.unpack('>I', rflie.read(4))
                    if loc_info == 0:
                        continue
                    chunk_locations.append(((loc_info >> 8) << 12, x, z))
            
            # Sort for seek performance
            for offset, x, z in sorted(chunk_locations):
                rflie.seek(offset)
                length, = struct.unpack('>I', rflie.read(4))
                compression = ord(rflie.read(1))
                # 1 - Gzip (unused), 2 - Zlib
                if compression != 2:
                    continue
                data = rflie.read(length)
                region._chunks[z][x] = data

        return region

    def get_chunk(self, x, z):
        data = self._chunks[z][x]
        if type(data) is not bytes:
            return data
        data = zlib.decompress(data)
        chunk_nbt = Chunk(read_root_tag(BytesIO(data)))
        self._chunks[z][x] = chunk_nbt
        return chunk_nbt
