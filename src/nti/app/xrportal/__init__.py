from zope.component import getGlobalSiteManager

import pyramid_zcml

from pyramid.config import Configurator

def configure(settings=None, registry=None):
    if registry is None:
        registry = getGlobalSiteManager()

    with Configurator(settings=settings) as config:
        config.setup_registry(settings=settings)
        config.include(pyramid_zcml)
        config.include('pyramid_chameleon')
        config.load_zcml('configure.zcml', features=settings.get('zcml.features', '').split())
    return config
        
def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    
    config = configure(settings)
    return config.make_wsgi_app()
