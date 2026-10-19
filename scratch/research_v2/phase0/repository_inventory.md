# NetOps Repository Inventory

## 1. Executive Overview
The NetOps repository (`d:\NetOpsAI`) is a full-stack autonomous AI-assisted Network Operations system consisting of a FastAPI backend, a React/Vite web frontend, a Linux Network Namespace testbed integration, an explainable CADD diagnosis rule engine, a CESO telemetry provider layer, an LLM gateway supporting local Ollama models, an MSVS 5-stage safety validation engine, and an automated evaluation suite.

## 2. Directory Structure & Inventory
- **Backend Core** (`backend/app/`): 34 Python modules (3,480 LOC).
  - `adapters/`: AIOps Challenge 2020 v3.5 dataset reader (`aiops2020_adapter.py`).
  - `api/`: FastAPI route handlers (`cadd_routes.py`, `ceso_routes.py`, `evaluation_routes.py`, `llm_routes.py`, `msvs_routes.py`, `router.py`, `scenario_routes.py`, `simulation_routes.py`).
  - `cadd/`: Diagnostic rule engine and service (`engine.py`, `service.py`).
  - `ceso/`: Telemetry collection providers (`provider.py`, `service.py`, `simulator.py`).
  - `evaluation/`: Benchmark execution and metric computation (`metrics.py`, `models.py`, `recorder.py`, `runner.py`).
  - `llm/`: Model providers and context formatting (`gateway.py`, `prompts.py`, `token_metrics.py`, `providers/base.py`, `providers/mock.py`, `providers/ollama.py`, `providers/openai.py`).
  - `models/`: Pydantic data schemas (`cadd_models.py`, `ceso_models.py`, `msvs_models.py`).
  - `msvs/`: Safety policy validator, approval queue, and execution coordinator (`policies.py`, `service.py`, `metrics.py`, `benchmark.py`).
  - `scenarios/`: Topology cases 01 to 04 (`base.py`, `case01_enterprise.py`, `case02_wan.py`, `case03_datacenter.py`, `case04_hybrid.py`, `registry.py`).
  - `testbed/`: Linux Network Namespace management and tc/ip fault injection (`config.py`, `faults.py`, `manager.py`).
- **Frontend Core** (`frontend/`): React 18.2 + Vite interface with 13 custom visualizer components (`TopologyMap.jsx`, `SpatialNetworkGraph.jsx`, `EvaluationDashboard.jsx`, etc.).
- **Tests** (`tests/`): 23 test files covering unit tests, workflow integrations, Linux testbed safety, and benchmark runners.
- **Data & Benchmark Artifacts** (`data/`, `scratch/`): Contains AIOps 2020 v3.5 raw dataset, Phase 7a benchmark JSON results, and Ollama experiment logs.
