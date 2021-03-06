#
# Flask-Watson
#
# Copyright (C) 2017 Boris Raicheff
# All rights reserved
#


import logging

import requests


logger = logging.getLogger('Flask-Watson')


class TextToSpeech(object):
    """
    https://www.ibm.com/watson/developercloud/text-to-speech.html
    """

    url = 'https://stream.watsonplatform.net/text-to-speech/api/v1'

    def init_app(self, app):
        session = requests.Session()
        username = app.config.get('WATSON_TEXTTOSPEECH_USERNAME')
        password = app.config.get('WATSON_TEXTTOSPEECH_PASSWORD')
        if not (username and password):
            logger.error('WATSON_TEXTTOSPEECH credentials not set')
            return
        session.auth = (username, password)
        headers = {
            'User-Agent': 'Flask-Watson/0.1.0 (https://github.com/raicheff/flask-watson)',
            'X-Watson-Learning-Opt-Out': '1',
        }
        session.headers.update(headers)
        self.session = session

    def synthesize(self, text, **kwargs):
        """
        http://www.ibm.com/watson/developercloud/text-to-speech/api/v1/#synthesize audio
        """
        response = self.session.post(self.url + '/synthesize', json={'text': text}, params=kwargs)
        response.raise_for_status()
        return response.content, response.headers['content-type']

    def get_voices(self):
        """
        http://www.ibm.com/watson/developercloud/text-to-speech/api/v1/#get_voices
        """
        headers = {'Accept': 'application/json'}
        response = self.session.get(self.url + '/voices', headers=headers)
        response.raise_for_status()
        return response.json()

    def get_token(self):
        """
        http://www.ibm.com/watson/developercloud/doc/getting_started/gs-tokens.shtml
        """
        url = 'https://stream.watsonplatform.net/authorization/api/v1/token'
        params = {'url': 'https://stream.watsonplatform.net/text-to-speech/api'}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.text


# EOF
