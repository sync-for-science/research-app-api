''' Define the routes in the API blueprint.
'''
from flask import (
    Blueprint,
    jsonify,
    redirect,
    request,
)
from fhirclient.client import FHIRUnauthorizedException
from furl import furl

from research_app.authentication import requires_auth
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


@BP.route('/providers/<provider_id>/launch/<participant_id>', methods=['POST'])
@requires_auth
def launch_provider(provider_id, participant_id):
    ''' Launch a provider.
    '''
    provider = Provider.query.get(provider_id)
    participant = Participant.query.get(participant_id)

    # Begin the authorization and generate an authorize_url
    auth = participant.begin_authorization(provider)
    authorize_url = auth.authorize_url()

    # Save the interim FHIRClient state
    db.session.commit()

    return redirect(authorize_url)


@BP.route('/participants', methods=['POST'])
@requires_auth
def create_participant():
    ''' Create a new participant.
    '''
    participant = Participant()
    db.session.add(participant)
    db.session.commit()

    return jsonify(participant.view_model)


@BP.route('/participants/<participant_id>/authorizations', methods=['POST'])
@requires_auth
def create_authorization(participant_id):
    ''' Store an authorization.
    '''
    callback_url = furl(request.form.get('redirect_uri'))
    code = callback_url.args['code']
    state = callback_url.args['state']

    participant = Participant.query.get(participant_id)

    try:
        # Create the authorization
        auth = participant.complete_authorization(code, state)
        db.session.commit()

        return jsonify(auth.view_model)
    except FHIRUnauthorizedException as err:
        resp = jsonify({
            'error': type(err).__name__,
            'message': str(err.response.text),
        })
        resp.status_code = 500
        return resp
    except AuthorizationException as err:
        resp = jsonify({
            'error': type(err).__name__,
            'message': str(err),
        })
        resp.status_code = 500
        return resp


@BP.route('/participants/<participant_id>/authorizations')
@requires_auth
def list_authorizations(participant_id):
    ''' Get all the authorizations for a Participant.
    '''
    participant = Participant.query.get(participant_id)
    return jsonify(participant.authorizations)


@BP.route('/participants/<participant_id>/authorizations/<provider_id>/$everything')
@requires_auth
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
