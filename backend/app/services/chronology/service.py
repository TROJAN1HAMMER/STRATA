"""
Longitudinal Evidence Chronicle Service (Phase 1 & Phase 6 Enhanced).
Manages tamper-evident hash-chained scientific audit records using SHA-256.
Guarantees mathematical integrity, chronological provenance, and analytical reproducibility.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.db.models import AnalysisResult, ChronologyRecord, Observation
from backend.app.schemas.consensus import ConsensusAssessment
from backend.app.services.chronology.hasher import (
    compute_chained_record_hash,
    compute_payload_hash,
)

GENESIS_HASH: str = "0" * 64


class EvidenceChronicleService:
    """
    Longitudinal Evidence Chronicle Service:
    Manages tamper-evident hash-chained scientific audit records using SHA-256.
    Ensures every observation and analysis result can be mathematically verified.
    """

    def __init__(self, genesis_hash: str = GENESIS_HASH):
        self.genesis_hash = genesis_hash

    def append_record(
        self,
        db: Session,
        observation_id: str,
        analysis_result_id: str,
        analysis_summary: Dict[str, Any],
        processing_metadata: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        infrastructure_id: Optional[str] = None,
    ) -> ChronologyRecord:
        """
        Appends a generic analysis record to the global SHA-256 evidence chain (backward-compatible).
        """
        record_time = timestamp or datetime.now(timezone.utc)

        # Infer infrastructure_id if not directly supplied
        if infrastructure_id is None:
            obs = db.query(Observation).filter(Observation.id == observation_id).first()
            if obs:
                infrastructure_id = obs.infrastructure_id

        # Get latest global record to find previous hash
        latest_record = (
            db.query(ChronologyRecord)
            .order_by(ChronologyRecord.record_index.desc())
            .first()
        )

        if latest_record is None:
            record_index = 0
            previous_hash = self.genesis_hash
        else:
            record_index = latest_record.record_index + 1
            previous_hash = latest_record.current_hash

        payload: Dict[str, Any] = {
            "record_index": record_index,
            "observation_id": observation_id,
            "analysis_result_id": analysis_result_id,
            "timestamp": record_time.isoformat(),
            "analysis_result": analysis_summary,
            "processing_metadata": processing_metadata,
        }
        if infrastructure_id:
            payload["infrastructure_id"] = infrastructure_id

        payload_hash = compute_payload_hash(payload)
        current_hash = compute_chained_record_hash(previous_hash, payload_hash)

        record = ChronologyRecord(
            observation_id=observation_id,
            analysis_result_id=analysis_result_id,
            infrastructure_id=infrastructure_id,
            record_index=record_index,
            timestamp=record_time,
            payload=payload,
            payload_hash=payload_hash,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )

        db.add(record)
        db.flush()

        logger.info(
            f"Appended Chronology Record #{record_index} [Hash: {current_hash[:12]}...] for observation {observation_id}"
        )
        return record

    def append_consensus_record(
        self,
        db: Session,
        observation_id: str,
        infrastructure_id: str,
        consensus_assessment: ConsensusAssessment,
        analysis_result_id: Optional[str] = None,
        acquisition_timestamp: Optional[datetime] = None,
    ) -> ChronologyRecord:
        """
        Appends a full Phase 5/6 ConsensusAssessment snapshot to the tamper-evident chronicle.
        Preserves all analytical inputs, ML probabilities, physics evidence, and component versions.
        """
        record_time = datetime.now(timezone.utc)

        # If analysis_result_id not provided, create a minimal AnalysisResult record or use placeholder
        if analysis_result_id is None:
            analysis_entity = AnalysisResult(
                observation_id=observation_id,
                ml_classification=consensus_assessment.ml_contribution.get("predicted_class"),
                ml_confidence=consensus_assessment.ml_contribution.get("confidence"),
                physics_classification=consensus_assessment.physics_contribution.get("classification"),
                physics_confidence=consensus_assessment.physics_contribution.get("evidence_strength"),
                consensus_confidence=consensus_assessment.consensus_confidence,
                consensus_classification=consensus_assessment.consensus_class.value,
                temporal_confidence=consensus_assessment.temporal_persistence_score,
                execution_metadata={
                    "model_versions": consensus_assessment.model_versions,
                    "flags": consensus_assessment.flags,
                    "agreement_score": consensus_assessment.agreement_score,
                },
            )
            db.add(analysis_entity)
            db.flush()
            analysis_result_id = analysis_entity.id

        latest_record = (
            db.query(ChronologyRecord)
            .order_by(ChronologyRecord.record_index.desc())
            .first()
        )

        if latest_record is None:
            record_index = 0
            previous_hash = self.genesis_hash
        else:
            record_index = latest_record.record_index + 1
            previous_hash = latest_record.current_hash

        acq_str = (
            acquisition_timestamp.isoformat()
            if acquisition_timestamp
            else record_time.isoformat()
        )

        payload: Dict[str, Any] = {
            "record_index": record_index,
            "infrastructure_id": infrastructure_id,
            "observation_id": observation_id,
            "analysis_result_id": analysis_result_id,
            "acquisition_timestamp": acq_str,
            "consensus_category": consensus_assessment.consensus_class.value,
            "consensus_confidence": consensus_assessment.consensus_confidence,
            "agreement_score": consensus_assessment.agreement_score,
            "disagreement_penalty": consensus_assessment.disagreement_penalty,
            "evidence_quality_score": consensus_assessment.evidence_quality_score,
            "temporal_persistence_score": consensus_assessment.temporal_persistence_score,
            "physics_classification": consensus_assessment.physics_contribution.get("classification"),
            "ml_predicted_class": consensus_assessment.ml_contribution.get("predicted_class"),
            "model_versions": consensus_assessment.model_versions,
            "consensus_engine_version": consensus_assessment.consensus_engine_version,
            "flags": consensus_assessment.flags,
        }

        payload_hash = compute_payload_hash(payload)
        current_hash = compute_chained_record_hash(previous_hash, payload_hash)

        record = ChronologyRecord(
            observation_id=observation_id,
            analysis_result_id=analysis_result_id,
            infrastructure_id=infrastructure_id,
            record_index=record_index,
            timestamp=record_time,
            payload=payload,
            payload_hash=payload_hash,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )

        db.add(record)
        db.flush()

        logger.info(
            f"Appended Consensus Chronology Record #{record_index} [Hash: {current_hash[:12]}...] for asset {infrastructure_id}"
        )
        return record

    def verify_chain(self, records: List[ChronologyRecord]) -> Tuple[bool, Optional[str]]:
        """
        Verifies the cryptographic integrity of a sequence of ChronologyRecords.
        Maintains backward compatibility with Phase 1 verification tests.
        """
        return self.verify_chain_enhanced(records)

    def verify_chain_enhanced(self, records: List[ChronologyRecord]) -> Tuple[bool, Optional[str]]:
        """
        Enhanced cryptographic verification for ChronologyRecords.
        Detects:
          - Sequential index gaps or duplicates
          - Duplicate sequence numbers
          - Previous hash link alterations
          - Payload tampering (payload modification)
          - Current record hash mismatch
          - Chronological timestamp inconsistencies
        """
        if not records:
            return True, None

        # Check for duplicate sequence numbers and out-of-order records as presented
        indices = [r.record_index for r in records]
        if len(indices) != len(set(indices)):
            return False, "Duplicate sequence number detected in chronology records."

        first_index = records[0].record_index
        for idx, rec in enumerate(records):
            expected_idx = first_index + idx
            if rec.record_index != expected_idx:
                return (
                    False,
                    f"Reordered or broken sequence: record index {rec.record_index} does not match expected position {expected_idx}.",
                )

        sorted_records = records
        expected_prev_hash = sorted_records[0].previous_hash

        # If starting at record 0, previous hash must be genesis
        if sorted_records[0].record_index == 0 and expected_prev_hash != self.genesis_hash:
            return False, f"Genesis record previous_hash mismatch: expected {self.genesis_hash[:12]}..., got {expected_prev_hash[:12]}..."

        prev_acq_time: Optional[datetime] = None

        for idx, rec in enumerate(sorted_records):

            # Check previous hash link
            if rec.previous_hash != expected_prev_hash:
                return (
                    False,
                    f"Hash link mismatch at record #{rec.record_index}: expected previous_hash {expected_prev_hash[:12]}..., got {rec.previous_hash[:12]}...",
                )

            # Check payload tampering
            recomputed_payload_hash = compute_payload_hash(rec.payload)
            if recomputed_payload_hash != rec.payload_hash:
                return (
                    False,
                    f"Payload tampering detected at record #{rec.record_index}: stored payload_hash {rec.payload_hash[:12]}... does not match recomputed {recomputed_payload_hash[:12]}...",
                )

            # Check current hash calculation
            recomputed_current_hash = compute_chained_record_hash(rec.previous_hash, rec.payload_hash)
            if recomputed_current_hash != rec.current_hash:
                return (
                    False,
                    f"Current hash mismatch at record #{rec.record_index}: stored {rec.current_hash[:12]}..., recomputed {recomputed_current_hash[:12]}...",
                )

            # Check chronological acquisition timestamp monotonicity (if present in payload)
            acq_str = rec.payload.get("acquisition_timestamp")
            if acq_str:
                try:
                    curr_acq = datetime.fromisoformat(acq_str.replace("Z", "+00:00"))
                    if prev_acq_time is not None and curr_acq < prev_acq_time:
                        return (
                            False,
                            f"Timestamp inconsistency: acquisition timestamp '{acq_str}' at record #{rec.record_index} is earlier than preceding record.",
                        )
                    prev_acq_time = curr_acq
                except ValueError:
                    pass

            expected_prev_hash = rec.current_hash

        return True, None

    def verify_infrastructure_chain(
        self,
        db: Session,
        infrastructure_id: str,
    ) -> Tuple[bool, Optional[str], int]:
        """
        Fetches and cryptographically validates all chronology records for a specific infrastructure asset.
        """
        records = (
            db.query(ChronologyRecord)
            .join(Observation, ChronologyRecord.observation_id == Observation.id)
            .filter(Observation.infrastructure_id == infrastructure_id)
            .order_by(ChronologyRecord.record_index.asc())
            .all()
        )
        if not records:
            # Also check direct infrastructure_id column if present
            records = (
                db.query(ChronologyRecord)
                .filter(ChronologyRecord.infrastructure_id == infrastructure_id)
                .order_by(ChronologyRecord.record_index.asc())
                .all()
            )

        is_valid, error = self.verify_chain_enhanced(records)
        return is_valid, error, len(records)
