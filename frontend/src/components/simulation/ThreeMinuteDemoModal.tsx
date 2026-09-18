import React, { useState } from 'react'
import { X, ChevronLeft, ChevronRight, RotateCcw, Volume2, Sparkles } from 'lucide-react'

interface DemoStep {
  timeWindow: string
  title: string
  plainQuestion: string
  conceptSummary: string
  visualDescription: string
  speakerNotes: string
  keyTakeaway: string
}

const DEMO_STEPS: DemoStep[] = [
  {
    timeWindow: '00:00 – 00:20',
    title: '1. What is Satellite Radar?',
    plainQuestion: 'How does a satellite monitor structures without photos?',
    conceptSummary: 'Radar satellites emit active microwave pulses day and night through clouds, penetrating darkness and weather.',
    visualDescription: 'Radar antenna transmitting coherent microwave beam down to the Golden Gate Bridge.',
    speakerNotes:
      '"Ladies and gentlemen, optical satellite photos cannot measure structural movement down to millimeters, and they fail at night or in rain. InSAR solves this by sending active microwave radar pulses to Earth and measuring the exact return echo."',
    keyTakeaway: 'Active microwave pulses ensure 24/7 all-weather measurement capability.',
  },
  {
    timeWindow: '00:20 – 00:40',
    title: '2. Repeated Observation & Phase Shift',
    plainQuestion: 'How do multiple visits reveal millimeter motion?',
    conceptSummary: 'By comparing the wave phase between consecutive satellite passes, tiny changes in distance along the Line-of-Sight are calculated.',
    visualDescription: 'Two satellite orbits 12 days apart showing wave interference fringe shifts.',
    speakerNotes:
      '"When the satellite passes again 12 days later, if the bridge deck has settled by even 4 millimeters, the radar wave echo returns slightly out of phase. This phase difference gives us sub-centimeter displacement tracking without physical sensors on the bridge."',
    keyTakeaway: 'Differential phase tracks minute displacement without ground sensor installation.',
  },
  {
    timeWindow: '00:40 – 01:00',
    title: '3. The Environmental Confusion Trap',
    plainQuestion: 'Why can environmental effects create misleading signals?',
    conceptSummary: 'Summer thermal expansion and rainwater saturation create large motion signals that are completely non-structural.',
    visualDescription: 'Bridge deck expanding in summer heat and contracting in winter cold.',
    speakerNotes:
      '"Here is the central engineering dilemma: a bridge expands in July and contracts in January by up to 15 millimeters. If a naive algorithm sees this, it triggers a false alarm. STRATA\'s temporal engine tests for environmental recurrence so normal seasonal cycles are never mistaken for structural failure."',
    keyTakeaway: 'Persistent cyclic motion is environmental, not structural deterioration.',
  },
  {
    timeWindow: '01:00 – 01:20',
    title: '4. Dual Independent Analytical Engines',
    plainQuestion: 'How does STRATA analyze the data?',
    conceptSummary: 'STRATA decouples statistical Machine Learning (GBDT) from deterministic kinematic physics rules.',
    visualDescription: 'Split-screen showing ML classification features on the left and physical velocity bounds on the right.',
    speakerNotes:
      '"Rather than trusting a single black-box neural network, STRATA deploys two decoupled engines: a calibrated Gradient-Boosted Classifier trained on historical deformation patterns, and a deterministic Physics Engine enforcing strict kinematic laws and noise floors."',
    keyTakeaway: 'Machine learning patterns are verified against deterministic kinematic laws.',
  },
  {
    timeWindow: '01:20 – 01:40',
    title: '5. Consensus & The Disagreement Principle',
    plainQuestion: 'What happens when the two engines disagree?',
    conceptSummary: 'Agreement amplifies confidence (+15%); disagreement is treated as evidence of uncertainty and triggers a confidence penalty (-30%).',
    visualDescription: 'Dynamic confidence meter expanding during agreement and contracting during divergent interpretations.',
    speakerNotes:
      '"STRATA never averages conflicting models or chooses the more alarming output. When ML predicts structural deformation but the Physics Engine detects seasonal cyclicity, STRATA lowers confidence and flags the asset as CONFLICTED. Disagreement is treated as proof of uncertainty."',
    keyTakeaway: 'Disagreement is evidence of uncertainty, preventing overconfident false alarms.',
  },
  {
    timeWindow: '01:40 – 02:00',
    title: '6. Multi-Epoch Temporal Evidence',
    plainQuestion: 'Does the movement persist across time?',
    conceptSummary: 'A state machine tracks motion across consecutive epochs, verifying whether deformation continues or reverts into historical noise.',
    visualDescription: 'Historical baseline band ±1σ with multi-epoch trajectory breaking out unidirectionally.',
    speakerNotes:
      '"A single anomalous measurement could be a cloud or atmospheric moisture artifact. STRATA requires temporal persistence: the movement must continue unidirectionally beyond the historical noise envelope across multiple satellite revisits before structural attention is escalated."',
    keyTakeaway: 'Single-epoch transients are suppressed; true persistence must be demonstrated.',
  },
  {
    timeWindow: '02:00 – 02:20',
    title: '7. Infrastructure Context & Asset Criticality',
    plainQuestion: 'Why does asset type and material matter?',
    conceptSummary: 'Steel suspension bridges, concrete dams, and earthen rail embankments respond differently to thermal loading and settlement.',
    visualDescription: 'Asset card showing structure type, material stiffness, critical zones, and historical geodetic baseline.',
    speakerNotes:
      '"Five millimeters of movement means something very different on a flexible steel suspension span than on a stiff concrete arch dam. STRATA weights the kinematic evidence against the asset\'s specific structure type, construction material, critical zones, and historical baseline."',
    keyTakeaway: 'Physical kinematics are interpreted in the specific context of the asset.',
  },
  {
    timeWindow: '02:20 – 02:40',
    title: '8. The Evidence Characterization Index',
    plainQuestion: 'What is STRATA\'s final output?',
    conceptSummary: 'A 0-100 diagnostic index indicating evidence significance for physical inspection scheduling.',
    visualDescription: 'Evidence Characterization Index dial (0 to 100) alongside analytical confidence percentage.',
    speakerNotes:
      '"The final output is the Evidence Characterization Index—a calibrated 0 to 100 score that prioritizes maintenance inspections. It is paired with an analytical confidence percentage so decision-makers know exactly how robust the satellite evidence is."',
    keyTakeaway: 'An actionable diagnostic index for inspection triage, not a safety certificate.',
  },
  {
    timeWindow: '02:40 – 03:00',
    title: '9. Tamper-Evident Chronology & Disclaimers',
    plainQuestion: 'How do we know the history was never altered?',
    conceptSummary: 'Every analytical step is linked into an immutable SHA-256 hash chain with strict regulatory non-safety disclaimers.',
    visualDescription: 'Cryptographic hash blocks linking Record 1 to Record 2 with verification stamp.',
    speakerNotes:
      '"To prevent retroactive tampering or liability disputes, every analysis is chained cryptographically using SHA-256 hashes. And critically: STRATA is an analytical decision aid—not an automated safety certification or collapse forecast. Physical engineering inspections remain essential."',
    keyTakeaway: 'Cryptographic auditability preserves provenance with full scientific humility.',
  },
]

interface ThreeMinuteDemoModalProps {
  isOpen: boolean
  onClose: () => void
}

export const ThreeMinuteDemoModal: React.FC<ThreeMinuteDemoModalProps> = ({ isOpen, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0)

  if (!isOpen) return null

  const step = DEMO_STEPS[currentStep]

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 7, 10, 0.88)',
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
          maxWidth: '860px',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-medium)',
          borderRadius: '10px',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px rgba(0, 0, 0, 0.7)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.75rem',
            borderBottom: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-secondary)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                backgroundColor: 'rgba(56, 189, 248, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--accent-cyan)',
              }}
            >
              <Sparkles size={18} color="var(--accent-cyan)" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', margin: 0, color: 'var(--text-primary)' }}>
                Explain STRATA in 3 Minutes
              </h2>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Faculty &amp; Reviewer Presentation Walkthrough • Step {currentStep + 1} of {DEMO_STEPS.length}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8rem',
                color: 'var(--accent-cyan)',
                backgroundColor: 'rgba(56, 189, 248, 0.08)',
                padding: '0.2rem 0.6rem',
                borderRadius: '4px',
                border: '1px solid rgba(56, 189, 248, 0.2)',
              }}
            >
              {step.timeWindow}
            </span>
            <button onClick={onClose} className="btn btn-ghost btn-sm" style={{ padding: '0.35rem' }}>
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Timeline Progress Bar */}
        <div style={{ display: 'flex', height: '4px', backgroundColor: 'var(--bg-primary)' }}>
          {DEMO_STEPS.map((_, idx) => (
            <div
              key={idx}
              onClick={() => setCurrentStep(idx)}
              style={{
                flex: 1,
                backgroundColor:
                  idx === currentStep
                    ? 'var(--accent-cyan)'
                    : idx < currentStep
                    ? 'rgba(56, 189, 248, 0.4)'
                    : 'transparent',
                cursor: 'pointer',
                transition: 'background-color 0.2s ease',
              }}
            />
          ))}
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Step Title & Question */}
          <div>
            <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              STAGE {currentStep + 1}
            </div>
            <h3 style={{ fontSize: '1.35rem', margin: '0.2rem 0 0.4rem 0', color: 'var(--text-primary)' }}>
              {step.title}
            </h3>
            <div style={{ color: 'var(--accent-cyan)', fontSize: '0.9rem', fontStyle: 'italic' }}>
              "{step.plainQuestion}"
            </div>
          </div>

          {/* Scientific Concept & Visual Guide */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1.2fr 1fr',
              gap: '1.25rem',
              backgroundColor: 'var(--bg-primary)',
              padding: '1.25rem',
              borderRadius: '6px',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem', fontFamily: 'var(--font-mono)' }}>
                Core Concept
              </div>
              <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {step.conceptSummary}
              </p>
            </div>

            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem', fontFamily: 'var(--font-mono)' }}>
                Visual Demonstration
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic', lineHeight: 1.4 }}>
                {step.visualDescription}
              </div>
            </div>
          </div>

          {/* Speaker Notes */}
          <div
            style={{
              backgroundColor: 'rgba(56, 189, 248, 0.04)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              borderRadius: '6px',
              padding: '1rem 1.25rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <Volume2 size={16} color="var(--accent-cyan)" />
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                Presenter Script (Say This)
              </span>
            </div>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', fontStyle: 'italic', lineHeight: 1.5 }}>
              {step.speakerNotes}
            </div>
          </div>

          {/* Key Takeaway */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>KEY TAKEAWAY</span>
            <span>{step.keyTakeaway}</span>
          </div>
        </div>

        {/* Navigation Footer */}
        <div
          style={{
            padding: '1rem 1.75rem',
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-secondary)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <button
            onClick={() => setCurrentStep(0)}
            className="btn btn-ghost btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <RotateCcw size={14} />
            <span>Restart</span>
          </button>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
              disabled={currentStep === 0}
              className="btn btn-secondary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <ChevronLeft size={16} />
              <span>Previous</span>
            </button>

            {currentStep < DEMO_STEPS.length - 1 ? (
              <button
                onClick={() => setCurrentStep((prev) => Math.min(DEMO_STEPS.length - 1, prev + 1))}
                className="btn btn-primary btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <span>Next Step</span>
                <ChevronRight size={16} />
              </button>
            ) : (
              <button
                onClick={onClose}
                className="btn btn-primary btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <span>Complete Walkthrough</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
