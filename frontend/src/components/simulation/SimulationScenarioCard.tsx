import React from 'react'
import { ArrowRight } from 'lucide-react'

export interface ScenarioCardData {
  id: string
  moduleNum: string
  title: string
  plainQuestion: string
  description: string
  category: string
  badgeColor?: string
  previewSvg?: React.ReactNode
}

interface SimulationScenarioCardProps {
  card: ScenarioCardData
  onSelect: (id: string) => void
}

export const SimulationScenarioCard: React.FC<SimulationScenarioCardProps> = ({ card, onSelect }) => {
  return (
    <div
      onClick={() => onSelect(card.id)}
      className="strata-card"
      style={{
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '1rem',
        padding: '1.5rem',
        transition: 'all 0.2s ease',
        border: '1px solid var(--border-subtle)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--accent-cyan)'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border-subtle)'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
          <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>
            {card.moduleNum}
          </span>
          <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            {card.category}
          </span>
        </div>

        <h3 style={{ fontSize: '1.05rem', margin: '0 0 0.35rem 0', color: 'var(--text-primary)' }}>
          {card.title}
        </h3>

        <div style={{ color: 'var(--accent-cyan)', fontSize: '0.82rem', fontStyle: 'italic', marginBottom: '0.6rem' }}>
          "{card.plainQuestion}"
        </div>

        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.45 }}>
          {card.description}
        </p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
          INTERACTIVE LAB
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onSelect(card.id)
          }}
          className="btn btn-primary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.35rem 0.7rem' }}
        >
          <span>Explore</span>
          <ArrowRight size={13} />
        </button>
      </div>
    </div>
  )
}
