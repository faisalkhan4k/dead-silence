"""Gemini language assistance and Windows speech output."""
import json, os, re, subprocess, urllib.request, urllib.error
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
    prompt = ('Suggest up to 3 possible next words or completions for the user message below. '
              'If the final word is unfinished, every suggestion must start with that word. '
              'Output only single words, one per line; no numbering or punctuation. Message:\n' + text[-500:])
    return generate(prompt)


def respond(text):
    prompt = ('You are a concise helpful crewmate in a voice chat. Correct obvious spelling in the message without changing its meaning. '
              'Then respond briefly to the corrected message. Return exactly JSON with keys cleaned and reply; no markdown. '
              'If uncertain preserve the original text. Message: ' + text[-1000:])
    data = json.loads(generate(prompt, json_output=True))
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) and data[k].strip() for k in ('cleaned', 'reply')):
        raise ValueError('Gemini did not return a valid cleaned message and reply.')
    return data['cleaned'], data['reply']


def speak(text):
    # The message is passed over stdin, never interpolated into the PowerShell command.
    script="Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SetOutputToDefaultAudioDevice(); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()"
    proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],input=text,
                        text=True,encoding='utf-8',capture_output=True,timeout=60,
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if proc.returncode: raise RuntimeError(proc.stderr.strip() or 'Speech output failed')
