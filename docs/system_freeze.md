# STRATA — Formal System & Analytical Freeze

**Document Version**: 1.0.0  
**Freeze Status**: IMMUTABLE SYSTEM FREEZE  
**Effective Date**: September 17, 2026  
**Analytical Pipeline Version**: `1.0.0`

---

## 1. Purpose of System Freeze

This document establishes an official and immutable system freeze for the **STRATA** (**Structural Temporal Analysis & Threat Assessment**) platform at the completion of Phase 9.

### STRICT POLICY: No Post-Freeze Scientific Modification
As of this freeze:
- **No scientific tuning** of the ML Deformation Classifier is permitted without incrementing `ML_MODEL_VERSION`.
- **No heuristic rule adjustments** of the Physics Consistency Engine are permitted without incrementing `PHYSICS_ENGINE_VERSION`.
- **No weight modifications or decision hierarchy changes** in the Cross-Model Consensus, Temporal Kinematics, or Infrastructure Risk Characterization engines are permitted without corresponding semantic version increments.
- **No benchmark data manipulation** is permitted.

Any future scientific research, fine-tuning, or model updates must be branched into a separate, distinct version track.

---

## 2. Component Semantic Version Registry

The following versions are registered in `backend/app/core/versions.py` and are recorded in every `AnalysisResult` and `ChronologyRecord`:

| Component Subsystem | Registered Semantic Version | Implementation Path | Status |
| :--- | :--- | :--- | :--- |
| **Pipeline Coordinator** | `1.0.0` | `backend/app/services/pipeline/service.py` | FROZEN |
| **ML Deformation Classifier** | `0.1.0` | `backend/app/services/ml/classifier.py` | FROZEN |
| **Feature Schema & Extractor** | `0.1.0` | `backend/app/services/ml/features.py` | FROZEN |
| **Physics InSAR Consistency Engine** | `0.2.1` | `backend/app/services/physics/engine.py` | FROZEN |
| **Cross-Model Consensus Engine** | `strata_consensus_v0.1.0` | `backend/app/services/consensus/engine.py` | FROZEN |
| **Temporal Evidence Engine** | `strata_temporal_v1_0_0` | `backend/app/services/temporal/engine.py` | FROZEN |
| **Risk Characterization Engine** | `strata_risk_v1_0_0` | `backend/app/services/risk/engine.py` | FROZEN |
| **Evidence Chronicle (SHA-256)** | `1.0.0` | `backend/app/services/chronology/service.py` | FROZEN |
| **Threshold Registry** | `1.0.0` | `docs/system_integration.md` | FROZEN |

---

## 3. Dataset Versions & Provenance Classification

| Dataset Track | Record Count | Location | Provenance Status |
| :--- | :--- | :--- | :--- |
| **Controlled Synthetic Dataset** | 3,500 sequences (7 classes, 70/15/15 split) | `data/synthetic/dataset/` | Controlled Synthetic Benchmark |
| **Case-Study External Placeholders** | 5 datasets (52 epochs each) | `data/real/` | `SYNTHETIC / CASE-STUDY PLACEHOLDER` |

*Note*: As documented in the Phase 8.1 scientific audit, all datasets under `data/real/` represent literature-calibrated parametric time-series placeholders, not raw satellite Single Look Complex (SLC) radar scenes. They are frozen as external case-study evaluation benchmarks.

---

## 4. Test Suite Baseline

The frozen codebase satisfies:
- **Total Tests**: `202 passed`
- **Total Regressions**: `0`
- **Warnings**: `3` (Standard deprecation warnings for HTTPX/AnyIO)
- **Execution Command**: `.venv/bin/pytest backend/tests`

---

## 5. Repository Environment Baseline

- **Python Runtime**: `Python 3.14.6`
- **Operating System**: macOS (Darwin 25.0.0 arm64)
- **Database**: SQLite / SQLAlchemy 2.0 (TestingSessionLocal & StaticPool)
- **FastAPI Core**: FastAPI 0.115+ / Pydantic v2
