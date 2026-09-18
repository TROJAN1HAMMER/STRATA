import React, { useState } from 'react'
import {
  Layers,
  Cpu,
  Scale,
  GitMerge,
  Clock,
  Compass,
  Building2,
} from 'lucide-react'
import { useFacultyMode } from './FacultyModeContext'

interface StageNode {
  id: string
  title: string
  plainTitle: string
  icon: React.ComponentType<{ size?: number; color?: string }>
  plainQuestion: string
  technicalSummary: string
  facultyExplanation: string
  keyParameters: string[]
}

const STAGES: StageNode[] = [
  {
    id: 'quality',
    title: '1. Measurement Quality Gate',
    plainTitle: '1. Radar Signal Reliability Check',
    icon: Layers,
    plainQuestion: 'Is the radar echo clear and trustworthy?',
    technicalSummary: 'Evaluates interferometric coherence (γ ≥ 0.60) and phase noise floor. Insufficient quality suppresses overconfident characterization.',
    facultyExplanation: 'Before making any claims, STRATA checks if the satellite photo was blurry. If radar coherence is low, the system refuses to guess.',
    keyParameters: ['Coherence γ', 'Phase Quality', 'Incidence Angle θ'],
  },
  {
    id: 'ml',
    title: '2. ML Deformation Engine',
    plainTitle: '2. Statistical Pattern Recognizer',
    icon: Cpu,
    plainQuestion: 'What deformation pattern does the learned model identify?',
    technicalSummary: 'Calibrated Gradient-Boosted Decision Tree (LightGBM) trained on 28 observable kinematic, statistical, and coherence features.',
    facultyExplanation: 'A machine learning system trained on thousands of past satellite patterns looks for signatures of movement or settling.',
    keyParameters: ['28-feature Allowlist', 'Isotonic Calibration', '7-Class Probabilities'],
  },
  {
    id: 'physics',
    title: '3. Physics Consistency Engine',
    plainTitle: '3. Physical Velocity & Kinematic Rule Check',
    icon: Scale,
    plainQuestion: 'Does the movement obey real-world physical limits?',
    technicalSummary: 'Deterministic kinematic rules testing velocity bounds, noise envelopes, and environmental periodicities without machine-learning assumptions.',
    facultyExplanation: 'A separate, non-AI rule checker verifies if the measured speed is physically realistic for steel or concrete structures.',
    keyParameters: ['Displacement Rate v', 'Kinematic Acceleration a', 'Baseline Envelope ±1σ'],
  },
  {
    id: 'consensus',
    title: '4. Cross-Model Consensus Engine',
    plainTitle: '4. Independent Engine Agreement Check',
    icon: GitMerge,
    plainQuestion: 'Do the statistical model and physics rules agree?',
    technicalSummary: 'Cross-model confidence modulation: agreement amplifies confidence by +15%; divergence triggers a -30% uncertainty penalty.',
    facultyExplanation: 'Like two consulting engineers: if they both agree the bridge settled, confidence rises. If they disagree, confidence drops and more monitoring is ordered.',
    keyParameters: ['Agreement Mass', 'Divergence Penalty (-30%)', 'Conflicted Flag'],
  },
  {
    id: 'temporal',
    title: '5. Multi-Epoch Temporal Evidence',
    plainTitle: '5. Multi-Visit Movement Tracking',
    icon: Clock,
    plainQuestion: 'Does the movement persist across repeated satellite visits?',
    technicalSummary: '9-state kinematic finite state machine verifying temporal persistence, acceleration support, and baseline noise departures.',
    facultyExplanation: 'One strange measurement is not enough. The movement must continue steadily across consecutive satellite visits weeks apart.',
    keyParameters: ['Persistence Count', 'Baseline Departure', 'Supported Acceleration'],
  },
  {
    id: 'environmental',
    title: '6. Environmental Recurrence Guard',
    plainTitle: '6. Seasonal & Weather Safeguard',
    icon: Compass,
    plainQuestion: 'Could this be caused by summer heat or rainy seasons?',
    technicalSummary: 'Tests for periodic sign changes and correlation with cyclic thermal/hydrological forcing. Suppresses false structural alarms.',
    facultyExplanation: 'Structures expand in hot summers and contract in cold winters. STRATA recognizes this cycle and refuses to label normal seasonal motion as damage.',
    keyParameters: ['Zero Crossings (≥2)', 'Thermal Cycle Period', 'Reversibility Flag'],
  },
  {
    id: 'characterization',
    title: '7. Infrastructure Context & Characterization',
    plainTitle: '7. Asset Significance & Final Rating',
    icon: Building2,
    plainQuestion: 'How urgent is this evidence for this specific structure?',
    technicalSummary: 'Fuses consensus evidence with asset type, material stiffness, critical zones, and geodetic baselines into the Evidence Characterization Index.',
    facultyExplanation: 'A few millimeters of movement matters more on a rigid concrete dam than on a flexible suspension bridge. The final index tells inspectors where to look first.',
    keyParameters: ['Asset Material Weight', 'Critical Zone Multiplier', 'Evidence Characterization Index (0-100)'],
  },
]

export const EvidenceFusionDiagram: React.FC = () => {
  const { facultyMode } = useFacultyMode()
  const [selectedStageId, setSelectedStageId] = useState<string>('consensus')

  const selectedStage = STAGES.find((s) => s.id === selectedStageId) || STAGES[3]

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
            STRATA Evidence Fusion Architecture
          </h3>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Click any analytical stage below to inspect its mechanism, input parameters, and reasoning logic
          </div>
        </div>
        <span className="badge badge-cyan" style={{ fontSize: '0.68rem' }}>
          INTERACTION PIPELINE
        </span>
      </div>

      {/* Interactive Stage Flow Steps */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '0.5rem',
        }}
      >
        {STAGES.map((stage) => {
          const isSelected = stage.id === selectedStageId
          const Icon = stage.icon

          return (
            <div
              key={stage.id}
              onClick={() => setSelectedStageId(stage.id)}
              style={{
                backgroundColor: isSelected ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-primary)',
                border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '0.75rem 0.6rem',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
                alignItems: 'center',
                textAlign: 'center',
                transition: 'all 0.2s ease',
              }}
            >
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: isSelected ? 'var(--accent-cyan)' : 'rgba(255, 255, 255, 0.05)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon size={14} color={isSelected ? 'var(--bg-primary)' : 'var(--text-secondary)'} />
              </div>
              <div
                style={{
                  fontSize: '0.72rem',
                  fontWeight: isSelected ? 700 : 500,
                  color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  lineHeight: 1.2,
                }}
              >
                {facultyMode ? stage.plainTitle : stage.title}
              </div>
            </div>
          )
        })}
      </div>

      {/* Detail Expansion Box */}
      <div
        style={{
          backgroundColor: 'var(--bg-primary)',
          border: '1px solid var(--border-medium)',
          borderRadius: '6px',
          padding: '1.25rem',
          display: 'grid',
          gridTemplateColumns: '1.4fr 1fr',
          gap: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
              STAGE DETAILS
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>•</span>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {facultyMode ? selectedStage.plainTitle : selectedStage.title}
            </span>
          </div>

          <div style={{ color: 'var(--accent-cyan)', fontSize: '0.88rem', fontStyle: 'italic', marginBottom: '0.6rem' }}>
            "{selectedStage.plainQuestion}"
          </div>

          <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {facultyMode ? selectedStage.facultyExplanation : selectedStage.technicalSummary}
          </p>

          <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              KEY FACTORS:
            </span>
            <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
              {selectedStage.keyParameters.map((param) => (
                <span
                  key={param}
                  style={{
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-mono)',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    padding: '0.15rem 0.45rem',
                    borderRadius: '3px',
                    color: 'var(--text-secondary)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  {param}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'rgba(56, 189, 248, 0.04)',
            border: '1px solid rgba(56, 189, 248, 0.15)',
            borderRadius: '6px',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
            Faculty Takeaway
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontStyle: 'italic', lineHeight: 1.45 }}>
            {selectedStage.facultyExplanation}
          </div>
        </div>
      </div>
    </div>
  )
}
