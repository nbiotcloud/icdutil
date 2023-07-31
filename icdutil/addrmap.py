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

"""Address Map."""

import typing

from attrs import field, frozen
from humannum import Bytes, Hex
from tabulate import tabulate

from .addrrange import AddrRange
from .num import calc_lowest_bit_set, calc_unsigned_width
from .slices import Slice


@frozen(repr=False)
class AddrMap:
    """
    Address Map.

    Keyword Args:
        addrwidth (int):          Address width. Calculated automatically.
        is_sub (bool):            Handle sub addresses only. Just the minimum number of address
                                  bits is evaluated.
        # default (object):         Default item, returned on unallocated address ranges.
        allow_overlapping (bool): Allow overlapping address ranges.

    >>> a = AddrMap()
    >>> a
    AddrMap()
    >>> a.add('T', size=0x400)
    AddrRange('T', 0x0, '1 KB')
    >>> a.add('A', 0x5000, 0x1000)
    AddrRange('A', 0x5000, '4 KB')
    >>> a.add('B', 0x2000, 0x1000)
    AddrRange('B', 0x2000, '4 KB')
    >>> a.add('C', 0xD000, 0x800)
    AddrRange('C', 0xD000, '2 KB')
    >>> a.add('Z', size=0x1000)
    AddrRange('Z', 0xE000, '4 KB')
    >>> a.add('X', 0xF0800000, 1024*1024*3)
    AddrRange('X', 0xF0800000, '3 MB')

    Addresses can be used only once:

    >>> a.add('D', 0xE400, 0x0400)
    Traceback (most recent call last):
        ...
    icdutil.addrmap.Conflict: AddrRange('D', 0xE400, '1 KB'): overlaps with AddrRange('Z', 0xE000, '4 KB').
    >>> a.add('D', 0x2000)
    Traceback (most recent call last):
        ...
    icdutil.addrmap.Conflict: AddrRange('D', 0x2000, '1 byte'): overlaps with AddrRange('B', 0x2000, '4 KB').
    >>> a.add('D', 0x2000, '8 KB')
    Traceback (most recent call last):
        ...
    icdutil.addrmap.Conflict: AddrRange('D', 0x2000, '8 KB'): overlaps with AddrRange('B', 0x2000, '4 KB').
    >>> a.add('D', 0x1800, '4 KB')
    Traceback (most recent call last):
        ...
    icdutil.addrmap.Conflict: AddrRange('D', 0x1800, '4 KB'): overlaps with AddrRange('B', 0x2000, '4 KB').

    An iteration will serve :class:`AddrRange` objects sorted by baseaddr:

    >>> for addrrange in a:
    ...     addrrange
    AddrRange('T', 0x0, '1 KB')
    AddrRange('B', 0x2000, '4 KB')
    AddrRange('A', 0x5000, '4 KB')
    AddrRange('C', 0xD000, '2 KB')
    AddrRange('Z', 0xE000, '4 KB')
    AddrRange('X', 0xF0800000, '3 MB')

    The size is defined by the numer of entries:

    >>> len(a)
    6

    By using a `default` the gaps are filled with this item:

    >>> for addrrange in a.get(default='d'):
    ...     addrrange
    AddrRange('T', 0x0, '1 KB')
    AddrRange('d', 0x400, '7 KB')
    AddrRange('B', 0x2000, '4 KB')
    AddrRange('d', 0x3000, '8 KB')
    AddrRange('A', 0x5000, '4 KB')
    AddrRange('d', 0x6000, '28 KB')
    AddrRange('C', 0xD000, '2 KB')
    AddrRange('d', 0xD800, '2 KB')
    AddrRange('Z', 0xE000, '4 KB')
    AddrRange('d', 0xF000, '3.76 GB')
    AddrRange('X', 0xF0800000, '3 MB')
    AddrRange('d', 0xF0B00000, '245 MB')
    >>> len(tuple(a.get('d')))
    12

    The `is_sub` attribute defines the address range defaults:

    >>> b = AddrMap(addrwidth=32, is_sub=True)
    >>> b
    AddrMap(addrwidth=32, is_sub=True)
    >>> b.add('T', size=0x400)
    AddrRange('T', 0x00000000, '1 KB', addrwidth=32, is_sub=True)
    >>> b.add('A', 0x5000, 0x1000)
    AddrRange('A', 0x00005000, '4 KB', addrwidth=32, is_sub=True)
    >>> b.add('B', 0x2000, 0x1000)
    AddrRange('B', 0x00002000, '4 KB', addrwidth=32, is_sub=True)
    >>> b.add('C', 0xD000, 0x800)
    AddrRange('C', 0x0000D000, '2 KB', addrwidth=32, is_sub=True)
    >>> b.add('Z', size=0x1000)
    AddrRange('Z', 0x0000E000, '4 KB', addrwidth=32, is_sub=True)
    >>> b.add('X', 0xF0800000, 1024*1024*3, is_sub=False)
    AddrRange('X', 0xF0800000, '3 MB', addrwidth=32)
    >>> for addrrange in b:
    ...     addrrange
    AddrRange('T', 0x00000000, '1 KB', addrwidth=32, is_sub=True)
    AddrRange('B', 0x00002000, '4 KB', addrwidth=32, is_sub=True)
    AddrRange('A', 0x00005000, '4 KB', addrwidth=32, is_sub=True)
    AddrRange('C', 0x0000D000, '2 KB', addrwidth=32, is_sub=True)
    AddrRange('Z', 0x0000E000, '4 KB', addrwidth=32, is_sub=True)
    AddrRange('X', 0xF0800000, '3 MB', addrwidth=32)

    The `allow_overlapping` attibute allows address ranges to intersect.

    >>> c = AddrMap(allow_overlapping=True)
    >>> c
    AddrMap(allow_overlapping=True)
    >>> c.add('L', size=0x1000)
    AddrRange('L', 0x0, '4 KB')
    >>> c.add('R', 0x400, size=0x1000)
    AddrRange('R', 0x400, '4 KB')
    >>> c.add('M', 0x200, '2 KB')
    AddrRange('M', 0x200, '2 KB')
    >>> for addrrange in c:
    ...     addrrange
    AddrRange('L', 0x0, '4 KB')
    AddrRange('M', 0x200, '2 KB')
    AddrRange('R', 0x400, '4 KB')
    """

    addrwidth: typing.Optional[int] = field(default=None)
    is_sub: bool = field(default=False)
    allow_overlapping: bool = field(default=False)
    __addrranges: list = field(factory=list)

    def __repr__(self):
        opt_kw = []
        if self.addrwidth:
            opt_kw.append(f"addrwidth={self.addrwidth}")
        if self.is_sub:
            opt_kw.append("is_sub=True")
        if self.allow_overlapping:
            opt_kw.append("allow_overlapping=True")
        return f"AddrMap({', '.join(opt_kw)})"

    def __iter__(self):
        yield from self.__addrranges

    def __len__(self):
        return len(tuple(self.__addrranges))

    @property
    def firstaddr(self) -> typing.Optional[int]:
        """
        First used address.

        >>> a = AddrMap()
        >>> a.firstaddr
        >>> a.add('A', 0x5000, '4 KB')
        AddrRange('A', 0x5000, '4 KB')
        >>> a.firstaddr
        Hex('0x5000')
        >>> a.add('B', 0x2000, '4 KB')
        AddrRange('B', 0x2000, '4 KB')
        >>> a.firstaddr
        Hex('0x2000')
        """
        try:
            return self.__addrranges[0].baseaddr
        except IndexError:
            return None

    @property
    def lastaddr(self) -> typing.Optional[int]:
        """Last used address."""
        try:
            return self.__addrranges[-1].endaddr
        except IndexError:
            return None

    @property
    def addrspace(self) -> typing.Optional[int]:
        """
        Allocated Address space.

        >>> a = AddrMap()
        >>> a.addrspace
        >>> a.add('A', 0x5000, '4 KB')
        AddrRange('A', 0x5000, '4 KB')
        >>> str(a.addrspace)
        '0x1000'
        >>> a.add('B', 0x2000, '4 KB')
        AddrRange('B', 0x2000, '4 KB')
        >>> str(a.addrspace)
        '0x4000'
        >>> a.add('C', 0x7000, 13)
        AddrRange('C', 0x7000, '13 bytes')
        >>> str(a.addrspace)
        '0x500D'
        """
        try:
            return self.__addrranges[-1].endaddr + 1 - self.__addrranges[0].baseaddr
        except IndexError:
            return None

    @property
    def eff_addrwidth(self) -> typing.Optional[int]:
        """
        Effective Address Width.

        Return address width, either explicitly set or calculated from existing entries.

        >>> a = AddrMap()
        >>> a.eff_addrwidth
        >>> a.add('A', 0x5000, '4 KB')
        AddrRange('A', 0x5000, '4 KB')
        >>> a.eff_addrwidth
        15
        >>> a = AddrMap(addrwidth=16)
        >>> a.eff_addrwidth
        16
        >>> a.add('A', 2**18, '4 KB')
        Traceback (most recent call last):
            ...
        RuntimeError: AddrRange('A', 0x40000, '4 KB', addrwidth=16): exceeds maximum address range of 0x10000.
        """
        eff_addrwidth = self.addrwidth
        if eff_addrwidth is None:
            lastaddr = self.lastaddr
            if lastaddr is None:
                eff_addrwidth = None
            else:
                eff_addrwidth = calc_unsigned_width(lastaddr)
        return eff_addrwidth

    @property
    def decode_lsb(self) -> typing.Optional[int]:
        """
        Address decoding LSB (counted from 0).

        >>> a = AddrMap()
        >>> a.decode_lsb is None
        True
        >>> a.add('A', 0x2000, '8 KB')
        AddrRange('A', 0x2000, '8 KB')
        >>> a.decode_lsb
        13
        >>> a.add('B', 0x5000, '1 KB')
        AddrRange('B', 0x5000, '1 KB')
        >>> a.decode_lsb
        10
        >>> a.add('C', 0x6000, '2 KB')
        AddrRange('C', 0x6000, '2 KB')
        >>> a.decode_lsb
        10
        """
        addrranges = self.__addrranges
        if addrranges:
            minsize = int(min(addrrange.size for addrrange in addrranges))
            return calc_lowest_bit_set(minsize)
        return None

    @property
    def decode_msb(self) -> typing.Optional[int]:
        """
        Address decoding MSB (counted from 0).

        >>> a = AddrMap(addrwidth=32)
        >>> a.is_sub
        False
        >>> a.decode_msb
        31
        >>> a.add('A', 0x5000, '4 KB')
        AddrRange('A', 0x00005000, '4 KB', addrwidth=32)
        >>> a.decode_msb
        31

        >>> a = AddrMap(is_sub=True)
        >>> a.is_sub
        True
        >>> a.decode_msb is None
        True
        >>> a.add('A', 0x1000, '1 KB')
        AddrRange('A', 0x1000, '1 KB', is_sub=True)
        >>> a.decode_msb
        12
        >>> a.add('B', 0x2000, '8 KB')
        AddrRange('B', 0x2000, '8 KB', is_sub=True)
        >>> a.decode_msb
        13
        >>> a.add('C', 0x4000, 1)
        AddrRange('C', 0x4000, '1 byte', is_sub=True)
        >>> a.decode_msb
        14
        """
        eff_addrwidth = self.eff_addrwidth
        if eff_addrwidth:
            return eff_addrwidth - 1
        return None

    @property
    def decode_slice(self):
        """
        Address Slice.

        >>> a = AddrMap()
        >>> a.decode_slice is None
        True
        >>> a.add('A', 0x1000, '4 KB')
        AddrRange('A', 0x1000, '4 KB')
        >>> a.decode_slice
        Slice('12')
        >>> a.add('B', 0x3000, '8 KB')
        AddrRange('B', 0x3000, '8 KB')
        >>> a.decode_slice
        Slice('14:12')
        """
        if not self.__addrranges:
            return None
        return Slice(left=self.decode_msb, right=self.decode_lsb)

    @property
    def is_full(self):
        """
        Return if entire address map range is covered.

        >>> a = AddrMap()
        >>> a.is_full is None
        True
        >>> a.add('A', size='8 KB')
        AddrRange('A', 0x0, '8 KB')
        >>> a.is_full
        True
        >>> a.add('B', size='4 KB')
        AddrRange('B', 0x2000, '4 KB')
        >>> a.is_full
        False
        >>> a.add('C', size='4 KB')
        AddrRange('C', 0x3000, '4 KB')
        >>> a.is_full
        True

        >>> b = AddrMap(addrwidth=13)
        >>> b.is_full is None
        True
        >>> b.add('A', 0x0, size='6 KB')
        AddrRange('A', 0x0000, '6 KB', addrwidth=13)
        >>> b.is_full
        False
        >>> b.add('B', size='2 KB')
        AddrRange('B', 0x1800, '2 KB', addrwidth=13)
        >>> b.is_full
        True
        """
        if not self.__addrranges:
            return None
        used = sum(addrrange.size for addrrange in self.__addrranges)
        return used == 1 << self.eff_addrwidth

    def __add(self, addrrange: AddrRange) -> None:
        """Insert new AddrRange into AddrMap."""

        addrranges = self.__addrranges
        baseaddr = addrrange.baseaddr

        # address space check
        addrwidth = self.addrwidth
        if addrwidth is not None:
            addrspace = 1 << addrwidth
            if addrrange.endaddr >= addrspace:
                raise RuntimeError(f"{addrrange!r}: exceeds maximum address range of 0x{addrspace:X}.")

        # add at proper position
        for pos, item in enumerate(addrranges):
            if item.baseaddr > baseaddr:
                break
        else:
            pos = len(addrranges)

        # check neighbors for overlap
        if not self.allow_overlapping:
            # lower
            try:
                lower = addrranges[pos - 1]
            except IndexError:
                pass
            else:
                if addrrange.is_overlapping(lower):
                    raise Conflict(addrrange, lower)
            # upper
            try:
                upper = addrranges[pos]
            except IndexError:
                pass
            else:
                if addrrange.is_overlapping(upper):
                    raise Conflict(addrrange, upper)
        self.__addrranges.insert(pos, addrrange)

    def __get(self, default):
        last = 0
        if default is None:
            yield from self.__addrranges
        else:
            for addrrange in self.__addrranges:
                baseaddr = addrrange.baseaddr
                if last < baseaddr:
                    yield AddrRange(baseaddr=last, size=baseaddr - last, addrwidth=self.addrwidth, item=default)
                yield addrrange
                last = addrrange.endaddr + 1
            eff_addrwidth = self.eff_addrwidth
            if eff_addrwidth:
                end = 1 << eff_addrwidth
                if last < end:
                    yield AddrRange(baseaddr=last, size=end - last, addrwidth=self.addrwidth, item=default)

    def __new(self, addrranges: typing.List[AddrRange]) -> "AddrMap":
        addrmap = AddrMap(addrwidth=self.addrwidth, is_sub=self.is_sub)
        addrranges = addrranges or []
        addrmap.cp_addrranges(addrranges)
        return addrmap

    def __cut(self, addrrange) -> typing.List[AddrRange]:
        addrranges = self.__addrranges
        idxs = []
        cuts = []
        for idx, cut in enumerate(addrranges):
            if cut.is_overlapping(addrrange):
                idxs.append(idx)
                cuts.append(cut)

        if idxs:
            first = cuts[0]
            last = cuts[-1]
            lastaddr = self.lastaddr
            # remove
            for idx in reversed(idxs):
                addrranges.pop(idx)
            # re-add left overlap
            if addrrange.baseaddr:
                left = first.get_difference(addrrange)
                if left:
                    self.__add(left[0])
            # re-add right overlap
            if lastaddr > addrrange.endaddr:
                right = last.get_difference(addrrange)
                if right:
                    self.__add(right[0])
            # shrink cuts
            cuts[0] = first.get_intersect(addrrange)
            if first is not last:
                cuts[-1] = last.get_intersect(addrrange)
        return cuts

    def __match(self, addrrange: "AddrRange"):
        return [a for a in self if a.is_overlapping(addrrange)]

    @staticmethod
    def _align(addr, align):
        addr = int(addr)
        misalign = addr % align
        if misalign:
            addr += align - misalign
        return Hex(addr)

    def _find_space(self, size, align, start=0):
        addr = start = self._align(start, align)
        for item in self.__addrranges:
            if item.endaddr < start:
                # skip all before start
                addr = max(self._align(item.nextaddr, align), addr)
                continue
            if item.baseaddr >= (addr + size):
                break
            addr = self._align(item.nextaddr, align)
        return addr

    def _check_end(self, addr, size):
        if self.addrwidth is not None:
            addrspace = 1 << self.addrwidth
            if addr >= addrspace or addr + size > addrspace:
                raise ValueError(
                    f"No space left in address map ({Bytes(addrspace)}) for new range at {addr} with size of {size}"
                )

    def cp_addrranges(self, addranges: typing.List[AddrRange]) -> None:
        """Copy address ranges from `other` AddrMap."""
        for addrrange in addranges:
            self.__add(addrrange)

    # pylint: disable=too-many-arguments
    def add(
        self,
        item,
        baseaddr: typing.Optional[int] = None,
        size: int = 1,
        is_sub: typing.Optional[bool] = None,
        align: typing.Optional[int] = None,
        startsearch: typing.Optional[int] = None,
    ) -> AddrRange:
        """
        Add `item` for address decoding.

        Args:
            item: any object managed by this address decoder

        Keyword Args:
            baseaddr: Base address. Behind last item by default.
            size:     Size in bytes
            is_sub:   Overwrite sub address attribute.
            align:    Alignment
            startsearch: Search of free address at given number (if `baseaddr` is `None`)

        >>> a = AddrMap()
        >>> a.add('A', baseaddr=0x3000, size='4 KB')
        AddrRange('A', 0x3000, '4 KB')
        >>> a.add('B', 0x1000, '1 KB', is_sub=True)
        AddrRange('B', 0x1000, '1 KB', is_sub=True)
        >>> a.add('C', 0x4500, '4 KB', align=0x1000)
        AddrRange('C', 0x5000, '4 KB')
        """
        ba_ = baseaddr or self.get_free_baseaddr(size, align=align, start=startsearch)
        if align is not None:
            ba_ = self._align(ba_, align)
        if is_sub is None:
            is_sub = self.is_sub
        addrrange = AddrRange(baseaddr=ba_, size=size, addrwidth=self.addrwidth, item=item, is_sub=is_sub)
        self.__add(addrrange)
        return addrrange

    def get_free_baseaddr(self, size: int, align=None, start=None) -> int:
        """
        Return baseaddress of free window with `size`.

        Args:
            size: Window Size

        Keyword Args:
            align: Alignment, default aligned to size
            start: Start search behind given address

        >>> a = AddrMap(is_sub=True, addrwidth=16)
        >>> a.get_free_baseaddr(0x10, start=0x0)
        Hex('0x0')
        >>> a.add('A', 0x1000, '1 KB')
        AddrRange('A', 0x1000, '1 KB', addrwidth=16, is_sub=True)
        >>> a.get_free_baseaddr(0x400)
        Hex('0x1400')
        >>> a.get_free_baseaddr('4 KB')
        Hex('0x2000')
        >>> a.get_free_baseaddr('8 KB', align=0x4000)
        Hex('0x4000')
        >>> a.get_free_baseaddr('1 KB', start=0x400)
        Hex('0x400')
        >>> a.get_free_baseaddr('1 KB', start=0x4000)
        Hex('0x4000')
        >>> a.add('B', 0x3000, '4 KB')
        AddrRange('B', 0x3000, '4 KB', addrwidth=16, is_sub=True)
        >>> a.get_free_baseaddr('4 KB', start=0x2800)
        Hex('0x4000')

        If the AddrMap has `addrwidth` set, a check for end range overflow is executed

        >>> a.get_free_baseaddr('8 KB', start=0xF0000)
        Traceback (most recent call last):
            ...
        ValueError: No space left in address map (64 KB) for new range at 0xF0000 with size of 8 KB
        >>> a.get_free_baseaddr('8 KB', align=0x1000, start=0xF000)
        Traceback (most recent call last):
            ...
        ValueError: No space left in address map (64 KB) for new range at 0xF000 with size of 8 KB
        """
        size = Bytes(size)
        if align is None:
            align = size
        if start is None:
            addr = self.lastaddr or 0
            if addr:
                addr += 1
            addr = self._align(addr, align)
        else:
            addr = self._find_space(size, align, start=start)
        self._check_end(addr, size)
        return addr

    def get(self, default=None):
        """
        Return all :any:`AddrRange` items and fill gaps with `default`.

        >>> a = AddrMap()
        >>> a.add('T', size=0x400)
        AddrRange('T', 0x0, '1 KB')
        >>> a.add('A', 0x5000, 0x1000)
        AddrRange('A', 0x5000, '4 KB')
        >>> a.add('B', 0x2000, 0x1000)
        AddrRange('B', 0x2000, '4 KB')
        >>> a.add('C', 0xD000, '2 KB')
        AddrRange('C', 0xD000, '2 KB')
        >>> a.add('Z', size=0x2000)
        AddrRange('Z', 0xE000, '8 KB')

        >>> for addrrange in a.get():
        ...     addrrange
        AddrRange('T', 0x0, '1 KB')
        AddrRange('B', 0x2000, '4 KB')
        AddrRange('A', 0x5000, '4 KB')
        AddrRange('C', 0xD000, '2 KB')
        AddrRange('Z', 0xE000, '8 KB')

        >>> for addrrange in a.get(default='reserved'):
        ...     addrrange
        AddrRange('T', 0x0, '1 KB')
        AddrRange('reserved', 0x400, '7 KB')
        AddrRange('B', 0x2000, '4 KB')
        AddrRange('reserved', 0x3000, '8 KB')
        AddrRange('A', 0x5000, '4 KB')
        AddrRange('reserved', 0x6000, '28 KB')
        AddrRange('C', 0xD000, '2 KB')
        AddrRange('reserved', 0xD800, '2 KB')
        AddrRange('Z', 0xE000, '8 KB')

        Empty:

        >>> a = AddrMap()
        >>> list(a.get())
        []
        >>> list(a.get(default="<default>"))
        []
        >>> a = AddrMap(addrwidth=16)
        >>> list(a.get(default="<default>"))
        [AddrRange('<default>', 0x0000, '64 KB', addrwidth=16)]

        Default items before and after real AddrRange:

        >>> a.add('A', 0x5000, 0x1000)
        AddrRange('A', 0x5000, '4 KB', addrwidth=16)
        >>> for addrrange in a.get(default='reserved'):
        ...     addrrange
        AddrRange('reserved', 0x0000, '20 KB', addrwidth=16)
        AddrRange('A', 0x5000, '4 KB', addrwidth=16)
        AddrRange('reserved', 0x6000, '40 KB', addrwidth=16)

        >>> a.add('Z', 0xE000, size=0x2000)
        AddrRange('Z', 0xE000, '8 KB', addrwidth=16)
        >>> for addrrange in a.get(default='reserved'):
        ...     addrrange
        AddrRange('reserved', 0x0000, '20 KB', addrwidth=16)
        AddrRange('A', 0x5000, '4 KB', addrwidth=16)
        AddrRange('reserved', 0x6000, '32 KB', addrwidth=16)
        AddrRange('Z', 0xE000, '8 KB', addrwidth=16)
        """
        return self.__get(default)

    def cut(self, baseaddr, size=1) -> "AddrMap":
        """
        Cut out address range from `baseaddr` for `size`.

        Return address map with cut address ranges.

        >>> a = AddrMap()
        >>> a.add('A', 0x0000, 0x1000)
        AddrRange('A', 0x0, '4 KB')
        >>> a.add('B', 0x1000, 0x1000)
        AddrRange('B', 0x1000, '4 KB')
        >>> a.add('C', 0x2000, 0x1000)
        AddrRange('C', 0x2000, '4 KB')
        >>> a.add('D', 0x3000, 0x1000)
        AddrRange('D', 0x3000, '4 KB')
        >>> print(a.get_overview())
        Baseaddr    Size           Sub    Item
        ----------  -------------  -----  ------
        0x0         0x1000 (4 KB)  No     'A'
        0x1000      0x1000 (4 KB)  No     'B'
        0x2000      0x1000 (4 KB)  No     'C'
        0x3000      0x1000 (4 KB)  No     'D'

        Cut multiple address ranges

        >>> c = a.cut(0x1800, 0x1000)
        >>> print(a.get_overview())
        Baseaddr    Size           Sub    Item
        ----------  -------------  -----  ------
        0x0         0x1000 (4 KB)  No     'A'
        0x1000      0x800 (2 KB)   No     'B'
        0x2800      0x800 (2 KB)   No     'C'
        0x3000      0x1000 (4 KB)  No     'D'
        >>> print(c.get_overview())
        Baseaddr    Size          Sub    Item
        ----------  ------------  -----  ------
        0x1800      0x800 (2 KB)  No     'B'
        0x2000      0x800 (2 KB)  No     'C'

        Cut at the front

        >>> c = a.cut(0, 0x1000)
        >>> print(a.get_overview())
        Baseaddr    Size           Sub    Item
        ----------  -------------  -----  ------
        0x1000      0x800 (2 KB)   No     'B'
        0x2800      0x800 (2 KB)   No     'C'
        0x3000      0x1000 (4 KB)  No     'D'
        >>> print(c.get_overview())
        Baseaddr    Size           Sub    Item
        ----------  -------------  -----  ------
        0x0         0x1000 (4 KB)  No     'A'

        Cut at the end

        >>> c = a.cut(0x3C00, 0x1000)
        >>> print(a.get_overview())
        Baseaddr    Size          Sub    Item
        ----------  ------------  -----  ------
        0x1000      0x800 (2 KB)  No     'B'
        0x2800      0x800 (2 KB)  No     'C'
        0x3000      0xC00 (3 KB)  No     'D'
        >>> print(c.get_overview())
        Baseaddr    Size          Sub    Item
        ----------  ------------  -----  ------
        0x3C00      0x400 (1 KB)  No     'D'

        Cut exactly one

        >>> c = a.cut(0x2800, '2 KB')
        >>> print(a.get_overview())
        Baseaddr    Size          Sub    Item
        ----------  ------------  -----  ------
        0x1000      0x800 (2 KB)  No     'B'
        0x3000      0xC00 (3 KB)  No     'D'
        >>> print(c.get_overview())
        Baseaddr    Size          Sub    Item
        ----------  ------------  -----  ------
        0x2800      0x800 (2 KB)  No     'C'

        Cut nothing

        >>> c = a.cut(0x2000, 0x100)
        >>> print(a.get_overview())
        Baseaddr    Size          Sub    Item
        ----------  ------------  -----  ------
        0x1000      0x800 (2 KB)  No     'B'
        0x3000      0xC00 (3 KB)  No     'D'
        >>> print(c.get_overview())
        Baseaddr    Size      Sub    Item
        ----------  --------  -----  ------
        """
        addrrange = AddrRange(baseaddr=baseaddr, size=size, addrwidth=self.addrwidth)
        return self.__new(self.__cut(addrrange))

    def lookup(self, addr: int):
        """
        Lookup address range by `addr`.

        >>> a = AddrMap()
        >>> a.add('A', 0x5000, 0x1000)
        AddrRange('A', 0x5000, '4 KB')
        >>> a.add('B', 0x2000, 0x1000)
        AddrRange('B', 0x2000, '4 KB')
        >>> a.add('C', 0xD000, 0x800)
        AddrRange('C', 0xD000, '2 KB')

        >>> a.lookup(0x2000)
        AddrRange('B', 0x2000, '4 KB')
        >>> a.lookup(0x2FFF)
        AddrRange('B', 0x2000, '4 KB')
        >>> a.lookup(0x3000)
        """
        for addrrange in self:
            if addr in addrrange:
                return addrrange
        return None

    def match(self, baseaddr: int, size: int = 1) -> "AddrMap":
        """
        Return address map with address ranges intersecting with range from `baseaddr` for `size`.

        >>> a = AddrMap()
        >>> a.add('A', 0x1000, 0x1000)
        AddrRange('A', 0x1000, '4 KB')
        >>> a.add('B', 0x2000, 0x1000)
        AddrRange('B', 0x2000, '4 KB')
        >>> a.add('C', 0x3000, 0x800)
        AddrRange('C', 0x3000, '2 KB')
        >>> m = a.match(0x1800, 0x1000)
        >>> m
        AddrMap()
        >>> list(m)
        [AddrRange('A', 0x1000, '4 KB'), AddrRange('B', 0x2000, '4 KB')]
        """
        addrrange = AddrRange(baseaddr, size=size, addrwidth=self.addrwidth)
        return self.__new(self.__match(addrrange))

    def match_addrrange(self, addrrange: "AddrRange") -> "AddrMap":
        """
        Return address map with address ranges intersecting with range from `baseaddr` for `size`.

        >>> a = AddrMap()
        >>> a.add('A', 0x1000, 0x1000)
        AddrRange('A', 0x1000, '4 KB')
        >>> a.add('B', 0x2000, 0x1000)
        AddrRange('B', 0x2000, '4 KB')
        >>> a.add('C', 0x3000, 0x800)
        AddrRange('C', 0x3000, '2 KB')
        >>> m = a.match_addrrange(AddrRange(0x1800, 0x1000))
        >>> m
        AddrMap()
        >>> list(m)
        [AddrRange('A', 0x1000, '4 KB'), AddrRange('B', 0x2000, '4 KB')]
        """
        return self.__new(self.__match(addrrange))

    def find(self, item) -> "AddrMap":
        """
        Return address map with address ranges containing `item`.

        >>> a = AddrMap()
        >>> a.add('A', 0x5000, 0x1000)
        AddrRange('A', 0x5000, '4 KB')
        >>> a.add('B', 0x2000, 0x1000)
        AddrRange('B', 0x2000, '4 KB')
        >>> a.add('A', 0xD000, 0x800)
        AddrRange('A', 0xD000, '2 KB')
        >>> list(a.find('A'))
        [AddrRange('A', 0x5000, '4 KB'), AddrRange('A', 0xD000, '2 KB')]
        """
        return self.__new([addrrange for addrrange in self if addrrange.item == item])

    def get_overview(self) -> str:
        """
        Return overview table.

        >>> a = AddrMap()
        >>> a.add('A', 0x5000, 0x1000)
        AddrRange('A', 0x5000, '4 KB')
        >>> a.add('B', 0x2000, 0x1000)
        AddrRange('B', 0x2000, '4 KB')
        >>> a.add('C', 0xD000, 0x800)
        AddrRange('C', 0xD000, '2 KB')
        >>> print(a.get_overview())
        Baseaddr    Size           Sub    Item
        ----------  -------------  -----  ------
        0x2000      0x1000 (4 KB)  No     'B'
        0x5000      0x1000 (4 KB)  No     'A'
        0xD000      0x800 (2 KB)   No     'C'
        """
        headers = ("Baseaddr", "Size  ", "Sub", "Item")
        matrix = []
        for addrrange in self:
            matrix.append(
                (
                    str(addrrange.baseaddr),
                    f"0x{addrrange.size:X} ({addrrange.size})",
                    "Yes" if addrrange.is_sub else "No",
                    repr(addrrange.item),
                )
            )
        return tabulate(matrix, headers=headers)


class Conflict(RuntimeError):
    """AddrMap Conflict Error."""

    def __init__(self, one, other) -> None:
        self.one = one
        self.other = other
        super().__init__(f"{one!r}: overlaps with {other!r}.")
