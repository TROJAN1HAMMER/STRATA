import React, { useState, useMemo } from 'react'
import { Compass } from 'lucide-react'
import { InteractiveDeformationChart, type ChartDataPoint } from './InteractiveDeformationChart'
import { useFacultyMode } from './FacultyModeContext'

export const WaterResponseSimulation: React.FC = () => {
  const { facultyMode } = useFacultyMode()

  const [rainIntensity, setRainIntensity] = useState<number>(75) // %
  const [saturation, setSaturation] = useState<number>(65) // %
  const loadWeight = 40 // %
  const [elapsedDays, setElapsedDays] = useState<number>(180) // 0-365 days

  // Compute conceptual displacement series across 12 monthly epochs
  const chartData: ChartDataPoint[] = useMemo(() => {
    const points: ChartDataPoint[] = []

    for (let i = 0; i < 12; i++) {
      // Seasonal rain pattern peaked in spring/autumn
      const seasonalRain = Math.sin((i / 11) * Math.PI * 2) * (rainIntensity / 100) * 6
      const soilPorePressure = (saturation / 100) * 3.5 * Math.sin(((i + 1) / 11) * Math.PI * 2)
      const loadEffect = (loadWeight / 100) * 1.5

      // Net displacement (reversible oscillation)
      const disp = seasonalRain + soilPorePressure - loadEffect

      points.push({
        epoch: i + 1,
        date: `2025-${(i + 1).toString().padStart(2, '0')}-15`,
        displacement_mm: disp,
        los_displacement_mm: disp * 0.8,
        coherence: 0.82 - (rainIntensity / 100) * 0.15,
        state: 'ENVIRONMENTAL_PATTERN',
        isEnvironmentalEvent: i === 3 || i === 9,
      })
    }
    return points
  }, [rainIntensity, saturation, loadWeight])

  // Current instantaneous displacement at elapsed days
  const currentMonthIdx = Math.min(11, Math.floor((elapsedDays / 365) * 12))
  const currentDisp = chartData[currentMonthIdx]?.displacement_mm ?? 0

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
            <span className="badge badge-cyan">MODULE 02</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              HYDROLOGICAL &amp; ENVIRONMENTAL RESPONSE
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-primary)' }}>
            {facultyMode ? 'Why Rain & Water Can Mimic Structural Settlement' : 'Environmental Loading & Reversible Surface Deformation'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.35rem 0 0 0', maxWidth: '750px' }}>
            {facultyMode
              ? 'Soil around bridges and embankments swells when soaked by rain and shrinks during droughts. STRATA identifies this reversible pattern so normal weather is never confused with concrete damage.'
              : 'Demonstrates environmental soil pore-pressure modulation and transient water loading creating apparent cyclic settlement and heave.'}
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>
            CONCEPTUAL SIMULATION
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Illustrative response model
          </div>
        </div>
      </div>

      {/* Main Simulation Layout */}
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
        {/* Animated Soil / Water Diagram */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ position: 'relative', width: '100%', height: '220px', backgroundColor: '#070d14', borderRadius: '6px', overflow: 'hidden' }}>
            <svg width="100%" height="100%" viewBox="0 0 400 220">
              {/* Rain clouds */}
              <g transform="translate(100, 25)">
                <ellipse cx="60" cy="15" rx="55" ry="18" fill="rgba(100, 116, 139, 0.4)" />
                <ellipse cx="100" cy="18" rx="45" ry="16" fill="rgba(148, 163, 184, 0.3)" />
                <ellipse cx="140" cy="15" rx="50" ry="18" fill="rgba(100, 116, 139, 0.4)" />
              </g>

              {/* Rain Droplets Animating */}
              {rainIntensity > 10 && (
                <g stroke="#38bdf8" strokeWidth="1.2" strokeDasharray="3,6" opacity={rainIntensity / 100}>
                  <line x1="120" y1="45" x2="110" y2="120" />
                  <line x1="150" y1="40" x2="140" y2="125" />
                  <line x1="180" y1="45" x2="170" y2="120" />
                  <line x1="210" y1="40" x2="200" y2="125" />
                  <line x1="240" y1="45" x2="230" y2="120" />
                  <line x1="270" y1="40" x2="260" y2="125" />
                </g>
              )}

              {/* Soil Layer Profile */}
              <path
                d={`M 20 140 Q 200 ${140 + currentDisp * 2} 380 140 L 380 210 L 20 210 Z`}
                fill="#1e293b"
                stroke="var(--accent-cyan)"
                strokeWidth="1.5"
                style={{ transition: 'all 0.3s ease' }}
              />

              {/* Saturation Water Table level */}
              <rect
                x="20"
                y={210 - (saturation / 100) * 55}
                width="360"
                height={(saturation / 100) * 55}
                fill="rgba(56, 189, 248, 0.2)"
              />
              <line
                x1="20"
                y1={210 - (saturation / 100) * 55}
                x2="380"
                y2={210 - (saturation / 100) * 55}
                stroke="#38bdf8"
                strokeWidth="1"
                strokeDasharray="4,2"
              />

              {/* Road / Rail Embankment Slab */}
              <rect
                x="120"
                y={120 + currentDisp * 2}
                width="160"
                height="14"
                fill="#475569"
                stroke="#94a3b8"
                strokeWidth="1.5"
                rx="2"
                style={{ transition: 'all 0.3s ease' }}
              />
              <text
                x="200"
                y={112 + currentDisp * 2}
                fill="#ffffff"
                fontSize="9"
                textAnchor="middle"
                fontFamily="var(--font-mono)"
                fontWeight="600"
              >
                INFRASTRUCTURE EMBANKMENT
              </text>

              {/* Displacement indicator */}
              <text x="30" y="30" fill="var(--text-muted)" fontSize="9" fontFamily="var(--font-mono)">
                DISPLACEMENT:
              </text>
              <text x="30" y="48" fill="var(--accent-cyan)" fontSize="13" fontFamily="var(--font-mono)" fontWeight="700">
                {currentDisp > 0 ? `+${currentDisp.toFixed(1)}` : currentDisp.toFixed(1)} mm
              </text>
              <text x="30" y="62" fill="var(--text-dim)" fontSize="8" fontFamily="var(--font-mono)">
                {currentDisp >= 0 ? '(SOIL HEAVE)' : '(SETTLEMENT)'}
              </text>
            </svg>
          </div>

          {/* Interactive Sliders */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>RAINFALL INTENSITY</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{rainIntensity}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={rainIntensity}
                onChange={(e) => setRainIntensity(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>SOIL SATURATION / PORE PRESSURE</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{saturation}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={saturation}
                onChange={(e) => setSaturation(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>SIMULATED TIME OF YEAR</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: '#ffffff' }}>Day {elapsedDays} / 365</span>
              </div>
              <input
                type="range"
                min="0"
                max="365"
                value={elapsedDays}
                onChange={(e) => setElapsedDays(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        {/* Dynamic Deformation Chart & STRATA Reasoning */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <InteractiveDeformationChart
            data={chartData}
            height={200}
            baselineNoiseMm={2.0}
            provenance="CONCEPTUAL SIMULATION"
          />

          {/* STRATA Guard Status */}
          <div
            style={{
              backgroundColor: 'rgba(56, 189, 248, 0.05)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Compass size={16} color="var(--state-environmental)" />
              <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--state-environmental)' }}>
                ENVIRONMENTAL RECURRENCE GUARD ACTIVE
              </span>
            </div>

            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              STRATA detects that the displacement wave repeatedly reverses direction as moisture drains. Because the net deformation returns toward baseline, structural alert escalation is suppressed.
            </div>

            <div style={{ display: 'flex', gap: '1.25rem', marginTop: '0.25rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
              <div>
                RECURRENCE: <strong style={{ color: 'var(--state-environmental)' }}>DETECTED</strong>
              </div>
              <div>
                STRUCTURAL ALERT: <strong style={{ color: 'var(--state-baseline)' }}>SUPPRESSED</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
