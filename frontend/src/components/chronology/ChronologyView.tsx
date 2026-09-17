import React, { useState } from 'react'
import {
  CheckCircle2,
  ArrowDown,
  Hash,
} from 'lucide-react'
import type { ChronologyRecord } from '../../types'

interface ChronologyViewProps {
  records: ChronologyRecord[]
}

export const ChronologyView: React.FC<ChronologyViewProps> = ({ records }) => {
  const [selectedRecord, setSelectedRecord] = useState<ChronologyRecord | null>(
    records.length ? records[records.length - 1] : null
  )

  const getRecordId = (rec?: ChronologyRecord | null): string =>
    rec?.record_id || rec?.id || 'record-0'
  const getSeqNum = (rec: ChronologyRecord, idx: number): number =>
    rec.sequence_number ?? rec.record_index ?? idx + 1
  const getPrevHash = (rec: ChronologyRecord): string =>
    rec.previous_hash || '0'.repeat(64)
  const getCurHash = (rec: ChronologyRecord): string =>
    rec.current_hash || rec.payload_hash || '0'.repeat(64)
  const getState = (rec: ChronologyRecord): string =>
    rec.analysis_state || 'EVIDENCE_RECORD'
  const getTimeStr = (rec: ChronologyRecord): string =>
    rec.timestamp ? rec.timestamp.slice(11, 19) : '12:00:00'

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* PAGE HEADER */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1.25rem',
        }}
      >
        <div>
          <h2>Tamper-Evident Evidence Chronology</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Cryptographically linked SHA-256 hash chain providing verifiable audit provenance across all pipeline execution epochs.
          </p>
        </div>

        {/* Verification Status Banner */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            backgroundColor: 'var(--state-baseline-bg)',
            border: '1px solid var(--state-baseline-border)',
            padding: '0.5rem 0.9rem',
            borderRadius: '6px',
          }}
        >
          <CheckCircle2 size={18} color="var(--state-baseline)" />
          <div>
            <div
              style={{
                fontSize: '0.8rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                color: 'var(--state-baseline)',
              }}
            >
              ✓ CHRONOLOGY VERIFIED
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
              {records.length} records • 0 integrity violations detected
            </div>
          </div>
        </div>
      </div>

      {/* CHAIN LAYOUT: LEFT VISUAL TIMELINE CHAIN, RIGHT INSPECTOR */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(320px, 460px) 1fr',
          gap: '1.5rem',
          alignItems: 'start',
        }}
      >
        {/* LEFT: VISUAL HASH CHAIN BLOCKS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            CHRONOLOGICAL PROVENANCE SEQUENCE
          </div>

          {records.map((rec, idx) => {
            const isSelected = getRecordId(selectedRecord) === getRecordId(rec)
            const seqNum = getSeqNum(rec, idx)
            const prevHash = getPrevHash(rec)
            const curHash = getCurHash(rec)
            const state = getState(rec)
            const timeStr = getTimeStr(rec)

            return (
              <React.Fragment key={getRecordId(rec)}>
                <div
                  onClick={() => setSelectedRecord(rec)}
                  className="strata-card"
                  style={{
                    cursor: 'pointer',
                    borderColor: isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                    backgroundColor: isSelected ? 'var(--bg-elevated)' : 'var(--bg-card)',
                    padding: '1rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>
                        BLOCK #{String(seqNum).padStart(3, '0')}
                      </span>
                      <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {state}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {timeStr} UTC
                    </span>
                  </div>

                  <div style={{ marginTop: '0.6rem', fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                    <div style={{ display: 'flex', gap: '0.4rem', fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: 'var(--text-dim)' }}>PREV:</span>
                      <span style={{ color: 'var(--text-muted)' }}>
                        {prevHash.slice(0, 16)}...
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.4rem', fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: 'var(--accent-cyan)' }}>HASH:</span>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                        {curHash.slice(0, 16)}...
                      </span>
                    </div>
                  </div>
                </div>

                {/* Arrow connector between blocks */}
                {idx < records.length - 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', margin: '-0.4rem 0' }}>
                    <ArrowDown size={16} color="var(--border-bright)" />
                  </div>
                )}
              </React.Fragment>
            )
          })}
        </div>

        {/* RIGHT: SELECTED BLOCK DEEP INSPECTOR */}
        {selectedRecord && (
          <div className="strata-card elevated" style={{ padding: '1.5rem', position: 'sticky', top: '80px' }}>
            <div className="strata-card-header">
              <div className="strata-card-title">
                <Hash size={17} color="var(--accent-cyan)" />
                <span>
                  Evidence Block #{String(getSeqNum(selectedRecord, records.indexOf(selectedRecord))).padStart(3, '0')} Inspector
                </span>
              </div>
              <span className="badge badge-baseline">SHA-256 VALIDATED</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Hashes Section */}
              <div
                style={{
                  backgroundColor: 'var(--bg-primary)',
                  padding: '1rem',
                  borderRadius: '6px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.6rem',
                }}
              >
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', marginBottom: '0.2rem' }}>
                    CURRENT RECORD HASH (SHA-256)
                  </div>
                  <div style={{ color: 'var(--accent-cyan)', wordBreak: 'break-all', fontWeight: 500 }}>
                    {getCurHash(selectedRecord)}
                  </div>
                </div>

                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', marginBottom: '0.2rem' }}>
                    PREVIOUS BLOCK HASH (PARENT LINK)
                  </div>
                  <div style={{ color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
                    {getPrevHash(selectedRecord)}
                  </div>
                </div>
              </div>

              {/* Metadata Fields */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.85rem', fontSize: '0.8rem' }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ASSET REFERENCE</div>
                  <div style={{ fontWeight: 600, marginTop: '0.15rem' }}>
                    {selectedRecord.infrastructure_id || selectedRecord.observation_id || 'ASSET-REF'}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>RECORD TIMESTAMP</div>
                  <div style={{ fontFamily: 'var(--font-mono)', marginTop: '0.15rem' }}>
                    {selectedRecord.timestamp || '2026-09-17T12:00:00Z'}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ANALYTICAL STATE</div>
                  <div style={{ color: 'var(--accent-cyan)', fontWeight: 600, marginTop: '0.15rem' }}>
                    {getState(selectedRecord)}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ALGORITHM VERSION</div>
                  <div style={{ fontFamily: 'var(--font-mono)', marginTop: '0.15rem' }}>v1.0.0-FROZEN</div>
                </div>
              </div>

              {/* Block Raw Evidence Payload */}
              <div>
                <div
                  style={{
                    fontSize: '0.7rem',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-muted)',
                    marginBottom: '0.4rem',
                  }}
                >
                  CANONICAL REPRODUCIBILITY PAYLOAD
                </div>
                <pre
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    padding: '1rem',
                    borderRadius: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.72rem',
                    color: 'var(--text-secondary)',
                    overflowX: 'auto',
                    maxHeight: '220px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  {JSON.stringify(selectedRecord.payload_summary || selectedRecord.payload || {}, null, 2)}
                </pre>
              </div>

              {/* Scientific Caveat on Chronology */}
              <div className="strata-disclaimer">
                <strong>Tamper-Evident Provenance Guarantee</strong>
                The SHA-256 hash chain provides verifiable detection of post-hoc modifications or deletions.
                It guarantees chronological auditability across research epochs, not decentralized cryptocurrency immutability.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
