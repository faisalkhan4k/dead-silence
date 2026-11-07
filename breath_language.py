"""Groq language assistance and Windows speech output."""
import json, os, subprocess, urllib.request, urllib.error
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

URL = 'https://api.groq.com/openai/v1/chat/completions'

def generate(prompt):
    key=os.environ.get('GROQ_API_KEY', '').strip()
    if not key: raise ValueError('Add GROQ_API_KEY to apps/acoustic-sensing/.env and restart the app.')
    model=os.environ.get('GROQ_MODEL', '').strip() or 'llama-3.3-70b-versatile'
    payload=json.dumps({'model':model, 'messages':[{'role':'user','content':prompt}],
                        'max_completion_tokens':300, 'temperature':0.2}).encode('utf-8')
    request=urllib.request.Request(URL, data=payload, headers={'Content-Type':'application/json', 'Authorization':'Bearer '+key})
    try:
        with urllib.request.urlopen(request,timeout=45) as response:
            result=json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Groq API request failed (HTTP {exc.code}); check key, model access and billing.') from None
    choices=result.get('choices') or []
    output=choices[0].get('message',{}).get('content') if choices else None
    if not isinstance(output,str) or not output.strip(): raise ValueError('Groq returned no text.')
    return output.strip()

def suggestions(text):
    prompt=('Suggest up to 3 possible next words or completions for the user message below. '
            'If the final word is unfinished, every suggestion must start with that word. '
            'Output only single words, one per line; no numbering or punctuation. Message:\n'+text[-500:])
    return generate(prompt)

def respond(text):
    prompt=('You are a concise helpful crewmate in a voice chat. Correct obvious spelling in the message without changing its meaning. '
            'Then respond briefly to the corrected message. Return exactly JSON with keys cleaned and reply; no markdown. '
            'If uncertain preserve the original text. Message: '+text[-1000:])
    data=json.loads(generate(prompt))
    return str(data['cleaned']),str(data['reply'])

def speak(text):
    # The message is passed over stdin, never interpolated into the PowerShell command.
    script="Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SetOutputToDefaultAudioDevice(); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()"
    proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],input=text,
                        text=True,encoding='utf-8',capture_output=True,timeout=60,
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if proc.returncode: raise RuntimeError(proc.stderr.strip() or 'Speech output failed')
