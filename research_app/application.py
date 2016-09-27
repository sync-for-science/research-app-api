''' The application.
'''
from flask import Flask


# Create and configure application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def create_app():
    ''' The application factory.
    '''
    from research_app import (
        extensions,
    )
    from research_app.views.api.views import BP as api_blueprint

    # Register blueprints
    app.register_blueprint(api_blueprint)

    # Init extensions
    extensions.db.init_app(app)

    return app
