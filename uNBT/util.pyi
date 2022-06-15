from collections import namedtuple
from typing import Dict, List, Literal, Optional, Tuple

RegionFileInfo = namedtuple('RegionFileInfo', ['path', 'x', 'z'])
RegionFormat = Literal['anvil', 'region']

def region_pos_from_path(path: str) -> Optional[Tuple[int, int]]: ...

def enumerate_region_files(path: str, fmt: RegionFormat = 'anvil') -> List[RegionFileInfo]: ...

def enumerate_world(path: str, fmt: RegionFormat = 'anvil') -> Dict[int, List[RegionFileInfo]]: ...
