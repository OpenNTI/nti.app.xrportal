from zope import interface

class IRedisClient(interface.Interface):
    """
    A very poor abstraction of a :class:`redis.StrictRedis` client.
    In general, this should only be used in the lowest low level code and
    abstractions should be built on top of this.
    """

class IXRPortal(interface.Interface):
    """
    The XRPortal Application
    """
