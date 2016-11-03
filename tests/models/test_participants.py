# pylint: disable=missing-docstring
import pytest

from research_app.models import participants, providers


def test_participant_authorizations():
    participant = participants.Participant()

    # Participants should start with no authorizations
    assert not participant.authorizations

    # But we can add them
    provider = providers.Provider(fhir_url='http://example.com',
                                  name='Example Provider')
    authorize_url = participant.begin_authorization(provider)

    assert authorize_url
    assert participant.authorizations


def test_resource_factories():
    valid_bundle = {
        'entry': [
            {
                'resource': {
                    'resourceType': 'Patient',
                },
            },
        ],
    }
    assert list(participants.Resource.from_json_bundle(valid_bundle))

    invalid_bundle = {}
    assert not list(participants.Resource.from_json_bundle(invalid_bundle))
