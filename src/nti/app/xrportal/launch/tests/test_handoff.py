from hamcrest import assert_that
from hamcrest import calling
from hamcrest import has_length
from hamcrest import is_
from hamcrest import is_not
from hamcrest import raises

import fakeredis

import unittest

import transaction

from nti.testing.matchers import verifiably_provides

from nti.testing.time import time_monotonically_increases

from ..interfaces import IHandoffToken

from ..handoff import _Z_BASE_32_ALPHABET
from ..handoff import HandoffTokenGenerator
from ..handoff import RedisBackedHandoffStorage

class TestHandoffTokenGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = HandoffTokenGenerator()

    def test_vends_token(self):
        token = self.generator.generate_token()
        assert_that(token, verifiably_provides(IHandoffToken))
    
    def test_code_length(self):
        token = self.generator.generate_token()
        assert_that(token.code, has_length(6))

    def test_always_upper(self):
        token = self.generator.generate_token()
        assert_that(set(token.code)-set(_Z_BASE_32_ALPHABET.upper()), has_length(0))

class TestRedisHandoffStorage(unittest.TestCase):

    def setUp(self):
        self.storage = RedisBackedHandoffStorage()
        self._redis = fakeredis.FakeStrictRedis()
        self.storage._redis = self._redis

        self.generator = HandoffTokenGenerator()
        self.storage._generator = self.generator

    def test_store_and_retrieve(self):
        token = self.storage.store_handoff_data(b'foo')

        # We only store the data if the transaction commits
        transaction.commit()
        
        data = self.storage.get_handoff_data(token)
        assert_that(data, is_(b'foo'))

    def test_missing_is_keyerror(self):
        token = self.storage.store_handoff_data(b'foo')
        # Note the token is missing because we didn't commit.
        assert_that(calling(self.storage.get_handoff_data).with_args(token),
                    raises(KeyError))

    def test_token_is_case_insensitive(self):
        token = self.storage.store_handoff_data(b'foo')
        new_code = token.code.lower()
        assert_that(token.code, is_not(new_code))
        transaction.commit() # store the data

        token.code = new_code
        data = self.storage.get_handoff_data(token)
        assert_that(data, is_(b'foo'))

    @time_monotonically_increases(301) # make each call to time.time() increase by 301 so our data expires immediatly
    def test_token_ttl(self):
        token = self.storage.store_handoff_data(b'foo')
        transaction.commit() # store the data

        # now role past the ttl
        assert_that(calling(self.storage.get_handoff_data).with_args(token),
                    raises(KeyError))

    def test_token_redeems_once(self):
        token = self.storage.store_handoff_data(b'foo')
        transaction.commit() # store the data

        data = self.storage.get_handoff_data(token)
        assert_that(data, is_(b'foo'))

        assert_that(calling(self.storage.get_handoff_data).with_args(token),
                    raises(KeyError))

    def test_token_restored_on_rollback(self):
        token = self.storage.store_handoff_data(b'foo')
        transaction.commit() # store the data

        data = self.storage.get_handoff_data(token)
        assert_that(data, is_(b'foo'))

        # But if our transaction rolls back the token is still redeemable
        transaction.abort()
        data = self.storage.get_handoff_data(token)
        assert_that(data, is_(b'foo'))
