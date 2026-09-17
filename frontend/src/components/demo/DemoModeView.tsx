import React, { useState, useEffect } from 'react'
import {
  Play,
  Pause,
  ChevronRight,
  ShieldCheck,
  Cpu,
  Scale,
  GitMerge,
} from 'lucide-react'
import type { DemoScenario } from '../../types'
import { DEMO_SCENARIOS } from '../../services/api'

interface DemoModeViewProps {
  onSelectScenarioForInspection: (scenario: DemoScenario) => void
}

export const DemoModeView: React.FC<DemoModeViewProps> = ({
  onSelectScenarioForInspection,
}) => {
  const [activeScenario, setActiveScenario] = useState<DemoScenario>(DEMO_SCENARIOS[0])
  const [activeScene, setActiveScene] = useState<number>(1)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)

  useEffect(() => {
    if (!isPlaying) return
    const timer = setInterval(() => {
      setActiveScene((prev) => (prev < 10 ? prev + 1 : 1))
    }, 4000)
    return () => clearInterval(timer)
  }, [isPlaying])

  const scenes = [
    {
      num: 1,
      title: 'Scene 1 — System & Portfolio Overview',
      summary: 'Multi-epoch InSAR telemetry overview across civil infrastructure assets.',
      badge: 'OVERVIEW',
    },
    {
      num: 2,
      title: 'Scene 2 — Asset Identification',
      summary: `Selected civil asset: ${activeScenario.structure_name} (${activeScenario.structure_type}).`,
      badge: 'TARGET ASSET',
    },
    {
      num: 3,
      title: 'Scene 3 — Multi-Epoch Trajectory',
      summary: `Observation history over ${activeScenario.displacements.length} epochs.`,
      badge: 'RADAR ACQUISITIONS',
    },
    {
      num: 4,
      title: 'Scene 4 — Dual Evidence Engines (ML + Physics)',
      summary: 'Decoupled gradient-boosted ML classifier and deterministic physics limits.',
      badge: 'DUAL-ENGINE',
    },
    {
      num: 5,
      title: 'Scene 5 — Cross-Model Consensus',
      summary: 'Evaluating engine agreement: convergence strengthens confidence, conflict triggers penalty.',
      badge: 'CONSENSUS',
    },
    {
      num: 6,
      title: 'Scene 6 — Temporal Evidence & Baseline Guard',
      summary: 'Persistence tracking across time; scientific baseline guard prevents false acceleration alarms.',
      badge: 'TEMPORAL ENGINE',
    },
    {
      num: 7,
      title: 'Scene 7 — Asset Engineering Context',
      summary: `Material: ${activeScenario.material} | Criticality: ${activeScenario.criticality} | Historical baseline noise.`,
      badge: 'CONTEXT',
    },
    {
      num: 8,
      title: 'Scene 8 — Prototype Characterization Index',
      summary: `Prototype Index: ${activeScenario.expected_index} / 100. Evidence State: ${activeScenario.expected_state}.`,
      badge: 'CHARACTERIZATION',
    },
    {
      num: 9,
      title: 'Scene 9 — Tamper-Evident Chronology',
      summary: 'Canonical SHA-256 hash linking each pipeline execution epoch for auditability.',
      badge: 'PROVENANCE',
    },
    {
      num: 10,
      title: 'Scene 10 — Scientific Transparency & Limitations',
      summary: 'Mandatory non-safety disclaimer: STRATA does not certify safety or forecast collapse.',
      badge: 'LEGAL & SCIENCE',
    },
  ]

  const handleNextScene = () => {
    setActiveScene((prev) => (prev < 10 ? prev + 1 : 1))
  }

  const handlePrevScene = () => {
    setActiveScene((prev) => (prev > 1 ? prev - 1 : 10))
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* HEADER WITH SCENARIO SELECTOR */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1.25rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
            <span className="badge badge-cyan">PRESENTATION CONTROLLER</span>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              CALIBRATED 2–3 MINUTE DEMONSTRATION WORKFLOW
            </span>
          </div>
          <h2>Live Demonstration &amp; Stakeholder Walkthrough</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Walk through the complete 10-scene evidence synthesis journey using verified test-suite scenarios.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={() => onSelectScenarioForInspection(activeScenario)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <span>Inspect in Full Workbench</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* SCENARIO SELECTOR BUTTON CHIPS */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          SELECT SCIENTIFIC TEST SCENARIO
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
          {DEMO_SCENARIOS.map((scen) => {
            const isSelected = activeScenario.id === scen.id
            return (
              <button
                key={scen.id}
                onClick={() => {
                  setActiveScenario(scen)
                  setActiveScene(1)
                }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  backgroundColor: isSelected ? 'var(--bg-elevated)' : 'var(--bg-card)',
                  border: '1px solid',
                  borderColor: isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                }}
              >
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-mono)',
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-muted)',
                    fontWeight: 600,
                  }}
                >
                  {scen.code}
                </span>
                <span
                  style={{
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                    marginTop: '0.2rem',
                    lineHeight: 1.25,
                  }}
                >
                  {scen.name}
                </span>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-mono)',
                    color:
                      scen.expected_state === 'BASELINE'
                        ? 'var(--state-baseline)'
                        : scen.expected_state === 'ENVIRONMENTAL_PATTERN'
                        ? 'var(--state-environmental)'
                        : 'var(--state-monitor)',
                    marginTop: '0.4rem',
                  }}
                >
                  {scen.expected_state}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* 10-SCENE TIMELINE NAVIGATION BAR */}
      <div
        className="strata-card"
        style={{
          padding: '1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="badge badge-cyan">SCENE {activeScene} OF 10</span>
            <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
              {scenes[activeScene - 1].title}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className={`btn btn-sm ${isPlaying ? 'btn-primary' : 'btn-secondary'}`}
              style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            >
              {isPlaying ? <Pause size={13} /> : <Play size={13} />}
              <span>{isPlaying ? 'Pause' : 'Auto Play'}</span>
            </button>
            <button onClick={handlePrevScene} className="btn btn-secondary btn-sm">
              Previous
            </button>
            <button onClick={handleNextScene} className="btn btn-primary btn-sm">
              Next
            </button>
          </div>
        </div>

        {/* Scene Dots / Stepper */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', width: '100%' }}>
          {scenes.map((s) => {
            const isCurrent = activeScene === s.num
            const isPassed = activeScene > s.num

            return (
              <div
                key={s.num}
                onClick={() => setActiveScene(s.num)}
                style={{
                  flex: 1,
                  height: '6px',
                  borderRadius: '3px',
                  backgroundColor: isCurrent
                    ? 'var(--accent-cyan)'
                    : isPassed
                    ? 'var(--state-baseline)'
                    : 'var(--border-subtle)',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease',
                }}
                title={s.title}
              />
            )
          })}
        </div>
      </div>

      {/* ACTIVE SCENE DEMONSTRATION WORKBENCH */}
      <div
        className="strata-card elevated"
        style={{
          padding: '1.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-medium)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <span className="badge badge-cyan" style={{ marginBottom: '0.4rem' }}>
              {scenes[activeScene - 1].badge}
            </span>
            <h3 style={{ fontSize: '1.3rem', color: '#ffffff' }}>
              {scenes[activeScene - 1].title}
            </h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.35rem', fontSize: '0.85rem' }}>
              {scenes[activeScene - 1].summary}
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.6rem' }}>
              <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(56, 189, 248, 0.3)', fontSize: '0.7rem' }}>
                Validation status: Preliminary case-study evaluation
              </span>
              <span className="badge" style={{ backgroundColor: 'rgba(148, 163, 184, 0.1)', color: 'var(--text-secondary)', border: '1px solid rgba(148, 163, 184, 0.3)', fontSize: '0.7rem' }}>
                Dataset provenance: Synthetic / Case-Study Placeholder
              </span>
            </div>
          </div>

          <div
            style={{
              padding: '0.5rem 0.85rem',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: '6px',
              border: '1px solid var(--border-subtle)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              textAlign: 'right',
            }}
          >
            <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>EXPECTED INDEX</div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '1.1rem' }}>
              {activeScenario.expected_index.toFixed(1)} / 100
            </div>
          </div>
        </div>

        {/* Scene-Specific Technical Presentation Render */}
        <div
          style={{
            backgroundColor: 'var(--bg-primary)',
            borderRadius: '6px',
            padding: '1.5rem',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {activeScene === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                Portfolio Telemetry Initialization
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                STRATA is monitoring civil infrastructure with calibrated C-Band SAR revisits.
                The system isolates deformation signals from atmospheric phase screen transients and seasonal thermal expansion.
              </p>
            </div>
          )}

          {activeScene === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                Target Infrastructure Profile
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                <div>
                  <span className="text-muted">Structure:</span>
                  <div style={{ color: '#ffffff', fontWeight: 600 }}>{activeScenario.structure_name}</div>
                </div>
                <div>
                  <span className="text-muted">Type / Material:</span>
                  <div style={{ color: '#ffffff' }}>{activeScenario.structure_type} ({activeScenario.material})</div>
                </div>
                <div>
                  <span className="text-muted">Criticality:</span>
                  <div style={{ color: 'var(--accent-cyan)' }}>{activeScenario.criticality}</div>
                </div>
              </div>
            </div>
          )}

          {activeScene === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                Multi-Epoch Displacement Sequence ({activeScenario.displacements.length} Acquisitions)
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {activeScenario.displacements.map((disp, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '0.35rem 0.6rem',
                      backgroundColor: 'var(--bg-secondary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                    }}
                  >
                    Epoch {i + 1}: <strong>{disp.toFixed(1)} mm</strong>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeScene === 4 && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
              <div style={{ padding: '1rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, color: 'var(--accent-indigo)' }}>
                  <Cpu size={16} /> ML Classification
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                  Evaluating spatiotemporal feature vectors. Model confidence scales strictly from empirical cross-validation.
                </p>
              </div>

              <div style={{ padding: '1rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                  <Scale size={16} /> Deterministic Physics Engine
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                  Verifying kinematic limits and noise floor thresholds without ML hallucination risk.
                </p>
              </div>
            </div>
          )}

          {activeScene === 5 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                <GitMerge size={17} color="var(--state-baseline)" />
                <span>Cross-Model Consensus Convergence</span>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                {activeScenario.narrative}
              </p>
            </div>
          )}

          {activeScene === 6 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                Temporal Reasoning &amp; Scientific Baseline Guard
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                STRATA evaluates persistence across time. If the asset is within nominal baseline standard deviation,
                the Scientific Baseline Guard firmly suppresses acceleration warnings.
              </p>
            </div>
          )}

          {activeScene === 7 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                Infrastructure Sensitivity Context
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                Asset-specific weighting applies criticality and structural material multipliers to the fused consensus evidence.
              </p>
            </div>
          )}

          {activeScene === 8 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                Evidence Characterization Index: {activeScenario.expected_index.toFixed(1)} / 100
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                Synthesized final state: <span className="badge badge-cyan">{activeScenario.expected_state}</span>.
                Provides an objective ranking metric for structural inspection prioritizing.
              </p>
            </div>
          )}

          {activeScene === 9 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, color: 'var(--state-baseline)' }}>
                <ShieldCheck size={16} /> Tamper-Evident Chronology Hash Chain
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                Every epoch produces an immutable SHA-256 fingerprint linked to previous epochs. Any alteration of historical observations is immediately detected.
              </p>
            </div>
          )}

          {activeScene === 10 && (
            <div className="strata-disclaimer">
              <strong>Mandatory Scientific Transparency &amp; Non-Safety Notice</strong>
              STRATA is an experimental research prototype for analytical evidence characterization and inspection prioritization.
              It does NOT certify structural safety, predict collapse, calculate failure probabilities, or forecast remaining fatigue life.
              It does not replace physical structural inspection or provide structural safety certification.
            </div>
          )}
        </div>

        {/* Presenter Notes Box */}
        <div
          style={{
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.78rem',
            color: 'var(--text-muted)',
          }}
        >
          <div>
            <strong>Presenter Commentary:</strong> {activeScenario.narrative}
          </div>
        </div>
      </div>
    </div>
  )
}
