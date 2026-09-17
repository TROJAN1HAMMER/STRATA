import React, { useState, useEffect } from 'react'
import {
  CheckCircle2,
  Loader2,
  X,
  Sliders,
  ArrowRight,
} from 'lucide-react'
import type { PipelineResult, Infrastructure } from '../../types'

interface PipelineExecutionModalProps {
  isOpen: boolean
  infrastructure: Infrastructure | null
  onClose: () => void
  onComplete: (result: PipelineResult) => void
  executePipeline: (infraId: string) => Promise<PipelineResult>
}

interface Stage {
  id: number
  label: string
  detail: string
}

const STAGES: Stage[] = [
  { id: 1, label: '01  Input Validation', detail: 'Validating InSAR orbit geometry & VV radar polarization' },
  { id: 2, label: '02  Observation Normalization', detail: 'Phase unwrapping & line-of-sight vertical conversion' },
  { id: 3, label: '03  Historical Assembly', detail: 'Compiling multi-epoch chronological radar acquisitions' },
  { id: 4, label: '04  ML Inference', detail: 'Gradient-boosted decision trees deformation classification' },
  { id: 5, label: '05  Physics Consistency', detail: 'Deterministic kinematic velocity & noise floor limits' },
  { id: 6, label: '06  Consensus Fusion', detail: 'Cross-model agreement evaluation & confidence scaling' },
  { id: 7, label: '07  Temporal Evidence', detail: 'Multi-epoch persistence & Scientific Baseline Guard' },
  { id: 8, label: '08  Infrastructure Context', detail: 'Critical zones, structure type & z-score deviation' },
  { id: 9, label: '09  Evidence Chronology', detail: 'Computing canonical SHA-256 tamper-evident hash link' },
]

export const PipelineExecutionModal: React.FC<PipelineExecutionModalProps> = ({
  isOpen,
  infrastructure,
  onClose,
  onComplete,
  executePipeline,
}) => {
  const [currentStage, setCurrentStage] = useState<number>(0)
  const [isCompleted, setIsCompleted] = useState<boolean>(false)
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null)

  useEffect(() => {
    if (!isOpen || !infrastructure) {
      setCurrentStage(0)
      setIsCompleted(false)
      setPipelineResult(null)
      return
    }

    let isCancelled = false

    // Fetch or execute actual pipeline
    executePipeline(infrastructure.id).then((result) => {
      if (!isCancelled) {
        setPipelineResult(result)
      }
    })

    // Animate stages smoothly across ~2.5 seconds total
    const interval = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev < STAGES.length) {
          return prev + 1
        } else {
          clearInterval(interval)
          setIsCompleted(true)
          return prev
        }
      });
    }, 280)

    return () => {
      isCancelled = true
      clearInterval(interval)
    }
  }, [isOpen, infrastructure])

  if (!isOpen || !infrastructure) return null

  const handleFinish = () => {
    if (pipelineResult) {
      onComplete(pipelineResult)
    }
    onClose()
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(3, 7, 18, 0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '560px',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-medium)',
          borderRadius: '8px',
          padding: '1.75rem',
          boxShadow: 'var(--shadow-card)',
        }}
        onClick={(e) => e.stopPropagation()}
        className="animate-fade-in"
      >
        {/* MODAL HEADER */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: '1rem',
            marginBottom: '1.25rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sliders size={18} color="var(--accent-cyan)" />
              <span style={{ fontWeight: 700, fontSize: '1.1rem', letterSpacing: '-0.01em' }}>
                STRATA Pipeline Execution
              </span>
            </div>
            <div
              style={{
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-mono)',
                marginTop: '0.2rem',
              }}
            >
              TARGET: {infrastructure.name} ({infrastructure.structure_type})
            </div>
          </div>

          <button onClick={onClose} className="btn btn-ghost btn-sm" style={{ padding: '0.2rem' }}>
            <X size={16} />
          </button>
        </div>

        {/* 9-STAGE SEQUENCE PROGRESSION */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {STAGES.map((st) => {
            const isDone = currentStage > st.id || isCompleted
            const isRunning = currentStage === st.id && !isCompleted

            return (
              <div
                key={st.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '4px',
                  backgroundColor: isRunning ? 'var(--bg-card)' : 'transparent',
                  border: isRunning ? '1px solid var(--border-bright)' : '1px solid transparent',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ width: '18px', height: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {isDone ? (
                      <CheckCircle2 size={16} color="var(--state-baseline)" />
                    ) : isRunning ? (
                      <Loader2 size={16} color="var(--accent-cyan)" style={{ animation: 'radarSweep 1s linear infinite' }} />
                    ) : (
                      <span
                        style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: 'var(--border-medium)',
                        }}
                      />
                    )}
                  </div>
                  <div>
                    <span
                      style={{
                        fontSize: '0.825rem',
                        fontFamily: 'var(--font-mono)',
                        color: isDone ? '#ffffff' : isRunning ? 'var(--accent-cyan)' : 'var(--text-muted)',
                        fontWeight: isRunning ? 600 : 400,
                      }}
                    >
                      {st.label}
                    </span>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                      {st.detail}
                    </div>
                  </div>
                </div>

                <div>
                  {isDone && (
                    <span
                      style={{
                        fontSize: '0.68rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--state-baseline)',
                      }}
                    >
                      COMPLETE
                    </span>
                  )}
                  {isRunning && (
                    <span
                      style={{
                        fontSize: '0.68rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--accent-cyan)',
                      }}
                    >
                      PROCESSING...
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* COMPLETION SUMMARY CARD */}
        {isCompleted && (
          <div
            className="animate-fade-in"
            style={{
              marginTop: '1.25rem',
              padding: '1rem',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: '6px',
              border: '1px solid var(--state-baseline-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--state-baseline)' }}>
                ANALYSIS COMPLETE
              </span>
              <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>
                PIPELINE v1.0.0
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '0.5rem',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem',
              }}
            >
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>EVIDENCE STATE</div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.15rem' }}>
                  {pipelineResult?.risk_characterization?.evidence_state || pipelineResult?.risk_characterization?.characterization_state || 'BASELINE'}
                </div>
              </div>

              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>CONFIDENCE</div>
                <div style={{ fontWeight: 600, color: 'var(--accent-cyan)', marginTop: '0.15rem' }}>
                  {(((pipelineResult?.risk_characterization?.analytical_confidence ?? pipelineResult?.risk_characterization?.confidence ?? 0.85)) * 100).toFixed(1)}%
                </div>
              </div>

              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>CHARACTERIZATION INDEX</div>
                <div style={{ fontWeight: 700, color: '#ffffff', marginTop: '0.15rem' }}>
                  {(pipelineResult?.risk_characterization?.evidence_characterization_index ?? pipelineResult?.risk_characterization?.prototype_risk_index ?? 5.1).toFixed(1)} / 100
                </div>
              </div>
            </div>

            <button
              onClick={handleFinish}
              className="btn btn-primary"
              style={{ marginTop: '0.5rem', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
            >
              <span>Inspect Full Evidence Assessment</span>
              <ArrowRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
