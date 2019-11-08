import json
import logging
import math
import requests
import os

from enum import Enum
from urllib.parse import urlparse, parse_qs, urlencode

from .__version__ import __version__
from .exceptions import AHException, AHBadRequestException, AHUnauthorizedException

logFormatter = logging.Formatter("AHClient: %(asctime)s [%(levelname)-7.7s]  %(message)s")
logger = logging.getLogger()

logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

API_VERSION = '6.0'

BASE_API_URL = 'https://search.amazinghiring.com/api/v6/'

PER_PAGE = 50

class HTTP_METHOD(Enum):
    GET = 'get'
    POST = 'post'

class AHClient:
    def __init__(self, token, version=API_VERSION):
        self.token = token
        self.version = version

    def _raise_for_error(self, response):
        code = response.status_code
        response_json = {}

        try:
            response_json = response.json()
        except Exception:
            pass

        if type(response_json) is dict:
            error_message = response_json.get('detail', response.text)
        else:
            error_message = response.text

        if code == 400:
            raise AHBadRequestException(error_message)
        elif code == 401:
            raise AHUnauthorizedException(error_message)
        elif code > 399:
            raise AHException(error_message)

        return

    def _request(self, method, path, params=None, headers=None, **kwargs):
        request = getattr(requests, method.value)

        if params:
            params = {key: value for key, value in params.items() if params[key]}
            params = '?' + urlencode(params) if params else ''
        else:
            params = ''
        url = f'{BASE_API_URL}{path}/{params}'
        

        if headers is None:
            headers = {}

        headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Token {self.token}',
        })

        logger.info(f'Requesting {url}...')

        response = request(url, headers=headers, **kwargs)

        self._raise_for_error(response)

        response_headers = response.headers
        response_json = response.json()

        pages_count = 0

        if 'Link' in response_headers:
            links = response_headers.get('Link').split(',')
            last_link_href = links[-1].strip('<>').split(';')[0]
            pages_count = int(parse_qs(urlparse(last_link_href).query).get('page', [0])[0])
        elif 'count' in response_json and 'next' in response_json:
            pages_count = math.ceil(response_json.get('count') / PER_PAGE)

        logger.info(f'Pages: {pages_count}')

        return response_json, pages_count

    def get_users(self):
        """ List of Amazing Hiring users """
        result, pages_count = self._request(HTTP_METHOD.GET, f'users')
        return result
    
    def get_profile(self, profile_id:int):
        """
            Profile by id

            Parameters
            ----------
            profile_id : int
                Profile id
        """
        result, pages_count = self._request(HTTP_METHOD.GET, f'profiles/{profile_id}')
        return result
    
    def get_folders_statuses(self):
        """ Available folders statuses """
        result, pages_count = self._request(HTTP_METHOD.GET, f'status_collection/statuses')
        return result

    def get_folders(self):
        """ List of folders """
        result, pages_count = self._request(HTTP_METHOD.GET, f'folders')
        yield result

        if pages_count > 0:
            for p in range(2, pages_count + 1):
                yield self._request(HTTP_METHOD.GET, f'folders', params={'page': p})[0]

    def get_folder(self, folder_id):
        """ 
            Folder by id

            Parameters
            ----------
            folder_id : int
                Folder id
        """
        result, pages_count = self._request(HTTP_METHOD.GET, f'folders/{folder_id}')
        return result
    
    def get_folder_candidates(self, folder_id:int, status_id:int=None):
        """ 
            List of candidates in folder

            Parameters
            ----------
            folder_id : int
                Folder id
            status_id : int
                Optional. Filder by status id
        """
        params = {
            'vacancy': folder_id,
            'status': status_id,
        }
        result, pages_count = self._request(HTTP_METHOD.GET, f'candidates', params=params)
        yield result.get('results')

        if pages_count > 0:
            for p in range(1, pages_count):
                params.update({
                    'limit': PER_PAGE, 
                    'offset': p * PER_PAGE,
                })
                yield self._request(HTTP_METHOD.GET, f'candidates', params=params)[0].get('results')
