import React, { useState, useMemo } from 'react'
import {
  Search,
  ArrowUpDown,
  ArrowUpRight,
} from 'lucide-react'
import type { Infrastructure, PipelineResult, RiskCharacterizationState } from '../../types'

interface InfrastructureTableProps {
  infrastructures: Infrastructure[]
  resultsMap: Record<string, PipelineResult>
  onSelectInfrastructure: (infra: Infrastructure) => void
  onRunPipeline: (infraId: string) => void
}

type SortField = 'name' | 'type' | 'criticality' | 'state' | 'index' | 'confidence'

export const InfrastructureTable: React.FC<InfrastructureTableProps> = ({
  infrastructures,
  resultsMap,
  onSelectInfrastructure,
  onRunPipeline,
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<string>('ALL')
  const [selectedState, setSelectedState] = useState<string>('ALL')
  const [sortField, setSortField] = useState<SortField>('index')
  const [sortAsc, setSortAsc] = useState(false)

  // Filtering & Sorting
  const filteredData = useMemo(() => {
    return infrastructures
      .filter((item) => {
        const matchesSearch =
          item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.structure_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.material.toLowerCase().includes(searchTerm.toLowerCase())

        const matchesType = selectedType === 'ALL' || item.structure_type === selectedType

        const res = resultsMap[item.id]
        const state = res?.risk_characterization?.evidence_state || res?.risk_characterization?.characterization_state || 'BASELINE'
        const matchesState = selectedState === 'ALL' || state === selectedState

        return matchesSearch && matchesType && matchesState
      })
      .sort((a, b) => {
        const resA = resultsMap[a.id]
        const resB = resultsMap[b.id]

        let valA: any = a.name
        let valB: any = b.name

        if (sortField === 'type') {
          valA = a.structure_type
          valB = b.structure_type
        } else if (sortField === 'criticality') {
          const critOrder: Record<string, number> = { LOW: 1, MODERATE: 2, HIGH: 3, CRITICAL: 4, UNKNOWN: 0 }
          valA = critOrder[a.criticality] || 0
          valB = critOrder[b.criticality] || 0
        } else if (sortField === 'index') {
          valA = resA?.risk_characterization?.evidence_characterization_index ?? resA?.risk_characterization?.prototype_risk_index ?? 0
          valB = resB?.risk_characterization?.evidence_characterization_index ?? resB?.risk_characterization?.prototype_risk_index ?? 0
        } else if (sortField === 'confidence') {
          valA = resA?.risk_characterization?.analytical_confidence ?? resA?.risk_characterization?.confidence ?? 0
          valB = resB?.risk_characterization?.analytical_confidence ?? resB?.risk_characterization?.confidence ?? 0
        } else if (sortField === 'state') {
          valA = resA?.risk_characterization?.evidence_state ?? resA?.risk_characterization?.characterization_state ?? 'BASELINE'
          valB = resB?.risk_characterization?.evidence_state ?? resB?.risk_characterization?.characterization_state ?? 'BASELINE'
        }

        if (valA < valB) return sortAsc ? -1 : 1
        if (valA > valB) return sortAsc ? 1 : -1
        return 0
      })
  }, [infrastructures, resultsMap, searchTerm, selectedType, selectedState, sortField, sortAsc])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(false)
    }
  }

  const renderStateBadge = (state: RiskCharacterizationState) => {
    switch (state) {
      case 'BASELINE':
        return <span className="badge badge-baseline">Baseline Nominal</span>
      case 'ENVIRONMENTAL_PATTERN':
        return <span className="badge badge-environmental">Cyclic Reversible</span>
      case 'MONITOR':
        return <span className="badge badge-monitor">Monitoring Req.</span>
      case 'ELEVATED_ATTENTION':
      case 'HIGH_ATTENTION':
        return <span className="badge badge-elevated">High Attention</span>
      case 'INSUFFICIENT_EVIDENCE':
      default:
        return <span className="badge badge-insufficient">{state}</span>
    }
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* PAGE HEADER */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1.25rem',
        }}
      >
        <div>
          <h2>Monitored Infrastructure Portfolio</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Multi-epoch radar interferometry telemetry table with calibrated historical baselines and consensus states.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span className="badge badge-cyan">{filteredData.length} ASSETS MATCHED</span>
        </div>
      </div>

      {/* FILTER & SEARCH CONTROLS */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'var(--bg-secondary)',
          padding: '0.85rem 1.1rem',
          borderRadius: '6px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: 'var(--bg-primary)',
            padding: '0.4rem 0.75rem',
            borderRadius: '4px',
            border: '1px solid var(--border-medium)',
            minWidth: '280px',
          }}
        >
          <Search size={15} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search by asset name, type, material..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.825rem',
              outline: 'none',
              width: '100%',
              fontFamily: 'var(--font-sans)',
            }}
          />
        </div>

        {/* Filter Dropdowns */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Type:</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '0.35rem 0.6rem',
                fontSize: '0.78rem',
                outline: 'none',
              }}
            >
              <option value="ALL">All Types</option>
              <option value="BRIDGE">Bridge</option>
              <option value="DAM">Dam</option>
              <option value="TUNNEL">Tunnel</option>
              <option value="BUILDING">Building</option>
              <option value="EMBANKMENT">Embankment</option>
              <option value="RETAINING_STRUCTURE">Retaining Wall</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>State:</span>
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '0.35rem 0.6rem',
                fontSize: '0.78rem',
                outline: 'none',
              }}
            >
              <option value="ALL">All States</option>
              <option value="BASELINE">Baseline Nominal</option>
              <option value="ENVIRONMENTAL_PATTERN">Cyclic Reversible</option>
              <option value="MONITOR">Monitoring Required</option>
              <option value="ELEVATED_ATTENTION">Elevated Attention</option>
            </select>
          </div>
        </div>
      </div>

      {/* DATA TABLE */}
      <div
        className="strata-card"
        style={{
          padding: 0,
          overflow: 'hidden',
          borderRadius: '6px',
        }}
      >
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  borderBottom: '1px solid var(--border-subtle)',
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                <th
                  onClick={() => handleSort('name')}
                  style={{ padding: '0.85rem 1.15rem', cursor: 'pointer', userSelect: 'none' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <span>Infrastructure Asset</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('type')}
                  style={{ padding: '0.85rem 1rem', cursor: 'pointer', userSelect: 'none' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <span>Type / Material</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('criticality')}
                  style={{ padding: '0.85rem 1rem', cursor: 'pointer', userSelect: 'none' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <span>Criticality</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('state')}
                  style={{ padding: '0.85rem 1rem', cursor: 'pointer', userSelect: 'none' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <span>Evidence State</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('index')}
                  style={{ padding: '0.85rem 1rem', cursor: 'pointer', userSelect: 'none', textAlign: 'right' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', justifyContent: 'flex-end' }}>
                    <span>Characterization Index</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('confidence')}
                  style={{ padding: '0.85rem 1rem', cursor: 'pointer', userSelect: 'none', textAlign: 'right' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', justifyContent: 'flex-end' }}>
                    <span>Confidence</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No infrastructure assets matched your active query filters.
                  </td>
                </tr>
              ) : (
                filteredData.map((infra) => {
                  const res = resultsMap[infra.id]
                  const state = res?.risk_characterization?.evidence_state || res?.risk_characterization?.characterization_state || 'BASELINE'
                  const index = res?.risk_characterization?.evidence_characterization_index ?? res?.risk_characterization?.prototype_risk_index ?? 0
                  const confidence = res?.risk_characterization?.analytical_confidence ?? res?.risk_characterization?.confidence ?? 0
                  const baselineStd = infra.historical_baseline?.baseline_std_mm ?? infra.baseline?.baseline_std_mm ?? 1.2

                  return (
                    <tr
                      key={infra.id}
                      onClick={() => onSelectInfrastructure(infra)}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'background-color var(--duration-fast) ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent'
                      }}
                    >
                      {/* Asset Name */}
                      <td style={{ padding: '1rem 1.15rem' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                          {infra.name}
                        </div>
                        <div
                          style={{
                            fontSize: '0.7rem',
                            color: 'var(--text-muted)',
                            fontFamily: 'var(--font-mono)',
                            marginTop: '0.15rem',
                          }}
                        >
                          ID: {infra.id} • BASELINE STD: ±{baselineStd.toFixed(1)} mm
                        </div>
                      </td>

                      {/* Type & Material */}
                      <td style={{ padding: '1rem 1rem' }}>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
                          {infra.structure_type}
                        </div>
                        <div
                          style={{
                            fontSize: '0.72rem',
                            color: 'var(--text-muted)',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {infra.material}
                        </div>
                      </td>

                      {/* Criticality */}
                      <td style={{ padding: '1rem 1rem' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '0.15rem 0.45rem',
                            borderRadius: '3px',
                            fontSize: '0.7rem',
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 600,
                            backgroundColor:
                              infra.criticality === 'CRITICAL'
                                ? 'rgba(239, 68, 68, 0.15)'
                                : infra.criticality === 'HIGH'
                                ? 'rgba(249, 115, 22, 0.15)'
                                : 'rgba(100, 116, 139, 0.15)',
                            color:
                              infra.criticality === 'CRITICAL'
                                ? '#f87171'
                                : infra.criticality === 'HIGH'
                                ? '#fb923c'
                                : '#94a3b8',
                            border: `1px solid ${
                              infra.criticality === 'CRITICAL'
                                ? 'rgba(239, 68, 68, 0.3)'
                                : infra.criticality === 'HIGH'
                                ? 'rgba(249, 115, 22, 0.3)'
                                : 'rgba(100, 116, 139, 0.3)'
                            }`,
                          }}
                        >
                          {infra.criticality}
                        </span>
                      </td>

                      {/* Evidence State */}
                      <td style={{ padding: '1rem 1rem' }}>{renderStateBadge(state)}</td>

                      {/* Prototype Index */}
                      <td style={{ padding: '1rem 1rem', textAlign: 'right' }}>
                        <div
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            fontSize: '0.95rem',
                            color:
                              index > 50
                                ? 'var(--state-elevated)'
                                : index > 20
                                ? 'var(--state-monitor)'
                                : 'var(--state-baseline)',
                          }}
                        >
                          {index.toFixed(1)}
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 400 }}>
                            {' '}/ 100
                          </span>
                        </div>
                      </td>

                      {/* Confidence */}
                      <td style={{ padding: '1rem 1rem', textAlign: 'right' }}>
                        <div
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 600,
                            fontSize: '0.85rem',
                            color: 'var(--accent-cyan)',
                          }}
                        >
                          {(confidence * 100).toFixed(0)}%
                        </div>
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '1rem 1rem', textAlign: 'right' }}>
                        <div
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.4rem' }}
                        >
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              onRunPipeline(infra.id)
                            }}
                            className="btn btn-secondary btn-sm"
                            title="Execute analytical pipeline"
                          >
                            Analyze
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              onSelectInfrastructure(infra)
                            }}
                            className="btn btn-primary btn-sm"
                            title="Open detailed evidence view"
                          >
                            <ArrowUpRight size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
