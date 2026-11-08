# dead-silence

A Windows headset-microphone prototype for detecting inhale/exhale in 50 ms windows and using breath codes to enter letters. It includes guided recording, model training, adjustable timing, local MLflow metrics, optional Gemini text assistance and Windows speech output. This is experimental and is not a reliable assistive communication system.

## Setup

1. Install Python 3.13 and create a virtual environment: `py -3.13 -m venv .venv`.
2. Run `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` if using text suggestions and replies. The application sends text to Gemini, not microphone audio. The default language model is `gemini-3.5-flash-lite`; set `GEMINI_MODEL` in `.env` to choose another available model.
4. Connect a microphone and run `Start Breath Dataset.cmd`. Record the prompted training and held-out examples; keep raw audio private.
5. Train the separate 50 ms model: `.venv\Scripts\python.exe breath_live.py --train`.
6. Run `Start Live Breath.cmd`, select the microphone, and click Start. The latest complete local dataset is selected.

## Operation

Inhale is 1; exhale is 2. Letter codes are shown in the on-screen keyboard and defined in `breath_decoder.py`; the previously unassigned code `2211` deletes the last letter. On one continuous silence, the defaults are 0.8 seconds to commit a letter, 2 seconds to accept a matching ghost suggestion and add a word space, and 4 seconds to send the message. The app shows a send countdown. Any newly detected breath before the send threshold restarts the silence timer. A single long pause sends at most once until more input has been entered. Set the three thresholds before starting; they must be in increasing order. They measure smoothed classifier output, not physical silence. The thresholds are provisional and a natural four-second pause may send unexpectedly. The decoder buffers at most five digits per code. All currently assigned letters and the delete command use at most four digits, so a five-digit code is unassigned. If more than five digits are entered before the letter pause, the entire sequence is rejected; pause before starting the next code.

For timing experiments, enter an optional target phrase, set thresholds, press Start, record a comfort rating, and select Stop and log. The local MLflow database stores thresholds, latency, comfort, and target-match metrics, not the target text. Final text may contain manual or model edits, so scores do not isolate classifier accuracy. Model and recorded audio are deliberately excluded from version control: do not load untrusted pickle models.

Current accuracy results apply only to the original limited test set. A separately labeled continuous-breath evaluation is needed to measure event and sequence accuracy. The code requires headset mic input and Windows speech output; no speaker probe is used. Speech uses the default installed Windows `System.Speech` voice and the default Windows audio output, not a hosted neural TTS model.

Run `Start Breath Sequences.cmd` to collect sequence-level examples (no event timestamps). The collector saves raw audio locally under the ignored `breath_sequence_dataset/`; it does not perform evaluation or log to MLflow. During live typing, a word pause accepts the matching ghost completion if one is available. The sequence collector has separate prompts for `2211` (delete) and a four-second send pause; older recordings of long-breath commands retain their original metadata.
