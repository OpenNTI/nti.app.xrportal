import random

import transaction

from zope import component
from zope import interface

from nti.externalization.persistence import NoPickle

from nti.transactions.transactions import ObjectDataManager

from zope.cachedescriptors.property import Lazy

from nti.app.xrportal.interfaces import IRedisClient

from nti.app.xrportal.launch.interfaces import IDeviceHandoffStorage
from nti.app.xrportal.launch.interfaces import IHandoffToken
from nti.app.xrportal.launch.interfaces import IHandoffTokenGenerator

_Z_BASE_32_ALPHABET = "13456789abcdefghijkmnopqrstuwxyz"

@NoPickle
@interface.implementer(IHandoffToken)
class _HandoffToken(object):

    def __init__(self, code):
        self.code = code

@interface.implementer(IHandoffTokenGenerator)
class HandoffTokenGenerator(object):

    code_length = 6
    alphabet = _Z_BASE_32_ALPHABET

    def generate_token(self):
        """
        Produce a IHandoffToken whose code is randomly generated from
        alphabet and code_length.
        """

        code = ''.join(random.choices(self.alphabet, k=self.code_length))
        return _HandoffToken(code.upper())

class _AbortingDataManager(ObjectDataManager):
    """
    A datamanager which, unlike it's superclass, calls
    the callable if the transaction aborts.
    RedisBackedHandoffStorage records tokens into redis at write time,
    rather than waiting for our main transaction to commit,
    in order to avoid time-of-check/time-of-use attacks.  This
    datamanger calls the provided callable on rollback/abort
    so that the token can be cleared from redis in case we
    end up being retried
    """

    def tpc_finish(self, _):
        pass

    def _abort(self):
        self.callable(*self.args, **self.kwargs)

    def abort(self, _):
        self._abort()

    def rollback(self):
        self._abort()



@interface.implementer(IDeviceHandoffStorage)
class RedisBackedHandoffStorage(object):
    """
    An IDeviceHandoffStorage implementation backed by the IRedisClient
    registered utility. IHandoffToken's have one time use codes and
    have a ttl defined by RedisBackedHandoffStorage.ttl
    """

    _redis = None
    _generator = None

    ttl = 300

    @property
    def _redis_client(self):
        return self._redis or component.getUtility(IRedisClient)

    @property
    def _token_generator(self):
        return self._generator or component.getUtility(IHandoffTokenGenerator)

    def _make_redis_key(self, token):
        return 'xr/devicehandoff/'+getattr(token, 'code', token).upper()

    def store_handoff_data(self, data):
        token = self._token_generator.generate_token()
        rkey = self._make_redis_key(token)
        redis = self._redis_client
        transaction.get().join(ObjectDataManager(target=redis,
                                                 method_name='set',
                                                 args=(rkey, data),
                                                 kwargs={'ex': self.ttl}))
        return token

    def _rollback_store(self, redis, key):
        redis.delete(key)

    def get_handoff_data(self, token):
        redis = self._redis_client
        rkey = self._make_redis_key(token)
        data = redis.get(rkey)
        if data is None:
            raise KeyError(token)
        ttl = redis.ttl(rkey)
        redis.delete(rkey)
        transaction.get().join(_AbortingDataManager(target=redis,
                                                    method_name='set',
                                                    args=(rkey, data),
                                                    kwargs={'ex': ttl}))
        return data

