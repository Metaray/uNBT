# μNBT

Simple pure-python library for reading and writing Minecraft's NBT data.

Includes some additional utilities for reading world save files.


# Warning

Currently I'm developing this library for use in my personal projects only so API may be unstable.


# Examples

Reading level.dat and displaying some info:
```
import uNBT as nbt

level = nbt.read_nbt_file('level.dat')
pos_tag = level['Data']['Player']['Pos']
print(nbt.fancy_tag_format(pos_tag))

x, z = pos_tag[0].value, pos_tag[2].value
print('Chunk:', int(x // 16), int(z // 16))
```

Output:
```
TagList [
  TagDouble(423.74648808189306)
  TagDouble(63.0)
  TagDouble(509.58013875078177)
]
Chunk: 26 31
```
