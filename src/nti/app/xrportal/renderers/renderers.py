#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contains renderers for the REST api.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from pyramid.httpexceptions import HTTPForbidden

from pyramid.interfaces import IRendererFactory

from nti.app.xrportal.renderers import MessageFactory as _

from nti.app.xrportal.renderers.interfaces import IResponseRenderer
from nti.app.xrportal.renderers.interfaces import IResponseCacheController
from nti.app.xrportal.renderers.interfaces import IPreRenderResponseCacheController

logger = __import__('logging').getLogger(__name__)

CLASS_BROWSER = 'browser'

@interface.provider(IRendererFactory)
@interface.implementer(IResponseRenderer)
class AbstractCachingRenderer(object):
    """
    A base-class for renderers that may support caching
    of the response based on the data object.
    """

    def __call__(self, data, system):
        request = system['request']
        response = request.response

        if response.status_int == 204:
            # No Content response is like 304 and has no body. We still
            # respect outgoing headers, though
            raise Exception("You should return an HTTPNoContent response")

        if data is None:
            # This cannot happen
            raise Exception("Can only get here with a body")

        try:
            IPreRenderResponseCacheController(data)(data, system)  # optional
        except TypeError:
            pass

        # classification = IRequestClassifier(request)(request.environ)
        classification = 'api'
        if classification == CLASS_BROWSER:
            body = self._render_to_browser(data, system)
        else:
            body = self._render_to_non_browser(data, system)

        system['nti.rendered'] = body

        IResponseCacheController(data)(data, system)
        return body

    def _render_to_browser(self, data, system):
        raise NotImplementedError()

    def _render_to_non_browser(self, data, system):
        raise NotImplementedError()


@interface.provider(IRendererFactory)
@interface.implementer(IResponseRenderer)
class DefaultRenderer(AbstractCachingRenderer):
    """
    A renderer that should be used by default. It delegates
    all of its actual work to other objects, and knows
    about handling caching and the difference between a
    REST-based request and one that should be rendered to HTML.

    See :class:`.IPreRenderResponseCacheController`,
    :class:`.IResponseRenderer`, and :class:`.IResponseCacheController`
    """

    def __init__(self, info):
        pass

    def _render_to_browser(self, unused_data, unused_system):
        # render to browser
        body = _(u"Rendering to a browser not supported yet")
        # This is mostly to catch application tests that are
        # not setting the right headers to be classified correctly
        raise HTTPForbidden(body)

    def _render_to_non_browser(self, data, system):
        renderer = IResponseRenderer(data)
        body = renderer(data, system)
        return body
