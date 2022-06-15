from typing import Iterator, Optional
from uNBT.nbt import TagCompound

class Chunk:
    def __init__(self, chunk_nbt: TagCompound) -> None: ...
    
    @property
    def nbt(self) -> TagCompound: ...


class Region:
    CHUNKS_WIDTH: int = ...
    
    def __init__(self) -> None: ...
    
    @classmethod
    def from_file(cls, path: str) -> Region: ...
    
    def get_chunk(self, x: int, z: int) -> Optional[Chunk]: ...
    
    def iter_nonempty(self) -> Iterator[Chunk]: ...