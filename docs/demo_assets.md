# STRATA — Demonstration Asset & Screenshot Specification

This document inventories recommended screenshot captures and figure assets for research papers, presentation slide decks (PPT), patent disclosures, and README documentation.

---

## Screenshot Inventory & Figure Mapping

| ID | Recommended Screen / View | Feature & Visual Purpose | Potential Uses |
|:---|:---|:---|:---|
| **FIG-01** | **System Dashboard Overview** (`/dashboard`) | Displays active InSAR telemetry bar (`v1.0.0 FROZEN`), portfolio metric counters, and topological schematic spatial corridor. Demonstrates non-geographic schematic radar visualization. | Research paper Fig 1, Presentation introduction, README hero banner |
| **FIG-02** | **Infrastructure Portfolio Table** (`/infrastructure`) | Sortable, filterable civil asset registry showing structural material, criticality rating, evidence state, characterization index, and confidence. Demonstrates portfolio-scale indexing. | Research paper portfolio overview, PPT slide deck |
| **FIG-03** | **Centerpiece Asset Header & Overview** (`/detail`) | Centerpiece view showing asset classification, observation window (2025–2026), and baseline noise envelope. Demonstrates asset identification. | Patent specification Fig 2, Presentation asset focus |
| **FIG-04** | **Multi-Epoch Deformation Trajectory** (`/detail#chart`) | Custom SVG chart showing vertical displacement trajectory, zero baseline, historical $\pm 1\sigma$ noise band, and interactive hover tooltip exposing coherence ($\gamma$) and LOS values. | Research paper Fig 4 (kinematic trajectory), Patent disclosure |
| **FIG-05** | **ML Deformation Evidence Card** (`/detail#ml`) | Independent machine learning classification card showing predicted structural class, model confidence, and feature attribution. | Research paper methodology section, PPT technical deep-dive |
| **FIG-06** | **Deterministic Physics Engine Card** (`/detail#physics`) | Independent kinematic consistency evaluation card showing velocity admissibility verification and consistency score. | Research paper physics engine section, Patent claim support |
| **FIG-07** | **Cross-Model Consensus Convergence** (`/detail#consensus`) | Dual-branch flow visualization showing ML and physics converging into fused consensus node, agreement ratio badge, and confidence modulation indicator. | Patent primary inventive diagram (Fig 3), Research paper core contribution |
| **FIG-08** | **Multi-Epoch Temporal Inspection Timeline** (`/detail#timeline`) | Horizontal scrubbable epoch timeline and instantaneous audit card exposing acquisition date, displacement, and coherence. | Research paper temporal analysis section, Demo video |
| **FIG-09** | **Infrastructure Context & Baseline Comparison** (`/detail#context`) | Material and criticality sensitivity breakdown paired with historical baseline $z$-score deviation comparison. | Research paper contextual modulation section, Patent disclosure |
| **FIG-10** | **Evidence Characterization Index Card** (`/detail#index`) | Large characterization gauge ($0-100$), analytical confidence progress bar, state badge, and prominent non-safety limitation notice. | Executive summary slide, README results summary |
| **FIG-11** | **Tamper-Evident Evidence Chronology** (`/chronology`) | Block-by-block SHA-256 hash chain with parent hash links, verification status banner (`✓ CHRONOLOGY VERIFIED`), and canonical JSON payload inspector. | Patent chronology claim support, Research paper audit section |
| **FIG-12** | **Curated Presentation Demo Mode** (`/demo`) | 10-Scene guided presentation stepper with test-scenario selector (Scenarios A through F), auto-play controls, and presenter commentary notes. | Video demonstration thumbnail, Live presentation walkthrough |
| **FIG-13** | **Scientific Methodology & Freeze Modal** (`/about`) | Explicit side-by-side breakdown of "What STRATA Does" vs. "What STRATA Does NOT Do" and frozen component version matrix ($1.0.0$). | Research transparency slide, Appendix |

---

## Capture Guidelines

1. **Resolution**: Minimum $1920 \times 1080$ (1080p) or $2560 \times 1440$ (1440p) desktop viewport.
2. **Color Profile**: Dark mode (aerospace obsidian `#07090e`) with sRGB fidelity.
3. **Format**: PNG with lossless compression.
4. **Data Integrity**: Ensure the case-study provenance tags (`Preliminary case-study evaluation` / `Synthetic / Case-Study Placeholder`) remain visible in all captures.
