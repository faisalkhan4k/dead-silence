# dead-silence

A Windows headset-microphone prototype for detecting inhale/exhale in 50 ms windows and using breath codes to enter letters. It includes guided recording, model training, adjustable timing, local MLflow metrics, optional Groq text assistance and Windows speech output. This is experimental and is not a reliable assistive communication system.

## Setup

1. Install Python 3.13 and create a virtual environment: `py -3.13 -m venv .venv`.
2. Run `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and add `GROQ_API_KEY` if using text suggestions and replies. `GEMINI_API_KEY` is reserved for later; it is not used. The application sends text to Groq, not microphone audio.
4. Connect a microphone and run `Start Breath Dataset.cmd`. Record the prompted training and held-out examples; keep raw audio private.
5. Train the separate 50 ms model: `.venv\Scripts\python.exe breath_live.py --train`.
6. Run `Start Live Breath.cmd`, select the microphone, and click Start. The latest complete local dataset is selected.

## Operation

Inhale is 1; exhale is 2. Letter codes are in `breath_decoder.py`. Pause 0.8 seconds after the last breath for a letter and 2 seconds for a word space. A long inhale deletes; a long exhale sends. Thresholds and recovery time are adjustable. These thresholds act on smoothed model predictions, not direct measurements of breath duration. The current model has weak labels and long controls require validation with new data.

For timing experiments, enter an optional target phrase, set thresholds, press Start, record a comfort rating, and select Stop and log. The local MLflow database stores thresholds, latency, comfort, and target-match metrics, not the target text. Final text may contain manual or model edits, so scores do not isolate classifier accuracy. Model and recorded audio are deliberately excluded from version control: do not load untrusted pickle models.

Current accuracy results apply only to the original limited test set. A separately labeled continuous-breath evaluation is needed to measure event and sequence accuracy. The code requires headset mic input and Windows speech output; no speaker probe is used.

Run `Start Breath Sequences.cmd` to collect sequence-level examples (no event timestamps). The collector saves raw audio locally under the ignored `breath_sequence_dataset/`; it does not perform evaluation or log to MLflow. During live typing, a word pause accepts the matching ghost completion if one is available.
