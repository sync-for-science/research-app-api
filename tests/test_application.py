# pylint: disable=missing-docstring
from research_app import application


def test_create_app():
    assert application.create_app()
