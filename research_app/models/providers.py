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

    @property
    def supported_endpoints(self):
        ''' A list of S4S endpoints supported by this provider.

        @TODO: Filter endpoints using conformance statement.
        '''
        return [
            # Smoking status
            'Observation?category=social-history&patient={patient_id}',
            # Problems
            'Condition?patient={patient_id}',
            # Medications and allergies
            'MedicationOrder?patient={patient_id}',
            'MedicationStatement?patient={patient_id}',
            'MedicationDispense?patient={patient_id}',
            'MedicationAdministration?patient={patient_id}',
            'AllergyIntolerance?patient={patient_id}',
            # Lab results
            'Observation?category=laboratory&patient={patient_id}',
            # Vital signs
            'Observation?category=vital-signs&patient={patient_id}',
            # Procedures
            'Procedure?patient={patient_id}',
            # Immunizations
            'Immunization?patient={patient_id}',
            # Patient documents
            'DocumentReference?patient={patient_id}',
        ]
