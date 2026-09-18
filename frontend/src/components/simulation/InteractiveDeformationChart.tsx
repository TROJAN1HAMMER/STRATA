import React, { useState } from 'react'

export interface ChartDataPoint {
  epoch: number
  date: string
  displacement_mm: number
  los_displacement_mm?: number
  coherence?: number
  state?: string
  isEnvironmentalEvent?: boolean
  isAtmosphericEvent?: boolean
  annotation?: string
}

interface InteractiveDeformationChartProps {
  data: ChartDataPoint[]
  height?: number
  baselineNoiseMm?: number
  provenance?: 'CONCEPTUAL SIMULATION' | 'STRATA ANALYTICAL OUTPUT' | 'SYNTHETIC BENCHMARK'
  unit?: string
}

export const InteractiveDeformationChart: React.FC<InteractiveDeformationChartProps> = ({
  data,
  height = 240,
  baselineNoiseMm = 2.0,
  provenance = 'CONCEPTUAL SIMULATION',
  unit = 'mm',
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  if (!data || data.length === 0) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--bg-secondary)',
          borderRadius: '6px',
          color: 'var(--text-muted)',
          fontSize: '0.8rem',
        }}
      >
        No deformation epoch data available
      </div>
    )
  }

  const padding = { top: 25, right: 30, bottom: 35, left: 50 }
  const svgWidth = 680
  const chartWidth = svgWidth - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  const displacements = data.map((d) => d.displacement_mm)
  const minVal = Math.min(-baselineNoiseMm * 1.5, Math.min(...displacements) - 2)
  const maxVal = Math.max(baselineNoiseMm * 1.5, Math.max(...displacements) + 2)
  const range = maxVal - minVal || 1

  const getX = (index: number) => {
    if (data.length <= 1) return padding.left + chartWidth / 2
    return padding.left + (index / (data.length - 1)) * chartWidth
  }

  const getY = (val: number) => {
    return padding.top + chartHeight - ((val - minVal) / range) * chartHeight
  }

  // Path generator
  const pointsString = data.map((d, i) => `${getX(i)},${getY(d.displacement_mm)}`).join(' ')
  const linePath = `M ${data.map((d, i) => `${getX(i)} ${getY(d.displacement_mm)}`).join(' L ')}`

  // Zero reference line
  const zeroY = getY(0)
  // Baseline band coordinates
  const baselineTopY = getY(baselineNoiseMm)
  const baselineBottomY = getY(-baselineNoiseMm)

  const hovered = hoveredIndex !== null ? data[hoveredIndex] : null

  return (
    <div style={{ position: 'relative', width: '100%', userSelect: 'none' }}>
      {/* Top Bar with Provenance Badge */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.4rem',
          fontSize: '0.72rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            className={
              provenance === 'CONCEPTUAL SIMULATION'
                ? 'badge badge-cyan'
                : provenance === 'STRATA ANALYTICAL OUTPUT'
                ? 'badge badge-baseline'
                : 'badge badge-secondary'
            }
            style={{ fontSize: '0.65rem' }}
          >
            {provenance}
          </span>
          <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            BASELINE NOISE: ±{baselineNoiseMm.toFixed(1)} {unit}
          </span>
        </div>

        <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
          {hovered ? (
            <span>
              Epoch {hovered.epoch}: <strong style={{ color: '#fff' }}>{hovered.displacement_mm.toFixed(2)} {unit}</strong> (γ={hovered.coherence ? hovered.coherence.toFixed(2) : '0.88'})
            </span>
          ) : (
            'Hover over points for epoch telemetry'
          )}
        </div>
      </div>

      <svg
        viewBox={`0 0 ${svgWidth} ${height}`}
        style={{
          width: '100%',
          height: 'auto',
          backgroundColor: 'var(--bg-secondary)',
          borderRadius: '6px',
          border: '1px solid var(--border-subtle)',
          overflow: 'visible',
        }}
        onMouseLeave={() => setHoveredIndex(null)}
      >
        <defs>
          <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.25" />
            <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Historical Baseline Noise Band */}
        <rect
          x={padding.left}
          y={baselineTopY}
          width={chartWidth}
          height={Math.max(0, baselineBottomY - baselineTopY)}
          fill="rgba(52, 211, 153, 0.08)"
          stroke="rgba(52, 211, 153, 0.25)"
          strokeDasharray="3,3"
        />
        <text
          x={svgWidth - padding.right - 5}
          y={baselineTopY + 12}
          fill="rgba(52, 211, 153, 0.6)"
          fontSize="9"
          textAnchor="end"
          fontFamily="var(--font-mono)"
        >
          +1σ Baseline Noise Band
        </text>

        {/* Zero displacement line */}
        <line
          x1={padding.left}
          y1={zeroY}
          x2={svgWidth - padding.right}
          y2={zeroY}
          stroke="rgba(255, 255, 255, 0.15)"
          strokeWidth="1"
        />

        {/* Y Axis Grid & Labels */}
        {[-8, -4, 0, 4, 8].map((val) => {
          if (val < minVal || val > maxVal) return null
          const y = getY(val)
          return (
            <g key={val}>
              <line
                x1={padding.left}
                y1={y}
                x2={svgWidth - padding.right}
                y2={y}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeDasharray="2,2"
              />
              <text
                x={padding.left - 8}
                y={y + 3}
                fill="var(--text-muted)"
                fontSize="9"
                textAnchor="end"
                fontFamily="var(--font-mono)"
              >
                {val > 0 ? `+${val}` : val}
              </text>
            </g>
          )
        })}

        {/* Trajectory Area Fill */}
        <polygon
          points={`${padding.left},${zeroY} ${pointsString} ${getX(data.length - 1)},${zeroY}`}
          fill="url(#chartGradient)"
        />

        {/* Trajectory Main Line */}
        <path
          d={linePath}
          fill="none"
          stroke="var(--accent-cyan)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Epoch Points & Tooltip Triggers */}
        {data.map((d, i) => {
          const cx = getX(i)
          const cy = getY(d.displacement_mm)
          const isSelected = hoveredIndex === i
          const isOut = Math.abs(d.displacement_mm) > baselineNoiseMm

          return (
            <g
              key={i}
              onMouseEnter={() => setHoveredIndex(i)}
              style={{ cursor: 'pointer' }}
            >
              {/* Vertical crosshair on hover */}
              {isSelected && (
                <line
                  x1={cx}
                  y1={padding.top}
                  x2={cx}
                  y2={height - padding.bottom}
                  stroke="rgba(56, 189, 248, 0.4)"
                  strokeDasharray="2,2"
                />
              )}

              {/* Point Outer Ring */}
              <circle
                cx={cx}
                cy={cy}
                r={isSelected ? 6 : isOut ? 4.5 : 3.5}
                fill={isOut ? 'var(--state-monitor)' : 'var(--bg-primary)'}
                stroke={isOut ? 'var(--state-monitor)' : 'var(--accent-cyan)'}
                strokeWidth={isSelected ? 2.5 : 1.8}
              />

              {/* Date / Epoch X Label */}
              {(i === 0 || i === data.length - 1 || i % Math.ceil(data.length / 5) === 0) && (
                <text
                  x={cx}
                  y={height - padding.bottom + 16}
                  fill="var(--text-muted)"
                  fontSize="9"
                  textAnchor="middle"
                  fontFamily="var(--font-mono)"
                >
                  {d.date ? d.date.slice(5) : `E${d.epoch}`}
                </text>
              )}
            </g>
          )
        })}
      </svg>
    </div>
  )
}
