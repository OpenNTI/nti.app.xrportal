from hamcrest import assert_that
from hamcrest import has_length

import unittest

from nti.testing.matchers import verifiably_provides

from ..interfaces import IHandoffToken

from ..handoff import HandoffTokenGenerator
from ..handoff import _Z_BASE_32_ALPHABET

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
