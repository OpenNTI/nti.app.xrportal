from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_properties
from hamcrest import has_property

from pyramid.testing import DummyRequest

import unittest

from nti.testing.matchers import verifiably_provides

from nti.app.xrportal.tests import  SharedConfiguringTestLayer

from ..cmi5 import launch_params_from_request

from ..interfaces import ICMI5LaunchParams


class TestLaunchParamParsing(unittest.TestCase):

    layer =  SharedConfiguringTestLayer

    def setUp(self):
        self.launchParams = {
            'endpoint': 'http://lrs.example.com/lrslistener/',
            'fetch': 'http://lms.example.com/tokenGen.htm?k=2390289x0',
            'actor': '{"objectType": "Agent","account": {"homePage": "http://www.example.com","name": "1625378"}}',
            'registration': '760e3480-ba55-4991-94b0-01820dbd23a2',
            'activityId': 'http://www.example.com/LA1/001/intro'
        }

    def test_param_parsing(self):
        request = DummyRequest(params=self.launchParams)
        params = ICMI5LaunchParams(request)
        assert_that(params, verifiably_provides(ICMI5LaunchParams))
        assert_that(params, has_properties(
            'endpoint', 'http://lrs.example.com/lrslistener/',
            'fetch', 'http://lms.example.com/tokenGen.htm?k=2390289x0',
            'registration', '760e3480-ba55-4991-94b0-01820dbd23a2',
            'activityId', 'http://www.example.com/LA1/001/intro',
            'actor', has_property('account', has_property('name', '1625378'))
        ))
