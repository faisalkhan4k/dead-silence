"""Gemini language assistance and ElevenLabs speech output."""
import json, os, re, urllib.request, urllib.error
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env', override=False)


def generate(prompt, *, json_output=False):
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not key:
        raise ValueError('Add GEMINI_API_KEY to the project .env and restart the app.')
    model = os.environ.get('GEMINI_MODEL', '').strip() or 'gemini-3.5-flash-lite'
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', model):
        raise ValueError('GEMINI_MODEL contains unsupported characters.')
    config = {'maxOutputTokens': 1024, 'temperature': 0.2}
    if json_output:
        config['responseMimeType'] = 'application/json'
    payload = {'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': config}
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': key},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Gemini API request failed (HTTP {exc.code}); check key, model access, and quota.') from None
    except urllib.error.URLError:
        raise RuntimeError('Could not connect to the Gemini API; check your internet connection.') from None
    candidates = result.get('candidates') or []
    parts = candidates[0].get('content', {}).get('parts', []) if candidates else []
    output = ''.join(part.get('text', '') for part in parts if isinstance(part.get('text'), str) and not part.get('thought'))
    if not output.strip():
        raise ValueError('Gemini returned no text; try again or check model access.')
    return output.strip()


def suggestions(text):
    text = text[-500:]
    match = re.search(r'[A-Za-z]+$', text)
    prefix = match.group() if match else ''
    prompt = ('Suggest up to three likely next words or completions for the user message. '
              'Return only a JSON array of complete single English words, not word fragments. '
              'If a prefix is supplied, every word must start with that prefix; '
              'for prefix "l", return "left", never the suffix "eft". '
              'Return [] if no good suggestion is available. '
              'Prefix: ' + json.dumps(prefix) + '\nMessage: ' + json.dumps(text))
    values = json.loads(generate(prompt, json_output=True))
    if not isinstance(values, list):
        raise ValueError('Gemini returned suggestions in an unexpected format.')
    words = []
    for value in values:
        if (isinstance(value, str) and re.fullmatch(r'[A-Za-z]+', value)
                and value.lower().startswith(prefix.lower())
                and value.lower() not in {word.lower() for word in words}):
            words.append(value)
    return '\n'.join(words[:3])


def respond(text):
    prompt = ('You are a concise helpful crewmate in a voice chat. Correct obvious spelling in the message without changing its meaning. '
              'Then respond briefly to the corrected message. Return exactly JSON with keys cleaned and reply; no markdown. '
              'If uncertain preserve the original text. Message: ' + text[-1000:])
    data = json.loads(generate(prompt, json_output=True))
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) and data[k].strip() for k in ('cleaned', 'reply')):
        raise ValueError('Gemini did not return a valid cleaned message and reply.')
    return data['cleaned'], data['reply']


def speak(text):
    """Stream 24 kHz signed 16-bit mono PCM to the default audio device.

    The live UI invokes this in a worker and pauses microphone decoding until
    playback completes. Chunks can end between sample bytes; carry that byte
    to the next chunk. API keys and generated audio are not logged or saved.
    """
    key = os.environ.get('ELEVENLABS_API_KEY', '').strip()
    voice = os.environ.get('ELEVENLABS_VOICE_ID', '').strip()
    if not key:
        raise ValueError('Add ELEVENLABS_API_KEY to the project .env and restart the app.')
    if not voice:
        raise ValueError('Add ELEVENLABS_VOICE_ID to the project .env and restart the app.')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('There is no text to speak.')
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.core.api_error import ApiError
        import sounddevice as sd
    except ImportError:
        raise RuntimeError('Install the project requirements to use ElevenLabs speech.') from None
    model = os.environ.get('ELEVENLABS_MODEL_ID', '').strip() or 'eleven_flash_v2_5'
    try:
        client = ElevenLabs(api_key=key, timeout=30)
        chunks = client.text_to_speech.stream(
            voice_id=voice, text=text, model_id=model, output_format='pcm_24000')
        played = False
        pending = b''
        with sd.RawOutputStream(samplerate=24000, channels=1, dtype='int16') as output:
            for chunk in chunks:
                if not chunk:
                    continue
                data = pending + bytes(chunk)
                length = len(data) - len(data) % 2
                if length:
                    output.write(data[:length])
                    played = True
                pending = data[length:]
        if pending:
            raise ValueError('incomplete PCM')
        if not played:
            raise ValueError('empty audio')
    except ApiError as exc:
        status = exc.status_code if isinstance(exc.status_code, int) else None
        detail = f' (HTTP {status})' if status else ''
        raise RuntimeError(f'ElevenLabs request failed{detail}; check the API key, voice ID, access, and quota.') from None
    except sd.PortAudioError:
        raise RuntimeError('Could not play speech on the default Windows audio device.') from None
    except ValueError:
        raise RuntimeError('ElevenLabs returned incomplete or empty audio.') from None
    except Exception:
        # Never surface raw SDK exceptions, which may contain private request data.
        raise RuntimeError('ElevenLabs speech failed; check your connection and audio device.') from None
