#
# MIT License
#
# Copyright (c) 2023 nbiotcloud
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""Hardware Related Numeric Calculations."""

import math
import typing

from .addrrange import AddrRange


class AlignError(RuntimeError):
    """Alignment Error."""


def unsigned_to_hex(value: int, width: int, prefix: str = "") -> str:
    """
    Convert unsigned `value` to `width` bit hex.

    Example:

    >>> unsigned_to_hex(166, 8)
    'A6'
    >>> unsigned_to_hex(3, 6)
    '03'
    >>> unsigned_to_hex(5, 9)
    '005'
    >>> unsigned_to_hex(26000000, 32)
    '018CBA80'
    >>> unsigned_to_hex(16, 4)
    Traceback (most recent call last):
        ...
    ValueError: 16 is not a unsigned 4 bit integer
    >>> unsigned_to_hex(-1, 4)
    Traceback (most recent call last):
        ...
    ValueError: -1 is not a unsigned 4 bit integer
    >>> unsigned_to_hex(26000000, 32, prefix="{width}'h")
    "32'h018CBA80"
    >>> unsigned_to_hex(248, 8, prefix="0x")
    '0xF8'
    """
    low = 0
    high = (1 << width) - 1
    if value < low or value > high:
        msg = f"{value} is not a unsigned {width} bit integer"
        raise ValueError(msg)
    hexwidth = (width + 3) >> 2
    pfx = prefix.format(value=value, width=width)
    return f"{pfx}{value:0{hexwidth}X}"


def signed_to_hex(value: int, width: int, prefix: str = "") -> str:
    """
    Convert signed `value` to `width` bit hex.

    Example:

    >>> signed_to_hex(15, 8)
    '0F'
    >>> signed_to_hex(-3, 6)
    '3D'
    >>> signed_to_hex(5, 9)
    '005'
    >>> signed_to_hex(-9, 4)
    Traceback (most recent call last):
        ...
    ValueError: -9 is not a signed 4 bit integer
    >>> signed_to_hex(8, 4)
    Traceback (most recent call last):
        ...
    ValueError: 8 is not a signed 4 bit integer
    >>> signed_to_hex(5, 9, prefix="{width}'h")
    "9'h005"
    """
    hexwidth = (width + 3) >> 2
    value = signed_to_unsigned(value, width)
    pfx = prefix.format(value=value, width=width)
    return f"{pfx}{value:0{hexwidth}X}"


def signed_to_unsigned(value: int, width: int) -> int:
    """
    Convert signed `value` to unsigned with `width`.

    Example:

    >>> signed_to_unsigned(3, 4)
    3
    >>> signed_to_unsigned(-3, 4)
    13
    >>> signed_to_unsigned(-3, 8)
    253
    >>> signed_to_unsigned(-9, 4)
    Traceback (most recent call last):
        ...
    ValueError: -9 is not a signed 4 bit integer
    >>> signed_to_unsigned(8, 4)
    Traceback (most recent call last):
        ...
    ValueError: 8 is not a signed 4 bit integer
    """
    high = (1 << (width - 1)) - 1
    low = ~high
    if value < low or value > high:
        msg = f"{value} is not a signed {width} bit integer"
        raise ValueError(msg)
    return (value + (1 << width)) & (~(-1 << width))


def unsigned_to_signed(value: int, width: int) -> int:
    """
    Convert unsigned `value` to signed with `width`.

    Example:

    >>> unsigned_to_signed(3, 4)
    3
    >>> unsigned_to_signed(13, 4)
    -3
    >>> unsigned_to_signed(253, 8)
    -3
    >>> unsigned_to_signed(-9, 4)
    Traceback (most recent call last):
        ...
    ValueError: -9 is not a unsigned 4 bit integer
    """
    low = 0
    high = (1 << width) - 1
    if value < low or value > high:
        msg = f"{value} is not a unsigned {width} bit integer"
        raise ValueError(msg)
    if value & (1 << (width - 1)):  # MSB set->negative
        return value - (1 << width)
    return value


def calc_unsigned_width(value: int) -> int:
    """
    Return width in bits for `value`.

    >>> calc_unsigned_width(3)
    2
    >>> calc_unsigned_width(4)
    3
    >>> calc_unsigned_width(7)
    3
    >>> calc_unsigned_width(8)
    4
    >>> calc_unsigned_width(15)
    4
    >>> calc_unsigned_width(16)
    5
    >>> calc_unsigned_width(8191)
    13
    >>> calc_unsigned_width(0)
    1
    >>> calc_unsigned_width(-5)
    Traceback (most recent call last):
        ...
    AssertionError: Value must be not negative. -5 is not.
    """
    assert value >= 0, f"Value must be not negative. {value!r} is not."
    return (value | 1).bit_length()  # to handle the case value==0


def calc_signed_width(value: int) -> int:
    """
    Return width in bits for `value`.

    >>> calc_signed_width(15)
    5
    >>> calc_signed_width(16)
    6
    >>> calc_signed_width(8191)
    14
    >>> calc_signed_width(-7)
    4
    >>> calc_signed_width(-8)
    4
    >>> calc_signed_width(-9)
    5
    >>> calc_signed_width(0)
    1
    """
    if value < 0:
        value = ~value
    return value.bit_length() + 1


def calc_lowest_bit_set(num: int) -> typing.Optional[int]:
    """
    Return bit number which is not zero.

    Example:

    >>> calc_lowest_bit_set(0xE0)
    5
    >>> calc_lowest_bit_set(-8)
    3
    >>> calc_lowest_bit_set(0)
    """
    if num:
        bit = 0
        # pylint: disable=superfluous-parens
        while not (num & 0x1):
            num >>= 1
            bit += 1
        return bit
    return None


def is_power_of2(value: int) -> int:
    """
    Return `True` if `value` is power of 2.

    >>> is_power_of2(15)
    False
    >>> is_power_of2(16)
    True
    >>> is_power_of2(17)
    False
    >>> is_power_of2(-5)
    Traceback (most recent call last):
        ...
    AssertionError: Value must be larger than zero. -5 is not.
    >>> is_power_of2(0)
    False
    """
    assert value >= 0, f"Value must be larger than zero. {value!r} is not."
    return value > 0 and ((value & (value - 1)) == 0)


def is_power_of(value: int, base: int = 2) -> int:
    """
    Return `True` if `value` is power of `base`.

    >>> is_power_of(15)
    False
    >>> is_power_of(16)
    True
    >>> is_power_of(17)
    False
    >>> is_power_of(-5)
    Traceback (most recent call last):
        ...
    AssertionError: Value must be larger than zero. -5 is not.

    >>> is_power_of(8, base=3)
    False
    >>> is_power_of(9, base=3)
    True
    >>> is_power_of(-9, base=3)
    Traceback (most recent call last):
        ...
    AssertionError: Value must be larger than zero. -9 is not.
    >>> is_power_of(0)
    False
    >>> is_power_of(0, base=6)
    False
    """
    assert value >= 0, f"Value must be larger than zero. {value!r} is not."

    if value == 0:
        return False
    if base == 2:
        return (value & (value - 1)) == 0
    exp = math.log(value, base)
    return exp == int(exp)


def calc_next_power_of2(value: int):
    """
    Return next power of 2.

    The returned value fulfills the rule `2**ceil(log2(value)) >= value`.

    >>> calc_next_power_of2(1)
    2
    >>> calc_next_power_of2(10)
    16
    >>> calc_next_power_of2(16)
    16
    >>> calc_next_power_of2(17)
    32
    >>> calc_next_power_of2(-5)
    Traceback (most recent call last):
        ...
    AssertionError: Value must be positive. -5 is not.
    """
    assert value > 0, f"Value must be positive. {value!r} is not."
    return 1 << calc_unsigned_width(value - 1)


def calc_next_power_of(value: int, base: int = 2):
    """
    Return next power of `base`.

    The returned value fulfills the rule `base**ceil(log_base(value)) >= value`.

    >>> calc_next_power_of(1)
    2
    >>> calc_next_power_of(1, base=5)
    5
    >>> calc_next_power_of(10)
    16
    >>> calc_next_power_of(10, base=3)
    27
    >>> calc_next_power_of(16)
    16
    >>> calc_next_power_of(9, base=3)
    9
    >>> calc_next_power_of(17)
    32
    >>> calc_next_power_of(-5)
    Traceback (most recent call last):
        ...
    AssertionError: Value must be positive. -5 is not.
    """
    assert value > 0, f"Value must be positive. {value!r} is not."
    exp = max(math.ceil(math.log(value, base)), 1)
    return base**exp


def calc_prev_power_of2(value: int):
    """
    Return previous power of `base`.

    The returned value fulfills the rule `2**floor(log2(value))  <= value`.

    >>> calc_prev_power_of2(1)
    1
    >>> calc_prev_power_of2(15)
    8
    >>> calc_prev_power_of2(16)
    16
    >>> calc_prev_power_of2(17)
    16
    >>> calc_prev_power_of2(-5)
    Traceback (most recent call last):
        ...
    AssertionError: Value must be positive. -5 is not.
    """
    assert value > 0, f"Value must be positive. {value!r} is not."
    return 1 << (calc_unsigned_width(value) - 1)


def calc_prev_power_of(value: int, base: int = 2):
    """
    Return previous power of `base`.

    The returned value fulfills the rule `base**exp <= value`.

    >>> calc_prev_power_of(1)
    1
    >>> calc_prev_power_of(1, base=7)
    1
    >>> calc_prev_power_of(15)
    8
    >>> calc_prev_power_of(16)
    16
    >>> calc_prev_power_of(17)
    16
    >>> calc_prev_power_of(10, base=3)
    9
    >>> calc_prev_power_of(27, base=3)
    27
    >>> calc_prev_power_of(-5)
    Traceback (most recent call last):
        ...
    AssertionError: Value must be positive. -5 is not.
    """
    assert value > 0, f"Value must be positive. {value!r} is not."
    exp = math.floor(math.log(value, base))
    return base**exp


# pylint: disable=redefined-outer-name
def align(
    value: int,
    offset: typing.Optional[int] = None,
    align: typing.Optional[int] = None,
    minalign: int = 1,
    rewind=False,
):
    """
    Forward `value` to `offset` and `align` and `minalign`.

    Without `offset` and `align` nothing happens.

    >>> align(5)
    5
    >>> align(7)
    7

    An `offset` forwards the count if necessary or raises an :any:`AlignError`.

    >>> align(5, offset=8)
    8
    >>> align(5, offset=3)
    Traceback (most recent call last):
        ...
    icdutil.num.AlignError: Cannot use offset 3 as we are already at 5

    A `align` forwards the value to the next multiple of `align`.

    >>> align(5, align=4)
    8
    >>> align(8, align=4)
    8
    >>> align(9, align=4)
    12

    A `minalign` without `align` forwards the value to the next multiple of `minalign`

    >>> align(5, minalign=4)
    8
    >>> align(8, minalign=4)
    8
    >>> align(9, minalign=4)
    12

    If both `align` and `minalign` are given, then the value is moved to the next multiple
    of whichever of the both align values is bigger

    >>> align(8, align=5, minalign=4)
    10
    >>> align(8, align=4, minalign=6)
    12

    If `offset` is given it is dominant over both `align` and `minalign`

    >>> align(8, offset=9, align=4, minalign=6)
    9
    """
    if offset is not None:
        if not rewind and value > offset:
            raise AlignError(f"Cannot use offset {offset} as we are already at {value}")
        return offset
    curalign = max(align, minalign) if align is not None else minalign
    misalign = value % curalign
    if misalign:
        value += curalign - misalign
    return value


def bytes2words(bytes_: typing.Sequence[int], bytesperword=4) -> typing.Sequence[int]:
    """
    Convert list of bytes to list of words.

    >>> for word in bytes2words([0x11, 0x22, 0x33, 0x44, 0x55, 0x66]):
    ...    print("0x%X" % word)
    0x44332211
    0x6655
    >>> for word in bytes2words(bytes.fromhex("112233445566")):
    ...    print("0x%X" % word)
    0x44332211
    0x6655

    >>> for word in bytes2words([0x11, 0x22, 0x33, 0x44, 0x55, 0x66], bytesperword=2):
    ...    print("0x%X" % word)
    0x2211
    0x4433
    0x6655

    >>> for word in bytes2words([]):
    ...    print("0x%X" % word)
    """
    words = []
    word = i = 0
    for byte_ in bytes_:
        word += byte_ << (8 * i)
        i += 1
        if i == bytesperword:
            words.append(word)
            word = i = 0
    if i != 0:
        words.append(word)
    return words


def bytes2word(bytes_: typing.Sequence[int]) -> int:
    """
    Convert list of bytes to one word.

    >>> print("0x%X" % bytes2word([0x11, 0x22, 0x33, 0x44, 0x55, 0x66]))
    0x665544332211
    """
    word = 0
    for i, byte_ in enumerate(bytes_):
        word += byte_ << (8 * i)
    return word


def words2bytes(words: typing.Sequence[int], bytesperword: int = 4) -> typing.Sequence[int]:
    """
    Convert list of words to list of bytes.

    >>> for byte_ in words2bytes([0x44332211, 0x6655]):
    ...    print("0x%X" % byte_)
    0x11
    0x22
    0x33
    0x44
    0x55
    0x66
    0x0
    0x0

    >>> for byte_ in words2bytes([0x44332211, 0x6655], bytesperword=6):
    ...    print("0x%X" % byte_)
    0x11
    0x22
    0x33
    0x44
    0x0
    0x0
    0x55
    0x66
    0x0
    0x0
    0x0
    0x0
    """
    bytes_ = []
    for word in words:
        for _ in range(bytesperword):
            byte_ = word & 0xFF
            word >>= 8
            bytes_.append(byte_)
    return bytes_


def convwidth(iterable, srcwidth=32, destwidth=8):
    """
    Convert iterable with values of `srcwidth` to list of values of `destwidth`.

    >>> [hex(i) for i in convwidth([0x04030201, 0x08070605], 32, 16)]
    ['0x201', '0x403', '0x605', '0x807']
    >>> [hex(i) for i in convwidth([0x0807060504030201], 64, 16)]
    ['0x201', '0x403', '0x605', '0x807']
    >>> [hex(i) for i in convwidth([0x0807060504030201], 64, 8)]
    ['0x1', '0x2', '0x3', '0x4', '0x5', '0x6', '0x7', '0x8']
    >>> [hex(i) for i in convwidth([], 32, 16)]
    []

    >>> [hex(i) for i in convwidth([0x201, 0x403, 0x605, 0x807], 16, 32)]
    ['0x4030201', '0x8070605']
    >>> [hex(i) for i in convwidth([0x201, 0x403, 0x605, 0x807], 16, 64)]
    ['0x807060504030201']
    >>> [hex(i) for i in convwidth([0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8], 8, 64)]
    ['0x807060504030201']
    >>> [hex(i) for i in convwidth([0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8], 8, 56)]
    ['0x7060504030201', '0x8']
    >>> [hex(i) for i in convwidth([], 16, 32)]
    []

    >>> [hex(i) for i in convwidth([0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8], 8, 8)]
    ['0x1', '0x2', '0x3', '0x4', '0x5', '0x6', '0x7', '0x8']
    """
    if srcwidth > destwidth:
        # wider to smaller
        assert (srcwidth % destwidth) == 0
        mask = (1 << destwidth) - 1
        iterations = srcwidth // destwidth
        for item in iterable:
            for _ in range(iterations):
                yield item & mask
                item >>= destwidth
            assert item == 0
    elif srcwidth < destwidth:
        # smaller to wider
        assert (destwidth % srcwidth) == 0
        dest = i = 0
        for item in iterable:
            dest += item << i
            i += srcwidth
            if i == destwidth:
                yield dest
                dest = i = 0
        if i != 0:
            yield dest
    else:
        yield from iterable


def to_mask(addrwidth: int, baseaddr: int, exp: int, dontcare="?") -> str:
    """
    Convert address range starting at `baseaddr` with 2**`exp` elements to mask with `addrwidth`
    using the `dontcare` character as mask bits.

    >>> to_mask(16, 0x4000, 6)
    '0100000000??????'
    >>> to_mask(16, 0x6000, 4, 'x')
    '011000000000xxxx'
    >>> to_mask(16, 0x4004, 6)
    Traceback (most recent call last):
        ...
    AssertionError: 6 LSBs of '0100000000000100' shall be '000000', not '000100'
    """
    base = bin(baseaddr)[2:].zfill(addrwidth)
    if exp:
        zeros = "0" * exp
        lsbs = base[-exp:]
        assert lsbs == zeros, f"{exp} LSBs of {base!r} shall be {zeros!r}, not {lsbs!r}"
    if exp:
        return base[:-exp] + dontcare * exp
    return base


def _iter_powerof2_segs(baseaddr: int, size: int) -> typing.Generator[typing.Tuple[int, int], None, None]:
    """
    Split region between at `baseaddr` and `baseaddr+size-1` into segments with maximum powers of 2.

    >>> for segm, bits in _iter_powerof2_segs(0x53, 0x80):
    ...     print(f"{hex(segm)}, {1<<bits}")
    0x53, 1
    0x54, 4
    0x58, 8
    0x60, 32
    0x80, 64
    0xc0, 16
    0xd0, 2
    0xd2, 1

    >>> for segm, bits in _iter_powerof2_segs(0x100, 0x80):
    ...     print(f"{hex(segm)}, {1<<bits}")
    0x100, 128

    >>> for segm, bits in _iter_powerof2_segs(0x140, 0x80):
    ...     print(f"{hex(segm)}, {1<<bits}")
    0x140, 64
    0x180, 64

    >>> for segm, bits in _iter_powerof2_segs(0x0, 0x27):
    ...     print(f"{hex(segm)}, {1<<bits}")
    0x0, 32
    0x20, 4
    0x24, 2
    0x26, 1
    """
    endaddr = baseaddr + size - 1
    # search largest chunk fitting aligned into window of size
    bits = 0
    for bits in reversed(range(size.bit_length())):
        csize = 1 << bits
        cbase = align(baseaddr, align=csize)
        cend = cbase + csize - 1
        if bits and cend <= endaddr:
            break
    # before chunk
    if baseaddr < cbase:
        yield from _iter_powerof2_segs(baseaddr, (cbase - baseaddr))
    # chunk
    yield cbase, bits
    # after chunk
    if cend < endaddr:
        yield from _iter_powerof2_segs(cend + 1, (endaddr - cend))


def calc_addrwinmasks(baseaddr, size, addrwidth=32, dontcare="?") -> typing.Tuple[str, ...]:
    """
    Return tuple of binary compare wildcard masks for address window of `size` starting at `baseaddr`.

    Args:
        baseaddr (int): Address window start addresss
        size (int):     Address window size

    Keyword Args:
        addrwidth:      Address width in bits
        dontcare:       Character used for don't care bits

    Example:

    >>> calc_addrwinmasks(0, 1, addrwidth=4)
    ('0000',)
    >>> calc_addrwinmasks(0xF000, 0x10, addrwidth=16)
    ('111100000000????',)
    >>> calc_addrwinmasks(0xF000, 0x180, addrwidth=16, dontcare='x')
    ('11110000xxxxxxxx', '111100010xxxxxxx')
    >>> calc_addrwinmasks(0xEFF0, 0x100, addrwidth=16)
    ('111011111111????', '111100000???????', '1111000010??????', '11110000110?????', '111100001110????')
    """
    assert len(dontcare) == 1, f"dontcare '{dontcare}' shall have length of 1"
    return tuple(to_mask(addrwidth, base, exp, dontcare) for base, exp in _iter_powerof2_segs(baseaddr, size))


def _iter_aligned_segs(baseaddr: int, size: int) -> typing.Generator[AddrRange, None, None]:
    endaddr = baseaddr + size - 1
    # search largest chunk fitting aligned into window of size
    sizeup = calc_next_power_of2(size)
    baseup = align(baseaddr, align=sizeup)
    end = baseup + size - 1
    while end > endaddr:
        sizeup //= 2
        size = sizeup
        baseup = align(baseaddr, align=sizeup)
        end = baseup + size - 1
    assert baseaddr <= baseup
    # before chunk
    pre_size = baseup - baseaddr
    if pre_size > 0:
        yield from _iter_aligned_segs(baseaddr, pre_size)
    # chunk
    yield AddrRange(baseup, size)
    # after chunk
    post_size = endaddr - end
    if post_size > 0:
        yield from _iter_aligned_segs(end + 1, post_size)


def split_aligned_segs(baseaddr: int, size: int) -> typing.Tuple[AddrRange, ...]:
    """
    Split address window starting at `baseaddr` with `size` into segments with aligned base addresses.

    The base addresses of the segments are aligned to `calc_next_power_of2(size)`.

    Returns tuple of :any:`AddrRange`. Segment starting at `baseaddr` with `size`.

    Args:
        baseaddr (int): Address window start addresss
        size (int):     Address window size

    Example:

    >>> split_aligned_segs(0, 1)
    (AddrRange(0x0, '1 byte'),)
    >>> split_aligned_segs(1024, 16)
    (AddrRange(0x400, '16 bytes'),)
    >>> split_aligned_segs(1024, 1024)
    (AddrRange(0x400, '1 KB'),)
    >>> split_aligned_segs(1024, 1024+768)
    (AddrRange(0x400, '1 KB'), AddrRange(0x800, '768 bytes'))
    >>> split_aligned_segs(256, 1024+768)
    (AddrRange(0x100, '256 bytes'), AddrRange(0x200, '512 bytes'), AddrRange(0x400, '1 KB'))
    >>> split_aligned_segs(1000, 1024)  # doctest: +ELLIPSIS
    (AddrRange(0x3E8, '8 bytes'), AddrRange(0x3F0, '16 bytes'), AddrRange(0x400, '512 bytes'), ...(0x600, '488 bytes'))
    """
    return tuple(_iter_aligned_segs(baseaddr, size))
