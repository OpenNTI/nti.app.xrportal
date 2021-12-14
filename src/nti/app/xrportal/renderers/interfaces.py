#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from pyramid.interfaces import IRenderer


class IResponseRenderer(IRenderer):
    """
    An intermediate layer that exists to transform a content
    object into data, and suitably mutate the IResponse object.
    The default implementation will use the externalization machinery,
    specialized implementations will directly access and return data.
    """


class IResponseCacheController(IRenderer):
    """
    Called as a post-render step with the express intent
    of altering the caching characteristics of the response.
    The __call__ method may raise an HTTP exception, such as
    :class:`pyramid.httpexceptions.HTTPNotModified`.
    """

    def __call__(data, system):
        """
        Optionally returns a new response or raises an HTTP exception.
        """


class IPreRenderResponseCacheController(IRenderer):
    """
    Called as a PRE-render step with the express intent of altering
    the caching characteristics. If rendering should not proceed,
    then the `__call__` method MUST raise an HTTP exception.
    """


class IUncacheableInResponse(interface.Interface):
    """
    Marker interface for things that should not be cached.
    """


class IPrivateUncacheableInResponse(IUncacheableInResponse):
    """
    Marker interface for things that should not be cached
    because they are sensitive or pertain to authentication.
    """


class IUnModifiedInResponse(interface.Interface):
    """
    Marker interface for things that should not provide
    a Last-Modified date, but may provide etags.
    """


class IUncacheableUnModifiedInResponse(IUncacheableInResponse, IUnModifiedInResponse):
    """
    Marker interface for things that not only should not be cached but should provide
    no Last-Modified date at all.
    """

class IExternalizationCatchComponentAction(interface.Interface):
    """
    To allow swizzling out the replacement during devmode and testing,
    we define our catch_component_action as a utility.

    See :func:`nti.externalization.externaliaztion.catch_replace_action`
    """


class INoHrefInResponse(interface.Interface):
    """
    Marker interface for things that should not add an href in response
    """
