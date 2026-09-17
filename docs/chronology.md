# STRATA — Tamper-Evident Chronology Layer (Phase 6)

## 1. Purpose & Core Principles

The STRATA Longitudinal Evidence Chronicle provides cryptographic auditability and provenance integrity for multi-epoch InSAR analysis.

Every observation ingestion and consensus evaluation produces an **immutable analytical snapshot** bound to a cryptographic SHA-256 hash chain.

### The Immutability Principle
If a machine learning model or physics algorithm is updated:
$$\text{historical analysis} \neq \text{overwritten analysis}$$

The chronicle preserves the exact model versions, physics versions, consensus versions, and parameters present at the moment the observation was analyzed. This enables STRATA to answer with mathematical certainty:

> **What evidence did STRATA possess at time $T$, in what exact order, using which model version, and what conclusion was reached?**

---

## 2. Cryptographic Hash Construction

### Canonical JSON Serialization (`canonical_json_bytes`)
To guarantee cross-platform bitwise determinism:
- Dictionary keys are strictly sorted in lexicographical order.
- Whitespace is strictly eliminated (separators: `(`,`, `:` )`).
- UTF-8 encoding is enforced with `ensure_ascii=False`.
- Timestamps are formatted as canonical ISO 8601 strings.
- Floating-point metrics are serialized deterministically without volatile memory references.

### Hash Chaining Protocol
$$\text{payload\_hash}_i = \text{SHA-256}\left(\text{canonical\_json}(\text{payload}_i)\right)$$

$$\text{current\_hash}_i = \text{SHA-256}\left(\text{previous\_hash}_i + \text{":"} + \text{payload\_hash}_i\right)$$

For the genesis record ($i = 0$):
$$\text{previous\_hash}_0 = \underbrace{\text{"00000000...0000"}}_{\text{64 zeros}}$$

---

## 3. Chronicle Record Schema

Each `ChronologyRecord` stores:

```json
{
  "record_index": 3,
  "infrastructure_id": "b55b0c9e-732f-425e-80bf-d3e6c08c7c4c",
  "observation_id": "obs_003",
  "analysis_result_id": "res_003",
  "acquisition_timestamp": "2025-01-25T00:00:00Z",
  "consensus_category": "STRUCTURAL",
  "consensus_confidence": 0.7412,
  "agreement_score": 0.8500,
  "disagreement_penalty": 0.1500,
  "evidence_quality_score": 0.8850,
  "temporal_persistence_score": 0.8650,
  "physics_classification": "STRUCTURALLY_CONSISTENT",
  "ml_predicted_class": "STRUCTURAL_MONOTONIC",
  "model_versions": {
    "ml_model": "strata_ml_v0_1_0",
    "physics_engine": "strata_physics_v0.2.1",
    "consensus_engine": "strata_consensus_v0.1.0"
  },
  "consensus_engine_version": "strata_consensus_v0.1.0",
  "flags": ["MODEL_AGREEMENT", "STRONG_MODEL_AGREEMENT"]
}
```

---

## 4. Tamper Detection Capabilities

The enhanced verification algorithm (`verify_chain_enhanced`) verifies six distinct tamper failure modes:

| Tamper Test | Description | Verification Response |
| :--- | :--- | :--- |
| **A. Payload Tampering** | Modifying any stored numerical value, classification, or version in payload. | `FAILED: Payload tampering detected at record #K...` |
| **B. Record Deletion** | Removing an intermediate record from the chain. | `FAILED: Broken sequence: record index mismatch...` |
| **C. Record Reordering** | Swapping two records or ingesting out-of-order records. | `FAILED: Reordered or broken sequence: record index does not match position...` |
| **D. Previous Hash Tampering** | Altering the `previous_hash` link to forge continuity. | `FAILED: Hash link mismatch at record #K...` |
| **E. Duplicate Sequence Index** | Inserting two records with the same `record_index`. | `FAILED: Duplicate sequence number detected in chronology records.` |
| **F. Timestamp Inconsistency** | An observation recorded with an acquisition timestamp preceding its predecessor. | `FAILED: Timestamp inconsistency: acquisition timestamp is earlier than preceding record.` |

---

## 5. Replay & Analytical Reproducibility

STRATA supports analytical replay verification:
1. Re-evaluating the identical multi-epoch observation sequence with the frozen analytical models yields bitwise identical `ConsensusAssessment` values.
2. Canonical JSON serialization produces identical `payload_hash` values.
3. Cryptographic chaining reproduces the identical `current_hash` digest.
4. If a model version has changed, the replay mechanism explicitly detects and flags the version mismatch rather than overwriting historical evidence.

---

## 6. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/analysis/chronology/{observation_id}` | Evaluates consensus and appends an immutable record to the evidence chronicle. |
| `GET` | `/api/v1/infrastructure/{infrastructure_id}/chronology` | Retrieves all ordered chronological records for an asset. |
| `GET` | `/api/v1/infrastructure/{infrastructure_id}/temporal-summary` | Generates complete longitudinal temporal evidence summary. |
| `GET` | `/api/v1/infrastructure/{infrastructure_id}/chronology/verify` | Cryptographically verifies SHA-256 chain integrity for an asset. |
| `GET` | `/api/v1/analysis/chronicle/verify` | Cryptographically verifies global SHA-256 evidence chronicle integrity. |

---

## 7. Operational Limitations

1. **Not a Raw Archive**: The chronicle stores analytical evidence snapshots and provenance metadata, not raw satellite Single Look Complex (SLC) SAR files.
2. **Local Cryptographic Integrity**: Hash chaining verifies internal immutability and tamper detection. Integration with external distributed ledgers (blockchain) is reserved for Phase 7.
3. **Absence of Safety Assertions**: The chronicle proves that an analysis was conducted deterministically; it does not certify physical structural safety.
