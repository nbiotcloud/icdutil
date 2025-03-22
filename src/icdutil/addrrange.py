#
# MIT License
#
# Copyright (c) 2023-2025 nbiotcloud
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
    addrwidth: int | None = field()
    item: typing.Any | None = field()
    is_sub: bool = field()

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        baseaddr: int,
        size: int,
        addrwidth: int | None = None,
        item: typing.Any | None = None,
        is_sub=False,
    ) -> None:
        """
        Address range starting at `baseaddr` with `size` in bytes.

        Example:

            >>> a = AddrRange(0x1000, 0x100)
            >>> a
            AddrRange(0x1000, '256 bytes')
            >>> b = AddrRange(0x1000, 0x100, item='B')
            >>> b
            AddrRange('B', 0x1000, '256 bytes')
            >>> c = AddrRange(0x1000, 0x100, is_sub=True)
            >>> c
            AddrRange(0x1000, '256 bytes', is_sub=True)
            >>> d =  AddrRange(0x1000, 0x100, item='D', is_sub=True)
            >>> d
            AddrRange('D', 0x1000, '256 bytes', is_sub=True)

        The addrwidth just formats the address representation:

            >>> a = AddrRange(0x1000, 0x100, addrwidth=32)
            >>> a
            AddrRange(0x00001000, '256 bytes', addrwidth=32)
            >>> str(a)
            '0x00001000-0x000010FF(256 bytes)'
            >>> str(a.nextaddr)
            '0x00001100'

        Address ranges can be compared:

            >>> AddrRange(0x1000, 0x100) == AddrRange(0x1000, 0x100)
            True
            >>> AddrRange(0x1000, 0x100) == AddrRange(0x1000, 0x200)
            False

        Comparing an AddrRange against another type just returns False:

            >>> AddrRange(0x1000, 0x100) == 42
            False

        Addresses can be checked whether they lie within the range:

            >>> 0x1008 in a
            True
            >>> 0x1400 in a
            False

        Address ranges can be iterated over:

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
        self.__attrs_init__(baseaddr, size, addrwidth, item, is_sub)

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
        it_ = f"{self.item!r}: " if self.item else ""
        return f"{it_}{self.baseaddr}-{self.endaddr}({self.size})"

    def __repr__(self):
        """Return extended representation."""
        aw_ = f", addrwidth={self.addrwidth}" if self.addrwidth else ""
        it_ = f"{self.item!r}, " if self.item else ""
        is_ = ", is_sub=True" if self.is_sub else ""
        return f"AddrRange({it_}{self.baseaddr}, '{self.size}'{aw_}{is_})"

    def __eq__(self, other):
        if other.__class__ is AddrRange:
            return (self.addrwidth, self.baseaddr, self.size) == (other.addrwidth, other.baseaddr, other.size)
        return NotImplemented

    def __contains__(self, value):
        """Check whether `value` lies within address range."""
        return self.baseaddr <= value <= self.endaddr

    def __iter__(self):
        """Iterate over all addresses inside range."""
        return iter(range(self.baseaddr, self.endaddr + 1))

    def is_overlapping(self, other: "AddrRange") -> bool:
        """
        Return `True` if `other` overlaps.

        Example:

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

    def get_intersect(self, other: "AddrRange", strict: bool = False) -> typing.Optional["AddrRange"]:
        """
        Return intersection of self and `other`.

        Args:
            other(AddrRange): The other AddrRange for intersection with `self`.

        Keyword Args:
            strict(bool):     Raise `IntersectError` when True and there is no intersection between self and `other`.

        Absolute AddrRanges just lead to the intersection:

            >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x2000, '4 KB'))
            >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x2000, 0x1))
            >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x1FFF, 0x1))
            AddrRange(0x1FFF, '1 byte')

        Remark: humandfriendly package is rounding 4095 bytes to 4 KB.

            >>> a = AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x1000, 0xFFF))
            >>> a
            AddrRange(0x1000, '4095 bytes')
            >>> int(a.size)
            4095
            >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x1000, '4 KB'))
            AddrRange(0x1000, '4 KB')
            >>> AddrRange(0x3000, '4 KB').get_intersect(AddrRange(0x2000, '4 KB'))
            >>> AddrRange(0x3000, '4 KB').get_intersect(AddrRange(0x2FFF, 0x1))
            >>> AddrRange(0x3000, '4 KB').get_intersect(AddrRange(0x3000, 0x1))
            AddrRange(0x3000, '1 byte')
            >>> AddrRange(0x3000, '4 KB').get_intersect(AddrRange(0x0000, 0x8000))
            AddrRange(0x3000, '4 KB')

        If `strict` is set and there is no insersection `IntersectError` is raised:

            >>> AddrRange(0x1000, '4 KB').get_intersect(AddrRange(0x1000, '4 KB'), strict=True)
            AddrRange(0x1000, '4 KB')
            >>> AddrRange(0x1000, '4 KB').get_intersect(
            ...     AddrRange(0x3000, '4 KB'), strict=True)  # doctest: +NORMALIZE_WHITESPACE
            Traceback (most recent call last):
                ...
            icdutil.addrrange.IntersectError: No intersection between AddrRange(0x1000, '4 KB') \
            and AddrRange(0x3000, '4 KB').

        If only one of the AddrRange is absolute, the sub range is taken relative to the absolute.
        If `self` is a subrange, then the intersection is again a subrange w/r/t to the absolute range.

            >>> AddrRange(0xF0000000, '1 MB').get_intersect(AddrRange(0x2000, '4 KB', is_sub=True))
            AddrRange(0xF0002000, '4 KB')
            >>> AddrRange(0x2000, '4 KB', is_sub=True).get_intersect(AddrRange(0xF0000000, '1 MB'))
            AddrRange(0x2000, '4 KB', is_sub=True)

        If there is no overlap b/w absolute range and sub-range at the offset,
        the result depends on the `strict` parameter:

            >>> AddrRange(0xF0000000, '1 KB').get_intersect(AddrRange(0x2000, '4 KB', is_sub=True))
            >>> AddrRange(0xF0000000, '1 KB').get_intersect(
            ...     AddrRange(0x2000, '4 KB', is_sub=True), strict=True)  # doctest: +NORMALIZE_WHITESPACE
            Traceback (most recent call last):
                ...
            icdutil.addrrange.IntersectError: No intersection between AddrRange(0xF0000000, '1 KB') \
            and AddrRange(0x2000, '4 KB', is_sub=True).

        If both are sub-ranges it also just leads to an intersection, but the result is a sub-range:

            >>> AddrRange(0x3000, '4 KB', is_sub=True).get_intersect(AddrRange(0x0000, 0x8000, is_sub=True))
            AddrRange(0x3000, '4 KB', is_sub=True)

        The item and aaddrwidth of the intersection is always inherited from `self`.

            >>> AddrRange(0x2000, '1 MB', item='A', addrwidth=20).get_intersect(
            ...    AddrRange(0x5000, '4 KB', item='B', addrwidth=24))
            AddrRange('A', 0x05000, '4 KB', addrwidth=20)
        """
        baseaddr = self.baseaddr
        is_sub = self.is_sub
        if self.is_sub == other.is_sub:  # either both or none is sub-range
            isect_base = max(self.baseaddr, other.baseaddr)
            isect_end = min(self.endaddr, other.endaddr)
            self_base = baseaddr
        else:  # one of them is a sub-range
            isect_base = baseaddr + other.baseaddr
            self_base = baseaddr if not is_sub else isect_base
            self_end = self_base + self.size - 1
            other_end = isect_base + other.size - 1 if other.is_sub else other.endaddr
            isect_end = min(self_end, other_end)
        size = isect_end - isect_base + 1
        if size > 0:
            strt = baseaddr + isect_base - self_base
            return AddrRange(strt, size, addrwidth=self.addrwidth, item=self.item, is_sub=is_sub)
        if not strict:
            return None
        raise IntersectError(f"No intersection between {self!r} and {other!r}.")

    def get_difference(self, other: "AddrRange") -> list["AddrRange"]:
        """
        Get difference of `self` and `other`.

        Args:
            other(AddrRange): The other AddrRange for intersection with `self`.

        Absolute AddrRanges just lead to the difference (i.e. the rest of `self` after the overlapping part
        has been removed):

            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x2000, '4 KB'))
            [AddrRange(0x1000, '4 KB')]
            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x800, '12 KB'))
            []
            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x1FFF, 0x1))
            [AddrRange(0x1000, '4095 bytes')]
            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x1001, '8 KB'))
            [AddrRange(0x1000, '1 byte')]
            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x1000, 0xFFF))
            [AddrRange(0x1FFF, '1 byte')]
            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x1800, 0x1))
            [AddrRange(0x1000, '2 KB'), AddrRange(0x1801, '2047 bytes')]

        If both are sub-ranges it also just leads to a difference, but the result is a sub-range:

            >>> AddrRange(0x1000, '4 KB', is_sub=True).get_difference(AddrRange(0x2000, '4 KB', is_sub=True))
            [AddrRange(0x1000, '4 KB', is_sub=True)]
            >>> AddrRange(0x1000, '4 KB', is_sub=True).get_difference(AddrRange(0x800, '12 KB', is_sub=True))
            []
            >>> AddrRange(0x1000, '4 KB', is_sub=True).get_difference(AddrRange(0x1FFF, 0x1, is_sub=True))
            [AddrRange(0x1000, '4095 bytes', is_sub=True)]

        If only one of the AddrRange is absolute, the sub range is taken relative to the absolute.
        If `self` is a subrange, then the difference is again a subrange w/r/t to the absolute range.

            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x2000, '4 KB', is_sub=True))
            [AddrRange(0x1000, '4 KB')]
            >>> AddrRange(0x1000, '4 KB', is_sub=True).get_difference(AddrRange(0x2000, '4 KB'))
            [AddrRange(0x1000, '4 KB', is_sub=True)]
            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x800, '2 KB', is_sub=True))
            [AddrRange(0x1000, '2 KB')]
            >>> AddrRange(0x1000, '4 KB').get_difference(AddrRange(0x800, '1 KB', is_sub=True))
            [AddrRange(0x1000, '2 KB'), AddrRange(0x1C00, '1 KB')]
            >>> AddrRange(0x1000, '4 KB', is_sub=True).get_difference(AddrRange(0x800, '4 KB'))
            [AddrRange(0x1000, '4 KB', is_sub=True)]
            >>> AddrRange(0x400, '4 KB', is_sub=True).get_difference(AddrRange(0xF0000800, '4 KB'))
            [AddrRange(0x1000, '1 KB', is_sub=True)]

        Regardless of the `other` range, the difference always inherits addrwidth, the item (if there is any) and
        the is_sub attribute:

            >>> AddrRange(0x1000, '4 KB', item='A').get_difference(AddrRange(0x1800, '4 KB', item='B'))
            [AddrRange('A', 0x1000, '2 KB')]
            >>> AddrRange(0x1000, '4 KB', addrwidth=16).get_difference(AddrRange(0x1800, '4 KB', addrwidth=18))
            [AddrRange(0x1000, '2 KB', addrwidth=16)]
        """
        res = []
        is_sub = self.is_sub
        if is_sub == other.is_sub:  # either both or none is sub-range
            self_base = self.baseaddr
            self_end = self.endaddr
            isect_base = max(self_base, other.baseaddr)
            isect_end = min(self_end, other.endaddr)
        else:  # one of them is a sub-range
            baseaddr = self.baseaddr
            isect_base = baseaddr + other.baseaddr
            self_base = baseaddr if not is_sub else isect_base
            self_end = self_base + self.size - 1
            other_end = isect_base + other.size - 1 if other.is_sub else other.endaddr
            isect_end = min(self_end, other_end)
        if isect_end < isect_base:  # no overlap at all
            return [self]
        if isect_base == self_base and isect_end == self_end:  # other completely overlaps self
            return []
        if self_base < isect_base:  # either both are sub or self is absolute
            res.append(
                AddrRange(
                    self.baseaddr, isect_base - self_base, addrwidth=self.addrwidth, item=self.item, is_sub=is_sub
                )
            )
        if isect_end < self_end:  # either both are sub or self is absolute
            strt = self.baseaddr + isect_end - self_base + 1
            res.append(AddrRange(strt, self_end - isect_end, addrwidth=self.addrwidth, item=self.item, is_sub=is_sub))
        return res


class IntersectError(RuntimeError):
    """AddrRange Intersection Error."""
