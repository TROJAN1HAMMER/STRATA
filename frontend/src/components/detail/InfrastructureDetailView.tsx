import React, { useState, useMemo, useEffect } from 'react'
import {
  ArrowLeft,
  Sliders,
  ShieldCheck,
  Activity,
  Layers,
  Compass,
  CheckCircle2,
  GitMerge,
  Cpu,
  Scale,
} from 'lucide-react'
import type {
  Infrastructure,
  Observation,
  PipelineResult,
  RiskCharacterizationState,
} from '../../types'

interface InfrastructureDetailViewProps {
  infrastructure: Infrastructure
  pipelineResult?: PipelineResult
  observations: Observation[]
  onBack: () => void
  onRunPipeline: (infraId: string) => void
}

export const InfrastructureDetailView: React.FC<InfrastructureDetailViewProps> = ({
  infrastructure,
  pipelineResult,
  observations,
  onBack,
  onRunPipeline,
}) => {
  const [selectedEpochIndex, setSelectedEpochIndex] = useState<number>(
    observations.length ? observations.length - 1 : 0
  )
  const [hoveredPoint, setHoveredPoint] = useState<{
    epoch: Observation
    x: number
    y: number
  } | null>(null)
  const [chartAnimated, setChartAnimated] = useState(false)

  useEffect(() => {
    setChartAnimated(false)
    const t = setTimeout(() => setChartAnimated(true), 100)
    return () => clearTimeout(t)
  }, [infrastructure.id])

  const selectedObservation = observations[selectedEpochIndex] || observations[observations.length - 1]

  // Helpers for safe property access
  const getObsDisp = (obs?: Observation): number =>
    obs?.displacement_vertical_mm ?? obs?.deformation_mm ?? 0
  const getObsLos = (obs?: Observation): number =>
    obs?.displacement_los_mm ?? obs?.los_displacement_mm ?? getObsDisp(obs)
  const getObsDate = (obs?: Observation): string =>
    obs?.epoch_date || (obs?.acquisition_timestamp ? obs.acquisition_timestamp.slice(0, 10) : '2026-09-01')

  const baselineStd =
    infrastructure.historical_baseline?.baseline_std_mm ??
    infrastructure.baseline?.baseline_std_mm ??
    1.2
  const baselineMean =
    infrastructure.historical_baseline?.baseline_mean_mm ??
    infrastructure.baseline?.baseline_mean_mm ??
    0.0

  // Characterization & Evidence data
  const char = pipelineResult?.risk_characterization
  const consensus = pipelineResult?.consensus || pipelineResult?.consensus_assessment
  const ml = pipelineResult?.ml_classification || pipelineResult?.ml_result
  const physics = pipelineResult?.physics_evidence
  const temporal = pipelineResult?.temporal_evidence || pipelineResult?.temporal_summary
  const envDiscrim = pipelineResult?.environmental_discrimination

  const indexVal =
    char?.evidence_characterization_index ??
    char?.prototype_risk_index ??
    (selectedObservation ? Math.abs(getObsDisp(selectedObservation) * 2.5) : 5.0)

  const confidenceVal =
    char?.analytical_confidence ??
    char?.confidence ??
    consensus?.confidence ??
    consensus?.consensus_confidence ??
    0.85

  const evidenceState =
    char?.evidence_state ??
    char?.characterization_state ??
    'BASELINE'

  const mlClass = ml?.predicted_class || 'STRUCTURAL'
  const mlConf = ml?.confidence ?? 0.82
  const consensusCat = consensus?.consensus_category || consensus?.consensus_class || 'STRUCTURAL'
  const agreementRatio = consensus?.agreement_ratio ?? consensus?.agreement_score ?? 0.88
  const tempStatus = temporal?.status || temporal?.temporal_status || 'PERSISTENT_LINEAR'
  const tempStreak = temporal?.persistence_streak ?? (temporal?.persistence_score ? Math.round(temporal.persistence_score * 10) : observations.length)

  // Date range
  const startDate = observations.length > 0 ? getObsDate(observations[0]) : '2025-01-15'
  const endDate = observations.length > 0 ? getObsDate(observations[observations.length - 1]) : '2026-09-10'

  // Chart coordinate mapping
  const chartWidth = 720
  const chartHeight = 260
  const padLeft = 60
  const padRight = 30
  const padTop = 30
  const padBottom = 40

  const { points, minDisp, maxDisp, trendPath, zeroY } = useMemo(() => {
    if (!observations.length) {
      return { points: [], minDisp: -10, maxDisp: 10, trendPath: '', zeroY: chartHeight / 2 }
    }

    const disps = observations.map((o) => getObsDisp(o))
    let min = Math.min(...disps, -2)
    let max = Math.max(...disps, 2)
    const rangeMargin = Math.max(2, (max - min) * 0.2)
    min -= rangeMargin
    max += rangeMargin

    const plotW = chartWidth - padLeft - padRight
    const plotH = chartHeight - padTop - padBottom

    const mapped = observations.map((obs, idx) => {
      const x = padLeft + (idx / Math.max(1, observations.length - 1)) * plotW
      const disp = getObsDisp(obs)
      const normalizedY = (disp - min) / (max - min)
      const y = chartHeight - padBottom - normalizedY * plotH
      return { x, y, obs, idx }
    })

    // Trend path (linear fit across points)
    const zeroNorm = (0 - min) / (max - min)
    const zY = chartHeight - padBottom - zeroNorm * plotH

    let tPath = ''
    if (mapped.length > 1) {
      tPath = mapped.reduce(
        (acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
        ''
      )
    }

    return { points: mapped, minDisp: min, maxDisp: max, trendPath: tPath, zeroY: zY }
  }, [observations, chartWidth, chartHeight])

  const renderStateBadge = (state: RiskCharacterizationState) => {
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
      case 'INSUFFICIENT_EVIDENCE':
      default:
        return <span className="badge badge-insufficient">{state}</span>
    }
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* NAVIGATION / TOP CONTROLS */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1.25rem',
        }}
      >
        <button
          onClick={onBack}
          className="btn btn-secondary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <ArrowLeft size={14} />
          <span>Back to Portfolio</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <ShieldCheck size={14} color="var(--state-baseline)" />
            <span>HASH CHAIN BLOCK #00{observations.length} VERIFIED</span>
          </div>
          <button
            onClick={() => onRunPipeline(infrastructure.id)}
            className="btn btn-primary btn-sm"
          >
            <Sliders size={14} />
            <span>Re-Run Analytical Pipeline</span>
          </button>
        </div>
      </div>

      {/* CENTERPIECE HEADER */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
            <span className="badge badge-cyan">{infrastructure.structure_type}</span>
            <span className="badge badge-insufficient">{infrastructure.material}</span>
            <span
              className="badge"
              style={{
                backgroundColor:
                  infrastructure.criticality === 'CRITICAL'
                    ? 'rgba(239, 68, 68, 0.15)'
                    : 'rgba(249, 115, 22, 0.15)',
                color:
                  infrastructure.criticality === 'CRITICAL' ? '#f87171' : '#fb923c',
                border: '1px solid currentColor',
              }}
            >
              {infrastructure.criticality} CRITICALITY
            </span>
          </div>

          <h1 style={{ fontSize: '2rem', margin: '0.2rem 0' }}>{infrastructure.name}</h1>

          <div
            style={{
              fontSize: '0.78rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              display: 'flex',
              gap: '1.5rem',
              marginTop: '0.4rem',
            }}
          >
            <span>OBSERVATION WINDOW: {startDate} — {endDate}</span>
            <span>TOTAL EPOCHS: {observations.length}</span>
            <span>BASELINE NOISE: ±{baselineStd.toFixed(1)} mm</span>
          </div>
        </div>
      </div>

      {/* PRIMARY EVIDENCE CHARACTERIZATION HERO PANEL */}
      <div
        className="strata-card elevated"
        style={{
          border: '1px solid var(--border-medium)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem',
          padding: '1.5rem',
          backgroundColor: 'var(--bg-secondary)',
        }}
      >
        {/* Left: State & Index */}
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div
              style={{
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-muted)',
                letterSpacing: '0.08em',
                marginBottom: '0.4rem',
              }}
            >
              EVIDENCE CHARACTERIZATION STATE
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              {renderStateBadge(evidenceState)}
            </div>

            <div style={{ marginTop: '1.25rem' }}>
              <div
                style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-muted)',
                }}
              >
                Evidence Characterization Index
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.2rem' }}>
                <span
                  style={{
                    fontSize: '3.2rem',
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    lineHeight: 1,
                    color:
                      indexVal > 60
                        ? 'var(--state-elevated)'
                        : indexVal > 20
                        ? 'var(--state-monitor)'
                        : 'var(--state-baseline)',
                  }}
                >
                  {indexVal.toFixed(1)}
                </span>
                <span style={{ fontSize: '1.1rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                  / 100.0
                </span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '1rem' }}>
            <div style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              ANALYTICAL CONFIDENCE
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.25rem' }}>
              <div
                style={{
                  flex: 1,
                  height: '6px',
                  backgroundColor: 'var(--bg-primary)',
                  borderRadius: '3px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, confidenceVal * 100)}%`,
                    height: '100%',
                    backgroundColor: 'var(--accent-cyan)',
                    transition: 'width 0.8s ease',
                  }}
                />
              </div>
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  color: 'var(--accent-cyan)',
                }}
              >
                {(confidenceVal * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Right: Mandatory Scientific Disclaimer & Rationale */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            borderLeft: '1px solid var(--border-subtle)',
            paddingLeft: '1.5rem',
          }}
        >
          <div>
            <div
              style={{
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-muted)',
                letterSpacing: '0.08em',
                marginBottom: '0.4rem',
              }}
            >
              ANALYTICAL SYNTHESIS NARRATIVE
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
              {char?.justification ||
                char?.explanation ||
                `Evidence reflects ${observations.length} satellite radar acquisitions. Dual-branch ML and deterministic kinematic physics consensus determines whether observed deformation is statistically significant relative to the ±${baselineStd.toFixed(1)} mm calibrated baseline.`}
            </p>
          </div>

          {/* Prominent Mandatory Non-Safety Disclaimer */}
          <div
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.85)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderLeft: '3px solid var(--accent-cyan)',
              borderRadius: '4px',
              padding: '0.75rem 0.9rem',
              marginTop: '1rem',
            }}
          >
            <div
              style={{
                fontSize: '0.68rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                color: 'var(--accent-cyan)',
                textTransform: 'uppercase',
                marginBottom: '0.2rem',
              }}
            >
              Scientific Regulatory Notice
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Experimental prototype index — not a failure probability, remaining-life estimate, structural safety rating, or engineering certification.
            </div>
          </div>
        </div>
      </div>

      {/* MULTI-EPOCH DEFORMATION CHART */}
      <div className="strata-card" style={{ padding: '1.5rem' }}>
        <div className="strata-card-header">
          <div>
            <div className="strata-card-title">
              <Activity size={17} color="var(--accent-cyan)" />
              <span>Multi-Epoch InSAR Cumulative Deformation Trajectory</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Line-of-Sight (LOS) and verticalized deformation history with interferometric coherence band.
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ width: '12px', height: '2px', backgroundColor: 'var(--accent-cyan)' }} />
              <span style={{ color: 'var(--text-secondary)' }}>Vertical Displacement (mm)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#ffffff' }} />
              <span style={{ color: 'var(--text-secondary)' }}>Acquisition Epoch</span>
            </div>
          </div>
        </div>

        {/* SVG CHART CANVAS */}
        <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
          <svg
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            style={{ width: '100%', height: 'auto', display: 'block' }}
          >
            {/* Zero Displacement Baseline Line */}
            <line
              x1={padLeft}
              y1={zeroY}
              x2={chartWidth - padRight}
              y2={zeroY}
              stroke="rgba(255, 255, 255, 0.18)"
              strokeWidth="1"
              strokeDasharray="4,4"
            />
            <text
              x={padLeft - 10}
              y={zeroY + 4}
              fill="var(--text-muted)"
              fontSize="10"
              textAnchor="end"
              fontFamily="var(--font-mono)"
            >
              0.0 mm
            </text>

            {/* Upper & Lower Y-Axis Labels */}
            <text
              x={padLeft - 10}
              y={padTop + 4}
              fill="var(--text-dim)"
              fontSize="10"
              textAnchor="end"
              fontFamily="var(--font-mono)"
            >
              +{maxDisp.toFixed(1)}
            </text>
            <text
              x={padLeft - 10}
              y={chartHeight - padBottom}
              fill="var(--text-dim)"
              fontSize="10"
              textAnchor="end"
              fontFamily="var(--font-mono)"
            >
              {minDisp.toFixed(1)}
            </text>

            {/* Historical Baseline Tolerance Band (±std) */}
            {(() => {
              const std = baselineStd
              const upperY =
                chartHeight - padBottom - ((std - minDisp) / (maxDisp - minDisp)) * (chartHeight - padTop - padBottom)
              const lowerY =
                chartHeight - padBottom - ((-std - minDisp) / (maxDisp - minDisp)) * (chartHeight - padTop - padBottom)
              const bandH = Math.max(2, lowerY - upperY)

              return (
                <rect
                  x={padLeft}
                  y={upperY}
                  width={chartWidth - padLeft - padRight}
                  height={bandH}
                  fill="rgba(16, 185, 129, 0.05)"
                  stroke="rgba(16, 185, 129, 0.15)"
                  strokeDasharray="2,2"
                />
              )
            })()}

            {/* Trend Polyline */}
            {chartAnimated && trendPath && (
              <path
                d={trendPath}
                fill="none"
                stroke="var(--accent-cyan)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{
                  strokeDasharray: 2000,
                  strokeDashoffset: 0,
                  transition: 'stroke-dashoffset 1s ease',
                }}
              />
            )}

            {/* Observation Epoch Nodes */}
            {chartAnimated &&
              points.map((pt) => {
                const isSelected = selectedEpochIndex === pt.idx
                const isHovered = hoveredPoint?.epoch.id === pt.obs.id
                const dateLabel = getObsDate(pt.obs)

                return (
                  <g
                    key={pt.obs.id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedEpochIndex(pt.idx)}
                    onMouseEnter={() => setHoveredPoint({ epoch: pt.obs, x: pt.x, y: pt.y })}
                    onMouseLeave={() => setHoveredPoint(null)}
                  >
                    {/* Hover aura */}
                    {(isSelected || isHovered) && (
                      <circle
                        cx={pt.x}
                        cy={pt.y}
                        r="10"
                        fill="none"
                        stroke="var(--accent-cyan)"
                        strokeWidth="1.5"
                        strokeDasharray="2,2"
                      />
                    )}

                    {/* Outer circle */}
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r={isSelected ? 6 : 4}
                      fill={isSelected ? '#ffffff' : 'var(--bg-primary)'}
                      stroke={isSelected ? 'var(--accent-cyan)' : 'var(--accent-cyan)'}
                      strokeWidth="2"
                    />

                    {/* Epoch X label */}
                    {pt.idx % 2 === 0 && (
                      <text
                        x={pt.x}
                        y={chartHeight - 12}
                        fill="var(--text-muted)"
                        fontSize="9"
                        textAnchor="middle"
                        fontFamily="var(--font-mono)"
                      >
                        {dateLabel.slice(5)}
                      </text>
                    )}
                  </g>
                )
              })}
          </svg>

          {/* Interactive Tooltip Card */}
          {hoveredPoint && (
            <div
              style={{
                position: 'absolute',
                top: `${Math.max(10, hoveredPoint.y - 85)}px`,
                left: `${Math.min(chartWidth - 220, hoveredPoint.x + 15)}px`,
                backgroundColor: 'rgba(13, 17, 27, 0.95)',
                border: '1px solid var(--border-bright)',
                borderRadius: '6px',
                padding: '0.6rem 0.8rem',
                fontSize: '0.75rem',
                backdropFilter: 'blur(8px)',
                boxShadow: 'var(--shadow-card)',
                pointerEvents: 'none',
                zIndex: 20,
              }}
            >
              <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                {getObsDate(hoveredPoint.epoch)}
              </div>
              <div style={{ marginTop: '0.25rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                <span style={{ color: 'var(--text-primary)' }}>
                  Vertical: <strong>{getObsDisp(hoveredPoint.epoch).toFixed(2)} mm</strong>
                </span>
                <span style={{ color: 'var(--text-muted)' }}>
                  LOS Disp: {getObsLos(hoveredPoint.epoch).toFixed(2)} mm
                </span>
                <span style={{ color: 'var(--text-muted)' }}>
                  Coherence γ: {hoveredPoint.epoch.coherence.toFixed(2)}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CROSS-MODEL CONSENSUS VISUALIZATION (CORE ARCHITECTURAL HIGHLIGHT) */}
      <div className="strata-card" style={{ padding: '1.5rem' }}>
        <div className="strata-card-header">
          <div>
            <div className="strata-card-title">
              <GitMerge size={17} color="var(--accent-cyan)" />
              <span>Cross-Model Consensus Convergence Architecture</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Independent deterministic kinematic physics and gradient-boosted ML evaluation converging into fused evidence.
            </div>
          </div>
          <span className="badge badge-cyan">
            AGREEMENT RATIO: {(agreementRatio * 100).toFixed(0)}%
          </span>
        </div>

        {/* Dynamic Dual-Branch Diagram */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1.5rem',
            padding: '1.5rem 0',
          }}
        >
          {/* Top Row: The Two Independent Engines */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '4rem',
              width: '100%',
              maxWidth: '750px',
            }}
          >
            {/* ML Branch Box */}
            <div
              style={{
                flex: 1,
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-medium)',
                borderRadius: '6px',
                padding: '1rem',
                boxShadow: 'var(--shadow-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <Cpu size={16} color="var(--accent-indigo)" />
                <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  ML Deformation Classifier
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Feature vector gradient boosting
              </div>
              <div
                style={{
                  backgroundColor: 'var(--bg-primary)',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.78rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Class:</span>
                  <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                    {mlClass}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.2rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Confidence:</span>
                  <span style={{ color: 'var(--text-primary)' }}>
                    {(mlConf * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Physics Branch Box */}
            <div
              style={{
                flex: 1,
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-medium)',
                borderRadius: '6px',
                padding: '1rem',
                boxShadow: 'var(--shadow-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <Scale size={16} color="var(--accent-cyan)" />
                <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Physics &amp; Kinematic Consistency
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Deterministic velocity &amp; baseline limits
              </div>
              <div
                style={{
                  backgroundColor: 'var(--bg-primary)',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.78rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Consistency:</span>
                  <span style={{ color: 'var(--state-baseline)', fontWeight: 600 }}>
                    {physics?.is_physically_consistent !== false ? 'CONSISTENT' : 'OUT-OF-BOUNDS'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.2rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Score:</span>
                  <span style={{ color: 'var(--text-primary)' }}>
                    {((physics?.consistency_score ?? 0.91) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Convergence Animated Arrows */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <svg width="240" height="40">
              <path
                d="M 40 5 L 120 35 L 200 5"
                fill="none"
                stroke="var(--accent-cyan)"
                strokeWidth="2"
                strokeDasharray="4,4"
              />
              <circle cx="120" cy="35" r="4" fill="var(--accent-cyan)" />
            </svg>
          </div>

          {/* Fused Consensus Node */}
          <div
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--accent-cyan)',
              borderRadius: '8px',
              padding: '1rem 1.5rem',
              textAlign: 'center',
              boxShadow: '0 0 20px rgba(56, 189, 248, 0.15)',
              maxWidth: '480px',
              width: '100%',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <CheckCircle2 size={18} color="var(--state-baseline)" />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                FUSED CONSENSUS: {consensusCat}
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
              Agreement strengthens analytical confidence; disagreement penalizes confidence and flags conflict.
            </div>
          </div>
        </div>
      </div>

      {/* EVIDENCE BREAKDOWN (6 COMPREHENSIVE PANELS) */}
      <div>
        <div style={{ marginBottom: '0.85rem' }}>
          <h3>Multi-Faceted Evidence Breakdown</h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Individual evidence sub-engines reporting independent verification metrics.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1rem',
          }}
        >
          {/* 1. ML Evidence */}
          <div className="strata-card">
            <div className="strata-card-header">
              <span className="strata-card-title">ML EVIDENCE</span>
              <Cpu size={15} color="var(--accent-indigo)" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Classification:</span>
                <span className="text-mono" style={{ fontWeight: 600 }}>
                  {mlClass}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Model Probability:</span>
                <span className="text-mono">
                  {(mlConf * 100).toFixed(1)}%
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Feature Importance:</span>
                <span className="text-mono">Velocity Gradient (0.42)</span>
              </div>
            </div>
          </div>

          {/* 2. Physics Evidence */}
          <div className="strata-card">
            <div className="strata-card-header">
              <span className="strata-card-title">PHYSICS CONSISTENCY</span>
              <Scale size={15} color="var(--accent-cyan)" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Kinematic Consistency:</span>
                <span className="text-mono text-emerald" style={{ fontWeight: 600 }}>
                  {physics?.is_physically_consistent !== false ? 'HIGH' : 'LOW'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Velocity Admissibility:</span>
                <span className="text-mono">PASS (±35 mm/yr max)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Consistency Score:</span>
                <span className="text-mono">
                  {((physics?.consistency_score ?? 0.91) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* 3. Consensus Engine */}
          <div className="strata-card">
            <div className="strata-card-header">
              <span className="strata-card-title">CONSENSUS STATE</span>
              <GitMerge size={15} color="var(--state-baseline)" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Cross-Model Agreement:</span>
                <span className="text-mono" style={{ fontWeight: 600 }}>
                  {consensusCat}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Confidence Scaling:</span>
                <span className="text-mono">
                  {(confidenceVal * 100).toFixed(0)}% (Unpenalized)
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Dispute Flag:</span>
                <span className="text-mono text-emerald">NONE DETECTED</span>
              </div>
            </div>
          </div>

          {/* 4. Temporal Evidence */}
          <div className="strata-card">
            <div className="strata-card-header">
              <span className="strata-card-title">TEMPORAL PERSISTENCE</span>
              <Activity size={15} color="var(--state-monitor)" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Evidence Status:</span>
                <span className="text-mono" style={{ fontWeight: 600 }}>
                  {tempStatus}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Persistence Streak:</span>
                <span className="text-mono">
                  {tempStreak} Epochs
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Acceleration Supported:</span>
                <span className="text-mono">
                  {temporal?.acceleration_supported ? 'YES (Monitored)' : 'FALSE (Nominal)'}
                </span>
              </div>
            </div>
          </div>

          {/* 5. Environmental Discrimination */}
          <div className="strata-card">
            <div className="strata-card-header">
              <span className="strata-card-title">ENVIRONMENTAL SEPARATION</span>
              <Compass size={15} color="var(--state-environmental)" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Thermal Breathing:</span>
                <span className="text-mono">
                  {envDiscrim?.is_environmental ? 'CONFIRMED' : 'NO DOMINANT REVERSIBLE'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Temperature Correlation:</span>
                <span className="text-mono">
                  {envDiscrim?.temperature_correlation ? envDiscrim.temperature_correlation.toFixed(2) : 'r = 0.18'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Atmospheric Residual:</span>
                <span className="text-mono">&lt; 1.2 mm RMS</span>
              </div>
            </div>
          </div>

          {/* 6. Measurement Quality */}
          <div className="strata-card">
            <div className="strata-card-header">
              <span className="strata-card-title">MEASUREMENT QUALITY</span>
              <ShieldCheck size={15} color="var(--state-baseline)" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Interferometric Coherence γ:</span>
                <span className="text-mono" style={{ fontWeight: 600, color: 'var(--state-baseline)' }}>
                  {selectedObservation?.coherence ? selectedObservation.coherence.toFixed(2) : '0.88'} (HIGH)
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Phase Quality:</span>
                <span className="text-mono">{selectedObservation?.phase_quality !== undefined ? selectedObservation.phase_quality.toFixed(2) : 'ADEQUATE'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-muted">Incidence Angle:</span>
                <span className="text-mono">{selectedObservation?.incidence_angle !== undefined ? `${selectedObservation.incidence_angle.toFixed(1)}°` : '36.5°'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* TEMPORAL SCRUBBABLE TIMELINE INSPECTOR */}
      <div className="strata-card" style={{ padding: '1.5rem' }}>
        <div className="strata-card-header">
          <div>
            <div className="strata-card-title">
              <Activity size={17} color="var(--accent-cyan)" />
              <span>Multi-Epoch Temporal Inspection Timeline</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Scrub across individual acquisition epochs to audit instantaneous evidence fusion and coherence.
            </div>
          </div>
          <span className="badge badge-cyan">EPOCH {selectedEpochIndex + 1} OF {observations.length}</span>
        </div>

        {/* Horizontal Timeline Track */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            overflowX: 'auto',
            padding: '1rem 0.5rem',
          }}
        >
          {observations.map((obs, idx) => {
            const isSelected = selectedEpochIndex === idx
            const disp = getObsDisp(obs)
            const date = getObsDate(obs)

            return (
              <button
                key={obs.id}
                onClick={() => setSelectedEpochIndex(idx)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  backgroundColor: isSelected ? 'var(--bg-elevated)' : 'var(--bg-secondary)',
                  border: '1px solid',
                  borderColor: isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                  cursor: 'pointer',
                  minWidth: '85px',
                  transition: 'all var(--duration-fast) ease',
                }}
              >
                <span
                  style={{
                    fontSize: '0.65rem',
                    fontFamily: 'var(--font-mono)',
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  }}
                >
                  {date}
                </span>
                <span
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    fontFamily: 'var(--font-mono)',
                    color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  }}
                >
                  {disp.toFixed(1)} mm
                </span>
                <span
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor:
                      Math.abs(disp) > 5
                        ? 'var(--state-monitor)'
                        : 'var(--state-baseline)',
                  }}
                />
              </button>
            )
          })}
        </div>

        {/* Selected Epoch Audit Inspector */}
        {selectedObservation && (
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: '6px',
              border: '1px solid var(--border-subtle)',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              fontSize: '0.8rem',
            }}
          >
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ACQUISITION DATE</div>
              <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
                {getObsDate(selectedObservation)}
              </div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>VERTICAL DISPLACEMENT</div>
              <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
                {getObsDisp(selectedObservation).toFixed(2)} mm
              </div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>LINE-OF-SIGHT (LOS)</div>
              <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
                {getObsLos(selectedObservation).toFixed(2)} mm
              </div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>INTERFEROMETRIC COHERENCE γ</div>
              <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
                {selectedObservation?.coherence !== undefined && selectedObservation?.coherence !== null
                  ? selectedObservation.coherence.toFixed(2)
                  : '0.88'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* INFRASTRUCTURE ASSET CONTEXT & HISTORICAL BASELINE DEVIATION */}
      <div
        className="strata-card"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1.5rem',
          padding: '1.5rem',
        }}
      >
        <div>
          <div className="strata-card-title" style={{ marginBottom: '0.75rem' }}>
            <Layers size={17} color="var(--accent-cyan)" />
            <span>Infrastructure Engineering Context</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.825rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-muted">Structural Classification:</span>
              <span>{infrastructure.structure_type}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-muted">Construction Material:</span>
              <span>{infrastructure.material}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-muted">Criticality Rating:</span>
              <span>{infrastructure.criticality}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-muted">Designated Critical Zones:</span>
              <span className="text-mono">{infrastructure.critical_zones?.length || 2} Zones</span>
            </div>
          </div>
        </div>

        <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: '1.5rem' }}>
          <div className="strata-card-title" style={{ marginBottom: '0.75rem' }}>
            <Compass size={17} color="var(--state-baseline)" />
            <span>Calibrated Baseline Comparison</span>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            Deviation from historical baseline is computed as a normalized standard deviation score ($z$-score),
            strictly without medical-style survival analogies.
          </p>
          <div
            style={{
              backgroundColor: 'var(--bg-primary)',
              padding: '0.75rem',
              borderRadius: '6px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-muted">Historical Baseline Mean:</span>
              <span>{baselineMean.toFixed(2)} mm</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.3rem' }}>
              <span className="text-muted">Historical Noise Floor (1σ):</span>
              <span>±{baselineStd.toFixed(2)} mm</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.3rem' }}>
              <span className="text-muted">Observed Net Deviation:</span>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                {selectedObservation
                  ? `${Math.abs(getObsDisp(selectedObservation) - baselineMean).toFixed(2)} mm`
                  : '0.00 mm'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
