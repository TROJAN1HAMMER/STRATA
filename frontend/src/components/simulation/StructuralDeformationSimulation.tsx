import React, { useState, useMemo } from 'react'
import { Cpu, Scale, GitMerge } from 'lucide-react'
import { InteractiveDeformationChart, type ChartDataPoint } from './InteractiveDeformationChart'
import { TemporalPlayback } from './TemporalPlayback'
import { useFacultyMode } from './FacultyModeContext'

type DeformationPattern = 'STABLE' | 'MONOTONIC' | 'ACCELERATING'

export const StructuralDeformationSimulation: React.FC = () => {
  const { facultyMode } = useFacultyMode()
  const [pattern, setPattern] = useState<DeformationPattern>('MONOTONIC')
  const [currentEpoch, setCurrentEpoch] = useState<number>(6)

  // 8 Epoch series based on selected pattern
  const allEpochData: Record<DeformationPattern, number[]> = {
    STABLE: [-0.4, 0.6, -0.2, 0.5, -0.6, 0.2, -0.3, 0.4],
    MONOTONIC: [-0.6, -1.8, -3.2, -4.9, -6.7, -8.6, -10.5, -12.4],
    ACCELERATING: [-0.5, -1.2, -2.4, -4.5, -7.5, -11.6, -17.2, -24.5],
  }

  const rawDisplacements = allEpochData[pattern]

  // Subset up to currentEpoch for playback
  const visibleChartData: ChartDataPoint[] = useMemo(() => {
    return rawDisplacements.slice(0, currentEpoch).map((val, idx) => ({
      epoch: idx + 1,
      date: `2025-0${idx + 1}-15`,
      displacement_mm: val,
      los_displacement_mm: val * 0.84,
      coherence: 0.88 - idx * 0.01,
      state: pattern === 'STABLE' ? 'BASELINE' : idx > 2 ? 'PERSISTENT' : 'EMERGING',
    }))
  }, [pattern, currentEpoch, rawDisplacements])

  // Live Metrics at currentEpoch
  const currentDisp = rawDisplacements[currentEpoch - 1] ?? 0

  const mlProbability = pattern === 'STABLE' ? 0.08 : pattern === 'MONOTONIC' ? 0.78 : 0.94
  const physicsScore = pattern === 'STABLE' ? 0.95 : pattern === 'MONOTONIC' ? 0.88 : 0.82
  const consensusAgreement = pattern === 'STABLE' ? 0.98 : pattern === 'MONOTONIC' ? 0.92 : 0.89
  const temporalStatus = pattern === 'STABLE' ? 'BASELINE' : currentEpoch < 3 ? 'EMERGING' : pattern === 'ACCELERATING' ? 'ACCELERATING' : 'PERSISTENT'

  const evidenceIndex =
    pattern === 'STABLE'
      ? 12.4
      : pattern === 'MONOTONIC'
      ? Math.min(85, 20 + currentEpoch * 9.5)
      : Math.min(96, 25 + currentEpoch * 11.5)

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
            <span className="badge badge-cyan">MODULE 05</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              MULTI-EPOCH KINEMATIC EVOLUTION
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-primary)' }}>
            {facultyMode ? 'How True Damage Emerges Over Multiple Visits' : 'Progressive Structural Deformation & Evidence Accumulation'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.35rem 0 0 0', maxWidth: '750px' }}>
            {facultyMode
              ? 'Watch how persistent structural settlement breaks out of the green baseline noise zone across 8 satellite revisits, simultaneously engaging both AI and physics engines.'
              : 'Demonstrates multi-epoch trajectory evaluation, temporal persistence criteria, and progressive escalation to the Evidence Characterization Index.'}
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>
            CONCEPTUAL SIMULATION
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Multi-epoch progression
          </div>
        </div>
      </div>

      {/* Pattern Selector Tabs */}
      <div style={{ display: 'flex', gap: '0.75rem' }}>
        {[
          { id: 'STABLE' as DeformationPattern, label: 'Stable Infrastructure (Within Baseline)' },
          { id: 'MONOTONIC' as DeformationPattern, label: 'Monotonic Linear Settlement (Persistent)' },
          { id: 'ACCELERATING' as DeformationPattern, label: 'Accelerating Subsidence (High Attention)' },
        ].map((p) => (
          <button
            key={p.id}
            onClick={() => {
              setPattern(p.id)
              setCurrentEpoch(8)
            }}
            className={`btn btn-sm ${pattern === p.id ? 'btn-primary' : 'btn-secondary'}`}
            style={{ flex: 1, padding: '0.5rem 0.75rem', fontSize: '0.78rem' }}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Main Grid: Chart & Synchronized Engine Readouts */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.3fr 1.1fr',
          gap: '1.5rem',
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '6px',
          padding: '1.25rem',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Left: Deformation Chart & Timeline Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <InteractiveDeformationChart
            data={visibleChartData}
            height={220}
            baselineNoiseMm={2.0}
            provenance="CONCEPTUAL SIMULATION"
          />

          <TemporalPlayback
            currentEpoch={currentEpoch}
            totalEpochs={8}
            onSelectEpoch={setCurrentEpoch}
            evidenceScore={Math.round((currentEpoch / 8) * (pattern === 'STABLE' ? 15 : 92))}
            statusLabel={temporalStatus}
          />
        </div>

        {/* Right: Synchronized Engine Telemetry Stack */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {/* Instantaneous Displacement Chip */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.5rem 0.85rem',
              backgroundColor: 'var(--bg-card)',
              borderRadius: '6px',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.75rem',
            }}
          >
            <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              EPOCH {currentEpoch} INSTANTANEOUS VERTICAL
            </span>
            <span
              style={{
                fontWeight: 700,
                fontFamily: 'var(--font-mono)',
                color: Math.abs(currentDisp) > 2.0 ? 'var(--state-monitor)' : 'var(--state-baseline)',
              }}
            >
              {currentDisp > 0 ? `+${currentDisp.toFixed(1)}` : currentDisp.toFixed(1)} mm
            </span>
          </div>

          {/* ML Classifier Readout */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '0.75rem 1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Cpu size={14} color="var(--accent-cyan)" />
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  ML DEFORMATION ENGINE
                </span>
              </div>
              <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                {(mlProbability * 100).toFixed(0)}% STRUCTURAL PROB
              </span>
            </div>
            <div style={{ height: '4px', backgroundColor: 'var(--bg-primary)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${mlProbability * 100}%`, backgroundColor: 'var(--accent-cyan)' }} />
            </div>
          </div>

          {/* Physics Consistency Engine Readout */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '0.75rem 1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Scale size={14} color="var(--state-baseline)" />
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  PHYSICS CONSISTENCY ENGINE
                </span>
              </div>
              <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--state-baseline)' }}>
                {(physicsScore * 100).toFixed(0)}% CONSISTENCY
              </span>
            </div>
            <div style={{ height: '4px', backgroundColor: 'var(--bg-primary)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${physicsScore * 100}%`, backgroundColor: 'var(--state-baseline)' }} />
            </div>
          </div>

          {/* Consensus Agreement */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '0.75rem 1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <GitMerge size={14} color="var(--state-environmental)" />
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  CROSS-MODEL CONSENSUS
                </span>
              </div>
              <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--state-environmental)' }}>
                AGREEMENT DETECTED (+15% BOOST)
              </span>
            </div>
            <div style={{ height: '4px', backgroundColor: 'var(--bg-primary)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${consensusAgreement * 100}%`, backgroundColor: 'var(--state-environmental)' }} />
            </div>
          </div>

          {/* Evidence Characterization Index Final Card */}
          <div
            style={{
              backgroundColor: 'rgba(56, 189, 248, 0.05)',
              border: '1px solid var(--border-medium)',
              borderRadius: '6px',
              padding: '0.85rem 1rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                EVIDENCE CHARACTERIZATION INDEX
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.1rem' }}>
                {evidenceIndex.toFixed(1)} <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>/ 100</span>
              </div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                Triage index — not a structural collapse forecast
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                ACTIONABLE STATUS
              </div>
              <span
                className={
                  pattern === 'STABLE'
                    ? 'badge badge-baseline'
                    : pattern === 'MONOTONIC'
                    ? 'badge badge-monitor'
                    : 'badge badge-elevated'
                }
                style={{ fontSize: '0.75rem', marginTop: '0.3rem', display: 'inline-block' }}
              >
                {pattern === 'STABLE' ? 'BASELINE NOMINAL' : pattern === 'MONOTONIC' ? 'MONITOR REQUIRED' : 'ELEVATED ATTENTION'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
