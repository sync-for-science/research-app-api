''' CLI commands.
'''
import click
from flask import Blueprint
import yaml

from research_app.application import app
from research_app.extensions import db
from research_app.models.participants import Authorization, Participant
from research_app.models.providers import Provider


BP = Blueprint('cli', __name__)


@app.cli.command()
def initdb():
    ''' Initialize the database.
    '''
    db.create_all()


@app.cli.command()
def create_providers():
    ''' Create provider records.
    '''
    with open('./providers.yml') as handle:
        config = yaml.load(handle)

    # Truncate existing records
    Provider.query.delete()

    for row in config:
        provider = Provider(**row)
        db.session.add(provider)
    db.session.commit()


@app.cli.command()
def create_participant():
    ''' Create a new participant.
    '''
    participant = Participant()
    db.session.add(participant)
    db.session.commit()


@app.cli.command()
@click.option('--participant', default=None, help='Participant id', type=int)
@click.option('--provider', default=None, help='Provider id', type=int)
def sync_fhir_resources(participant, provider):
    ''' Download all authorized FHIR resources.
    '''
    conditions = {
        'status': Authorization.STATUS_ACTIVE,
    }
    if participant:
        conditions['_participant_id'] = participant
    if provider:
        conditions['_provider_id'] = provider

    authorizations = Authorization.query.filter_by(**conditions)

    try:
        for auth in authorizations:
            auth.fetch_resources()
    finally:
        db.session.commit()
