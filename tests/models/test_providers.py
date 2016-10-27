# pylint: disable=missing-docstring
from research_app.models import providers


def tests_create_fhirclient():
    provider = providers.Provider(fhir_url='http://example.com')

    assert provider.fhirclient
