import React from 'react'
import { CheckCircle2, AlertTriangle, XCircle, ShieldCheck } from 'lucide-react'

export interface ExplainabilityItem {
  id: string
  label: string
  plainQuestion: string
  status: 'passed' | 'warning' | 'failed'
  detail: string
  scientificRule?: string
}

interface ExplainabilityPanelProps {
  title?: string
  evidenceState: string
  evidenceIndex?: number
  confidence?: number
  items: ExplainabilityItem[]
  isConceptual?: boolean
}

export const ExplainabilityPanel: React.FC<ExplainabilityPanelProps> = ({
  title = 'Why Did STRATA Make This Decision?',
  evidenceState,
  evidenceIndex = 62.5,
  confidence = 0.85,
  items,
  isConceptual = true,
}) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
            <ShieldCheck size={17} color="var(--accent-cyan)" />
            <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              {title}
            </h4>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Transparent audit checklist of analytical gates, consensus checks, and safeguards
          </div>
        </div>

        <span
          className={isConceptual ? 'badge badge-cyan' : 'badge badge-baseline'}
          style={{ fontSize: '0.65rem' }}
        >
          {isConceptual ? 'EXPLANATORY AUDIT' : 'STRATA v1.0.0 OUTPUT'}
        </span>
      </div>

      {/* Decision Summary Banner */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.2fr 1fr 1fr',
          gap: '0.75rem',
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '6px',
          padding: '0.75rem 1rem',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            EVIDENCE CHARACTERIZATION STATE
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.15rem' }}>
            {evidenceState}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            EVIDENCE INDEX
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '0.15rem' }}>
            {evidenceIndex.toFixed(1)} <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>/ 100</span>
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            ANALYTICAL CONFIDENCE
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginTop: '0.15rem' }}>
            {(confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Checklist Items */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        {items.map((item) => {
          let Icon = CheckCircle2
          let iconColor = 'var(--state-baseline)'
          let badgeBg = 'rgba(52, 211, 153, 0.1)'

          if (item.status === 'warning') {
            Icon = AlertTriangle
            iconColor = 'var(--state-monitor)'
            badgeBg = 'rgba(251, 191, 36, 0.1)'
          } else if (item.status === 'failed') {
            Icon = XCircle
            iconColor = 'var(--state-elevated)'
            badgeBg = 'rgba(244, 63, 94, 0.1)'
          }

          return (
            <div
              key={item.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                padding: '0.6rem 0.85rem',
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                borderRadius: '5px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ marginTop: '0.15rem' }}>
                <Icon size={16} color={iconColor} />
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {item.label}
                  </span>
                  <span
                    style={{
                      fontSize: '0.65rem',
                      fontFamily: 'var(--font-mono)',
                      color: iconColor,
                      backgroundColor: badgeBg,
                      padding: '0.1rem 0.4rem',
                      borderRadius: '3px',
                      textTransform: 'uppercase',
                    }}
                  >
                    {item.status}
                  </span>
                </div>

                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.2rem', lineHeight: 1.4 }}>
                  {item.detail}
                </div>

                {item.scientificRule && (
                  <div
                    style={{
                      fontSize: '0.7rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text-muted)',
                      marginTop: '0.3rem',
                    }}
                  >
                    Rule: {item.scientificRule}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
