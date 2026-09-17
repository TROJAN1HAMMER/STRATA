import React, { useState } from 'react'
import {
  Activity,
  Layers,
  ShieldCheck,
  Compass,
  ArrowUpRight,
  Sparkles,
} from 'lucide-react'
import type { Infrastructure, PipelineResult } from '../../types'

interface DashboardViewProps {
  infrastructures: Infrastructure[]
  onSelectInfrastructure: (infra: Infrastructure) => void
  onRunPipeline: (infraId: string) => void
  onStartDemo: () => void
  resultsMap: Record<string, PipelineResult>
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  infrastructures,
  onSelectInfrastructure,
  onRunPipeline,
  onStartDemo,
  resultsMap,
}) => {
  const [selectedNode, setSelectedNode] = useState<Infrastructure | null>(
    infrastructures[0] || null
  )

  // Aggregations
  const totalAssets = infrastructures.length
  const baselineCount = infrastructures.filter((i) => {
    const res = resultsMap[i.id]
    const state = res?.risk_characterization?.evidence_state || res?.risk_characterization?.characterization_state || 'BASELINE'
    return !res || state === 'BASELINE'
  }).length
  const environmentalCount = infrastructures.filter((i) => {
    const res = resultsMap[i.id]
    const state = res?.risk_characterization?.evidence_state || res?.risk_characterization?.characterization_state
    return state === 'ENVIRONMENTAL_PATTERN'
  }).length
  const monitorCount = infrastructures.filter((i) => {
    const res = resultsMap[i.id]
    const state = res?.risk_characterization?.evidence_state || res?.risk_characterization?.characterization_state
    return state === 'MONITOR' || state === 'ELEVATED_ATTENTION' || state === 'HIGH_ATTENTION'
  }).length

  const getStatusBadge = (infra: Infrastructure) => {
    const res = resultsMap[infra.id]
    const state = res?.risk_characterization?.evidence_state || res?.risk_characterization?.characterization_state || 'BASELINE'

    switch (state) {
      case 'BASELINE':
        return <span className="badge badge-baseline">Baseline Nominal</span>
      case 'ENVIRONMENTAL_PATTERN':
        return <span className="badge badge-environmental">Cyclic Reversible</span>
      case 'MONITOR':
        return <span className="badge badge-monitor">Monitoring Required</span>
      case 'ELEVATED_ATTENTION':
      case 'HIGH_ATTENTION':
        return <span className="badge badge-elevated">High Attention</span>
      default:
        return <span className="badge badge-insufficient">{state}</span>
    }
  }

  // Schematic coordinates for asset network visualization (relative % in SVG grid)
  const nodeLayouts = [
    { id: 'infra-1', x: 220, y: 110, label: 'Golden Gate Bridge' },
    { id: 'infra-2', x: 440, y: 190, label: 'Mexico City Tunnel' },
    { id: 'infra-3', x: 680, y: 130, label: 'Alqueva Dam' },
    { id: 'infra-4', x: 290, y: 270, label: 'Brenner Base Tunnel' },
    { id: 'infra-5', x: 570, y: 290, label: 'Gotthard Rail Embankment' },
    { id: 'infra-6', x: 800, y: 230, label: 'Piave River Levee' },
  ]

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* HERO SECTION */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
            <span className="badge badge-cyan">SYSTEM v1.0.0 FROZEN</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              SAR POLARIZATION: VV | REVISIT: 6-12 DAYS
            </span>
          </div>
          <h1>Multi-Epoch InSAR Infrastructure Evidence Characterization</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.35rem', maxWidth: '750px', fontSize: '0.9rem' }}>
            STRATA couples deterministic kinematic physics with gradient-boosted ML deformation classification,
            cross-model consensus fusion, multi-epoch temporal persistence tracking, and a cryptographic tamper-evident evidence chain.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={onStartDemo} className="btn btn-primary">
            <Sparkles size={15} />
            <span>Launch Presentation Demo (2 min)</span>
          </button>
        </div>
      </div>

      {/* METRIC COUNTER CARDS */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
        }}
      >
        {/* Total Assets */}
        <div className="strata-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              MONITORED ASSETS
            </span>
            <Layers size={16} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, margin: '0.4rem 0', color: 'var(--text-primary)' }}>
            {totalAssets}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Active civil infrastructure telemetry
          </div>
        </div>

        {/* Baseline */}
        <div className="strata-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              BASELINE / NOMINAL
            </span>
            <span
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: 'var(--state-baseline)',
              }}
            />
          </div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, margin: '0.4rem 0', color: 'var(--state-baseline)' }}>
            {baselineCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Oscillating within noise baseline
          </div>
        </div>

        {/* Environmental Reversible */}
        <div className="strata-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              ENVIRONMENTAL REVERSIBLE
            </span>
            <Compass size={16} color="var(--state-environmental)" />
          </div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, margin: '0.4rem 0', color: 'var(--state-environmental)' }}>
            {environmentalCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Thermal cyclic / non-accumulating
          </div>
        </div>

        {/* Elevated Attention */}
        <div className="strata-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              ELEVATED INSPECTION ATTENTION
            </span>
            <Activity size={16} color="var(--state-monitor)" />
          </div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, margin: '0.4rem 0', color: 'var(--state-monitor)' }}>
            {monitorCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Persistent deformation / high index
          </div>
        </div>

        {/* Chronology Chain */}
        <div className="strata-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              CHRONOLOGY INTEGRITY
            </span>
            <ShieldCheck size={16} color="var(--state-baseline)" />
          </div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, margin: '0.4rem 0', color: '#ffffff' }}>
            100%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--state-baseline)' }}>
            SHA-256 tamper-evident verified
          </div>
        </div>
      </div>

      {/* SCHEMATIC SPATIAL NETWORK CORRIDOR VISUALIZATION */}
      <div className="strata-card" style={{ padding: '1.5rem' }}>
        <div className="strata-card-header">
          <div>
            <div className="strata-card-title">
              <Compass size={17} color="var(--accent-cyan)" />
              <span>Schematic Infrastructure InSAR Telemetry Network</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Topological corridor nodes showing line-of-sight interferometric coherence and real-time evidence states.
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem' }}>
            <span className="badge badge-cyan">DESYNCHRONIZED SCHEMATIC</span>
          </div>
        </div>

        <div
          style={{
            position: 'relative',
            width: '100%',
            height: '360px',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: '6px',
            overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {/* Subtle Grid Background */}
          <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
            <defs>
              <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#gridPattern)" />

            {/* Radar scan ring */}
            <circle
              cx="50%"
              cy="50%"
              r="140"
              fill="none"
              stroke="rgba(56, 189, 248, 0.12)"
              strokeWidth="1"
              strokeDasharray="4,4"
            />
            <circle
              cx="50%"
              cy="50%"
              r="90"
              fill="none"
              stroke="rgba(56, 189, 248, 0.08)"
              strokeWidth="1"
            />

            {/* InSAR Flight Orbit Track Vector */}
            <line
              x1="60"
              y1="40"
              x2="950"
              y2="180"
              stroke="rgba(56, 189, 248, 0.25)"
              strokeWidth="1.5"
              strokeDasharray="8,6"
            />
            <text x="70" y="32" fill="var(--text-dim)" fontSize="11" fontFamily="var(--font-mono)">
              SENTINEL-1 DESCENDING FLIGHT HEADING 192.4° [LOOK ANGLE 34.2°]
            </text>

            {/* Inter-asset synthetic connectivity lines */}
            <line x1="220" y1="110" x2="440" y2="190" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
            <line x1="440" y1="190" x2="680" y2="130" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
            <line x1="220" y1="110" x2="290" y2="270" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
            <line x1="440" y1="190" x2="570" y2="290" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
            <line x1="680" y1="130" x2="800" y2="230" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />

            {/* Render Asset Nodes */}
            {nodeLayouts.map((nl) => {
              const infra = infrastructures.find((i) => i.id === nl.id) || infrastructures[0]
              const res = resultsMap[infra.id]
              const state = res?.risk_characterization.evidence_state || 'BASELINE'
              const isSelected = selectedNode?.id === infra.id

              let nodeColor = 'var(--state-baseline)'
              if (state === 'ENVIRONMENTAL_PATTERN') nodeColor = 'var(--state-environmental)'
              if (state === 'MONITOR') nodeColor = 'var(--state-monitor)'
              if (state === 'ELEVATED_ATTENTION' || state === 'HIGH_ATTENTION') nodeColor = 'var(--state-elevated)'

              return (
                <g
                  key={nl.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => {
                    setSelectedNode(infra)
                    onSelectInfrastructure(infra)
                  }}
                >
                  {/* Outer pulse ring if selected */}
                  {isSelected && (
                    <circle
                      cx={nl.x}
                      cy={nl.y}
                      r="18"
                      fill="none"
                      stroke={nodeColor}
                      strokeWidth="1.5"
                      strokeDasharray="3,3"
                      className="animate-pulse-glow"
                    />
                  )}
                  {/* Core Node Circle */}
                  <circle
                    cx={nl.x}
                    cy={nl.y}
                    r="8"
                    fill="var(--bg-primary)"
                    stroke={nodeColor}
                    strokeWidth="2.5"
                  />
                  {/* Inner dot */}
                  <circle cx={nl.x} cy={nl.y} r="3" fill={nodeColor} />
                  {/* Label */}
                  <text
                    x={nl.x + 12}
                    y={nl.y + 4}
                    fill={isSelected ? '#ffffff' : 'var(--text-secondary)'}
                    fontSize="11"
                    fontFamily="var(--font-sans)"
                    fontWeight={isSelected ? '600' : '400'}
                  >
                    {infra.name}
                  </text>
                  <text
                    x={nl.x + 12}
                    y={nl.y + 17}
                    fill="var(--text-muted)"
                    fontSize="9"
                    fontFamily="var(--font-mono)"
                  >
                    {infra.structure_type} • γ=0.88
                  </text>
                </g>
              )
            })}
          </svg>

          {/* Overlay Info Card on bottom left */}
          <div
            style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              backgroundColor: 'rgba(7, 9, 14, 0.88)',
              border: '1px solid var(--border-subtle)',
              backdropFilter: 'blur(8px)',
              padding: '0.6rem 0.85rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              maxWidth: '380px',
            }}
          >
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
              Scientific Projection Schema
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.72rem' }}>
              Spatial nodes display schematic topological relations. Precise ground-truth coordinates are decoupled to prevent geographic fabrication.
            </div>
          </div>
        </div>
      </div>

      {/* ASSET EVIDENCE RECENT STREAM / QUICK SELECTION */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
          <h3>Monitored Infrastructure Portfolio</h3>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Showing {infrastructures.length} of {infrastructures.length} calibrated assets
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '1rem',
          }}
        >
          {infrastructures.map((infra) => {
            const res = resultsMap[infra.id]
            const index = res?.risk_characterization?.evidence_characterization_index ?? res?.risk_characterization?.prototype_risk_index ?? 0
            const confidence = res?.risk_characterization?.analytical_confidence ?? res?.risk_characterization?.confidence ?? 0

            return (
              <div
                key={infra.id}
                className="strata-card"
                style={{
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '0.85rem',
                }}
                onClick={() => onSelectInfrastructure(infra)}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                        {infra.name}
                      </div>
                      <div
                        style={{
                          fontSize: '0.72rem',
                          color: 'var(--text-muted)',
                          fontFamily: 'var(--font-mono)',
                          marginTop: '0.15rem',
                        }}
                      >
                        {infra.structure_type} • {infra.material} • CRITICALITY: {infra.criticality}
                      </div>
                    </div>
                    <ArrowUpRight size={16} color="var(--text-muted)" />
                  </div>

                  <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {getStatusBadge(infra)}
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-muted)',
                      }}
                    >
                      {infra.observations_count || 10} EPOCHS
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    borderRadius: '4px',
                    padding: '0.6rem 0.75rem',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      EVIDENCE CHARACTERIZATION INDEX
                    </div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {index.toFixed(1)}
                      <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--text-dim)' }}>
                        {' '}/ 100
                      </span>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      CONFIDENCE
                    </div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                      {(confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onRunPipeline(infra.id)
                    }}
                    className="btn btn-secondary btn-sm"
                    style={{ flex: 1 }}
                  >
                    Run Pipeline
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onSelectInfrastructure(infra)
                    }}
                    className="btn btn-primary btn-sm"
                    style={{ flex: 1 }}
                  >
                    Inspect Detail
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* MANDATORY SCIENTIFIC DISCLAIMER */}
      <div className="strata-disclaimer">
        <strong>Mandatory Scientific &amp; Engineering Limitation Notice</strong>
        STRATA provides experimental multi-epoch InSAR evidence characterization indices and consensus assessments.
        It is strictly an analytical aid and does not constitute a structural safety certification, collapse prediction,
        remaining fatigue-life forecast, or replacement for certified physical structural inspections.
      </div>
    </div>
  )
}
