"""
Structured explainability engine for Phase 7 Risk Characterization.
Generates auditable, evidence-grounded human summaries adhering strictly to
scientific safety standards. Prohibits catastrophic claims (collapse, failure, safety guarantee).
"""
from typing import List, Optional
import re

from backend.app.db.models import CriticalityLevel, RiskCharacterizationState
from backend.app.schemas.risk import EvidenceComponents

PROHIBITED_WORDS_REGEX = re.compile(
    r"\b(collapse|collapsing|failure|unsafe|guarantee|certified|certification|danger)\b",
    re.IGNORECASE,
)


def generate_structured_explanation(
    state: RiskCharacterizationState,
    evidence: EvidenceComponents,
    supporting_factors: List[str],
    suppressing_factors: List[str],
    uncertainty_factors: List[str],
    structure_type: str,
    material: str,
    criticality: CriticalityLevel,
) -> str:
    """
    Constructs an evidence-traceable, multi-factor explanation text.
    Programmatically verifies that no prohibited terms are emitted.
    """
    lines: List[str] = []

    # 1. Primary Evidence Header
    crit_str = criticality.value if hasattr(criticality, "value") else (str(criticality) if criticality else "UNKNOWN")
    lines.append(f"STRATA Risk Characterization: {state.value}")
    lines.append(f"Asset Context: {structure_type} ({material}), Criticality: {crit_str}")
    lines.append("")

    # 2. State Interpretation
    if state == RiskCharacterizationState.BASELINE:
        lines.append(
            "Primary Evidence: Multi-epoch InSAR observations remain within the nominal baseline stability envelope. "
            "No coherent non-baseline deformation trend is established."
        )
    elif state == RiskCharacterizationState.ENVIRONMENTAL_PATTERN:
        lines.append(
            "Primary Evidence: Multi-epoch deformation displays recurring cyclical characteristics consistent with "
            "environmental or seasonal processes. Temporal accumulation is treated as non-structural evidence."
        )
    elif state == RiskCharacterizationState.INSUFFICIENT_EVIDENCE:
        lines.append(
            "Primary Evidence: Available interferometric measurements or temporal baseline span are insufficient "
            "to support a definitive structural characterization."
        )
    elif state == RiskCharacterizationState.MONITOR:
        lines.append(
            "Primary Evidence: Observed displacement pattern exhibits moderate volatility, model conflict, or "
            "nascent persistence that warrants continued longitudinal observation."
        )
    elif state == RiskCharacterizationState.ELEVATED_ATTENTION:
        lines.append(
            "Primary Evidence: Multiple independent analytical components indicate persistent multi-epoch deformation "
            "deviating from nominal baseline behavior. Analytical attention is elevated."
        )
    elif state == RiskCharacterizationState.HIGH_ATTENTION:
        lines.append(
            "Primary Evidence: Persistent, cross-model-supported deformation is confirmed in conjunction with "
            "significant baseline deviation or critical zone spatial context. Prompt engineering investigation is warranted."
        )

    lines.append("")

    # 3. Supporting Evidence
    if supporting_factors:
        lines.append("Supporting Evidence:")
        for factor in supporting_factors:
            lines.append(f"  - {factor}")
        lines.append("")

    # 4. Suppression Factors
    if suppressing_factors:
        lines.append("Suppression & Attenuation Factors:")
        for factor in suppressing_factors:
            lines.append(f"  - {factor}")
        lines.append("")

    # 5. Uncertainty Factors
    if uncertainty_factors:
        lines.append("Analytical Uncertainty & Observational Limitations:")
        for factor in uncertainty_factors:
            lines.append(f"  - {factor}")
        lines.append("")

    # 6. Scientific Disclaimer (Mandatory)
    lines.append(
        "Disclaimer: This assessment represents an analytical InSAR evidence characterization for inspection prioritization "
        "and does not provide an engineering sign-off or physical structural prognosis."
    )

    full_text = "\n".join(lines)

    # Programmatic Safety Verification
    match = PROHIBITED_WORDS_REGEX.search(full_text)
    if match:
        raise ValueError(
            f"Safety Violation: Prohibited claim word '{match.group(0)}' detected in generated explanation."
        )

    return full_text
