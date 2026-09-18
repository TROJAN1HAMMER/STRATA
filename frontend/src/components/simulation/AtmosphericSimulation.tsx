import React, { useState, useMemo } from 'react'
import { AlertTriangle } from 'lucide-react'
import { InteractiveDeformationChart, type ChartDataPoint } from './InteractiveDeformationChart'
import { useFacultyMode } from './FacultyModeContext'

export const AtmosphericSimulation: React.FC = () => {
  const { facultyMode } = useFacultyMode()

  const [waterVaporDelayMm, setWaterVaporDelayMm] = useState<number>(14.5) // mm apparent delay
  const [cloudPositionX, setCloudPositionX] = useState<number>(220) // horizontal drift
  const transientEpoch = 5 // epoch when cloud was overhead

  // Multi-epoch time series: structure is 100% STATIC (0.0 mm true deformation),
  // but epoch 5 has an atmospheric phase artifact
  const chartData: ChartDataPoint[] = useMemo(() => {
    const points: ChartDataPoint[] = []

    for (let i = 1; i <= 10; i++) {
      const isCloudVisit = i === transientEpoch
      // Apparent displacement includes atmospheric delay spike on transientEpoch
      const apparentDisp = isCloudVisit ? waterVaporDelayMm : (Math.sin(i * 4.3) * 0.4)

      points.push({
        epoch: i,
        date: `2025-05-${(i * 3).toString().padStart(2, '0')}`,
        displacement_mm: apparentDisp,
        los_displacement_mm: apparentDisp * 0.85,
        coherence: isCloudVisit ? 0.72 : 0.89,
        state: isCloudVisit ? 'ATMOSPHERIC_EVENT' : 'BASELINE',
        isAtmosphericEvent: isCloudVisit,
        annotation: isCloudVisit ? 'Tropospheric Vapor Spike' : undefined,
      })
    }
    return points
  }, [waterVaporDelayMm, transientEpoch])

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
            <span className="badge badge-cyan">MODULE 04</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              ATMOSPHERIC PHASE DELAY &amp; ARTIFACT FILTERING
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-primary)' }}>
            {facultyMode ? 'The Atmospheric Distortion Illusion' : 'Tropospheric Water-Vapor Delay & Non-Structural Spikes'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.35rem 0 0 0', maxWidth: '750px' }}>
            {facultyMode
              ? 'Notice that the concrete bridge below does not move at all (0.0 mm). Yet a passing moisture cloud slows down the radar beam, creating a fake 14 mm spike. STRATA filters this out as an atmospheric transient.'
              : 'Demonstrates path-delay phase modulation where localized tropospheric water vapor creates apparent single-epoch deformation spikes while structural integrity is unaffected.'}
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>
            CONCEPTUAL SIMULATION
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Atmospheric path model
          </div>
        </div>
      </div>

      {/* Main Interactive Stage */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.3fr 1.2fr',
          gap: '1.5rem',
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '6px',
          padding: '1.25rem',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* SVG Atmospheric Column Simulation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ position: 'relative', width: '100%', height: '260px', backgroundColor: '#060b13', borderRadius: '6px', overflow: 'hidden' }}>
            <svg width="100%" height="100%" viewBox="0 0 460 260">
              {/* Satellite Position at top left */}
              <g transform="translate(100, 35)">
                <rect x="-10" y="-8" width="20" height="16" fill="#1e293b" stroke="#38bdf8" strokeWidth="1.5" rx="2" />
                <rect x="-30" y="-5" width="18" height="10" fill="#0284c7" />
                <rect x="12" y="-5" width="18" height="10" fill="#0284c7" />
                <text x="0" y="-12" fill="var(--accent-cyan)" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)">
                  RADAR SATELLITE
                </text>
              </g>

              {/* Ground Structure (STABLE at 0 mm) */}
              <g transform="translate(340, 210)">
                <rect x="-40" y="-35" width="80" height="35" fill="#334155" stroke="#94a3b8" strokeWidth="1.5" rx="2" />
                <rect x="-10" y="0" width="20" height="45" fill="#1e293b" />
                <text x="0" y="-42" fill="#ffffff" fontSize="9" textAnchor="middle" fontWeight="600">
                  RIGID BRIDGE PIER
                </text>
                <text x="0" y="-18" fill="var(--state-baseline)" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="700">
                  TRUE MOTION: 0.0 mm
                </text>
              </g>

              {/* Atmospheric Boundary Layer Box */}
              <rect x="50" y="80" width="360" height="90" fill="rgba(148, 163, 184, 0.05)" stroke="rgba(255, 255, 255, 0.08)" strokeDasharray="3,3" />
              <text x="60" y="95" fill="var(--text-dim)" fontSize="8" fontFamily="var(--font-mono)">
                TROPOSPHERE (0 - 4 KM ALTITUDE)
              </text>

              {/* Moving Water Vapor Delay Pocket / Cloud */}
              <g transform={`translate(${cloudPositionX}, 110)`} opacity={0.85}>
                <ellipse cx="0" cy="0" rx="55" ry="25" fill="rgba(56, 189, 248, 0.25)" filter="blur(3px)" />
                <ellipse cx="10" cy="-5" rx="40" ry="20" fill="rgba(186, 230, 253, 0.35)" />
                <text x="0" y="4" fill="#ffffff" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="600">
                  WATER VAPOR DELAY
                </text>
                <text x="0" y="16" fill="var(--accent-cyan)" fontSize="8" textAnchor="middle" fontFamily="var(--font-mono)">
                  +{waterVaporDelayMm.toFixed(1)} mm path delay
                </text>
              </g>

              {/* Radar beam passing directly through the cloud */}
              <line
                x1="100"
                y1="45"
                x2="340"
                y2="200"
                stroke="var(--accent-cyan)"
                strokeWidth="2"
                strokeDasharray="5,4"
              />

              {/* Distortion indicator at intersection */}
              <circle cx={cloudPositionX} cy="115" r="14" fill="none" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="2,2" />
              <text x={cloudPositionX + 20} y="118" fill="#f43f5e" fontSize="9" fontFamily="var(--font-mono)">
                PHASE RETARDATION
              </text>
            </svg>
          </div>

          {/* Interactive Sliders */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>TROPOSPHERIC VAPOR DELAY STRENGTH</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>+{waterVaporDelayMm.toFixed(1)} mm</span>
              </div>
              <input
                type="range"
                min="2"
                max="25"
                step="0.5"
                value={waterVaporDelayMm}
                onChange={(e) => setWaterVaporDelayMm(parseFloat(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>CLOUD HORIZONTAL POSITION ACROSS BEAM</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: '#ffffff' }}>{cloudPositionX} px</span>
              </div>
              <input
                type="range"
                min="140"
                max="300"
                step="2"
                value={cloudPositionX}
                onChange={(e) => setCloudPositionX(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        {/* Dynamic Deformation Chart & STRATA Filter Explanation */}
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
              backgroundColor: 'rgba(244, 63, 94, 0.05)',
              border: '1px solid rgba(244, 63, 94, 0.25)',
              borderRadius: '6px',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.45rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={16} color="var(--state-monitor)" />
              <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--state-monitor)' }}>
                STRATA TRANSIENT FILTER: ATMOSPHERICALLY SUSPECT
              </span>
            </div>

            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              STRATA detects that the spike on Epoch {transientEpoch} is a non-persistent, single-epoch anomaly that instantly reverts to baseline on Epoch {transientEpoch + 1}. The temporal engine rejects it as an atmospheric phase artifact.
            </div>

            <div style={{ display: 'flex', gap: '1.25rem', marginTop: '0.2rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
              <div>
                CLASSIFICATION: <strong style={{ color: 'var(--state-monitor)' }}>ATMOSPHERIC_EVENT</strong>
              </div>
              <div>
                STRUCTURAL DAMAGE: <strong style={{ color: 'var(--state-baseline)' }}>DISPROVEN (FALSE ALARM)</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
