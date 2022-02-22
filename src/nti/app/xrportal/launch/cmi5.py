import json

from io import BytesIO

import requests

from requests.auth import AuthBase

from requests.exceptions import HTTPError

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from qrcode.image.svg import SvgImage

from qrcode.main import QRCode

from urllib import parse

from zope import component

from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.schema.interfaces import IFromUnicode

from nti.externalization import update_from_external_object

from zope.schema import getFields
from zope.schema import getValidationErrors
from zope.schema import ValidationError

from nti.externalization import to_external_object
from nti.externalization import update_from_external_object

from nti.externalization.interfaces import LocatedExternalDict

from nti.xapi.activity import Activity

from nti.xapi.client import LRSClient

from nti.xapi.entities import Agent

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.app.xrportal.launch.interfaces import ICMI5LaunchParams
from nti.app.xrportal.launch.interfaces import IDeviceHandoffStorage

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ICMI5LaunchParams)
class CMI5LaunchParams(SchemaConfigured):

    createDirectFieldProperties(ICMI5LaunchParams)


def launch_params_from_request(request):
    """
    Turn a pyramid request into an ICMI5LaunchParams and validate that
    the incoming parameters meet the CMI spec.
    """

    params = CMI5LaunchParams()

    for name, field in getFields(ICMI5LaunchParams).items():
        val = request.params.get(name)
        if val:
            if field is ICMI5LaunchParams['actor']:
                json_val = val
                val = Agent()
                update_from_external_object(val, json.loads(json_val))
            elif IFromUnicode.providedBy(field):
                val = field.fromUnicode(val)
        setattr(params, name, val)

    # validate
    errors = getValidationErrors(ICMI5LaunchParams, params)
    if errors:
        __traceback_info__ = errors
        raise errors[0][1]

    return params


class CMI5TokenAuth(AuthBase):
    """
    A requests.auth implementation that uses the cmi5 token
    """
    def __init__(self, token):
        if not token:
            raise ValueError('Must supply token')
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Basic '+self.token
        return r


@view_config(route_name='cmi5launch',
             request_method='GET',
             renderer='templates/launch.pt')
class CMI5LaunchView(object):

    def __init__(self, request):
        self.request = request

    @property
    def code(self):
        return self.token.code if self.token else None

    @Lazy
    def qr_svg(self):
        qr = QRCode(version=None)
        qr.add_data(self.code)
        qr.make(fit=True)
        image = qr.make_image(image_factory=SvgImage)

        stream = BytesIO()
        image.save(stream)
        stream.seek(0)
        return stream.read()

    def __call__(self):
        try:
            params = ICMI5LaunchParams(self.request)

            resp = requests.post(params.fetch)
            resp.raise_for_status()
            auth = resp.json()['auth-token']

            lrs = LRSClient(params.endpoint, auth=CMI5TokenAuth(auth))
            activity = Activity()
            activity.id = params.activityId
            document = lrs.retrieve_state(activity,
                                          params.actor,
                                          'LMS.LaunchData',
                                          params.registration)

            if document is None:
                logger.warn('Unable to fetch LMS.LaunchData state document for %s %s %s',
                            params.actor, activity, params.registration)
                raise hexc.HTTPBadRequest('No LMS.LaunchData found')

            try:
                launch_data = json.loads(document.content)
            except ValueError:
                # The spec says it must be JSON
                # https://github.com/AICC/CMI-5_Spec_Current/blob/quartz/cmi5_spec.md#101-overview
                logger.error('Invalid content for LMS.LaunchData. Expected json. got "%s"', document.content)
                raise hexc.HTTPBadRequest()

            # We expect our launch params to be json. This bit I
            # suppose it not totally generally, the spec says this is
            # a string. Our AUs will use strings that represent json.
            launch_params = launch_data.get('launchParameters')
            if launch_params:
                try:
                    launch_data['launchParameters'] = json.loads(launch_params)
                except ValueError:
                    # We're the AU, so if we get something that can't
                    # be converted to json here that's a failure in
                    # our generation of the cmi5.xml declaration and
                    # it's unlikely that downstream can handle this.
                    # Fail fast? If this were to be more general we
                    # would probably rather opt to take the launch
                    # params as is in this case.
                    raise hexc.HTTPBadRequest()

            # Construct the payload we will ultimately provide to the
            # device that needs the launch data
            launch_info = {
                'launchData': launch_data,
                'endpoint': params.endpoint,
                'token': auth,
                'actor': to_external_object(params.actor),
                'registration': params.registration,
                'activityId': params.activityId
            }

            # TODO should we run this entire object through nti.externalization? That's
            # probably overkill here right now?
            data = json.dumps(launch_info)
            self.token = component.getUtility(IDeviceHandoffStorage).store_handoff_data(data)

            # If we roll our transaction back we will also roll our redis operation back.
            # Mark we had side effects so we don't do that implicitly.
            self.request.environ['nti.request_had_transaction_side_effects'] = True
        except ValidationError as e:
            logger.debug('Invalid launch request %s', e)
            raise hexc.HTTPBadRequest()

        platforms = launch_data['launchParameters']['Platforms']

        webgl_launch = platforms.get('WebGL', {})
        webgl_launch_url = webgl_launch.get('URL')
        if webgl_launch_url:
            #Add the code, be careful not to mangle query strings
            parsed = parse.urlparse(webgl_launch_url)
            query = parse.parse_qs('')
            #TODO should we namespace the launch param or raise if it is already in use
            query['launch'] = self.code
            parsed = parsed._replace(query=parse.urlencode(query))
            webgl_launch_url = parse.urlunparse(parsed)

        #If all we have is webgl, just redirect
        # Stop auto redirecting as there may be a headset
        # to launch this on. 2/2/22 -cutz
        #if len(platforms) == 1 and webgl_launch_url:
        #   raise hexc.HTTPSeeOther(webgl_launch_url)

        return {
            'codettl': 300-10, # ttl with some buffer. FIXME don't hardcode this, expose it on the code
            'mode': 'launch',
            'returnURL': launch_data.get('returnURL'),
            'target': 'aspire',
            'code': self.code,
            'launch_params': params,
            'launch_data': data,
            'auth': auth,
            'statusinfo': {
                'lrstoken': auth,
                'lrsendpoint': params.endpoint,
                'cmi5registration': params.registration,
                'cmi5session': launch_data['contextTemplate']['extensions']['https://w3id.org/xapi/cmi5/context/extensions/sessionid'],
                'activityid': params.activityId,
                'apihref': self.request.route_url('cmi5status')
            },
            'webgl_launch': webgl_launch_url
        }

@view_config(route_name='cmi5status',
             request_method='POST',
             renderer='rest')
class XRLaunchStatusView(object):
    """
    A view that looks for the statements related to the provided
    launch session/registration to return details and insight into the
    current status of the session. Note this is stateless, we expect
    everything to be provided, including the credentials we can use to
    access the lms. In general our cmi5 page has access to all of this
    from the launch request.
    """
    def __init__(self, request):
        self.request = request

    @Lazy
    def params(self):
        return self.request.json_body

    def __call__(self):
        # We need token, endpoint, session, registration
        token = self.params.get('token')
        endpoint = self.params.get('endpoint')
        session = self.params.get('session')
        registration = self.params.get('registration')
        activityId = self.params.get('activity')

        if not token or not endpoint or not session or not registration or not activityId:
            raise hexc.HTTPBadRequest()

        lrs = LRSClient(endpoint, auth=CMI5TokenAuth(token))
        stmts = lrs.query_statements({'activity': activityId,
                                      'registration': registration})
        if stmts is None:
            return {'HeadsetStatus': 'Terminated',
                    'href': self.request.path_qs}

        def _in_session(stmt):
            return stmt.context.extensions.get('https://w3id.org/xapi/cmi5/context/extensions/sessionid') == session
        
        session_stmts = [x for x in stmts if _in_session(x)]

        status = 'Unknown'

        verbs_to_states = {
            'http://adlnet.gov/expapi/verbs/initialized': 'Started',
            'http://adlnet.gov/expapi/verbs/terminated': 'Terminated'
        }

        # session statements come back asc by default and we know
        # cmi5 transitions from Lauched (us), Initialized (headset), Terminated (headset)
        # so we can process them in order to figure out the latest state
        for stmt in session_stmts:
            verbid = stmt.verb.id
            if verbid in verbs_to_states:
                status = verbs_to_states[verbid]
        
        return {
            'HeadsetStatus': status,
            'Statements': session_stmts,
            'href': self.request.path_qs
        }

@view_config(route_name='cmi5handoff',
             request_method='POST',
             renderer='rest')
class LaunchHandoffView(object):
    """
    The second part of the handoff exchanges a code provided by query
    param for the launch data. IDeviceHandoffStorage enforces the
    codes are one time use and short lived. Should we consider also
    rate limiting this API?
    """
    def __init__(self, request):
        self.request = request

    def __call__(self):
        storage = component.getUtility(IDeviceHandoffStorage)
        code = self.request.json_body.get('code')
        if not code:
            raise hexc.HTTPBadRequest()
        
        try:
            data = storage.get_handoff_data(code)
        except KeyError:
            raise hexc.HTTPNotFound()

        # Mark sideeffects so we don't put the data back in redis when
        # the GET request rolls back the transaction.
        self.request.environ['nti.request_had_transaction_side_effects'] = True

        # Our data is a json encoded string. We could round trip it
        # back through the json module or nti.externalization, but
        # that seems wasted. If redis isn't a trusted source seems
        # like we had bigger issues.
        response = self.request.response
        response.status_code = 200
        response.content_type = 'application/json'
        response.body = data
        return response
