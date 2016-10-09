''' Providers module.
'''
from fhirclient import client

from research_app.extensions import db


class Provider(db.Model):
    ''' FHIR API Provider.
    '''
    _id = db.Column('id', db.Integer, primary_key=True)
    client_id = db.Column(db.String)
    client_secret = db.Column(db.String)
    name = db.Column(db.String)
    fhir_url = db.Column(db.String)
    redirect_uri = db.Column(db.String)
    scope = db.Column(db.String)

    @property
    def fhirclient(self):
        ''' Make a client.
        '''
        fhirclient = client.FHIRClient({
            'app_id': self.client_id,
            'app_secret': self.client_secret,
            'api_base': self.fhir_url,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
        })
        fhirclient.prepare()

        return fhirclient

    @property
    def view_model(self):
        ''' This is the object the view expects.
        '''
        return {
            'id': self._id,
            'client_id': self.client_id,
            'name': self.name,
        }
