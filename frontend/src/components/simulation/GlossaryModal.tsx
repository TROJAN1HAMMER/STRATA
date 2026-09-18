import React, { useState } from 'react'
import { X, Search, BookOpen } from 'lucide-react'

interface GlossaryEntry {
  term: string
  plain: string
  technical: string
  category: 'InSAR Physics' | 'Machine Learning' | 'Consensus & Temporal' | 'Audit & Integrity'
  analogy?: string
}

const GLOSSARY_TERMS: GlossaryEntry[] = [
  {
    term: 'SAR (Synthetic Aperture Radar)',
    plain: 'A satellite radar that illuminates the ground with microwave pulses to build detailed images day or night through clouds.',
    technical: 'Active microwave imaging system utilizing the motion of the satellite platform to synthesize an electronically large antenna aperture.',
    category: 'InSAR Physics',
    analogy: 'Like illuminating a dark room with a strobe flash rather than waiting for sunlight.',
  },
  {
    term: 'InSAR (Interferometric SAR)',
    plain: 'Comparing two radar images taken at different times to measure tiny surface movements down to millimeters.',
    technical: 'Technique exploiting phase differences between two or more complex coregistered SAR acquisitions to estimate surface displacement.',
    category: 'InSAR Physics',
    analogy: 'Like taking two photos from the exact same spot and comparing how much things shifted.',
  },
  {
    term: 'LOS (Line-Of-Sight)',
    plain: 'The direct diagonal straight line connecting the satellite radar antenna to the infrastructure on Earth.',
    technical: 'One-dimensional projection vector of 3D displacement along the radar range direction (defined by incidence angle θ and flight heading).',
    category: 'InSAR Physics',
    analogy: 'The line formed by an optical laser pointer between the satellite and the bridge.',
  },
  {
    term: 'Coherence (γ)',
    plain: 'How clear, stable, and reliable the radar reflection is between satellite passes (0.0 to 1.0).',
    technical: 'Normalized cross-correlation coefficient of the complex radar phase signals across interferometric pairs. Values below 0.60 indicate decorrelation.',
    category: 'InSAR Physics',
    analogy: 'High coherence is like a clear glass mirror; low coherence is like rough sandpaper.',
  },
  {
    term: 'Phase (ϕ)',
    plain: 'The exact stage of the microwave wave cycle when it hits the target and bounces back.',
    technical: 'Fractional angular portion of the sinusoidal electromagnetic carrier wave (2π radians per cycle), sensitive to sub-wavelength range shifts.',
    category: 'InSAR Physics',
  },
  {
    term: 'Interferogram',
    plain: 'A color fringe map created by subtracting two radar phase images to reveal ground motion.',
    technical: '2D phase difference image produced by complex conjugate multiplication of two coregistered SLC SAR scenes.',
    category: 'InSAR Physics',
  },
  {
    term: 'Deformation',
    plain: 'Physical movement, settlement, bending, or shifting of a structure over time.',
    technical: 'Kinematic displacement field of an infrastructure asset relative to a stable reference point or historical geodetic baseline.',
    category: 'InSAR Physics',
  },
  {
    term: 'Temporal Baseline',
    plain: 'The number of days between two satellite radar snapshots (e.g. 6 or 12 days for Sentinel-1).',
    technical: 'Elapsed calendar duration Δt between master and slave SAR acquisitions, critical for kinematic rate computation.',
    category: 'InSAR Physics',
  },
  {
    term: 'Atmospheric Artifact',
    plain: 'A false motion signal caused when radar waves pass through humid air, clouds, or rain.',
    technical: 'Tropospheric water-vapor phase delay inducing spurious apparent phase gradients that mimic surface deformation.',
    category: 'InSAR Physics',
    analogy: 'A coin at the bottom of a wavy swimming pool appears to move even though it is completely still.',
  },
  {
    term: 'Seasonal Deformation',
    plain: 'Natural cyclic expansion and contraction of structures caused by summer heating and winter cooling.',
    technical: 'Periodic, reversible deformation correlated with ambient temperature cycles that must be separated from irreversible structural failure.',
    category: 'Consensus & Temporal',
  },
  {
    term: 'ML Classifier',
    plain: 'A statistical model that recognizes patterns in deformation history based on thousands of past examples.',
    technical: 'Calibrated Gradient-Boosted Decision Tree (LightGBM) trained on 28 kinematic, statistical, and coherence features.',
    category: 'Machine Learning',
  },
  {
    term: 'Physics Consistency',
    plain: 'A rule-checking engine that asks: "Does this measurement obey known physical velocity and acceleration limits?"',
    technical: 'Deterministic heuristic engine evaluating strict kinematic bounds, noise floor margins, and environmental thresholds.',
    category: 'InSAR Physics',
  },
  {
    term: 'Cross-Model Consensus',
    plain: 'A mechanism where two independent methods compare answers: agreement boosts confidence, while disagreement lowers confidence.',
    technical: 'Evidence fusion layer modulating analytical confidence based on mathematical agreement between statistical ML and deterministic kinematics.',
    category: 'Consensus & Temporal',
  },
  {
    term: 'Persistence',
    plain: 'A deformation pattern that continues steadily over multiple visits rather than jumping back to normal.',
    technical: 'Multi-epoch temporal state requiring unidirectional monotonic trend sustained across consecutive acquisitions beyond baseline noise.',
    category: 'Consensus & Temporal',
  },
  {
    term: 'Evidence Characterization Index',
    plain: 'A diagnostic triage rating (0-100) indicating the urgency of engineering attention based on evidence.',
    technical: 'Composite index weighted across kinematic rate, measurement quality, consensus confidence, and asset criticality. NOT a failure probability.',
    category: 'Consensus & Temporal',
  },
  {
    term: 'SHA-256 Hash Chain',
    plain: 'A digital tamper-evident chain of seals ensuring no historical analysis record can be secretly altered.',
    technical: 'Cryptographic ledger linking sequential analytical records via SHA-256 parent hash pointers, providing full retroactive auditability.',
    category: 'Audit & Integrity',
    analogy: 'Consecutive pages in an indelible audit register, each stamped with an unbroken seal referencing the previous page.',
  },
]

interface GlossaryModalProps {
  isOpen: boolean
  onClose: () => void
}

export const GlossaryModal: React.FC<GlossaryModalProps> = ({ isOpen, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('ALL')

  if (!isOpen) return null

  const filtered = GLOSSARY_TERMS.filter((item) => {
    const matchesSearch =
      item.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.plain.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.technical.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCat = activeCategory === 'ALL' || item.category === activeCategory
    return matchesSearch && matchesCat
  })

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 7, 10, 0.85)',
        backdropFilter: 'blur(8px)',
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
          maxWidth: '820px',
          maxHeight: '85vh',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-medium)',
          borderRadius: '8px',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: 'var(--bg-secondary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <BookOpen size={20} color="var(--accent-cyan)" />
            <div>
              <h2 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--text-primary)' }}>
                STRATA Scientific Glossary &amp; Technical Reference
              </h2>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Concise plain-language and scientific definitions for academic and patent review
              </div>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost btn-sm" style={{ padding: '0.3rem' }}>
            <X size={18} />
          </button>
        </div>

        {/* Search & Category Filter */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            gap: '1rem',
            alignItems: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.01)',
          }}
        >
          <div
            style={{
              position: 'relative',
              flex: 1,
            }}
          >
            <Search
              size={15}
              color="var(--text-muted)"
              style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              placeholder="Search terms, concepts, or plain-English keywords..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '0.45rem 0.8rem 0.45rem 2.2rem',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                color: 'var(--text-primary)',
                fontSize: '0.85rem',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.4rem', fontSize: '0.72rem' }}>
            {['ALL', 'InSAR Physics', 'Machine Learning', 'Consensus & Temporal', 'Audit & Integrity'].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`btn btn-sm ${activeCategory === cat ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '0.25rem 0.55rem', fontSize: '0.7rem' }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Term List */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          {filtered.map((item) => (
            <div
              key={item.term}
              style={{
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '1rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--accent-cyan)' }}>
                  {item.term}
                </span>
                <span
                  style={{
                    fontSize: '0.65rem',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-muted)',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    padding: '0.15rem 0.45rem',
                    borderRadius: '3px',
                  }}
                >
                  {item.category}
                </span>
              </div>

              {/* Plain English */}
              <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.5rem', lineHeight: 1.4 }}>
                <strong style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginRight: '0.4rem' }}>
                  Plain English:
                </strong>
                {item.plain}
              </div>

              {/* Technical Definition */}
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', lineHeight: 1.4 }}>
                <strong style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase', marginRight: '0.4rem' }}>
                  Technical:
                </strong>
                {item.technical}
              </div>

              {/* Analogy if available */}
              {item.analogy && (
                <div
                  style={{
                    marginTop: '0.5rem',
                    padding: '0.4rem 0.6rem',
                    backgroundColor: 'rgba(56, 189, 248, 0.05)',
                    borderLeft: '2px solid var(--accent-cyan)',
                    fontSize: '0.75rem',
                    color: 'var(--text-secondary)',
                    fontStyle: 'italic',
                  }}
                >
                  Analogy: {item.analogy}
                </div>
              )}
            </div>
          ))}

          {filtered.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              No glossary terms match your search filter.
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '0.75rem 1.5rem',
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-secondary)',
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>STRATA v1.0.0 Scientific Dictionary</span>
          <span>16 Standard InSAR &amp; Integrity Terms</span>
        </div>
      </div>
    </div>
  )
}
