''' Define the routes in the API blueprint.
'''
from flask import (
    Blueprint,
    jsonify,
    request,
)

from research_app.extensions import db
from research_app.models.participants import (
    Participant,
    AuthorizationException
)
from research_app.models.providers import Provider

BP = Blueprint('api', __name__)


@BP.route('/providers')
def list_providers():
    ''' List available providers.
    '''
    providers = Provider.query.all()

    return jsonify([provider.view_model for provider in providers])


@BP.route('/participants', methods=['POST'])
def create_participant():
    ''' Create a new participant.
    '''
    participant = Participant()
    db.session.add(participant)
    db.session.commit()

    return jsonify(participant.view_model)


@BP.route('/participants/<participant_id>/authorizations/<provider_id>', methods=['POST'])
def create_authorization(participant_id, provider_id):
    ''' Store an authorization.
    '''
    code = request.form.get('code')

    participant = Participant.query.get(participant_id)
    provider = Provider.query.get(provider_id)

    try:
        participant.authorize(provider, code)
        db.session.commit()

        return jsonify(participant.authorization(provider))
    except AuthorizationException as err:
        resp = jsonify({
            'error': type(err).__name__,
            'message': str(err),
        })
        resp.status_code = 500
        return resp


@BP.route('/participants/<participant_id>/authorizations')
def list_authorizations(participant_id):
    ''' Get all the authorizations for a Participant.
    '''
    participant = Participant.query.get(participant_id)
    return jsonify(participant.authorizations)


@BP.route('/participants/<participant_id>/authorizations/<provider_id>/$everything')
def list_resources(participant_id, provider_id):
    ''' Get all the Resources for a Participant for a given Provider.
    '''
    participant = Participant.query.get(participant_id)
    provider = Provider.query.get(provider_id)
    resources = participant.resources(provider)

    return jsonify({
        'resourceType': 'Bundle',
        'type': 'searchset',
        'entry': resources,
    })
