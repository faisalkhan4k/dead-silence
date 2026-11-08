# Inhale/exhale pilot

Microphone-only; six broadband energy bands across 12 time bins.
Guided trials; training fit is not independent validation. Held-out trials follow headset repositioning.
A balanced two-class chance baseline is 50%.

| Model | Training fit | Held-out accuracy |
|---|---:|---:|
| SVM | 100.0% | 95.0% |
| RandomForest | 100.0% | 100.0% |
| LightGBM | 100.0% | 100.0% |
| XGBoost | 100.0% | 100.0% |

See evaluation.json for class metrics, confusion matrices and prediction probabilities.
Top-3 accuracy is not meaningful for two classes. Continuous breathing, segmentation and alphabet decoding are not tested.
