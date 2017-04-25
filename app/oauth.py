from flask import url_for, current_app, redirect, request
from rauth import OAuth2Service
import json, urllib3

class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name, _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers={}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        urllib3.disable_warnings()
        http = urllib3.PoolManager()
        googleinfo = http.request('GET', 'https://accounts.google.com/.well-known/openid-configuration')
        google_params = json.loads(googleinfo.data.decode('utf-8'))
        self.service = OAuth2Service(
            name='google',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url=google_params.get('authorization_endpoint'),
            base_url=google_params.get('userinfo_endpoint'),
            access_token_url=google_params.get('token_endpoint')
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None

        data={'code': request.args['code'],
              'grant_type': 'authorization_code',
              'redirect_uri': self.get_callback_url()
             }
        oauth_session = self.service.get_auth_session(
                data=data, decoder=oauth_decode
        )
        me = oauth_session.get('').json()
        return (None, me['name'], me['email']) # (nickname, name, email)


class FacebookSignIn(OAuthSignIn):
    def __init__(self):
        super(FacebookSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name='facebook',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None

        data={'code': request.args['code'],
              'grant_type': 'authorization_code',
              'redirect_uri': self.get_callback_url()
             }
        oauth_session = self.service.get_auth_session(
                data=data, decoder=oauth_decode
        )
        me = oauth_session.get('me?fields=email').json()
        return (None, None, me['email']) # (nickname, name, email)


def oauth_decode(data):
    new_data = data.decode("utf-8", "strict")
    return json.loads(new_data)
