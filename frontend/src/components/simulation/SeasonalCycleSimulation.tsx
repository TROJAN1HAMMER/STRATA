import React, { useState, useMemo } from 'react'
import { Compass } from 'lucide-react'
import { InteractiveDeformationChart, type ChartDataPoint } from './InteractiveDeformationChart'
import { useFacultyMode } from './FacultyModeContext'

export const SeasonalCycleSimulation: React.FC = () => {
  const { facultyMode } = useFacultyMode()

  const [amplitudeMm, setAmplitudeMm] = useState<number>(8.5) // mm
  const cyclePeriodMonths = 12
  const [noiseLevelMm, setNoiseLevelMm] = useState<number>(0.8)
  const [selectedMonth, setSelectedMonth] = useState<number>(6) // July (peak heat)

  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

  // Temperature approximation centered on July (+heat) and Jan (-cold)
  const getTempC = (mIdx: number) => {
    // Peak at index 6 (July)
    return 15 + 14 * Math.sin(((mIdx - 3) / 12) * Math.PI * 2)
  }

  const chartData: ChartDataPoint[] = useMemo(() => {
    const points: ChartDataPoint[] = []

    for (let i = 0; i < 24; i++) {
      const monthIdx = i % 12
      // Sinusoidal thermal expansion curve
      const angle = (i / cyclePeriodMonths) * Math.PI * 2
      const idealDisp = amplitudeMm * Math.sin(angle)
      // Small pseudo-noise
      const pseudoNoise = Math.sin(i * 11.3) * noiseLevelMm
      const disp = idealDisp + pseudoNoise

      points.push({
        epoch: i + 1,
        date: `2024-${((monthIdx % 12) + 1).toString().padStart(2, '0')}-01`,
        displacement_mm: disp,
        los_displacement_mm: disp * 0.82,
        coherence: 0.88,
        state: 'ENVIRONMENTAL_PATTERN',
      })
    }
    return points
  }, [amplitudeMm, cyclePeriodMonths, noiseLevelMm])

  const currentTemp = getTempC(selectedMonth)
  const currentExpansionMm = amplitudeMm * Math.sin(((selectedMonth - 3) / 12) * Math.PI * 2)

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '1.5rem',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <span className="badge badge-cyan">MODULE 03</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              ANNUAL THERMAL EXPANSION CYCLE
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-primary)' }}>
            {facultyMode ? 'Why Summer Heat & Winter Cold Cause False Alarms' : 'Seasonal Thermal Dynamics & Cyclic Pattern Discrimination'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.35rem 0 0 0', maxWidth: '750px' }}>
            {facultyMode
              ? 'Large steel and concrete structures expand in summer heat and contract in winter cold. Even though this movement is large and persistent, it is completely reversible and safe.'
              : 'Demonstrates multi-year sinusoidal deformation profiles and zero-crossing analysis enabling STRATA to reject cyclic reversible motion from structural deformation tracking.'}
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>
            CONCEPTUAL SIMULATION
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Illustrative thermal model
          </div>
        </div>
      </div>

      {/* Main Interactive Stage */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.2fr 1.3fr',
          gap: '1.5rem',
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '6px',
          padding: '1.25rem',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Visual Structure Expansion Diagram */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ position: 'relative', width: '100%', height: '220px', backgroundColor: '#070e18', borderRadius: '6px', overflow: 'hidden' }}>
            <svg width="100%" height="100%" viewBox="0 0 400 220">
              {/* Temperature Background Tint */}
              <rect
                width="100%"
                height="100%"
                fill={currentTemp > 20 ? 'rgba(239, 68, 68, 0.08)' : 'rgba(56, 189, 248, 0.08)'}
              />

              {/* Sun / Snowflake Indicator */}
              <g transform="translate(340, 20)">
                {currentTemp > 20 ? (
                  <circle cx="20" cy="20" r="14" fill="#f59e0b" opacity="0.85" />
                ) : (
                  <polygon points="20,8 24,18 34,20 25,26 28,36 20,30 12,36 15,26 6,20 16,18" fill="#38bdf8" />
                )}
              </g>

              {/* Two Bridge Piers */}
              <rect x="70" y="110" width="30" height="90" fill="#1e293b" stroke="#475569" strokeWidth="1.5" />
              <rect x="300" y="110" width="30" height="90" fill="#1e293b" stroke="#475569" strokeWidth="1.5" />

              {/* Center Arch / Steel Span Expanding / Contracting */}
              <rect
                x={85 - currentExpansionMm * 1.5}
                y={95 - currentExpansionMm * 0.5}
                width={230 + currentExpansionMm * 3}
                height="16"
                fill="#334155"
                stroke={currentTemp > 20 ? '#f87171' : '#38bdf8'}
                strokeWidth="2"
                rx="2"
                style={{ transition: 'all 0.25s ease' }}
              />

              {/* Expansion Indicators */}
              <text x="200" y="80" fill="#ffffff" fontSize="10" textAnchor="middle" fontWeight="600">
                STEEL SUPERSTRUCTURE SPAN
              </text>

              <g transform="translate(200, 150)">
                <text x="0" y="0" fill="var(--text-muted)" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)">
                  AMBIENT TEMPERATURE: {currentTemp.toFixed(1)}°C
                </text>
                <text x="0" y="18" fill="var(--accent-cyan)" fontSize="13" textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="700">
                  {currentExpansionMm > 0 ? `+${currentExpansionMm.toFixed(1)}` : currentExpansionMm.toFixed(1)} mm
                </text>
                <text x="0" y="32" fill="var(--text-dim)" fontSize="8" textAnchor="middle" fontFamily="var(--font-mono)">
                  {currentExpansionMm >= 0 ? '(THERMAL ELONGATION)' : '(THERMAL CONTRACTION)'}
                </text>
              </g>
            </svg>
          </div>

          {/* Month Selector Buttons */}
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            {months.map((m, idx) => (
              <button
                key={m}
                onClick={() => setSelectedMonth(idx)}
                style={{
                  flex: 1,
                  padding: '0.35rem 0',
                  borderRadius: '3px',
                  border: idx === selectedMonth ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                  backgroundColor: idx === selectedMonth ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                  color: idx === selectedMonth ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  fontSize: '0.65rem',
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer',
                }}
              >
                {m}
              </button>
            ))}
          </div>

          {/* Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>EXPANSION AMPLITUDE</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>±{amplitudeMm.toFixed(1)} mm</span>
              </div>
              <input
                type="range"
                min="2"
                max="15"
                step="0.5"
                value={amplitudeMm}
                onChange={(e) => setAmplitudeMm(parseFloat(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>MEASUREMENT NOISE FLOOR</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>±{noiseLevelMm.toFixed(1)} mm</span>
              </div>
              <input
                type="range"
                min="0.2"
                max="2.5"
                step="0.1"
                value={noiseLevelMm}
                onChange={(e) => setNoiseLevelMm(parseFloat(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        {/* Dynamic Multi-Year Deformation Chart & STRATA Decision */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <InteractiveDeformationChart
            data={chartData}
            height={200}
            baselineNoiseMm={2.0}
            provenance="CONCEPTUAL SIMULATION"
          />

          {/* STRATA Decision Card */}
          <div
            style={{
              backgroundColor: 'rgba(56, 189, 248, 0.05)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.45rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Compass size={16} color="var(--state-environmental)" />
              <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--state-environmental)' }}>
                CYCLIC RECURRENCE CONFIRMED (PERIOD = 12 MONTHS)
              </span>
            </div>

            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              STRATA measures 4 sign reversals across 24 observation epochs. The temporal state machine classifies this trajectory as <strong>ENVIRONMENTAL_PATTERN</strong> and automatically suppresses monotonic deformation alarms.
            </div>

            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.2rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
              <div>
                TEMPORAL STATE: <strong style={{ color: 'var(--state-environmental)' }}>ENVIRONMENTAL_PATTERN</strong>
              </div>
              <div>
                STRUCTURAL CONTRIBUTION: <strong style={{ color: 'var(--state-baseline)' }}>SUPPRESSED (0%)</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
