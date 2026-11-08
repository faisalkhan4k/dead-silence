import os
import unittest
from unittest.mock import patch, MagicMock
from elevenlabs.core.api_error import ApiError
import sounddevice
import breath_language as language


class ElevenLabsSpeechTests(unittest.TestCase):
    @patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-secret', 'ELEVENLABS_VOICE_ID': 'test-voice'}, clear=True)
    @patch('sounddevice.RawOutputStream')
    @patch('elevenlabs.client.ElevenLabs')
    def test_streams_complete_pcm_samples_to_default_audio(self, client_type, output_type):
        client = client_type.return_value
        client.text_to_speech.stream.return_value = iter([b'\x01', b'\x02\x03', b'', b'\x04\x05\x06'])
        output = output_type.return_value.__enter__.return_value
        language.speak('Hello there')
        client_type.assert_called_once_with(api_key='test-secret', timeout=30)
        client.text_to_speech.stream.assert_called_once_with(
            voice_id='test-voice', text='Hello there', model_id='eleven_flash_v2_5', output_format='pcm_24000')
        output_type.assert_called_once_with(samplerate=24000, channels=1, dtype='int16')
        self.assertEqual([call.args[0] for call in output.write.call_args_list], [b'\x01\x02', b'\x03\x04\x05\x06'])

    @patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-secret'}, clear=True)
    def test_missing_voice_fails_before_request(self):
        with self.assertRaisesRegex(ValueError, 'ELEVENLABS_VOICE_ID'):
            language.speak('Hello')

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key_fails_before_request(self):
        with self.assertRaisesRegex(ValueError, 'ELEVENLABS_API_KEY'):
            language.speak('Hello')

    @patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-secret', 'ELEVENLABS_VOICE_ID': 'test-voice'}, clear=True)
    @patch('sounddevice.RawOutputStream')
    @patch('elevenlabs.client.ElevenLabs')
    def test_truncated_pcm_is_rejected(self, client_type, output_type):
        client_type.return_value.text_to_speech.stream.return_value = iter([b'\x01'])
        with self.assertRaisesRegex(RuntimeError, 'incomplete or empty audio'):
            language.speak('Hello')

    @patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-secret', 'ELEVENLABS_VOICE_ID': 'test-voice'}, clear=True)
    @patch('elevenlabs.client.ElevenLabs')
    def test_api_errors_are_sanitized(self, client_type):
        client_type.return_value.text_to_speech.stream.side_effect = ApiError(status_code=401, body={'detail':'test-secret'})
        with self.assertRaisesRegex(RuntimeError, 'HTTP 401') as caught:
            language.speak('Hello')
        self.assertNotIn('test-secret', str(caught.exception))


if __name__ == '__main__': unittest.main()

