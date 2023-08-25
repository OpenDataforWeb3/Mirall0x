import datetime
import requests

class _BearerAuth(requests.auth.AuthBase):
    def __init__(self, key):
        self.key = key
    def __call__(self, r):
        r.headers['authorization'] = 'Bearer ' + self.key
        return r

class W3Exception(Exception):
    def __init__(self, response, *params):
        try:
            json = response.json()
            params = (json['name'], json['message'], *params)
        except:
            params = (response.text, *params)
        super().__init__(*params)

class W3BadRequest(W3Exception):
    pass

class W3Unauthorized(W3Exception):
    pass

class W3Forbidden(W3Exception):
    pass

class W3InternalServerError(W3Exception):
    pass

class W3HTTPError(W3Exception):
    pass

class API:
    def __init__(self, token = None, url = 'https://api.web3.storage'):
        self._url = url
        self._auth = _BearerAuth(token) if token is not None else None

    def status(self, cid):
        r = self._get('status', str(cid))
        return r.json()

    def post_upload(self, *files):

        r = self._post(
            'upload',
            files=[
                ('file', file)
                for file in files
            ]
        )
        return r.json()['cid']

    def user_uploads(self, before: str = None, size: int = None):

        params = {}
        if before is not None:
            if type(before) is int:
                before = datetime.datetime.fromtimestamp()
            elif type(before) is str:
                before = datetime.datetime.fromisoformat(before)
            before = before.isoformat()
            params['before'] = before
        if size is not None:
            params['size'] = int(size)
        r = self._get('user', 'uploads', params=params)
        return r.json()

    def _head(self, *params, **kwparams):
        return self._request(*params, method='HEAD', **kwparams)
    def _get(self, *params, **kwparams):
        return self._request(*params, method='GET', **kwparams)
    def _post(self, *params, **kwparams):
        return self._request(*params, method='POST', **kwparams)
    def _request(self, *params, **kwparams):
        params = (self._url, *params)
        if self._auth is not None and 'auth' not in kwparams:
            kwparams['auth'] = self._auth
        r = requests.request(url='/'.join(params), **kwparams)
        try:
            r.raise_for_status()
            return r
        except Exception as exception:
            http_exception = exception
        if r.status_code == 400:
            raise W3BadRequest(r)
        elif r.status_code == 401:
            raise W3Unauthorized(r)
        elif r.status_code == 403:
            raise W3Forbidden(r)
        elif r.status_code >= 500 and r.status_code < 600:
            raise W3InternalServerError(r)
        else:
            raise W3HTTPError(r, r.status_code, http_exception)