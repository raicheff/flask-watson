#
# Flask-Watson
#
# Copyright (C) 2017 Boris Raicheff
# All rights reserved
#


import logging

from flask import Blueprint

from .services.speech_to_text import SpeechToText
from .services.text_to_speech import TextToSpeech


logger = logging.getLogger('Flask-Watson')


class Watson(object):
    """
    Flask-Watson

    Documentation:
    https://flask-watson.readthedocs.io

    API:
    https://www.ibm.com/watson/developercloud

    SDK:
    https://github.com/watson-developer-cloud/python-sdk

    :param app: Flask app to initialize with. Defaults to `None`
    """

    blueprint = None

    def __init__(self, app=None, blueprint=None, url_prefix=None):
        self.speech_to_text = SpeechToText()
        self.text_to_speech = TextToSpeech()
        if app is not None:
            self.init_app(app, blueprint, url_prefix)

    def init_app(self, app, blueprint=None, url_prefix=None):

        # Blueprint
        if blueprint is None:
            blueprint = Blueprint('watson', __name__, url_prefix=url_prefix)
        self.blueprint = blueprint

        # Services
        self.speech_to_text.init_app(app, blueprint)
        self.text_to_speech.init_app(app)


# EOF
