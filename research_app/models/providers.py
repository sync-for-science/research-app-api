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
            'signin_details': self.signin_details,
        }

    @property
    def signin_details(self):
        signin_details = {
            "Allscripts": {
                'username': 'floppyrobot10',
                'password': 's4s_pilot!'
            },
            "athenahealth": {
                'username': 'ewiffin',
                'password': '29NMfRhyygoG7iC9'
            },
            "Cerner": {
                'username': 'ewiffin',
                'password': '29NMfRhyygoG7iC9'
            },
            "CMS": {
                'username': 'BBUser00000',
                'password': 'PW00000!'
            },
            "drchrono": {
                'username': 'api@drchrono.com',
                'password': 'X6mx5AYmT7rUdVv44sZP'
            },
            "eClinicalWorks": {
                'username': 'user2',
                'password': 'Password2'
            },
            "Epic": {
                'username': 'fhirjason',
                'password': 'epicepic1'
            },
            "McKesson": {},
            "SMART_EHR_STU2": {},
            "SMART_EHR_STU3": {},
            "SMART_FINANCIAL_STU3": {},
            "Other": {},
        }

        return signin_details.get(self.name, {})

    @property
    def supported_endpoints(self):
        ''' A list of S4S endpoints supported by this provider.
        '''
        conformance = self.fhirclient.server.conformance.as_json()

        resources = set()
        for rest in conformance.get('rest', []):
            for resource in rest.get('resource', []):
                resources.add(resource.get('type'))

        endpoints = [
            # Smoking status
            ('Observation', 'category=social-history&patient={patient_id}'),
            # Problems
            ('Condition', 'patient={patient_id}'),
            # Medications and allergies
            ('MedicationOrder', 'patient={patient_id}'),
            ('MedicationStatement', 'patient={patient_id}'),
            ('MedicationDispense', 'patient={patient_id}'),
            ('MedicationAdministration', 'patient={patient_id}'),
            ('AllergyIntolerance', 'patient={patient_id}'),
            # Lab results
            ('Observation', 'category=laboratory&patient={patient_id}'),
            # Vital signs
            ('Observation', 'category=vital-signs&patient={patient_id}'),
            # Procedures
            ('Procedure', 'patient={patient_id}'),
            # Immunizations
            ('Immunization', 'patient={patient_id}'),
            # Patient documents
            ('DocumentReference', 'patient={patient_id}'),
        ]

        return [
            resource + '?' + query
            for resource, query in endpoints
            if resource in resources
        ]
