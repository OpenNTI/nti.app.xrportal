#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zope.testing.cleanup

from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin


class SharedConfiguringTestLayer(ZopeComponentLayer,
                                 ConfiguringLayerMixin):

    set_up_packages = ('nti.app.xrportal')

    @classmethod
    def setUp(cls):
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, test=None):
        pass

    @classmethod
    def testTearDown(cls):
        pass
