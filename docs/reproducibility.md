# STRATA — Complete Reproducibility Package & Audit Instructions

**Document Version**: 1.0.0  
**Status**: AUDIT VERIFICATION MANUAL  
**Analytical Pipeline Version**: `1.0.0`

This document provides exact, deterministic commands to reproduce all evaluations, tests, datasets, and demonstrations across the STRATA repository.

---

## 1. System Environment

```bash
# Verify Python Runtime
.venv/bin/python --version
# Expected: Python 3.14.6 (or Python 3.10+ compatible)

# Verify Operating System
uname -a
# Expected: Darwin 25.0.0 (or Linux kernel 5.4+)
```

---

## 2. Automated Test Suite Execution (202 / 202 Tests)

Run the full, regression-free test suite:
```bash
.venv/bin/pytest backend/tests
```
Expected output:
```text
======================= 202 passed, 3 warnings in ~10s =======================
```

To run individual phase test suites:
```bash
# Phase 1 & Normalization
.venv/bin/pytest backend/tests/test_observations.py backend/tests/test_analysis.py

# Phase 2 & Physics Consistency
.venv/bin/pytest backend/tests/test_physics_units.py backend/tests/test_physics_scenarios.py

# Phase 3 & Controlled Dataset Audit
.venv/bin/pytest backend/tests/test_synthetic_dataset.py backend/tests/test_dataset_audit.py

# Phase 4 & ML Classifier
.venv/bin/pytest backend/tests/test_ml_classifier.py

# Phase 5 & Cross-Model Consensus
.venv/bin/pytest backend/tests/test_consensus.py

# Phase 6 & Temporal Kinematics + Chronology
.venv/bin/pytest backend/tests/test_temporal_evidence.py backend/tests/test_chronology_phase6.py

# Phase 7 & Infrastructure Risk Characterization
.venv/bin/pytest backend/tests/test_risk_characterization.py

# Phase 8 & External Case-Study Audit
.venv/bin/pytest backend/tests/test_real_data_validation.py

# Phase 9 & System Hardening
.venv/bin/pytest backend/tests/test_system_hardening.py
```

---

## 3. Dataset Generation (Deterministic Seeds)

### 3.1 Case-Study External Benchmark Datasets (Phase 8 / 8.1)
Regenerates the 5 literature-calibrated external benchmark datasets (`data/real/`):
```bash
.venv/bin/python scripts/generate_real_benchmark_datasets.py
```
- **Random Seed**: `42` (Fixed deterministic seed)
- **Output Files**:
  - `data/real/real_sentinel1_stable_bridge_01.json`
  - `data/real/real_sentinel1_subsidence_tunnel_02.json`
  - `data/real/real_sentinel1_seasonal_dam_03.json`
  - `data/real/real_sentinel1_atmospheric_wave_04.json`
  - `data/real/real_sentinel1_low_quality_embankment_05.json`

---

## 4. Analytical Evaluation Scripts

### 4.1 Phase 7 Risk Characterization Synthetic Evaluation
Evaluates representative multi-epoch sequences across the 7 synthetic classes:
```bash
.venv/bin/python scripts/evaluate_phase7_synthetic.py
```

### 4.2 Phase 8 Preliminary Case-Study Benchmark Evaluation
Executes the external benchmark validation suite:
```bash
.venv/bin/python scripts/validate_phase8_real.py
```

### 4.3 Phase 9 End-to-End Pipeline Integration Demonstration
Executes unified pipeline and validates SHA-256 evidence chain:
```bash
.venv/bin/python scripts/run_end_to_end_demo.py
.venv/bin/python scripts/run_end_to_end_demo.py --json
```

### 4.4 Phase 10 Final Research Prototype Demonstration
Executes research prototype presentation:
```bash
.venv/bin/python scripts/final_demo.py
.venv/bin/python scripts/final_demo.py --json
```

### 4.5 Research Demonstration Web Application (Frontend + API)
Executes the interactive scientific presentation GUI:
```bash
# Terminal 1: Launch FastAPI Analytical Backend
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Launch Vite React Frontend
cd frontend
npm install
npm run dev
# Open http://localhost:5173

# Frontend Production Build Verification
npm run build
```

---

## 5. Provenance & Version Verification

Check centralized version dictionary:
```bash
.venv/bin/python -c "from backend.app.core.versions import get_system_versions; import json; print(json.dumps(get_system_versions(), indent=2))"
```
Expected output:
```json
{
  "pipeline_version": "1.0.0",
  "ml_model_version": "0.1.0",
  "feature_schema_version": "0.1.0",
  "physics_engine_version": "0.2.1",
  "consensus_engine_version": "strata_consensus_v0.1.0",
  "temporal_engine_version": "strata_temporal_v1_0_0",
  "risk_characterization_version": "strata_risk_v1_0_0",
  "chronology_engine_version": "1.0.0",
  "threshold_registry_version": "1.0.0"
}
```

---

## 6. Audit Notes on Machine Learning Model

- **Model File**: `backend/app/services/ml/classifier.py`
- **Architecture**: Scikit-Learn Random Forest Classifier (100 estimators, max depth 12, balanced weighting).
- **Original Training Seed**: `42`.
- **Frozen Status**: The ML model weights are frozen at version `0.1.0`. In accordance with Phase 10 rules, **the model was not retrained** to ensure complete empirical reproducibility.
