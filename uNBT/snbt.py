from .nbt import TagByte, TagByteArray, TagCompound, TagDouble, TagFloat, TagInt, TagIntArray, TagList, TagLong, TagLongArray, TagShort, TagString
import re

__all__ = ['to_snbt', 'parse_snbt']


def _quote_string(s):
    return '"{}"'.format(s.replace('"', '\\"').replace("'", "\\'").replace('\\', '\\\\'))


def _quote_compound_key(s):
    if re.match(r'^[0-9a-zA-Z.+_-]+$', s):
        return s
    else:
        return _quote_string(s)


def to_snbt(tag, *, sort=False):
    tt = type(tag)
    if tt is TagByte:
        return '{}b'.format(tag.value)
    if tt is TagShort:
        return '{}s'.format(tag.value)
    if tt is TagInt:
        return '{}'.format(tag.value)
    if tt is TagLong:
        return '{}l'.format(tag.value)
    if tt is TagFloat:
        return '{}f'.format(tag.value)
    if tt is TagDouble:
        return '{}d'.format(tag.value)
    if tt is TagByteArray:
        return '[B;{}]'.format(','.join(map('{}b'.format, tag.value)))
    if tt is TagIntArray:
        return '[I;{}]'.format(','.join(map('{}'.format, tag.value)))
    if tt is TagLongArray:
        return '[L;{}]'.format(','.join(map('{}l'.format, tag.value)))
    if tt is TagString:
        return _quote_string(tag.value)
    if tt is TagList:
        return '[{}]'.format(','.join(map(to_snbt, tag)))
    if tt is TagCompound:
        keys = tag.keys()
        if sort:
            keys = sorted(keys)
        return '{{{}}}'.format(','.join('{}:{}'.format(_quote_compound_key(k), to_snbt(tag[k])) for k in keys))
    raise ValueError('Unknown tag')


def parse_snbt(s):
    unparsed, tag = _parse_rec(s)
    if not unparsed or unparsed.isspace():
        return tag
    raise ValueError('Unparsed string remaining')


def _parse_rec(s):
    s = s.lstrip()
    if not s:
        raise ValueError('Nothing to parse')
    
    # Parse string
    if s[0] == '"' or s[0] == "'":
        s, v = _parse_quoted_string(s)
        return s, TagString(v)
    
    # Parse int arrays
    # Done before list tag to simplify parsing
    m = re.match(r'\[([BIL]);', s)
    if m:
        s = s[3:]
        atype = m.group(1).lower()

        values = []
        while True:
            s = s.lstrip()
            if not s:
                raise ValueError('Unclosed integer array tag')
            if s[0] == ']':
                s = s[1:]
                break
            if values:
                if s[0] == ',':
                    s = s[1:].lstrip()
                else:
                    raise ValueError('Elements of an array must be comma separated')
            
            res = _try_parse_integer(s)
            if not res:
                raise ValueError('Expected integer tag')
            
            s, value, suf = res
            if suf != atype:
                raise ValueError('Wrong integer inside array')
            
            values.append(value)

        if atype == 'b':
            return s, TagByteArray(values)
        elif atype == 'l':
            return s, TagLongArray(values)
        else:
            return s, TagIntArray(values)

    # Parse list tag
    if s[0] == '[':
        s = s[1:]
        tags = []
        while True:
            s = s.lstrip()
            if not s:
                raise ValueError('Unclosed list tag')
            if s[0] == ']':
                s = s[1:]
                break
            if tags:
                if s[0] == ',':
                    s = s[1:].lstrip()
                else:
                    raise ValueError('Elements of a list must be comma separated: {}'.format(s))
            
            s, tag = _parse_rec(s)
            tags.append(tag)
        
        if tags:
            tag_cls = type(tags[0])
        else:
            tag_cls = TagInt  # Choice as good as any if no tags were read
        return s, TagList(tag_cls, tags)

    # Parse compound tag
    if s[0] == '{':
        s = s[1:]
        tags = {}
        while True:
            s = s.lstrip()
            if not s:
                raise ValueError('Unclosed compound tag')
            if s[0] == '}':
                s = s[1:]
                break
            if tags:
                if s[0] == ',':
                    s = s[1:].lstrip()
                else:
                    raise ValueError('Elements of a compound must be comma separated')
            
            if s[0] == '"' or s[0] == "'":
                s, key = _parse_quoted_string(s)
            else:
                s, key = _parse_unquoted_string(s)

            m = re.match(r'\s*:', s)
            if not m:
                raise ValueError('Invalid compound tag key: {}'.format(s))
            s = s[m.end():]

            s, value = _parse_rec(s)
            
            tags[key] = value
        
        return s, TagCompound(tags)

    # When no letter is used,
    # it assumes double if there's a decimal point,
    # int if there's no decimal point and the size fits within 32 bits,
    # or string if neither is true.
    s, chunk = _parse_unquoted_string(s)

    # Parse floats
    m = re.match(r'([-+]?(?:[0-9]+[.]?|[0-9]*[.][0-9]+)(?:e[-+]?[0-9]+)?)([fd])$', chunk)
    if not m:
        m = re.match(r'([-+]?(?:[0-9]+[.]|[0-9]*[.][0-9]+)(?:e[-+]?[0-9]+)?)()$', chunk)
    if m:
        value = float(m.group(1))
        vtype = m.group(2).lower()
        if vtype == 'f':
            return s, TagFloat(value)
        else:
            return s, TagDouble(value)
    
    # Parse integers
    m = _try_parse_integer(chunk)
    if m:
        _, value, vtype = m
        if vtype == 'b':
            return s, TagByte(value)
        elif vtype == 's':
            return s, TagShort(value)
        elif vtype == 'l':
            return s, TagLong(value)
        else:
            return s, TagInt(value)
    
    # Special constants
    if chunk == 'true':
        return s, TagByte(1)
    elif chunk == 'false':
        return s, TagByte(0)

    # TODO: Game parser default to string on parsing fail, maybe mimic?
    raise ValueError('Failed to parse')


def _parse_unquoted_string(s):
    m = re.match(r'[0-9a-zA-Z.+_-]*', s)
    val = m.group()
    if not val:
        raise ValueError('Empty unquoted string')
    return s[m.end():], val


def _parse_quoted_string(s):
    quote = s[0]
    if s[1] == quote:
        return s[2:], ''
    m = re.match(r'{0}(.*?[^\\](?:\\\\)*){0}'.format(quote), s)
    if not m:
        raise ValueError('Unclosed string tag')
    value = m.group(1).replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
    s = s[m.end():]
    return s, value


def _try_parse_integer(s):
    m = re.match(r'([+-]?(?:0|[1-9][0-9]*))([bsl]?)', s)
    if not m:
        return None
    # TODO: Bounds check parsed int. Game parser fails if out of range int is created.
    value = int(m.group(1))
    vtype = m.group(2).lower() or 'i'
    s = s[m.end():]
    return s, value, vtype
