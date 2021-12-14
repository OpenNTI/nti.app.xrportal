#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decorator helpers for :mod:`nti.externalization` that are
used when externalizing for a remote client.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from abc import ABCMeta
from abc import abstractmethod

from nti.property.property import alias

logger = __import__('logging').getLogger(__name__)


class AbstractRequestAwareDecorator(object):
    """
    A base class providing support for decorators that
    are request-aware. Subclasses can be registered
    as either :class:`.IExternalMappingDecorator` objects
    or :class:`.IExternalObjectDecorator` objects and this
    class will unify the interface.
    """

    __metaclass__ = ABCMeta

    def __init__(self, unused_context, request):
        self.request = request

    def _predicate(self, unused_context, unused_result):
        """
        You may implement this method to check a precondition, return False if no decoration.
        """
        return True

    def decorateExternalMapping(self, context, result):
        if self._predicate(context, result):
            self._do_decorate_external(context, result)

    decorateExternalObject = alias('decorateExternalMapping')

    @abstractmethod
    def _do_decorate_external(self, context, result):
        """
        Implement this to do your actual decoration
        """
        raise NotImplementedError()

