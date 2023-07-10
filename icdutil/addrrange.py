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

"""Helper Class For Handling Address Ranges."""


import typing

from attrs import field, frozen
from humannum import Bytes, Hex
from mementos import mementos


@frozen(init=False, repr=False, str=False)
class AddrRange(mementos):
    """Address range starting at `baseaddr` with `size` in bytes."""

    baseaddr: Hex = field()
    size: Bytes = field()
    addrwidth: typing.Optional[int] = field()

    def __init__(self, baseaddr: int, size: int, addrwidth: typing.Optional[int] = None) -> None:
        """
            Address range starting at `baseaddr` with `size` in bytes.

        >>> a = AddrRange(0x1000, 0x100)
        >>> a
        AddrRange(0x1000, '256 bytes')

        The addrwidth just formats the address representation:
        >>> a = AddrRange(0x1000, 0x100, addrwidth=32)
        >>> a
        AddrRange(0x00001000, '256 bytes', addrwidth=32)
        >>> str(a)
        '0x00001000-0x000010FF(256 bytes)'
        >>> str(a.nextaddr)
        '0x00001100'

        Address ranges can be compared
        >>> AddrRange(0x1000, 0x100) == AddrRange(0x1000, 0x100)
        True
        >>> AddrRange(0x1000, 0x100) == AddrRange(0x1000, 0x200)
        False

        Addresses can be checked whether they lie within the range
        >>> 0x1008 in a
        True
        >>> 0x1400 in a
        False

        Address ranges can be iterated over
        >>> for i in AddrRange(0x200, 6):
        ...     print(i)
        512
        513
        514
        515
        516
        517
        """
        baseaddr = Hex(baseaddr, width=addrwidth)
        size = Bytes(size)
        # pylint: disable=no-member
        self.__attrs_init__(baseaddr, size, addrwidth)

    @property
    def endaddr(self) -> Hex:
        """Hexvalue of end address of range."""
        return Hex(self.baseaddr + self.size - 1, width=self.addrwidth)

    @property
    def nextaddr(self) -> Hex:
        """Hexvalue of first address after range."""
        return Hex(self.endaddr + 1, width=self.addrwidth)

    def __str__(self):
        """Return String representation."""
        return f"{self.baseaddr}-{self.endaddr}({self.size})"

    def __repr__(self):
        """Return extended representation."""
        aw_ = f", addrwidth={self.addrwidth}" if self.addrwidth else ""
        return f"AddrRange({self.baseaddr}, '{self.size}'{aw_})"

    def __eq__(self, other):
        if other.__class__ is AddrRange:
            return (self.addrwidth, self.baseaddr, self.size) == (other.addrwidth, other.baseaddr, other.size)
        return NotImplemented

    def __contains__(self, value):
        """Check wether `value` lies wirhin address range."""
        return self.baseaddr <= value <= self.endaddr

    def __iter__(self):
        """Iterate over all addresses inside range."""
        return iter(range(self.baseaddr, self.endaddr + 1))

    def is_overlapping(self, other: "AddrRange") -> bool:
        """
        Return `True` if `other` overlaps.

        >>> AddrRange(0x1000, '4 KB').is_overlapping(AddrRange(0x3000, '4 KB'))
        False
        >>> AddrRange(0x1000, '4 KB').is_overlapping(AddrRange(0x2000, '4 KB'))
        False
        >>> AddrRange(0x1000, '4 KB').is_overlapping(AddrRange(0x2000, 0x1))
        False
        >>> AddrRange(0x1000, '4 KB').is_overlapping(AddrRange(0x1FFF, 0x1))
        True
        >>> AddrRange(0x1000, '4 KB').is_overlapping(AddrRange(0x1000, '4 KB'))
        True

        >>> AddrRange(0x3000, '4 KB').is_overlapping(AddrRange(0x2000, '4 KB'))
        False
        >>> AddrRange(0x3000, '4 KB').is_overlapping(AddrRange(0x2FFF, 0x1))
        False
        >>> AddrRange(0x3000, '4 KB').is_overlapping(AddrRange(0x3000, 0x1))
        True
        >>> AddrRange(0x3000, '4 KB').is_overlapping(AddrRange(0x0000, 0x8000))
        True
        """
        if self.baseaddr < other.baseaddr:
            # other is to the right of self
            return self.endaddr >= other.baseaddr
        # other is to the left of self
        return self.baseaddr <= other.endaddr

    def get_intersect(self, other: "AddrRange") -> typing.Optional["AddrRange"]:
        """
        Return :any:`AddrRange` instance which intersects self and `other` address range.

        >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x3000, '4 KB'))
        >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x2000, '4 KB'))
        >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x2000, 0x1))
        >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x1FFF, 0x1))
        AddrRange(0x1FFF, '1 byte')
        >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x1000, '4 KB'))
        AddrRange(0x1000, '4 KB')

        >>> AddrRange(0x3000, '4 KB').get_intersect(AddrRange(0x2000, '4 KB'))
        >>> AddrRange(0x3000, '4 KB').get_intersect(AddrRange(0x2FFF, 0x1))
        >>> AddrRange(0x3000, '4 KB').get_intersect(AddrRange(0x3000, 0x1))
        AddrRange(0x3000, '1 byte')
        >>> AddrRange(0x3000, '4 KB').get_intersect(AddrRange(0x0000, 0x8000))
        AddrRange(0x3000, '4 KB')
        """
        baseaddr = max(self.baseaddr, other.baseaddr)
        endaddr = min(self.endaddr, other.endaddr)
        size = endaddr - baseaddr + 1
        return AddrRange(baseaddr, size, addrwidth=self.addrwidth) if size > 0 else None
