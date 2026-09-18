import React, { useState } from 'react'
import { ArrowLeft, Maximize2 } from 'lucide-react'

type PatentFigureId = 'FIG_1' | 'FIG_2' | 'FIG_3' | 'FIG_4' | 'FIG_5' | 'FIG_6' | 'FIG_7' | 'FIG_8'

interface PatentFigureMeta {
  id: PatentFigureId
  figureNum: string
  title: string
  subtitle: string
  claimsAlignment: string
}

const FIGURES: PatentFigureMeta[] = [
  {
    id: 'FIG_1',
    figureNum: 'FIG. 1',
    title: 'OVERALL STRATA SYSTEM INTERACTION ARCHITECTURE',
    subtitle: 'Schematic coupling multi-epoch satellite InSAR evidence, dual decoupled analytical engines, and cryptographic ledger.',
    claimsAlignment: 'Claim 1: Multi-engine evidence characterization architecture with consensus confidence modulation.',
  },
  {
    id: 'FIG_2',
    figureNum: 'FIG. 2',
    title: 'MULTI-EPOCH INSAR DIFFERENTIAL GEOMETRY & VERTICAL PROJECTION',
    subtitle: 'Geometric projection from slant range Line-Of-Sight (LOS) into true vertical deformation via incidence angle θ.',
    claimsAlignment: 'Claim 2: Deterministic projection of differential microwave phase into geodetic displacement vectors.',
  },
  {
    id: 'FIG_3',
    figureNum: 'FIG. 3',
    title: 'ENVIRONMENTAL RECURRENCE DISCRIMINATION SAFEGUARD',
    subtitle: 'Zero-crossing periodic discrimination separating cyclic thermal/hydrological motion from structural settlement.',
    claimsAlignment: 'Claim 3: Cyclic recurrence detection suppressing false structural alarm contributions.',
  },
  {
    id: 'FIG_4',
    figureNum: 'FIG. 4',
    title: 'SYMMETRICAL CROSS-MODEL CONSENSUS & CONFIDENCE MODULATION',
    subtitle: 'Evidence fusion mechanism amplifying confidence under agreement (+15%) and penalizing divergence (-30%).',
    claimsAlignment: 'Claim 4: Cross-model consensus treating analytical disagreement as mathematical uncertainty.',
  },
  {
    id: 'FIG_5',
    figureNum: 'FIG. 5',
    title: 'MULTI-EPOCH TEMPORAL STATE MACHINE TRANSITIONS',
    subtitle: '9-state kinematic persistence tracking with baseline envelope guard and acceleration support criteria.',
    claimsAlignment: 'Claim 5: Multi-epoch state machine evaluating kinematic persistence across consecutive acquisitions.',
  },
  {
    id: 'FIG_6',
    figureNum: 'FIG. 6',
    title: 'INFRASTRUCTURE CONTEXT & EVIDENCE CHARACTERIZATION INDEX',
    subtitle: 'Six-dimensional contextual weighting where measurement quality strictly dominates asset criticality.',
    claimsAlignment: 'Claim 6: Hierarchical evidence fusion where physical measurement quality gates infrastructure context.',
  },
  {
    id: 'FIG_7',
    figureNum: 'FIG. 7',
    title: 'CANONICAL SHA-256 TAMPER-EVIDENT EVIDENCE CHRONOLOGY',
    subtitle: 'Immutable hash chain linking consecutive analysis snapshots with parent pointers for retroactive auditability.',
    claimsAlignment: 'Claim 7: Cryptographic audit chain enforcing analytical reproducibility and tamper detection.',
  },
  {
    id: 'FIG_8',
    figureNum: 'FIG. 8',
    title: 'COMPLETE NINE-STAGE STRATA ANALYTICAL PIPELINE',
    subtitle: 'End-to-end transactional execution sequence from observation ingestion to chronology persistence.',
    claimsAlignment: 'Claim 8: Integrated 9-stage pipeline with atomic rollback and idempotent execution cache.',
  },
]

interface PatentFigureModeProps {
  onExit: () => void
}

export const PatentFigureMode: React.FC<PatentFigureModeProps> = ({ onExit }) => {
  const [selectedFigId, setSelectedFigId] = useState<PatentFigureId>('FIG_1')
  const [isCleanMode, setIsCleanMode] = useState<boolean>(false)

  const activeFigure = FIGURES.find((f) => f.id === selectedFigId) || FIGURES[0]

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
        backgroundColor: '#020408',
        minHeight: '80vh',
        padding: isCleanMode ? '2rem' : '1.5rem',
        borderRadius: '8px',
        border: '1px solid var(--border-medium)',
      }}
    >
      {/* Top Patent Navigation Bar */}
      {!isCleanMode && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button
              onClick={onExit}
              className="btn btn-secondary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <ArrowLeft size={14} />
              <span>Back to Simulation Lab</span>
            </button>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="badge badge-cyan" style={{ fontSize: '0.68rem' }}>
                  PATENT VISUALIZATION MODE
                </span>
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                  STRATA v1.0.0 SPECIFICATION FIGURES
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={() => setIsCleanMode(true)}
              className="btn btn-primary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              title="Hide UI controls for clean publication screenshots"
            >
              <Maximize2 size={14} />
              <span>Clean Screenshot View</span>
            </button>
          </div>
        </div>
      )}

      {/* Figure Selector Buttons */}
      {!isCleanMode && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '0.5rem',
          }}
        >
          {FIGURES.map((fig) => (
            <button
              key={fig.id}
              onClick={() => setSelectedFigId(fig.id)}
              style={{
                padding: '0.5rem 0.75rem',
                backgroundColor: selectedFigId === fig.id ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-card)',
                border: selectedFigId === fig.id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                borderRadius: '5px',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                {fig.figureNum}
              </div>
              <div
                style={{
                  fontSize: '0.72rem',
                  color: selectedFigId === fig.id ? '#ffffff' : 'var(--text-secondary)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  marginTop: '0.15rem',
                }}
              >
                {fig.title}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Clean Mode Exit Button */}
      {isCleanMode && (
        <button
          onClick={() => setIsCleanMode(false)}
          className="btn btn-secondary btn-sm"
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            zIndex: 50,
            opacity: 0.7,
          }}
        >
          Exit Clean View
        </button>
      )}

      {/* High-Contrast Patent Figure Composition Canvas */}
      <div
        style={{
          backgroundColor: '#050911',
          border: '2px solid rgba(255, 255, 255, 0.15)',
          borderRadius: '8px',
          padding: '2rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
        }}
      >
        {/* Figure Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.5rem', width: '100%' }}>
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '1.25rem',
              fontWeight: 800,
              color: '#ffffff',
              letterSpacing: '0.05em',
            }}
          >
            {activeFigure.figureNum}
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--accent-cyan)', marginTop: '0.25rem' }}>
            {activeFigure.title}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.35rem', maxWidth: '800px', margin: '0.35rem auto 0' }}>
            {activeFigure.subtitle}
          </div>
        </div>

        {/* Vector Schematic Content Per Figure */}
        <div style={{ width: '100%', maxWidth: '820px', minHeight: '380px' }}>
          {selectedFigId === 'FIG_1' && (
            <svg width="100%" height="380" viewBox="0 0 800 380">
              {/* Satellite SAR Observation Layer */}
              <rect x="40" y="30" width="720" height="55" fill="#0f172a" stroke="#38bdf8" strokeWidth="1.5" rx="4" />
              <text x="400" y="52" fill="#38bdf8" fontSize="11" textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="700">
                100: MULTI-EPOCH SATELLITE INSAR OBSERVATIONS (SENTINEL-1 C-BAND)
              </text>
              <text x="400" y="70" fill="var(--text-muted)" fontSize="9" textAnchor="middle">
                Line-of-Sight Displacement | Interferometric Coherence γ | Temporal Baseline Δt
              </text>

              {/* Downward Fork Arrows */}
              <line x1="240" y1="85" x2="240" y2="120" stroke="#38bdf8" strokeWidth="1.5" markerEnd="url(#arrow)" />
              <line x1="560" y1="85" x2="560" y2="120" stroke="#38bdf8" strokeWidth="1.5" markerEnd="url(#arrow)" />

              {/* Dual Decoupled Engines */}
              <rect x="80" y="120" width="320" height="75" fill="#0f172a" stroke="#ffffff" strokeWidth="1.2" rx="4" />
              <text x="240" y="145" fill="#ffffff" fontSize="10" textAnchor="middle" fontWeight="700">
                200: ML DEFORMATION ENGINE
              </text>
              <text x="240" y="162" fill="var(--text-secondary)" fontSize="8.5" textAnchor="middle">
                Calibrated GBDT Classifier (28 Features)
              </text>
              <text x="240" y="178" fill="var(--accent-cyan)" fontSize="8.5" textAnchor="middle" fontFamily="var(--font-mono)">
                P(Structural) | Isotonic Probability Mass
              </text>

              <rect x="400" y="120" width="320" height="75" fill="#0f172a" stroke="#ffffff" strokeWidth="1.2" rx="4" />
              <text x="560" y="145" fill="#ffffff" fontSize="10" textAnchor="middle" fontWeight="700">
                300: PHYSICS CONSISTENCY ENGINE
              </text>
              <text x="560" y="162" fill="var(--text-secondary)" fontSize="8.5" textAnchor="middle">
                Deterministic Kinematic Rate &amp; Noise Floors
              </text>
              <text x="560" y="178" fill="#34d399" fontSize="8.5" textAnchor="middle" fontFamily="var(--font-mono)">
                Velocity Bounds | Environmental Periodicity
              </text>

              {/* Convergence to Consensus */}
              <line x1="240" y1="195" x2="380" y2="230" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="560" y1="195" x2="420" y2="230" stroke="#ffffff" strokeWidth="1.5" />

              {/* Consensus Engine */}
              <rect x="180" y="230" width="440" height="55" fill="#0f172a" stroke="#f59e0b" strokeWidth="1.5" rx="4" />
              <text x="400" y="252" fill="#f59e0b" fontSize="10.5" textAnchor="middle" fontWeight="700">
                400: CROSS-MODEL CONSENSUS &amp; CONFIDENCE MODULATION
              </text>
              <text x="400" y="270" fill="var(--text-muted)" fontSize="8.5" textAnchor="middle">
                Symmetrical Agreement Boost (+15%) | Divergence Uncertainty Penalty (-30%)
              </text>

              {/* Final Flow to Characterization & Chronology */}
              <line x1="400" y1="285" x2="400" y2="315" stroke="#ffffff" strokeWidth="1.5" />

              <rect x="60" y="315" width="320" height="50" fill="#0f172a" stroke="#34d399" strokeWidth="1.2" rx="4" />
              <text x="220" y="336" fill="#34d399" fontSize="9.5" textAnchor="middle" fontWeight="700">
                500: EVIDENCE CHARACTERIZATION (0-100)
              </text>
              <text x="220" y="352" fill="var(--text-muted)" fontSize="8" textAnchor="middle">
                Asset Material + Criticality + Baseline Envelope
              </text>

              <rect x="420" y="315" width="320" height="50" fill="#0f172a" stroke="#38bdf8" strokeWidth="1.2" rx="4" />
              <text x="580" y="336" fill="#38bdf8" fontSize="9.5" textAnchor="middle" fontWeight="700">
                600: CANONICAL SHA-256 CHRONOLOGY
              </text>
              <text x="580" y="352" fill="var(--text-muted)" fontSize="8" textAnchor="middle">
                Tamper-Evident Hash Chain Audit Log
              </text>
            </svg>
          )}

          {selectedFigId === 'FIG_2' && (
            <svg width="100%" height="380" viewBox="0 0 800 380">
              {/* Satellite Position */}
              <g transform="translate(180, 50)">
                <rect x="-15" y="-10" width="30" height="20" fill="#1e293b" stroke="#38bdf8" strokeWidth="1.5" rx="2" />
                <rect x="-40" y="-6" width="22" height="12" fill="#0284c7" />
                <rect x="18" y="-6" width="22" height="12" fill="#0284c7" />
                <text x="0" y="-18" fill="#ffffff" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">
                  PLATFORM SATELLITE (ALTITUDE ~693 KM)
                </text>
              </g>

              {/* Target Infrastructure */}
              <g transform="translate(560, 290)">
                <rect x="-80" y="-20" width="160" height="25" fill="#334155" stroke="#ffffff" strokeWidth="1.5" rx="2" />
                <rect x="-20" y="5" width="40" height="55" fill="#1e293b" stroke="#475569" strokeWidth="1.5" />
                <text x="0" y="-30" fill="#ffffff" fontSize="10" textAnchor="middle" fontWeight="700">
                  OBSERVED INFRASTRUCTURE DECK
                </text>
                <line x1="0" y1="0" x2="0" y2="40" stroke="#f43f5e" strokeWidth="2.5" />
                <text x="15" y="25" fill="#f43f5e" fontSize="9" fontFamily="var(--font-mono)">
                  d_vertical
                </text>
              </g>

              {/* Nadir line */}
              <line x1="180" y1="60" x2="180" y2="290" stroke="rgba(255,255,255,0.2)" strokeDasharray="3,3" />
              <text x="185" y="270" fill="var(--text-muted)" fontSize="8.5" fontFamily="var(--font-mono)">
                NADIR VECTOR
              </text>

              {/* Slant Range Line Of Sight */}
              <line x1="180" y1="60" x2="560" y2="270" stroke="#38bdf8" strokeWidth="2.5" />
              <text x="360" y="150" fill="#38bdf8" fontSize="11" fontFamily="var(--font-mono)" fontWeight="700">
                LINE-OF-SIGHT SLANT RANGE (d_LOS)
              </text>

              {/* Incidence Angle Arc */}
              <g transform="translate(180, 60)">
                <path d="M 0 80 A 80 80 0 0 1 50 65" fill="none" stroke="#f59e0b" strokeWidth="2" />
                <text x="30" y="105" fill="#f59e0b" fontSize="10" fontFamily="var(--font-mono)">
                  θ (INCIDENCE ANGLE)
                </text>
              </g>

              {/* Equation Box */}
              <rect x="220" y="315" width="360" height="50" fill="#0f172a" stroke="#38bdf8" strokeWidth="1.5" rx="4" />
              <text x="400" y="336" fill="#ffffff" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">
                GEOMETRIC PROJECTION FORMULA:
              </text>
              <text x="400" y="354" fill="#38bdf8" fontSize="12" textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="700">
                d_vertical = d_LOS / cos(θ)
              </text>
            </svg>
          )}

          {selectedFigId === 'FIG_3' && (
            <svg width="100%" height="380" viewBox="0 0 800 380">
              {/* Sinusoidal thermal/rain wave */}
              <path
                d="M 60 180 Q 140 80 220 180 T 380 180 T 540 180 T 700 180"
                fill="none"
                stroke="#38bdf8"
                strokeWidth="2.5"
              />
              {/* Baseline band */}
              <rect x="60" y="155" width="680" height="50" fill="rgba(52, 211, 153, 0.08)" stroke="rgba(52, 211, 153, 0.3)" strokeDasharray="3,3" />
              <text x="730" y="170" fill="#34d399" fontSize="8.5" textAnchor="end" fontFamily="var(--font-mono)">
                ±1σ BASELINE NOISE ENVELOPE
              </text>

              {/* Zero Crossings Markers */}
              <circle cx="220" cy="180" r="5" fill="#f59e0b" />
              <circle cx="380" cy="180" r="5" fill="#f59e0b" />
              <circle cx="540" cy="180" r="5" fill="#f59e0b" />
              <text x="380" y="210" fill="#f59e0b" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)">
                ≥ 2 ZERO CROSSINGS CONFIRM PERIODICITY
              </text>

              {/* Decision Flow */}
              <rect x="180" y="260" width="440" height="70" fill="#0f172a" stroke="#34d399" strokeWidth="1.5" rx="4" />
              <text x="400" y="285" fill="#34d399" fontSize="10.5" textAnchor="middle" fontWeight="700">
                ENVIRONMENTAL RECURRENCE DETECTED
              </text>
              <text x="400" y="303" fill="#ffffff" fontSize="9" textAnchor="middle">
                Temporal State Machine: Flagged ENVIRONMENTAL_PATTERN
              </text>
              <text x="400" y="319" fill="var(--text-muted)" fontSize="8.5" textAnchor="middle">
                Structural Evidence Contribution: SUPPRESSED (0% False Alarm Escalation)
              </text>
            </svg>
          )}

          {selectedFigId === 'FIG_4' && (
            <svg width="100%" height="380" viewBox="0 0 800 380">
              {/* Symmetrical Agreement Block */}
              <rect x="60" y="60" width="320" height="240" fill="#0f172a" stroke="#34d399" strokeWidth="1.5" rx="6" />
              <text x="220" y="90" fill="#34d399" fontSize="11" textAnchor="middle" fontWeight="700">
                CASE A: ENGINE AGREEMENT
              </text>
              <text x="220" y="115" fill="#ffffff" fontSize="9" textAnchor="middle">
                ML: Structural | Physics: Structural
              </text>
              <text x="220" y="145" fill="var(--text-muted)" fontSize="8.5" textAnchor="middle">
                CONFIDENCE FORMULA:
              </text>
              <text x="220" y="165" fill="#34d399" fontSize="10.5" textAnchor="middle" fontFamily="var(--font-mono)">
                Conf_fused = min(1.0, Conf_base × 1.15)
              </text>
              <rect x="90" y="190" width="260" height="30" fill="rgba(52, 211, 153, 0.15)" stroke="#34d399" rx="3" />
              <text x="220" y="210" fill="#ffffff" fontSize="9.5" textAnchor="middle" fontWeight="700">
                ANALYTICAL CONFIDENCE AMPLIFIED (+15%)
              </text>

              {/* Symmetrical Divergence Block */}
              <rect x="420" y="60" width="320" height="240" fill="#0f172a" stroke="#f43f5e" strokeWidth="1.5" rx="6" />
              <text x="580" y="90" fill="#f43f5e" fontSize="11" textAnchor="middle" fontWeight="700">
                CASE B: ENGINE DISAGREEMENT
              </text>
              <text x="580" y="115" fill="#ffffff" fontSize="9" textAnchor="middle">
                ML: Structural | Physics: Seasonal
              </text>
              <text x="580" y="145" fill="var(--text-muted)" fontSize="8.5" textAnchor="middle">
                CONFIDENCE FORMULA:
              </text>
              <text x="580" y="165" fill="#f43f5e" fontSize="10.5" textAnchor="middle" fontFamily="var(--font-mono)">
                Conf_fused = Conf_base × 0.70
              </text>
              <rect x="450" y="190" width="260" height="30" fill="rgba(244, 63, 94, 0.15)" stroke="#f43f5e" rx="3" />
              <text x="580" y="210" fill="#ffffff" fontSize="9.5" textAnchor="middle" fontWeight="700">
                UNCERTAINTY PENALTY APPLIED (-30%)
              </text>
            </svg>
          )}

          {selectedFigId === 'FIG_5' && (
            <svg width="100%" height="380" viewBox="0 0 800 380">
              {/* 9 States in Horizontal/Circular Layout */}
              {[
                { name: 'INSUFFICIENT_HISTORY', x: 120, y: 80, c: '#94a3b8' },
                { name: 'BASELINE', x: 280, y: 80, c: '#34d399' },
                { name: 'EMERGING', x: 440, y: 80, c: '#38bdf8' },
                { name: 'PERSISTENT', x: 600, y: 80, c: '#f59e0b' },
                { name: 'ACCELERATING', x: 680, y: 200, c: '#f43f5e' },
                { name: 'REVERTED', x: 440, y: 200, c: '#94a3b8' },
                { name: 'ENVIRONMENTAL_PATTERN', x: 280, y: 200, c: '#38bdf8' },
                { name: 'ATMOSPHERIC_EVENT', x: 120, y: 200, c: '#f59e0b' },
                { name: 'CONFLICTED', x: 400, y: 310, c: '#f43f5e' },
              ].map((st) => (
                <g key={st.name} transform={`translate(${st.x}, ${st.y})`}>
                  <rect x="-65" y="-18" width="130" height="36" fill="#0f172a" stroke={st.c} strokeWidth="1.5" rx="4" />
                  <text x="0" y="4" fill="#ffffff" fontSize="7.5" textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="600">
                    {st.name}
                  </text>
                </g>
              ))}
              {/* Transition Arrows */}
              <line x1="185" y1="80" x2="215" y2="80" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="345" y1="80" x2="375" y2="80" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="505" y1="80" x2="535" y2="80" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="600" y1="98" x2="680" y2="182" stroke="#ffffff" strokeWidth="1.5" />
            </svg>
          )}

          {selectedFigId === 'FIG_6' && (
            <svg width="100%" height="380" viewBox="0 0 800 380">
              {/* Six Contextual Dimensions */}
              <rect x="60" y="50" width="680" height="280" fill="#0f172a" stroke="#ffffff" strokeWidth="1.2" rx="6" />
              <text x="400" y="80" fill="#38bdf8" fontSize="12" textAnchor="middle" fontWeight="700">
                SIX-DIMENSIONAL INFRASTRUCTURE CONTEXT FUSION
              </text>

              <g transform="translate(100, 110)">
                <text x="0" y="0" fill="#ffffff" fontSize="10" fontWeight="600">1. Structure Type:</text>
                <text x="140" y="0" fill="var(--text-muted)" fontSize="9">Bridge / Dam / Tunnel / Embankment</text>

                <text x="0" y="30" fill="#ffffff" fontSize="10" fontWeight="600">2. Material Stiffness:</text>
                <text x="140" y="30" fill="var(--text-muted)" fontSize="9">Steel (Flexible) vs Concrete (Rigid) vs Earth</text>

                <text x="0" y="60" fill="#ffffff" fontSize="10" fontWeight="600">3. Criticality Tier:</text>
                <text x="140" y="60" fill="var(--text-muted)" fontSize="9">Strategic Highway / Spillway / High-Speed Rail</text>

                <text x="0" y="90" fill="#ffffff" fontSize="10" fontWeight="600">4. Critical Zones:</text>
                <text x="140" y="90" fill="var(--text-muted)" fontSize="9">Mid-span Deck, Dam Crest, Abutment Weighting</text>

                <text x="0" y="120" fill="#ffffff" fontSize="10" fontWeight="600">5. Geodetic Baseline:</text>
                <text x="140" y="120" fill="var(--text-muted)" fontSize="9">Historical Mean μ and Standard Deviation σ</text>

                <text x="0" y="150" fill="#ffffff" fontSize="10" fontWeight="600">6. Evidence Quality Gate:</text>
                <text x="140" y="150" fill="#34d399" fontSize="9" fontWeight="700">DOMINATES CONTEXT (Quality &lt; 0.60 mutes criticality)</text>
              </g>

              {/* Output Result */}
              <rect x="200" y="280" width="400" height="40" fill="rgba(56, 189, 248, 0.15)" stroke="#38bdf8" rx="4" />
              <text x="400" y="305" fill="#ffffff" fontSize="10.5" textAnchor="middle" fontWeight="700">
                EVIDENCE CHARACTERIZATION INDEX (0 - 100)
              </text>
            </svg>
          )}

          {selectedFigId === 'FIG_7' && (
            <svg width="100%" height="380" viewBox="0 0 800 380">
              {/* Chained Blocks */}
              {[
                { id: '1', hash: 'e3b0c44298fc1c14...', prev: '0000000000000000...', x: 80 },
                { id: '2', hash: '8f434346648f6b96...', prev: 'e3b0c44298fc1c14...', x: 300 },
                { id: '3', hash: 'a1b2c3d4e5f60718...', prev: '8f434346648f6b96...', x: 520 },
              ].map((blk, idx) => (
                <g key={blk.id} transform={`translate(${blk.x}, 100)`}>
                  <rect x="0" y="0" width="190" height="150" fill="#0f172a" stroke="#38bdf8" strokeWidth="1.5" rx="4" />
                  <text x="95" y="25" fill="#ffffff" fontSize="10" textAnchor="middle" fontWeight="700">
                    RECORD {blk.id} (EPOCH {idx + 1})
                  </text>
                  <text x="15" y="55" fill="var(--text-muted)" fontSize="7.5" fontFamily="var(--font-mono)">
                    PREV HASH:
                  </text>
                  <text x="15" y="70" fill="var(--text-dim)" fontSize="7.5" fontFamily="var(--font-mono)">
                    {blk.prev.slice(0, 16)}...
                  </text>
                  <text x="15" y="95" fill="var(--text-muted)" fontSize="7.5" fontFamily="var(--font-mono)">
                    CURRENT HASH:
                  </text>
                  <text x="15" y="110" fill="#38bdf8" fontSize="7.5" fontFamily="var(--font-mono)">
                    {blk.hash.slice(0, 16)}...
                  </text>
                  <text x="95" y="135" fill="#34d399" fontSize="8" textAnchor="middle" fontFamily="var(--font-mono)">
                    ✓ VERIFIED INTACT
                  </text>

                  {idx < 2 && (
                    <line x1="190" y1="75" x2="220" y2="75" stroke="#ffffff" strokeWidth="2" markerEnd="url(#arrow)" />
                  )}
                </g>
              ))}

              {/* Hash Calculation Formula */}
              <rect x="150" y="280" width="500" height="50" fill="#0f172a" stroke="#ffffff" strokeWidth="1" rx="4" />
              <text x="400" y="302" fill="var(--text-muted)" fontSize="8.5" textAnchor="middle" fontFamily="var(--font-mono)">
                CANONICAL HASH CHAIN FORMULA:
              </text>
              <text x="400" y="320" fill="#38bdf8" fontSize="11" textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="700">
                h_i = SHA256(h_{'{i-1}'} || SHA256(canonical_payload_i))
              </text>
            </svg>
          )}

          {selectedFigId === 'FIG_8' && (
            <svg width="100%" height="380" viewBox="0 0 800 380">
              {/* 9 Stages in Linear Progression */}
              {[
                '1. Input Validation',
                '2. Observation Normalization',
                '3. History Sequence Assembly',
                '4. ML Classification (GBDT)',
                '5. Physics Consistency Engine',
                '6. Cross-Model Consensus',
                '7. Temporal Evidence Engine',
                '8. Risk Characterization',
                '9. Chronology & Persistence',
              ].map((stage, idx) => (
                <g key={stage} transform={`translate(${60 + (idx % 3) * 235}, ${50 + Math.floor(idx / 3) * 100})`}>
                  <rect x="0" y="0" width="210" height="65" fill="#0f172a" stroke={idx === 5 ? '#f59e0b' : '#38bdf8'} strokeWidth="1.5" rx="4" />
                  <text x="15" y="25" fill="#ffffff" fontSize="9" fontWeight="700">
                    STAGE {idx + 1}
                  </text>
                  <text x="15" y="45" fill={idx === 5 ? '#f59e0b' : 'var(--text-secondary)'} fontSize="8">
                    {stage}
                  </text>
                </g>
              ))}
            </svg>
          )}
        </div>

        {/* Figure Caption & Patent Claim Mapping */}
        <div
          style={{
            marginTop: '1.5rem',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '1rem',
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <div>
            PATENT DISCLOSURE ALIGNMENT: <span style={{ color: 'var(--accent-cyan)' }}>{activeFigure.claimsAlignment}</span>
          </div>
          <div>STRATA v1.0.0 PROTOTYPE SPECIFICATION</div>
        </div>
      </div>

      {/* Mandatory Non-Safety Legal Notice */}
      <div
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '6px',
          padding: '0.75rem 1rem',
          fontSize: '0.72rem',
          color: 'var(--text-dim)',
          textAlign: 'center',
        }}
      >
        <strong>Mandatory Scientific Notice:</strong> This patent figure set illustrates the architectural interaction of the STRATA prototype.
        STRATA provides experimental evidence characterization indices and does not constitute a structural safety certification, collapse prediction, or replacement for certified physical inspection.
      </div>
    </div>
  )
}
