import React from 'react'
import {
  Activity,
  Layers,
  Clock,
  ShieldCheck,
  Play,
  Info,
  Sliders,
  Radio,
  FileCheck2,
  FlaskConical,
} from 'lucide-react'
import type { ViewTab } from '../../types'

interface ShellProps {
  currentTab: ViewTab
  onSelectTab: (tab: ViewTab) => void
  onOpenAbout: () => void
  onOpenAnalysis: () => void
  onToggleDemo: () => void
  isDemoMode: boolean
  children: React.ReactNode
}

export const Shell: React.FC<ShellProps> = ({
  currentTab,
  onSelectTab,
  onOpenAbout,
  onOpenAnalysis,
  onToggleDemo,
  isDemoMode,
  children,
}) => {
  const navItems = [
    { id: 'dashboard' as ViewTab, label: 'Dashboard', icon: Activity },
    { id: 'infrastructure' as ViewTab, label: 'Infrastructure Assets', icon: Layers },
    { id: 'temporal' as ViewTab, label: 'Temporal History', icon: Clock },
    { id: 'chronology' as ViewTab, label: 'Evidence Chronology', icon: ShieldCheck },
    { id: 'simulation' as ViewTab, label: 'Simulation Lab', icon: FlaskConical },
    { id: 'demo' as ViewTab, label: 'Demo Mode (Curated)', icon: Play, highlight: true },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', width: '100%' }}>
      {/* TOP SCIENTIFIC TELEMETRY HEADER */}
      <header
        style={{
          height: '60px',
          backgroundColor: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 1.5rem',
          position: 'sticky',
          top: 0,
          zIndex: 40,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            onClick={() => onSelectTab('dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                border: '1px solid #38bdf8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 12px rgba(56, 189, 248, 0.3)',
              }}
            >
              <Radio size={18} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontWeight: 700, fontSize: '1.15rem', letterSpacing: '0.05em' }}>
                  STRATA
                </span>
                <span className="badge badge-cyan" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                  v1.0.0 FROZEN
                </span>
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', lineHeight: 1 }}>
                Structural Temporal Analysis &amp; Threat Assessment
              </div>
            </div>
          </div>
        </div>

        {/* CENTER TELEMETRY CHIPS */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.85rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
          }}
          className="telemetry-bar"
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.25rem 0.6rem',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: '4px',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)',
            }}
          >
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: 'var(--state-baseline)',
                boxShadow: '0 0 6px var(--state-baseline)',
              }}
            />
            <span>SENTINEL-1A C-BAND [LOS]</span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.25rem 0.6rem',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: '4px',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)',
            }}
          >
            <FileCheck2 size={13} color="var(--accent-cyan)" />
            <span>202 / 202 VERIFIED</span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.25rem 0.6rem',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: '4px',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)',
            }}
          >
            <ShieldCheck size={13} color="var(--state-baseline)" />
            <span>CHRONOLOGY TAMPER-EVIDENT</span>
          </div>
        </div>

        {/* RIGHT QUICK ACTIONS */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={onOpenAnalysis}
            className="btn btn-primary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <Sliders size={14} />
            <span>Run Pipeline</span>
          </button>

          <button
            onClick={onToggleDemo}
            className={`btn btn-sm ${isDemoMode ? 'btn-primary' : 'btn-secondary'}`}
            style={{
              borderColor: isDemoMode ? 'var(--accent-cyan)' : 'var(--border-medium)',
              boxShadow: isDemoMode ? '0 0 10px rgba(56, 189, 248, 0.4)' : 'none',
            }}
          >
            <Play size={14} />
            <span>{isDemoMode ? 'Demo Active' : 'Presentation Demo'}</span>
          </button>

          <button
            onClick={onOpenAbout}
            className="btn btn-ghost btn-sm"
            title="Scientific Methodology & Frozen Versions"
          >
            <Info size={16} />
          </button>
        </div>
      </header>

      {/* MAIN BODY: SIDEBAR + CONTENT AREA */}
      <div style={{ display: 'flex', flex: 1, position: 'relative' }}>
        {/* SIDEBAR NAVIGATION */}
        <aside
          style={{
            width: '230px',
            backgroundColor: 'var(--bg-secondary)',
            borderRight: '1px solid var(--border-subtle)',
            padding: '1.25rem 0.75rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <div
              style={{
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-muted)',
                padding: '0.2rem 0.75rem 0.6rem',
                letterSpacing: '0.08em',
              }}
            >
              Analytical Navigation
            </div>

            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = currentTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '6px',
                    border: '1px solid',
                    borderColor: isActive ? 'var(--border-bright)' : 'transparent',
                    backgroundColor: isActive
                      ? 'var(--bg-card)'
                      : item.highlight
                      ? 'rgba(56, 189, 248, 0.05)'
                      : 'transparent',
                    color: isActive
                      ? '#ffffff'
                      : item.highlight
                      ? 'var(--accent-cyan)'
                      : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    transition: 'all var(--duration-fast) ease',
                    textAlign: 'left',
                    width: '100%',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'
                      e.currentTarget.style.color = 'var(--text-primary)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = item.highlight
                        ? 'rgba(56, 189, 248, 0.05)'
                        : 'transparent'
                      e.currentTarget.style.color = item.highlight
                        ? 'var(--accent-cyan)'
                        : 'var(--text-secondary)'
                    }
                  }}
                >
                  <Icon
                    size={17}
                    color={
                      isActive
                        ? 'var(--accent-cyan)'
                        : item.highlight
                        ? 'var(--accent-cyan)'
                        : 'var(--text-muted)'
                    }
                  />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </div>

          {/* SIDEBAR FOOTER: SYSTEM SPECS */}
          <div
            style={{
              padding: '0.85rem',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: '6px',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <span>PIPELINE</span>
              <span style={{ color: 'var(--accent-cyan)' }}>v1.0.0-LOCKED</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <span>CONSENSUS</span>
              <span style={{ color: 'var(--text-secondary)' }}>DUAL-ENGINE</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <span>BASELINE GUARD</span>
              <span style={{ color: 'var(--state-baseline)' }}>ENGAGED</span>
            </div>
            <div
              style={{
                marginTop: '0.6rem',
                paddingTop: '0.5rem',
                borderTop: '1px solid var(--border-subtle)',
                fontSize: '0.68rem',
                color: 'var(--text-dim)',
                textAlign: 'center',
              }}
            >
              ESA Sentinel InSAR Evidence
            </div>
          </div>
        </aside>

        {/* PRIMARY CONTENT REGION */}
        <main
          style={{
            flex: 1,
            backgroundColor: 'var(--bg-primary)',
            padding: '1.75rem 2rem 3rem',
            overflowY: 'auto',
            maxHeight: 'calc(100vh - 60px)',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  )
}
