''' Participants module.
'''
from itertools import groupby
import json
import subprocess

from fhirclient import client
from fhirclient.models.fhirabstractbase import FHIRValidationError
from fhirclient.models.fhirelementfactory import FHIRElementFactory
from furl import furl

from research_app.extensions import db


class Participant(db.Model):
    ''' A user who would like to share their medical data.
    '''
    _id = db.Column('id', db.Integer, primary_key=True)

    _authorizations = db.relationship('Authorization')

    @property
    def view_model(self):
        ''' This is the object the view expects.
        '''
        return {
            'id': self._id,
        }

    @property
    def authorizations(self):
        ''' A list of all this Participant's authorizations.
        '''
        return [auth.view_model for auth in self._authorizations]

    def begin_authorization(self, provider):
        ''' Create a new Authorization and start the token exchange process.
        '''
        auth = Authorization(provider)
        self._authorizations.append(auth)

        return auth

    def complete_authorization(self, code, state):
        ''' Complete the Authorization process.
        '''
        try:
            auth = [auth for auth in self._authorizations
                    if auth.state == state][0]

            # Deactivate existing authorizations with this provider
            for old in self._authorizations:
                if old is auth:
                    continue
                if old.provider is not auth.provider:
                    continue
                old.expire()

        except IndexError:
            message = 'Authorization with state "{}" not found.'.format(state)
            raise AuthorizationException(message)

        auth.complete(code)

        return auth

    def resources(self, provider):
        ''' Return all the Resources for this Provider, if available.
        '''
        for authorization in self._authorizations:
            if authorization.provider is provider:
                return authorization.resources
        return []


class Authorization(db.Model):
    ''' An Authorization record for a given provider.
    '''
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_EXPIRED = 'expired'

    _id = db.Column('id', db.Integer, primary_key=True)
    status = db.Column(db.String)
    _fhirclient = db.Column('fhirclient', db.Text)

    _participant_id = db.Column('participant_id',
                                db.Integer,
                                db.ForeignKey('participant.id'))

    _provider_id = db.Column('provider_id',
                             db.Integer,
                             db.ForeignKey('provider.id'))
    provider = db.relationship('Provider')

    _resources = db.relationship('Resource', cascade='all, delete, delete-orphan')

    def __init__(self, provider):
        self.status = self.STATUS_PENDING
        self.provider = provider
        self._fhirclient = None
        self._resources = []

    @property
    def state(self):
        ''' Accessor for the FHIRClient temporary variable.
        '''
        return self.fhirclient().server.auth.auth_state

    def authorize_url(self):
        ''' Generate a FHIRClient authorize url.
        '''
        return self.fhirclient().authorize_url

    def complete(self, code):
        ''' Complete the authorization process.
        '''
        fhirclient = self.fhirclient()
        fhirclient.handle_callback(self.callback_url(code))
        self.status = self.STATUS_ACTIVE

        # TODO: Something more robust than this to kick-start resource syncing
        subprocess.Popen([
            'flask',
            'sync_fhir_resources'
            '--participant=' + str(self._participant_id),
            '--provider=' + str(self._provider_id),
        ])

    def expire(self):
        ''' Expire an Authorization.
        '''
        self.status = self.STATUS_EXPIRED

    def fetch_resources(self):
        ''' Downloads all the available resources.
        '''
        fhirclient = self.fhirclient()
        self._resources = []

        try:
            resource = Resource.from_fhirclient_model(fhirclient.patient)
            self._resources.append(resource)

            for endpoint in self.provider.supported_endpoints:
                endpoint = endpoint.format(patient_id=fhirclient.patient_id)
                bundle = fhirclient.server.request_json(endpoint)
                self._resources += Resource.from_json_bundle(bundle)
        except client.FHIRUnauthorizedException:
            self.status = self.STATUS_EXPIRED
            raise AuthorizationException('Authorization Expired.')

    def fhirclient(self):
        ''' Returns a FHIRClient object from the current state.
        '''
        def save_func(state):  # pylint: disable=missing-docstring
            self._fhirclient = json.dumps(state)

        if not self._fhirclient:
            fhirclient = self.provider.fhirclient
            fhirclient.prepare()
            state = fhirclient.state
        else:
            state = json.loads(self._fhirclient)

        return client.FHIRClient(state=state,
                                 save_func=save_func)

    def callback_url(self, code):
        ''' Builds a "callback url" from this Authorization.
        '''
        url = furl(self.provider.redirect_uri)
        url.args['code'] = code
        url.args['state'] = self.state

        return url.url

    @property
    def view_model(self):
        ''' This is the object the view expects.
        '''
        resources = self.resources
        resources.sort(key=lambda x: x['resourceType'])
        grouped = groupby(resources, lambda x: x['resourceType'])
        counts = {key: len(list(val)) for key, val in grouped}

        return {
            'status': self.status,
            'provider': self.provider.name,
            'resources_endpoint': self.provider.fhir_url,
            'counts': counts,
        }

    @property
    def resources(self):
        ''' A list of Resources.
        '''
        return [resource.view_model for resource in self._resources]


class Resource(db.Model):
    ''' A FHIR Resource.
    '''
    _id = db.Column('id', db.Integer, primary_key=True)
    entry_json = db.Column(db.Text)
    resource_type = db.Column(db.String)

    _authorization_id = db.Column('authorization_id',
                                  db.Integer,
                                  db.ForeignKey('authorization.id'))

    def __init__(self, entry):
        self.entry_json = json.dumps(entry)
        self.resource_type = entry['resourceType']

    @property
    def view_model(self):
        ''' This is the object the view expects.
        '''
        return json.loads(self.entry_json)

    @classmethod
    def from_fhirclient_model(cls, model):
        ''' Resource factory method.

        Args:
            model (fhirclient.models.fhirabstractbase.FHIRAbstractBase)

        Returns:
            Resource
        '''
        return cls(entry=model.as_json())

    @classmethod
    def from_json_bundle(cls, bundle):
        ''' Resource factory generator.

        Args:
            bundle (dict): A dictionary representation of a FHIR Bundle.

        Yields:
            Resource
        '''
        for entry in bundle.get('entry', []):
            try:
                res = entry.get('resource', {})
                res_type = res.get('resourceType', None)
                model = FHIRElementFactory.instantiate(res_type, res)
                yield cls.from_fhirclient_model(model)
            except FHIRValidationError:
                continue


class AuthorizationException(Exception):
    ''' An error occurred during the authorization process.
    '''
