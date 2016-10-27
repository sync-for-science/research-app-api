''' Participants module.
'''
from itertools import groupby
import json

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

    def authorize(self, provider, code, state):
        ''' Create a new Authorization and start the token exchange process.
        '''
        if self.authorization(provider):
            message = 'Provider "{}" already authorized.'.format(provider.name)
            raise AuthorizationException(message)
        auth = Authorization(provider, code, state)
        self._authorizations.append(auth)

        return auth

    def authorization(self, provider):
        ''' Return the Authorization for this Provider, if available.
        '''
        for authorization in self._authorizations:
            if authorization.provider is provider and authorization.is_useful:
                return authorization.view_model
        return None

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
    code = db.Column(db.String)
    state = db.Column(db.String)
    _fhirclient = db.Column('fhirclient', db.Text)

    _participant_id = db.Column('participant_id',
                                db.Integer,
                                db.ForeignKey('participant.id'))

    _provider_id = db.Column('provider_id',
                             db.Integer,
                             db.ForeignKey('provider.id'))
    provider = db.relationship('Provider')

    _resources = db.relationship('Resource', cascade='all, delete, delete-orphan')

    def __init__(self, provider, code, state):
        self.status = self.STATUS_PENDING
        self.provider = provider
        self.code = code
        self.state = state
        self._fhirclient = None
        self._resources = []

    def complete(self):
        ''' Complete the authorization process.
        '''
        fhirclient = self.provider.fhirclient
        fhirclient.prepare()
        fhirclient.server.auth.auth_state = self.state
        fhirclient.handle_callback(self.as_callback_url)
        self._fhirclient = json.dumps(fhirclient.state)
        self.status = self.STATUS_ACTIVE
        self.code = None
        self.state = None

    def fetch_resources(self):
        ''' Downloads all the available resources.
        '''
        fhirclient = self.fhirclient()
        self._resources = []

        resource = Resource.from_fhirclient_model(fhirclient.patient)
        self._resources.append(resource)

        for endpoint in self.provider.supported_endpoints:
            endpoint = endpoint.format(patient_id=fhirclient.patient_id)
            bundle = fhirclient.server.request_json(endpoint)
            self._resources += Resource.from_json_bundle(bundle)

    def fhirclient(self):
        ''' Returns a FHIRClient object from the current state.
        '''
        def save_func(state):  # pylint: disable=missing-docstring
            self._fhirclient = json.dumps(state)

        state = json.loads(self._fhirclient)
        return client.FHIRClient(state=state,
                                 save_func=save_func)

    @property
    def as_callback_url(self):
        ''' Builds a "callback url" from this Authorization.
        '''
        url = furl(self.provider.redirect_uri)
        url.args['code'] = self.code
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
    def is_useful(self):
        ''' True if this Authorization has not yet expired.
        '''
        return self.status in [self.STATUS_ACTIVE]

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
