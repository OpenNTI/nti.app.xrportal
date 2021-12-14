#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF response rendering, based on :mod:`z3c.rml`.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.interfaces import IRenderer
from pyramid.interfaces import IRendererFactory

from pyramid_chameleon.renderer import template_renderer_factory

from zope import interface

from z3c.rml import rml2pdf

from nti.app.pyramid_zope.z3c_zpt import ZPTTemplateRenderer

from nti.app.xrportal.renderers.renderers import AbstractCachingRenderer

logger = __import__('logging').getLogger(__name__)


@interface.provider(IRendererFactory)
@interface.implementer(IRenderer)
def PDFRendererFactory(info):
    """
    A renderer that creates a PDF given an /asset specification/ or absolute
    path to an RML template.
    """
    # We use pyramid_chameleon's implementation to find asset files,
    # support overrides, etc, as well as caching implementation objects.
    return template_renderer_factory(info, _PDFRMLRenderer)


# pylint: disable=abstract-method,locally-disabled


class _PDFRMLRenderer(AbstractCachingRenderer):

    def __init__(self, path, lookup, macro=None):
        self.zpt_renderer = ZPTTemplateRenderer(path, lookup, macro=macro)

    def _render_to_pdf(self, value, system):
        rml = self.zpt_renderer(value, system)
        # TODO: Probably need to set headers for forcing inline view vs download?
        pdf_stream = rml2pdf.parseString(rml)
        system['request'].response.content_type = 'application/pdf'

        # Here we don't want to override those that have already set the content_disposition,
        # in which they may support optional download.
        if system['request'].response.content_disposition is None:
            # inline view
            if getattr(system['view'], 'filename', None):
                system['request'].response.content_disposition = 'filename="{0}"'.format(system['view'].filename)

        return pdf_stream.read()
    _render_to_browser = _render_to_non_browser = _render_to_pdf
