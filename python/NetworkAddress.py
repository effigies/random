"""Handle network addresses and ranges

Tools for validating, parsing, and comparing network addresses, ranges,
and for querying whether a given address is within a set of ranges.

Address is an abstract class, of which IPv4 and IPv6 are subclasses,
which builds on top of the socket parsing of network addresses and
represents addresses directly as their integer values. IP is the
direct superclass of IPv4 and IPv6, which accepts valid addresses for
either class, preferring IPv4 in ambiguous cases.

AddressRange is a general construct for specifying a contiguous block
of addresses, and does not connote a structure. Subnet adds CIDR
structure. AddressRanges are addable, and Subnets devolve into
AddressRanges for this purpose if there isn't a trivial overlap.
"""

import socket


class Address(int):
    """Unsigned integer representations of network addresses, building on the
    socket library.

    Subclass with number of bits and address family."""
    bits = None
    family = None

    def __new__(cls, val=0):
        """Convert a number or a string to an Address."""
        if isinstance(val, str):
            try:
                return cls.from_bytes(socket.inet_pton(cls.family, val), 'big')
            except OSError:
                raise ValueError("invalid literal for {}(): {!r}".format(
                    cls.__name__, val))
        address = super(Address, cls).__new__(cls, val)
        if address < 0:
            raise OverflowError("can't convert negative int to {}".format(
                cls.__name__))
        if address.bit_length() > cls.bits:
            raise OverflowError("too large a value for {}: {!s}".format(
                cls.__name__, val))
        return address

    def __str__(self):
        """Use socket library formatting"""
        return socket.inet_ntop(self.family,
                                self.to_bytes(self.bits // 8, 'big'))

    def mask(self, nbits):
        """Return an address with the first n bits preserved and the
        rest zeroes out."""
        ones = (1 << self.bits) - 1
        return self.__class__(self & (ones << (self.bits - nbits)))


class IP(Address):
    """Generic IP address

    IP() == IPv4('0.0.0.0')
    IP('::') == IPv6('::')

    Enables conversion between IP classes:

    IP().to(IPv6) == IPv6('::ffff:0:0')
    IP('::ffff:0:0').to(IPv4) == IPv4('0.0.0.0')
    """
    v4mask = 0xffff00000000

    def __new__(cls, val=0):
        if cls.family is None:
            for subclass in cls.subclasses:
                try:
                    return subclass(val)
                except (ValueError, OverflowError):
                    pass
            raise ValueError('Invalid address: {}'.format(val))
        return super(IP, cls).__new__(cls, val)

    def to(self, cls):  # pylint: disable=invalid-name
        """Convert between IP classes, if possible.

        IPv4('w.x.y.z').to(IPv6) == IPv6('::ffff:w.x.y.z')
        IPv6('::ffff:w.x.y.z').to(IPv4) == IPv4('w.x.y.z')
        """
        if isinstance(self, cls):
            return self
        try:
            return cls(self.convert[type(self)][cls](self))
        except (KeyError, OverflowError):
            raise ValueError("not convertible to {}".format(cls.__name__))


class IPv4(IP):
    """Integer representation of IPv4 network addresses, building on the
    socket library."""
    bits = 32
    family = socket.AF_INET


class IPv6(IP):
    """Integer representation of IPv6 network addresses, building on the
    socket library."""
    bits = 128
    family = socket.AF_INET6


IP.subclasses = (IPv4, IPv6)
IP.convert = {IPv4: {IPv6: lambda ipv4: ipv4 | IP.v4mask},
              IPv6: {IPv4: lambda ipv6: ipv6 ^ IP.v4mask}}


class AddressRange(object):     # pylint: disable=R0903
    """Range within a given address family that allows unions, comparisons,
    and checks for inclusion."""
    def __init__(self, start, end=None):
        """Create range of from start to end, or lift address into a
        range, if no end."""
        if end is None:
            end = start
        assert start <= end
        self.start = start
        self.end = end
        self.family = type(start)

    def __str__(self):
        return '{}-{}'.format(self.start, self.end)

    def __contains__(self, addr):
        if isinstance(addr, AddressRange):
            return addr.start >= self.start and addr.end <= self.end
        return addr >= self.start and addr <= self.end

    def __add__(self, addr):
        if isinstance(addr, AddressRange):
            if addr.start > self.end + 1:
                return (self, addr)
            elif self.start > addr.end + 1:
                return (addr, self)
            else:
                return AddressRange(min(self.start, addr.start),
                                    max(self.end, addr.end))
        if addr > self.end + 1:
            return (self, AddressRange(addr))
        elif self.start > addr + 1:
            return (AddressRange(addr), self)
        else:
            return AddressRange(min(self.start, addr), max(self.end, addr))

    def __lt__(self, addr):
        """True if there is at least one address above the range and below x"""
        if isinstance(addr, AddressRange):
            return addr.start > self.end + 1
        return addr > self.end + 1

    def __gt__(self, addr):
        """True if there is at least one address below the range and above x"""
        if isinstance(addr, AddressRange):
            return self.start > addr.end + 1
        return self.start > addr + 1

    def __eq__(self, addr):
        return self.start == addr.start and self.end == addr.end

    @classmethod
    def from_string(cls, iprange):
        """Parse address range of the form start-end"""
        start, _, end = iprange.partition('-')
        startip = IP(start)
        if end:
            endip = IP(end)
            assert startip.bits == endip.bits
        else:
            endip = None
        return cls(startip, endip)


class Subnet(AddressRange):     # pylint: disable=R0903
    """Address range that operates on the logic of CIDR blocks.

    If addition of new addresses breaks this logic, revert to AddressRange."""
    def __init__(self, address, cidr):
        self.address = address.mask(cidr)
        self.cidr = cidr

        start = self.address
        diff = (1 << (address.bits - cidr)) - 1
        end = address.__class__(start + diff)

        super(Subnet, self).__init__(start, end)

    def __str__(self):
        return '{}/{:d}'.format(self.address, self.cidr)

    def __contains__(self, addr):
        """Determine if an address or Subnet is subsumed by this Subset"""
        if isinstance(addr, Subnet):
            return addr.cidr > self.cidr and addr.address in self
        return super(Subnet, self).__contains__(addr)

    def __add__(self, addr):
        """If a Subnet subsumes another range, keep the larger Subnet. If not,
        revert to AddressRange addition."""
        if addr in self:
            return self
        elif self in addr:
            return addr
        else:
            return super(Subnet, self).__add__(addr)

    @classmethod
    def from_string(cls, netstring):
        """Parse CIDR string of the form IP/CIDR"""
        ipstring, _, cidr = netstring.partition('/')
        addr = IP(ipstring)
        return cls(addr, int(cidr) if cidr else addr.bits)
