from urllib.parse import urlparse

from zope import component
from zope import interface

import redis

from nti.app.xrportal.interfaces import IRedisClient
from nti.app.xrportal.interfaces import IXRPortal

logger = __import__('logging').getLogger(__name__)

@interface.implementer(IXRPortal)
class XRPortal(object):

    def __init__(self, settings):
        self.redis = self._setup_redis(settings)

    def _setup_redis(self, settings):
        redis_url = settings.get('redis_url')
        if not redis_url:
            msg = 'Missing redis_url configuration property'
            logger.warn(msg)
            raise DeprecationWarning(msg)

        logger.debug('Initializing redis %s', redis_url)
        parsed_url = urlparse(redis_url)
        if parsed_url.scheme == 'file':
            # Redis client doesn't natively understand file://, only redis://
            client = redis.StrictRedis(unix_socket_path=parsed_url.path)  # XXX Windows
        else:
            client = redis.StrictRedis.from_url(redis_url)
        interface.alsoProvides(client, IRedisClient)
        component.getGlobalSiteManager().registerUtility(client, IRedisClient)
        return client

    def close(self):
        self.redis.connection_pool.disconnect()
