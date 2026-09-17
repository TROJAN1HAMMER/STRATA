import React from 'react'
import { X, CheckCircle2, AlertTriangle } from 'lucide-react'

interface AboutModalProps {
  isOpen: boolean
  onClose: () => void
}

export const AboutModal: React.FC<AboutModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null

  const versionMatrix = [
    { component: 'System Pipeline', version: 'v1.0.0 (FROZEN)', status: '202/202 Tests Passing' },
    { component: 'ML Deformation Classifier', version: 'v0.1.0 (Gradient-Boosted)', status: 'Feature-Frozen' },
    { component: 'Deterministic Physics Engine', version: 'v0.2.1 (Kinematic Limits)', status: 'Threshold-Locked' },
    { component: 'Cross-Model Consensus Engine', version: 'v0.1.0 (Dual-Engine Fused)', status: 'Validated' },
    { component: 'Temporal Evidence & Baseline Guard', version: 'v1.0.0 (Phase 6.2 Locked)', status: 'Suppression Active' },
    { component: 'Infrastructure Risk Characterization', version: 'v1.0.0 (Context-Aware)', status: 'Standardized' },
    { component: 'Tamper-Evident Evidence Chronology', version: 'v1.0.0 (SHA-256 Chain)', status: 'Audit-Verified' },
  ]

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
          maxWidth: '680px',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-medium)',
          borderRadius: '8px',
          padding: '1.75rem',
          boxShadow: 'var(--shadow-card)',
          maxHeight: '90vh',
          overflowY: 'auto',
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
              <span style={{ fontWeight: 700, fontSize: '1.2rem', letterSpacing: '-0.01em' }}>
                STRATA Scientific Methodology &amp; System Freeze
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
              Structural Temporal Analysis &amp; Threat Assessment — Research Prototype
            </div>
          </div>

          <button onClick={onClose} className="btn btn-ghost btn-sm" style={{ padding: '0.2rem' }}>
            <X size={16} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* WHAT STRATA DOES VS DOES NOT DO */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {/* What STRATA Does */}
            <div
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.05)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                borderRadius: '6px',
                padding: '1rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--state-baseline)', fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                <CheckCircle2 size={16} /> What STRATA Does
              </div>
              <ul style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', paddingLeft: '1.1rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <li>Multi-epoch InSAR satellite observations</li>
                <li>Learned statistical deformation classification</li>
                <li>Deterministic physical consistency verification</li>
                <li>Cross-model evidence consensus &amp; confidence scaling</li>
                <li>Longitudinal temporal evidence &amp; baseline guard</li>
                <li>Infrastructure-specific contextual sensitivity</li>
                <li>Tamper-evident SHA-256 evidence chronology</li>
              </ul>
            </div>

            {/* What STRATA Does NOT Do */}
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.05)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: '6px',
                padding: '1rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#f87171', fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                <AlertTriangle size={16} /> What STRATA Does NOT Do
              </div>
              <ul style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', paddingLeft: '1.1rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <li>Does NOT certify structural safety or stability</li>
                <li>Does NOT predict imminent structural collapse</li>
                <li>Does NOT compute material failure probabilities</li>
                <li>Does NOT estimate remaining structural fatigue life</li>
                <li>Does NOT replace physical certified inspections</li>
              </ul>
            </div>
          </div>

          {/* SYSTEM FROZEN COMPONENT SPECIFICATION */}
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.6rem' }}>
              Frozen Subsystem Architecture &amp; Version Register
            </div>
            <div
              style={{
                backgroundColor: 'var(--bg-primary)',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                overflow: 'hidden',
              }}
            >
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Subsystem Component</th>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Locked Version</th>
                    <th style={{ padding: '0.6rem 0.8rem', textAlign: 'right' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {versionMatrix.map((vm, i) => (
                    <tr key={i} style={{ borderBottom: i < versionMatrix.length - 1 ? '1px solid var(--border-subtle)' : 'none' }}>
                      <td style={{ padding: '0.6rem 0.8rem', fontWeight: 500 }}>{vm.component}</td>
                      <td style={{ padding: '0.6rem 0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                        {vm.version}
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem', fontFamily: 'var(--font-mono)', textAlign: 'right', color: 'var(--state-baseline)' }}>
                        {vm.status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* SCIENTIFIC LEGAL DISCLAIMER */}
          <div className="strata-disclaimer">
            <strong>Research Prototype Legal Notice</strong>
            STRATA is developed strictly for multi-epoch synthetic and benchmark InSAR research demonstrations.
            All analytical outputs represent experimental decision-support telemetry.
          </div>
        </div>
      </div>
    </div>
  )
}
