"""
Real-Data Adapter Service for STRATA Phase 8.
Ingests external InSAR datasets, applies strict unit normalization and radar geometry
projections, and transforms external records into STRATA's canonical ObservationRead format.

CRITICAL PROGRAMMATIC FIREWALL:
- Strips and isolates all external evaluation labels and ground-truth references.
- External validation references remain solely in the evaluation layer.
- Strictly validates that no reference data leaks into ObservationRead metadata or features.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from backend.app.db.models import (
    CriticalityLevel,
    Infrastructure,
    MaterialType,
    StructureType,
)
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.risk import CriticalZone, HistoricalBaseline
from backend.app.services.real_data.models import (
    DisplacementType,
    ExternalDatasetMetadata,
    ExternalReference,
    RawObservationRecord,
)
from backend.app.services.real_data.normalization import (
    convert_displacement_to_mm,
    normalize_coherence,
    normalize_timestamp,
    project_los_to_vertical,
)

# Programmatic evaluation labels forbidden in observation payloads or metadata
LEAKAGE_FORBIDDEN_KEYS = {
    "ground_truth_class",
    "ground_truth",
    "reference_type",
    "reference_source",
    "reference_strength",
    "reference_limitations",
    "documented_behavior",
    "expected_strata_behavior",
    "known_deformation",
    "true_structural_displacement_mm",
    "true_environmental_displacement_mm",
    "true_atmospheric_displacement_mm",
    "true_noise_mm",
    "event_name",
    "evaluation_label",
}


def verify_no_leakage(obj: Any, path: str = "observation") -> None:
    """Recursively validates that no evaluation or ground-truth keys exist in observational data."""
    if obj is None or isinstance(obj, (int, float, bool, bytes)):
        return
    if isinstance(obj, str):
        for forbidden in LEAKAGE_FORBIDDEN_KEYS:
            if forbidden in obj.lower():
                raise ValueError(
                    f"Programmatic Leakage Firewall Violation: Forbidden reference string '{obj}' "
                    f"detected at path '{path}'."
                )
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in LEAKAGE_FORBIDDEN_KEYS:
                raise ValueError(
                    f"Programmatic Leakage Firewall Violation: Forbidden evaluation key '{k}' "
                    f"detected at path '{path}.{k}'."
                )
            verify_no_leakage(v, path=f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            verify_no_leakage(item, path=f"{path}[{idx}]")
    elif hasattr(obj, "__dict__"):
        for k, v in vars(obj).items():
            if k.startswith("_"):
                continue
            if str(k).lower() in LEAKAGE_FORBIDDEN_KEYS:
                raise ValueError(
                    f"Programmatic Leakage Firewall Violation: Forbidden key '{k}' in {type(obj).__name__}."
                )
            verify_no_leakage(v, path=f"{path}.{k}")


class RealDataIngestionService:
    """
    Ingests and normalizes external InSAR datasets into STRATA canonical observations.
    """

    @classmethod
    def load_dataset_metadata(cls, dataset_dir: Path) -> ExternalDatasetMetadata:
        """Loads and parses dataset metadata.json."""
        metadata_file = dataset_dir / "metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file missing: {metadata_file}")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ExternalDatasetMetadata.model_validate(data)

    @classmethod
    def load_raw_observations(cls, dataset_dir: Path) -> List[RawObservationRecord]:
        """Loads raw observation records from observations.json or observations/observations.json."""
        candidates = [
            dataset_dir / "observations.json",
            dataset_dir / "observations" / "observations.json",
        ]
        obs_file = None
        for cand in candidates:
            if cand.exists():
                obs_file = cand
                break
        
        if obs_file is None:
            raise FileNotFoundError(f"Observations file not found in {dataset_dir}")
        
        with open(obs_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        if not isinstance(raw_data, list):
            raise ValueError(f"Observations file must contain a JSON list of records, got {type(raw_data)}")
        
        return [RawObservationRecord.model_validate(r) for r in raw_data]

    @classmethod
    def convert_to_observations(
        cls,
        metadata: ExternalDatasetMetadata,
        raw_records: List[RawObservationRecord],
        infrastructure_id: Optional[str] = None,
    ) -> List[ObservationRead]:
        """
        Converts raw records to canonical ObservationRead list with strict unit normalization
        and LOS/vertical handling.
        """
        inf_id = infrastructure_id or str(uuid.uuid4())
        observations: List[ObservationRead] = []

        # Sort chronologically by timestamp
        sorted_records = sorted(
            raw_records,
            key=lambda r: normalize_timestamp(r.timestamp)
        )

        for rec in sorted_records:
            dt = normalize_timestamp(rec.timestamp)
            disp_mm = convert_displacement_to_mm(rec.displacement, rec.displacement_unit)

            # Determine incidence angle (record-specific or dataset nominal)
            inc_angle = rec.incidence_angle if rec.incidence_angle is not None else metadata.incidence_angle_deg

            # Determine displacement representation
            disp_rep = rec.displacement_type if rec.displacement_type != DisplacementType.UNKNOWN else metadata.displacement_representation

            deformation_mm: Optional[float] = None
            los_displacement_mm: Optional[float] = None
            obs_flags = list(rec.flags)

            if disp_rep == DisplacementType.VERTICAL:
                # External source already provides vertical displacement
                # Do NOT project it again!
                deformation_mm = disp_mm
                los_displacement_mm = None
                obs_flags.append("EXTERNAL_VERTICAL_PROVIDED")
            elif disp_rep == DisplacementType.LOS:
                los_displacement_mm = disp_mm
                vert_mm, geom_ok = project_los_to_vertical(disp_mm, inc_angle)
                if geom_ok and vert_mm is not None:
                    deformation_mm = vert_mm
                else:
                    deformation_mm = None
                    obs_flags.append("GEOMETRY_UNAVAILABLE")
            else:
                # Unknown representation - mark geometry unavailable
                los_displacement_mm = disp_mm
                deformation_mm = None
                obs_flags.append("GEOMETRY_UNAVAILABLE")

            # Coherence normalization
            coherence_val, has_coherence = normalize_coherence(rec.coherence)
            if not has_coherence:
                obs_flags.append("COHERENCE_UNAVAILABLE")

            # Build metadata dict (free of any ground truth or evaluation labels)
            obs_meta = {
                "dataset_id": metadata.dataset_id,
                "sensor": metadata.sensor,
                "flags": obs_flags,
                "raw_metadata": {k: v for k, v in rec.raw_metadata.items() if k.lower() not in LEAKAGE_FORBIDDEN_KEYS}
            }

            obs_read = ObservationRead(
                id=str(uuid.uuid4()),
                infrastructure_id=inf_id,
                acquisition_timestamp=dt,
                deformation_mm=deformation_mm,
                velocity_mm_per_year=None,
                coherence=coherence_val,
                phase_quality=rec.phase_quality,
                incidence_angle=inc_angle,
                los_displacement_mm=los_displacement_mm,
                atmospheric_indicator=rec.atmospheric_indicator,
                source=metadata.sensor.upper(),
                metadata=obs_meta,
                created_at=dt,
            )

            # Enforce leakage firewall on each observation
            verify_no_leakage(obs_read)

            observations.append(obs_read)

        return observations

    @classmethod
    def load_dataset(
        cls,
        dataset_path: str | Path,
        infrastructure_id: Optional[str] = None,
    ) -> Tuple[ExternalDatasetMetadata, List[ObservationRead]]:
        """
        Loads, validates, and normalizes a complete external dataset directory.
        """
        p = Path(dataset_path)
        meta = cls.load_dataset_metadata(p)
        raw_recs = cls.load_raw_observations(p)
        obs_list = cls.convert_to_observations(meta, raw_recs, infrastructure_id=infrastructure_id)
        return meta, obs_list
