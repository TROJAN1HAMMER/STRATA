import React, { useEffect, useState } from 'react'
import { Play, Pause, SkipBack, SkipForward, RotateCcw } from 'lucide-react'

interface TemporalPlaybackProps {
  currentEpoch: number
  totalEpochs: number
  onSelectEpoch: (epoch: number) => void
  evidenceScore?: number // 0 to 100 illustrative evidence
  statusLabel?: string
  isPlaying?: boolean
  onTogglePlay?: () => void
  onReset?: () => void
}

export const TemporalPlayback: React.FC<TemporalPlaybackProps> = ({
  currentEpoch,
  totalEpochs,
  onSelectEpoch,
  evidenceScore = 45,
  statusLabel = 'PERSISTENCE EVALUATING',
  isPlaying: controlledIsPlaying,
  onTogglePlay,
  onReset,
}) => {
  const [internalPlaying, setInternalPlaying] = useState(false)
  const [speed, setSpeed] = useState<number>(1000)

  const isPlaying = controlledIsPlaying !== undefined ? controlledIsPlaying : internalPlaying

  const togglePlay = () => {
    if (onTogglePlay) {
      onTogglePlay()
    } else {
      setInternalPlaying((prev) => !prev)
    }
  }

  const handleReset = () => {
    if (onReset) {
      onReset()
    } else {
      setInternalPlaying(false)
      onSelectEpoch(1)
    }
  }

  // Automatic epoch advancement when playing
  useEffect(() => {
    if (!isPlaying) return

    const timer = setInterval(() => {
      onSelectEpoch(currentEpoch >= totalEpochs ? 1 : currentEpoch + 1)
    }, speed)

    return () => clearInterval(timer)
  }, [isPlaying, currentEpoch, totalEpochs, speed, onSelectEpoch])

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '6px',
        padding: '0.85rem 1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      {/* Top Controller Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={handleReset}
            className="btn btn-secondary btn-sm"
            title="Reset to Epoch 1"
            style={{ padding: '0.35rem 0.5rem' }}
          >
            <RotateCcw size={13} />
          </button>

          <button
            onClick={() => onSelectEpoch(Math.max(1, currentEpoch - 1))}
            disabled={currentEpoch <= 1}
            className="btn btn-secondary btn-sm"
            title="Previous Epoch"
            style={{ padding: '0.35rem 0.5rem' }}
          >
            <SkipBack size={13} />
          </button>

          <button
            onClick={togglePlay}
            className={`btn btn-sm ${isPlaying ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.35rem 0.8rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            {isPlaying ? <Pause size={13} /> : <Play size={13} />}
            <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>
              {isPlaying ? 'Pause' : 'Play Timeline'}
            </span>
          </button>

          <button
            onClick={() => onSelectEpoch(Math.min(totalEpochs, currentEpoch + 1))}
            disabled={currentEpoch >= totalEpochs}
            className="btn btn-secondary btn-sm"
            title="Next Epoch"
            style={{ padding: '0.35rem 0.5rem' }}
          >
            <SkipForward size={13} />
          </button>

          {/* Speed selector */}
          <div style={{ display: 'flex', gap: '0.25rem', marginLeft: '0.5rem' }}>
            {[
              { label: '0.5x', ms: 1600 },
              { label: '1x', ms: 1000 },
              { label: '2x', ms: 500 },
            ].map((s) => (
              <button
                key={s.label}
                onClick={() => setSpeed(s.ms)}
                style={{
                  fontSize: '0.65rem',
                  fontFamily: 'var(--font-mono)',
                  padding: '0.15rem 0.35rem',
                  borderRadius: '3px',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: speed === s.ms ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                  color: speed === s.ms ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  cursor: 'pointer',
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Current State Chip */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            STATUS:
          </span>
          <span
            className="badge badge-cyan"
            style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', textTransform: 'uppercase' }}
          >
            {statusLabel}
          </span>
        </div>
      </div>

      {/* Epoch Stepper Navigation */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
        {Array.from({ length: totalEpochs }, (_, i) => i + 1).map((ep) => {
          const isCurrent = ep === currentEpoch
          const isPast = ep < currentEpoch
          return (
            <button
              key={ep}
              onClick={() => onSelectEpoch(ep)}
              style={{
                flex: 1,
                height: '24px',
                borderRadius: '4px',
                border: isCurrent
                  ? '1px solid var(--accent-cyan)'
                  : '1px solid var(--border-subtle)',
                backgroundColor: isCurrent
                  ? 'rgba(56, 189, 248, 0.2)'
                  : isPast
                  ? 'rgba(255, 255, 255, 0.05)'
                  : 'transparent',
                color: isCurrent ? 'var(--accent-cyan)' : isPast ? 'var(--text-secondary)' : 'var(--text-muted)',
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: isCurrent ? 700 : 400,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              title={`Jump to Epoch ${ep}`}
            >
              {ep}
            </button>
          )
        })}
      </div>

      {/* Cumulative Evidence Meter */}
      <div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.68rem',
            color: 'var(--text-muted)',
            marginBottom: '0.3rem',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <span>CUMULATIVE EVIDENCE WEIGHT</span>
          <span>{evidenceScore}%</span>
        </div>
        <div
          style={{
            height: '6px',
            backgroundColor: 'var(--bg-primary)',
            borderRadius: '3px',
            overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${Math.min(100, Math.max(0, evidenceScore))}%`,
              background: 'linear-gradient(90deg, #0284c7 0%, #38bdf8 100%)',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
        <div style={{ fontSize: '0.62rem', color: 'var(--text-dim)', marginTop: '0.2rem', fontStyle: 'italic' }}>
          Illustrative evidence accumulation — not a statistical probability
        </div>
      </div>
    </div>
  )
}
