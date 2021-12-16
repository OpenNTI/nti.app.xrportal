# NOTE: We must not import *anything* before the patch
# This fails with attribute errors for some reason...
#import gevent; gevent.config.resolver = 'dnspython'
import gevent.monkey
gevent.monkey.patch_all()

from pyramid.config import Configurator

from pyramid.tweens import EXCVIEW

from zope.component import getGlobalSiteManager

import pyramid_zcml

from nti.app.xrportal.appserver import XRPortal

from nti.app.xrportal.appserver import IXRPortal

def configure(settings=None, registry=None):
    if registry is None:
        registry = getGlobalSiteManager()

    with Configurator(settings=settings) as config:
        config.setup_registry(settings=settings)
        config.include(pyramid_zcml)
        config.include('pyramid_chameleon')
        config.load_zcml('configure.zcml', features=settings.get('zcml.features', '').split())
        config.add_renderer(name='rest', factory='nti.app.xrportal.renderers.renderers.DefaultRenderer')
        config.add_renderer(name='.rml', factory="nti.app.xrportal.renderers.pdf.PDFRendererFactory")
        config.add_renderer(name='.pt', factory='nti.app.pyramid_zope.z3c_zpt.renderer_factory')
        config.add_tween('nti.transactions.pyramid_tween.transaction_tween_factory',
                         over=EXCVIEW)

        config.load_zcml( 'nti.app.xrportal:pyramid.zcml' )
    return config
        
def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    
    config = configure(settings)
    portal = XRPortal(settings)
    getGlobalSiteManager().registerUtility(portal, IXRPortal)
    return config.make_wsgi_app()
