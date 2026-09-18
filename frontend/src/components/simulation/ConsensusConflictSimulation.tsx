import React, { useState } from 'react'
import { GitMerge, Cpu, Scale } from 'lucide-react'
import { useFacultyMode } from './FacultyModeContext'

type ConflictScenario = 'AGREEMENT' | 'DISAGREEMENT' | 'LOW_QUALITY'

export const ConsensusConflictSimulation: React.FC = () => {
  const { facultyMode } = useFacultyMode()
  const [activeScenario, setActiveScenario] = useState<ConflictScenario>('DISAGREEMENT')

  // Scenario-specific values
  const config = {
    AGREEMENT: {
      title: 'Symmetrical Model Agreement',
      mlClass: 'STRUCTURAL_DEFORMATION',
      mlConfidence: 0.88,
      physicsClass: 'STRUCTURAL_CONSISTENT',
      physicsConsistency: 0.86,
      consensusResult: 'STRUCTURAL_CONFIRMED',
      confidenceMultiplier: 1.15,
      finalConfidence: 0.96,
      actionStatus: 'ELEVATED_ATTENTION',
      explanation:
        'Both the statistical pattern recognizer and deterministic physical velocity limits confirm continuous settlement. Symmetrical agreement amplifies analytical confidence (+15%).',
    },
    DISAGREEMENT: {
      title: 'Cross-Model Divergence & Conflict Penalty',
      mlClass: 'STRUCTURAL_DEFORMATION (PROB = 84%)',
      mlConfidence: 0.84,
      physicsClass: 'SEASONAL_CYCLIC (RECURRENCE DETECTED)',
      physicsConsistency: 0.42,
      consensusResult: 'CONFLICTED (UNCERTAINTY DETECTED)',
      confidenceMultiplier: 0.7,
      finalConfidence: 0.58,
      actionStatus: 'MONITOR (SUPPRESSED ALARM)',
      explanation:
        'STRATA does NOT choose the more alarming model. When ML predicts structural damage but the Physics Engine detects seasonal cyclicity, STRATA applies a -30% uncertainty penalty and downgrades the alert to MONITOR.',
    },
    LOW_QUALITY: {
      title: 'Interferometric Quality Degradation Gate',
      mlClass: 'LOW_COHERENCE_SUPPRESSED',
      mlConfidence: 0.35,
      physicsClass: 'BELOW_NOISE_FLOOR (γ < 0.60)',
      physicsConsistency: 0.3,
      consensusResult: 'INSUFFICIENT_QUALITY',
      confidenceMultiplier: 0.5,
      finalConfidence: 0.32,
      actionStatus: 'INSUFFICIENT_EVIDENCE',
      explanation:
        'Radar coherence is poor (γ = 0.48). STRATA’s measurement quality gate automatically overrides and mutes both ML and Physics engines to prevent confident hallucinations on noisy data.',
    },
  }[activeScenario]

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '1.5rem',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <span className="badge badge-cyan">MODULE 06</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              CROSS-MODEL CONSENSUS &amp; UNCERTAINTY MODULATION
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-primary)' }}>
            {facultyMode ? 'Why Disagreement Lowers Confidence' : 'Cross-Model Consensus: Agreement Amplification vs. Conflict Suppression'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.35rem 0 0 0', maxWidth: '750px' }}>
            {facultyMode
              ? 'If an AI model and a physics model disagree, naive systems guess or pick the worst case. STRATA treats disagreement itself as proof of uncertainty and immediately lowers confidence.'
              : 'Demonstrates mathematical cross-model evidence fusion where divergent interpretations trigger an uncertainty penalty rather than cherry-picking worst-case extremes.'}
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>
            CONCEPTUAL SIMULATION
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Consensus mechanism
          </div>
        </div>
      </div>

      {/* Scenario Selector */}
      <div style={{ display: 'flex', gap: '0.75rem' }}>
        {[
          { id: 'DISAGREEMENT' as ConflictScenario, label: 'Model Disagreement (ML vs Physics Conflict)' },
          { id: 'AGREEMENT' as ConflictScenario, label: 'Model Agreement (Symmetrical Confidence Boost)' },
          { id: 'LOW_QUALITY' as ConflictScenario, label: 'Measurement Degradation (Quality Override)' },
        ].map((s) => (
          <button
            key={s.id}
            onClick={() => setActiveScenario(s.id)}
            className={`btn btn-sm ${activeScenario === s.id ? 'btn-primary' : 'btn-secondary'}`}
            style={{ flex: 1, padding: '0.5rem 0.75rem', fontSize: '0.78rem' }}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Split Screen Diagram */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '6px',
          padding: '1.5rem',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Top Single Observation Point */}
        <div style={{ textAlign: 'center' }}>
          <span
            style={{
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              padding: '0.3rem 0.8rem',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-medium)',
              borderRadius: '4px',
              color: '#ffffff',
            }}
          >
            MULTI-EPOCH INSAR OBSERVATION SEQUENCE (8 EPOCHS)
          </span>
          <div style={{ color: 'var(--accent-cyan)', margin: '0.4rem 0' }}>▼</div>
        </div>

        {/* Dual Engine Split Screen Columns */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1.5rem',
            position: 'relative',
          }}
        >
          {/* Left Column: Machine Learning Engine */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.6rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Cpu size={16} color="var(--accent-cyan)" />
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                ENGINE 1: ML CLASSIFIER (STATISTICAL)
              </span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Trained on 28 observable features across 3,500 sequences
            </div>

            <div style={{ marginTop: '0.4rem', backgroundColor: 'var(--bg-primary)', padding: '0.75rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                INTERPRETATION OUTPUT
              </div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '0.2rem' }}>
                {config.mlClass}
              </div>
              <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                Confidence: {(config.mlConfidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Right Column: Physics Engine */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.6rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Scale size={16} color="var(--state-baseline)" />
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                ENGINE 2: PHYSICS ENGINE (DETERMINISTIC)
              </span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Kinematic velocity bounds, noise floors &amp; environmental periodicity
            </div>

            <div style={{ marginTop: '0.4rem', backgroundColor: 'var(--bg-primary)', padding: '0.75rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                KINEMATIC EVALUATION
              </div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--state-baseline)', marginTop: '0.2rem' }}>
                {config.physicsClass}
              </div>
              <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                Consistency: {(config.physicsConsistency * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>

        {/* Fusion Arrows */}
        <div style={{ textAlign: 'center', color: 'var(--accent-cyan)', margin: '-0.3rem 0' }}>
          ▼ ▼
        </div>

        {/* Consensus Convergence / Conflict Result Box */}
        <div
          style={{
            backgroundColor:
              activeScenario === 'DISAGREEMENT'
                ? 'rgba(244, 63, 94, 0.08)'
                : activeScenario === 'AGREEMENT'
                ? 'rgba(52, 211, 153, 0.08)'
                : 'rgba(251, 191, 36, 0.08)',
            border: `1px solid ${
              activeScenario === 'DISAGREEMENT'
                ? 'var(--state-elevated)'
                : activeScenario === 'AGREEMENT'
                ? 'var(--state-baseline)'
                : 'var(--state-monitor)'
            }`,
            borderRadius: '6px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.85rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <GitMerge
                size={20}
                color={
                  activeScenario === 'DISAGREEMENT'
                    ? 'var(--state-elevated)'
                    : activeScenario === 'AGREEMENT'
                    ? 'var(--state-baseline)'
                    : 'var(--state-monitor)'
                }
              />
              <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {config.title}
              </span>
            </div>

            <span
              className={
                activeScenario === 'DISAGREEMENT'
                  ? 'badge badge-elevated'
                  : activeScenario === 'AGREEMENT'
                  ? 'badge badge-baseline'
                  : 'badge badge-monitor'
              }
              style={{ fontSize: '0.75rem' }}
            >
              {config.actionStatus}
            </span>
          </div>

          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {config.explanation}
          </p>

          {/* Dynamic Confidence Meter */}
          <div style={{ marginTop: '0.4rem' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.72rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-muted)',
                marginBottom: '0.35rem',
              }}
            >
              <span>ANALYTICAL CONFIDENCE MODULATION</span>
              <span style={{ fontWeight: 700, color: '#ffffff' }}>
                {(config.finalConfidence * 100).toFixed(0)}% ({config.confidenceMultiplier > 1 ? '+15% Boost' : '-30% Penalty'})
              </span>
            </div>
            <div style={{ height: '8px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${config.finalConfidence * 100}%`,
                  backgroundColor:
                    activeScenario === 'DISAGREEMENT'
                      ? 'var(--state-elevated)'
                      : activeScenario === 'AGREEMENT'
                      ? 'var(--state-baseline)'
                      : 'var(--state-monitor)',
                  transition: 'width 0.4s ease',
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
