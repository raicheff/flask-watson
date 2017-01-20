#
# Flask-Watson
#
# Copyright (C) 2017 Boris Raicheff
# All rights reserved
#


import base64
import hashlib
import hmac
import logging
import uuid

import itsdangerous
import requests

from flask import Response, abort, request, url_for
from flask.signals import Namespace
from six.moves.http_client import BAD_REQUEST, OK


logger = logging.getLogger('Flask-Watson')


namespace = Namespace()


recognitions_started = namespace.signal('recognitions.started')
recognitions_completed = namespace.signal('recognitions.completed')
recognitions_completed_with_results = namespace.signal('recognitions.completed_with_results')
recognitions_failed = namespace.signal('recognitions.failed')


BASE_URL = 'https://stream.watsonplatform.net/speech-to-text/api/v1'

ENDPOINT = 'watson-speech-to-text'


class SpeechToText(object):
    """
    https://www.ibm.com/watson/developercloud/speech-to-text.html
    """

    session = None

    blueprint = None

    user_secret = None

    def init_app(self, app, blueprint=None):

        # Session
        session = requests.Session()
        username = app.config.get('WATSON_SPEECHTOTEXT_USERNAME')
        password = app.config.get('WATSON_SPEECHTOTEXT_PASSWORD')
        if not (username and password):
            logger.error('WATSON_SPEECHTOTEXT credentials not set')
            return
        session.auth = (username, password)
        session.headers.update({'X-Watson-Learning-Opt-Out': '1'})
        self.session = session

        # Blueprint
        blueprint.add_url_rule('/watson/speech-to-text', ENDPOINT, self.handle_callback, methods=['GET', 'POST'])
        self.blueprint = blueprint

        # Secret
        user_secret = app.config.get('WATSON_SPEECHTOTEXT_USER_SECRET')
        if user_secret is None:
            logger.error('WATSON_SPEECHTOTEXT_USER_SECRET not set')
            return
        self.user_secret = user_secret

    def recognize(self, data, content_type, user_token=None, **kwargs):
        """
        http://www.ibm.com/watson/developercloud/speech-to-text/api/v1/#async_methods
        """
        user_token = user_token or uuid.uuid4().hex
        headers = {'content-type': content_type}
        params = {'callback_url': self._callback_url, 'user_token': user_token, **kwargs}
        response = self.session.post(BASE_URL + '/recognitions', data=data, headers=headers, params=params)
        response.raise_for_status()
        return response.json(), user_token

    def check_job(self, id):
        """
        http://www.ibm.com/watson/developercloud/speech-to-text/api/v1/#check_job
        """
        response = self.session.get(BASE_URL + '/recognitions/{id}'.format(id=id))
        response.raise_for_status()
        return response.json()

    def delete_job(self, id):
        """
        http://www.ibm.com/watson/developercloud/speech-to-text/api/v1/#delete_job
        """
        self.session.delete(BASE_URL + '/recognitions/{id}'.format(id=id)).raise_for_status()

    def register_callback(self):
        """
        http://www.ibm.com/watson/developercloud/doc/speech-to-text/async.shtml#register
        """
        params = {'callback_url': self._callback_url, 'user_secret': self.user_secret}
        response = self.session.post(BASE_URL + '/register_callback', params=params)
        response.raise_for_status()
        return response.json()

    def handle_callback(self):
        """
        http://www.ibm.com/watson/developercloud/speech-to-text/api/v1/#async_methods
        """

        # White-list
        if request.method == 'GET':
            challenge_string = request.args.get('challenge_string')
            if challenge_string is None:
                abort(BAD_REQUEST)
            self._abort_for_signature(challenge_string.encode())
            return challenge_string

        # Notification
        self._abort_for_signature(request.get_data())
        notification = request.get_json(silent=True)
        if notification is None:
            abort(BAD_REQUEST)
        event = notification.pop('event', None)
        if event is None:
            abort(BAD_REQUEST)
        namespace.signal(event).send(self, **notification)
        return Response(status=OK)

    def _abort_for_signature(self, message):
        signature = request.headers.get('x-callback-signature')
        if signature is None:
            abort(BAD_REQUEST)
        digest = hmac.new(self.user_secret.encode(), message, hashlib.sha1).digest()
        if not itsdangerous.constant_time_compare(base64.b64encode(digest), signature.encode()):
            abort(BAD_REQUEST)

    @property
    def _callback_url(self):
        return url_for('.'.join((self.blueprint.name, ENDPOINT)), _external=True)


# EOF
