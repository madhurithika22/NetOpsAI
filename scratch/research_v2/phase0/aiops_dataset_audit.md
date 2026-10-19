# NetOps AIOps Dataset Audit

`AIOps2020Adapter` (`backend/app/adapters/aiops2020_adapter.py`) parses Excel/CSV files from `data/external/aiops_challenge_2020/`. The dataset is used strictly for offline metric computation; active MSVS probes and remediation execution loops are correctly disabled (`NOT_APPLICABLE`) for dataset runs.
