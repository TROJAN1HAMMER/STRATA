import React, { useState } from 'react'
import { useFacultyMode } from './FacultyModeContext'

export const SarInSarSimulation: React.FC = () => {
  const { facultyMode } = useFacultyMode()
  const [incidenceAngle, setIncidenceAngle] = useState<number>(36.5) // degrees
  const [losDisplacementMm, setLosDisplacementMm] = useState<number>(-8.4) // mm

  // Satellite wavelength Sentinel-1 C-band ~ 55.46 mm (5.55 cm)
  const wavelengthMm = 55.46

  // Geometry: d_vertical = d_LOS / cos(theta)
  const thetaRad = (incidenceAngle * Math.PI) / 180
  const verticalDisplacementMm = losDisplacementMm / Math.cos(thetaRad)

  // Phase shift: Delta_phi = (4 * pi / lambda) * d_LOS
  const phaseShiftRad = ((4 * Math.PI) / wavelengthMm) * losDisplacementMm
  const phaseShiftDeg = ((phaseShiftRad * 180) / Math.PI) % 360

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
            <span className="badge badge-cyan">MODULE 01</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              SAR / INSAR INTERFEROMETRIC GEOMETRY
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-primary)' }}>
            {facultyMode ? 'How Satellite Radar Measures Millimeter Motion' : 'SAR Line-Of-Sight & Phase Geometry Engine'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.35rem 0 0 0', maxWidth: '750px' }}>
            {facultyMode
              ? 'Satellites do not take normal optical photographs. They beam microwave radar pulses to Earth and measure tiny fractions of the wave cycle between visits.'
              : 'Demonstrates phase difference interferometry Δϕ and geometric projection from Line-Of-Sight (LOS) slant range into vertical deformation.'}
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>
            CONCEPTUAL SIMULATION
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Illustrative visualization
          </div>
        </div>
      </div>

      {/* Main Interactive Stage & Diagram */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.4fr 1fr',
          gap: '1.5rem',
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '6px',
          padding: '1.25rem',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* SVG Visualization */}
        <div style={{ position: 'relative', width: '100%', height: '340px' }}>
          <svg width="100%" height="100%" viewBox="0 0 520 340">
            {/* Dark Sky Gradient */}
            <defs>
              <linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#08101a" />
                <stop offset="100%" stopColor="#020408" />
              </linearGradient>
              <radialGradient id="satelliteGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="rgba(56, 189, 248, 0.4)" />
                <stop offset="100%" stopColor="transparent" />
              </radialGradient>
            </defs>
            <rect width="100%" height="100%" fill="url(#skyGrad)" rx="6" />

            {/* Orbit path dashed line */}
            <line x1="40" y1="50" x2="480" y2="50" stroke="rgba(255, 255, 255, 0.1)" strokeDasharray="4,4" />
            <text x="490" y="53" fill="var(--text-dim)" fontSize="9" fontFamily="var(--font-mono)">
              ORBIT ALTITUDE 693 KM
            </text>

            {/* Satellite Position */}
            <g transform="translate(130, 50)">
              <circle cx="0" cy="0" r="24" fill="url(#satelliteGlow)" />
              {/* Solar Panels */}
              <rect x="-35" y="-6" width="22" height="12" fill="#0284c7" stroke="#38bdf8" strokeWidth="1" />
              <rect x="13" y="-6" width="22" height="12" fill="#0284c7" stroke="#38bdf8" strokeWidth="1" />
              {/* Satellite Body */}
              <rect x="-10" y="-8" width="20" height="16" fill="#1e293b" stroke="#94a3b8" strokeWidth="1.5" rx="2" />
              {/* Radar Antenna */}
              <polygon points="-8,10 8,10 14,16 -14,16" fill="#38bdf8" opacity="0.8" />
              <text x="0" y="-14" fill="var(--accent-cyan)" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)">
                SENTINEL-1 C-BAND
              </text>
            </g>

            {/* Ground / Bridge Pier & Deck */}
            <g transform="translate(340, 260)">
              {/* Bridge Tower / Pier */}
              <rect x="-25" y="-50" width="50" height="110" fill="#1e293b" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" rx="2" />
              {/* Bridge Deck */}
              <rect
                x="-120"
                y="-65"
                width="240"
                height="16"
                fill="#334155"
                stroke="#64748b"
                strokeWidth="1.5"
                rx="3"
                transform={`translate(0, ${verticalDisplacementMm * 1.5})`}
                style={{ transition: 'transform 0.25s ease' }}
              />
              <text x="0" y="-72" fill="#ffffff" fontSize="10" textAnchor="middle" fontWeight="600">
                MONITORED BRIDGE DECK
              </text>
              {/* True motion arrow */}
              {Math.abs(verticalDisplacementMm) > 0.5 && (
                <g transform={`translate(60, -55)`}>
                  <line x1="0" y1="0" x2="0" y2={verticalDisplacementMm * 2} stroke="#f43f5e" strokeWidth="2.5" markerEnd="url(#arrow)" />
                  <text x="8" y="10" fill="#f43f5e" fontSize="9" fontFamily="var(--font-mono)">
                    {verticalDisplacementMm.toFixed(1)} mm
                  </text>
                </g>
              )}
            </g>

            {/* Radar Beam / Slant Range Line-Of-Sight */}
            <line
              x1="130"
              y1="66"
              x2="340"
              y2={195 + verticalDisplacementMm * 1.5}
              stroke="var(--accent-cyan)"
              strokeWidth="2"
              strokeDasharray="6,4"
              opacity="0.85"
            />

            {/* Wave Pulses Animating Down LOS */}
            <circle cx="180" cy="100" r="4" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.5" />
            <circle cx="230" cy="130" r="7" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.5" />
            <circle cx="285" cy="165" r="10" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.5" />

            {/* Incidence Angle θ arc */}
            <g transform="translate(130, 66)">
              {/* Nadir line (straight down) */}
              <line x1="0" y1="0" x2="0" y2="120" stroke="rgba(255,255,255,0.2)" strokeDasharray="3,3" />
              <path
                d="M 0 50 A 50 50 0 0 1 28 42"
                fill="none"
                stroke="var(--state-monitor)"
                strokeWidth="1.5"
              />
              <text x="12" y="65" fill="var(--state-monitor)" fontSize="10" fontFamily="var(--font-mono)">
                θ = {incidenceAngle.toFixed(1)}°
              </text>
            </g>

            {/* Geometry Label Box */}
            <rect x="20" y="270" width="180" height="50" fill="rgba(0,0,0,0.6)" stroke="var(--border-subtle)" rx="4" />
            <text x="30" y="288" fill="var(--text-muted)" fontSize="9" fontFamily="var(--font-mono)">
              GEOMETRY FORMULA:
            </text>
            <text x="30" y="306" fill="var(--accent-cyan)" fontSize="11" fontFamily="var(--font-mono)" fontWeight="700">
              d_vert = d_LOS / cos(θ)
            </text>
          </svg>
        </div>

        {/* Interactive Controls & Live Metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '0.4rem' }}>
              SLANT RANGE LINE-OF-SIGHT DISPLACEMENT (d_LOS)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input
                type="range"
                min="-20"
                max="5"
                step="0.2"
                value={losDisplacementMm}
                onChange={(e) => setLosDisplacementMm(parseFloat(e.target.value))}
                style={{ flex: 1 }}
              />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600, width: '65px', textAlign: 'right' }}>
                {losDisplacementMm.toFixed(1)} mm
              </span>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '0.4rem' }}>
              RADAR INCIDENCE ANGLE (θ)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input
                type="range"
                min="20"
                max="55"
                step="0.5"
                value={incidenceAngle}
                onChange={(e) => setIncidenceAngle(parseFloat(e.target.value))}
                style={{ flex: 1 }}
              />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600, width: '65px', textAlign: 'right' }}>
                {incidenceAngle.toFixed(1)}°
              </span>
            </div>
          </div>

          {/* Computed Readouts */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>TRUE VERTICAL DEFORMATION</span>
              <span style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                {verticalDisplacementMm.toFixed(2)} mm
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PHASE SHIFT Δϕ (C-BAND)</span>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                {phaseShiftDeg.toFixed(1)}° ({phaseShiftRad.toFixed(2)} rad)
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PROJECTION FACTOR (1 / cos θ)</span>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                {(1 / Math.cos(thetaRad)).toFixed(3)}x
              </span>
            </div>
          </div>

          {/* Faculty Explanatory Note */}
          <div
            style={{
              backgroundColor: 'rgba(56, 189, 248, 0.04)',
              border: '1px solid rgba(56, 189, 248, 0.15)',
              borderRadius: '6px',
              padding: '0.75rem',
              fontSize: '0.78rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.45,
            }}
          >
            <strong style={{ color: 'var(--accent-cyan)' }}>Why Geometry Matters:</strong> The satellite does not look straight down; it looks sideways at an angle θ. Therefore, vertical movement appears compressed along the slant radar beam. STRATA trigonometrically projects this back to true vertical displacement.
          </div>
        </div>
      </div>
    </div>
  )
}
