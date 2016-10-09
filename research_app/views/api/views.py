''' Define the routes in the API blueprint.
'''
from flask import (
    Blueprint,
    jsonify,
    redirect,
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


@BP.route('/providers/<provider_id>/launch')
def launch_provider(provider_id):
    ''' Launch a provider.
    '''
    provider = Provider.query.get(provider_id)
    client = provider.fhirclient('http://tests.dev.syncfor.science:9003/authorized/')

    return redirect(client.authorize_url)


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
    callback_url = furl(request.form.get('callback_url'))
    code = callback_url.args['code']
    state = callback_url.args['state']

    participant = Participant.query.get(participant_id)
    provider = Provider.query.get(provider_id)

    try:
        # Create the authorization
        auth = participant.authorize(provider, code, state)
        db.session.commit()

        # Two-step process in case the OAuth steps don't complete
        auth.complete()
        db.session.commit()

        return jsonify(auth.view_model)
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
