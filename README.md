# dead-silence

A Windows headset-microphone prototype for detecting inhale/exhale in 50 ms windows and using breath codes to enter letters. It includes guided recording, model training, adjustable timing, local MLflow metrics, optional Gemini text assistance and ElevenLabs speech output. This is experimental and is not a reliable assistive communication system.

## Setup

1. Install Python 3.13 and create a virtual environment: `py -3.13 -m venv .venv`.
2. Run `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` if using text suggestions and replies. The application sends text to Gemini, not microphone audio. For speech, set `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` in `.env` and choose your headset as the default Windows output device. `ELEVENLABS_MODEL_ID` is optional and defaults to `eleven_flash_v2_5`. The default language model is `gemini-3.5-flash-lite`; set `GEMINI_MODEL` in `.env` to choose another available model.
4. Connect a microphone and run `Start Breath Dataset.cmd`. Record the prompted training and held-out examples; keep raw audio private.
5. Train the separate 50 ms model: `.venv\Scripts\python.exe breath_live.py --train`.
6. Run `Start Live Breath.cmd`, select the microphone, and click Start. The latest complete local dataset is selected.
7. To test the selected ElevenLabs voice separately, run `Start ElevenLabs Voice Test.cmd`. The test sends a short sample sentence to ElevenLabs and plays it on the default output device.

## Operation

Inhale is 1; exhale is 2. Every letter uses exactly five breaths. The keyboard shows all codes; 22121 deletes. A completed code is committed when the fifth breath ends; wait for the configurable between-letter pause (default 0.8 s) before starting the next. If a code remains incomplete for the word gap (default 2 s), it is discarded. Following a completed letter, the word gap adds a space and the send gap (default 4 s) sends. Thresholds measure classified silence, not physical silence. A fixed length cannot distinguish background noise from a breath; false detections remain possible.

For timing experiments, enter an optional target phrase, set thresholds, press Start, record a comfort rating, and select Stop and log. The local MLflow database stores thresholds, latency, comfort, and target-match metrics, not the target text. Final text may contain manual or model edits, so scores do not isolate classifier accuracy. Model and recorded audio are deliberately excluded from version control: do not load untrusted pickle models.

Current accuracy results apply only to the original limited test set. A separately labeled continuous-breath evaluation is needed to measure event and sequence accuracy. The code requires headset mic input and Windows audio output; no speaker probe is used. The AI reply is sent to ElevenLabs for speech generation and streamed as 24 kHz mono PCM to the default Windows output. ElevenLabs requests may incur charges. The app pauses breath inference during generation and playback. ElevenLabs errors are shown without logging request data or falling back silently to a different voice.

Run `Start Breath Sequences.cmd` to collect sequence-level examples (no event timestamps). The collector saves raw audio locally under the ignored `breath_sequence_dataset/`; it does not perform evaluation or log to MLflow. During live typing, a word pause accepts the matching ghost completion if one is available. The sequence collector includes older protocol prompts; older recordings of long-breath commands retain their original metadata.

## Breath and background recordings

Run `Start Breath Noise Dataset.cmd` to collect intentional inhale, intentional exhale, and no-intentional-breath clips under selectable background conditions. Train and held-out clips should be from separate sittings. The intended category labels each whole clip, not individual 50 ms windows; annotate actual breath boundaries before frame-level training. Audio is saved locally in the ignored `breath_noise_dataset/` directory. This collector does not retrain the model.

Run `Start Breath Annotator.cmd` to review the noise-dataset WAVs. Drag the shaded selection over a clearly audible interval, play the selection, and mark it as INHALE, EXHALE, or NO_BREATH; click Save markers before moving to the next clip. Green, red and gold show the respective marked intervals. Recordings and markers remain local under the ignored dataset directory. Unmarked audio is unlabeled, not automatically silence. Markers are saved as sample indices in annotations.json; this tool does not train a model.

`propose_breath_markers.py --apply` can create provisional amplitude-based annotations without overwriting existing markers. The largest amplitude change may be speech or background noise rather than a breath. No-breath clips are labeled across the whole clip according to their intended category. These AUTO markers are not human-verified ground truth and should be reviewed before they are used as training or evaluation labels. The script without `--apply` only reports proposals.

Run `python train_noisy_candidate.py` to train a separate candidate from the original training windows and provisional noise-dataset markers. It compares the original and candidate on the original held-out windows and noisy clips assigned to held-out, stores results and candidate under the ignored `breath_noise_dataset/experiments/` directory, and logs aggregate metrics to local MLflow. Automatic amplitude markers and old prompt-window labels are weak, windows within clips are correlated, and the noisy results are not verified accuracy. The candidate is not automatically installed as the live model.

When `breath_noise_dataset/active_model.pkl` exists, the live app loads that locally selected model; otherwise it loads the original model. The title identifies which is active. Both model files and data remain excluded from Git. Automatic amplitude annotations are weak labels and no verified live-accuracy claim follows from selecting the model.
