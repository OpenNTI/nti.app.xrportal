"""
This package is copied in it's entirety from nti.dataserver:nti.app.renderers.

The following non general components have been stripped away:

1. Removed adapters.py (and tests) containing display name adapters.

2. Removed concrete implementations of
   AbstractReliableLastModifiedCacheController in caching.py

3. Removed .decorators.AbstractAuthenticatedRequestAwareDecorator 
   and .decorators.AbstractTwoStateViewLinkDecorator. The former would ideally remain
   if we can find a general substitute for get_remote_user

4. Remove dependency on who browser classification from renderers.AbstractCachingRenderer.
   This removes the ability to write renderers that render to the browser.

5. Drop enclosed content handling from .rest

6. Update imports from nti.app.renderers to nti.app.environments.renderers

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory('nti.app.environments')
