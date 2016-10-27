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
    participant.authorize(provider, 'AUTHORIZATION_CODE', 'STATE')

    assert participant.authorizations

    # Until they are active, they don't count
    assert not participant.authorization(provider)

    try:
        # pylint: disable=protected-access
        participant._authorizations[0].status = participants.Authorization.STATUS_ACTIVE
    finally:
        pass
    assert participant.authorization(provider)

    # Once they've been activated, they can't be re-authorized
    with pytest.raises(participants.AuthorizationException):
        participant.authorize(provider, 'NEW_AUTHORIZATION_CODE', 'STATE')


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
