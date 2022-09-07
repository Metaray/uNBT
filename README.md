# μNBT

Simple Pythonic library for reading and writing files in Minecraft's Named Binary Tag (NBT) format.

Includes some additional utilities for reading world save data.


## Example

Reading level.dat and displaying info about player position:

```python
import uNBT as nbt

level = nbt.read_nbt_file('level.dat')
pos_tag = level['Data']['Player']['Pos']
print(repr(pos_tag))

x, z = pos_tag[0].value, pos_tag[2].value
print('Chunk:', int(x // 16), int(z // 16))
```

Output:
```
TagList(TagDouble, [TagDouble(388.5), TagDouble(93.62000000476837), TagDouble(-790.5)])
Chunk: 24 -50
```


## Notes

- Only big-endian NBT (used by java version) is supported
- Currently treats strings as UTF-8 instead of MUTF-8
