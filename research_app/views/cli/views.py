''' CLI commands.
'''
from flask import Blueprint
import yaml

from research_app.application import app
from research_app.extensions import db
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

    for row in config:
        provider = Provider(**row)
        db.session.add(provider)
    db.session.commit()
