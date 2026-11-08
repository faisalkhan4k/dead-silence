import io
import json
import os
import urllib.error
import unittest
from unittest.mock import patch

import breath_language as language


class FakeResponse:
    def __init__(self, payload):
        self.stream = io.BytesIO(json.dumps(payload).encode('utf-8'))
    def __enter__(self): return self.stream
    def __exit__(self, *args): self.stream.close()


class GeminiLanguageTests(unittest.TestCase):
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'test-model'}, clear=True)
    @patch('breath_language.urllib.request.urlopen')
    def test_request_uses_header_and_extracts_output(self, urlopen):
        urlopen.return_value = FakeResponse({'candidates': [{'content': {'parts': [
            {'text': 'private thought', 'thought': True}, {'text': 'left'}, {'text': '\nright'}
        ]}}]})
        self.assertEqual(language.suggestions('move l'), 'left\nright')
        request = urlopen.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, 'https://generativelanguage.googleapis.com/v1beta/models/test-model:generateContent')
        self.assertNotIn('test-key', request.full_url)
        self.assertEqual(request.get_header('X-goog-api-key'), 'test-key')
        self.assertIn('move l', body['contents'][0]['parts'][0]['text'])

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}, clear=True)
    @patch('breath_language.urllib.request.urlopen')
    def test_reply_requests_json_and_validates_result(self, urlopen):
        urlopen.return_value = FakeResponse({'candidates': [{'content': {'parts': [
            {'text': '{"cleaned":"I have three", "reply":"Got it"}'}
        ]}}]})
        self.assertEqual(language.respond('I have threa'), ('I have three', 'Got it'))
        body = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(body['generationConfig']['responseMimeType'], 'application/json')

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}, clear=True)
    @patch('breath_language.urllib.request.urlopen')
    def test_empty_response_is_reported(self, urlopen):
        urlopen.return_value = FakeResponse({'candidates': []})
        with self.assertRaisesRegex(ValueError, 'no text'):
            language.generate('test')

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}, clear=True)
    @patch('breath_language.urllib.request.urlopen')
    def test_api_error_never_exposes_key(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError('https://example.test', 429, 'error', {}, None)
        with self.assertRaisesRegex(RuntimeError, 'HTTP 429') as result:
            language.generate('test')
        self.assertNotIn('test-key', str(result.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key_fails_before_network(self):
        with self.assertRaisesRegex(ValueError, 'GEMINI_API_KEY'):
            language.generate('test')

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': '../bad'}, clear=True)
    def test_invalid_model_fails_before_network(self):
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            language.generate('test')


if __name__ == '__main__': unittest.main()
