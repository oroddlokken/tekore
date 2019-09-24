import unittest
from unittest.mock import MagicMock, patch

from spotipy.auth import Token
from spotipy.util import (
    RefreshingToken,
    parse_code_from_url,
    prompt_for_user_token,
    read_environment
)


def make_token(value: str, expiring: bool):
    token = MagicMock()
    token.is_expiring.return_value = expiring
    token.access_token = value
    return token


class TestRefreshingToken(unittest.TestCase):
    def test_fresh_token_returned(self):
        low_token = make_token('token', False)
        cred = MagicMock()

        auto_token = RefreshingToken(low_token, cred)
        self.assertEqual(auto_token.access_token, 'token')

    def test_expiring_token_refreshed(self):
        expiring = make_token('expiring', True)
        refreshed = make_token('refreshed', False)
        cred = MagicMock()
        cred.refresh_token.return_value = refreshed

        auto_token = RefreshingToken(expiring, cred)
        self.assertEqual(auto_token.access_token, 'refreshed')

    def test_refreshing_token_has_same_attributes_as_regular(self):
        token_info = MagicMock()
        token = Token(token_info)
        cred = MagicMock()
        auto_token = RefreshingToken(token, cred)

        token_attributes = [a for a in dir(token) if not a.startswith('_')]
        auto_attributes = [a for a in dir(auto_token) if not a.startswith('_')]

        for attribute in token_attributes:
            with self.subTest(f'Attribute: `{attribute}`'):
                self.assertTrue(attribute in auto_attributes)


class TestReadEnvironment(unittest.TestCase):
    def test_environment_read_according_to_specified_names(self):
        import os
        id_name = 'SP_client_id'
        secret_name = 'SP_client_secret'
        uri_name = 'SP_redirect_uri'
        os.environ[id_name] = 'id'
        os.environ[secret_name] = 'secret'
        os.environ[uri_name] = 'uri'

        id_, secret, uri = read_environment(id_name, secret_name, uri_name)
        with self.subTest('Client ID'):
            self.assertEqual(id_, 'id')
        with self.subTest('Client secret'):
            self.assertEqual(secret, 'secret')
        with self.subTest('Redirect URI'):
            self.assertEqual(uri, 'uri')


class TestParseCodeFromURL(unittest.TestCase):
    def test_empty_url_raises(self):
        with self.assertRaises(KeyError):
            parse_code_from_url('')

    def test_no_code_raises(self):
        with self.assertRaises(KeyError):
            parse_code_from_url('http://example.com')

    def test_multiple_codes_raises(self):
        with self.assertRaises(KeyError):
            parse_code_from_url('http://example.com?code=1&code=2')

    def test_single_code_returned(self):
        r = parse_code_from_url('http://example.com?code=1')
        self.assertEqual(r, '1')


class TestPromptForToken(unittest.TestCase):
    def test_user_prompted_for_input(self):
        cred = MagicMock()
        cred.authorisation_url.return_value = 'http://example.com'
        cred.request_access_token.return_value = MagicMock()
        input_ = MagicMock(return_value='http://example.com?code=1')
        with patch('spotipy.util.Credentials', cred),\
                patch('spotipy.util.webbrowser', MagicMock()),\
                patch('spotipy.util.input', input_):
            prompt_for_user_token('', '', '')
            input_.assert_called_once()

    def test_refreshing_token_returned(self):
        cred = MagicMock()
        cred.authorisation_url.return_value = 'http://example.com'
        cred.request_access_token.return_value = MagicMock()
        input_ = MagicMock(return_value='http://example.com?code=1')
        with patch('spotipy.util.Credentials', cred),\
                patch('spotipy.util.webbrowser', MagicMock()),\
                patch('spotipy.util.input', input_):
            token = prompt_for_user_token('', '', '')
            self.assertIsInstance(token, RefreshingToken)


if __name__ == '__main__':
    unittest.main()