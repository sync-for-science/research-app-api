''' Providers module.
'''
from research_app.extensions import db


class Provider(db.Model):
    ''' FHIR API Provider.
    '''
    _id = db.Column('id', db.Integer, primary_key=True)
    client_id = db.Column(db.String)
    client_secret = db.Column(db.String)
    name = db.Column(db.String)
    fhir_url = db.Column(db.String)
    scope = db.Column(db.String)

    @property
    def view_model(self):
        ''' This is the object the view expects.
        '''
        return {
            'id': self._id,
            'client_id': self.client_id,
            'name': self.name,
        }
