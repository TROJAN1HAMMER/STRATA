import React, { createContext, useContext, useState, useMemo } from 'react'

interface TermDefinition {
  plain: string
  technical: string
  analogy: string
}

const DICTIONARY: Record<string, TermDefinition> = {
  'los_deformation': {
    plain: "Movement measured along the satellite's line of sight",
    technical: "Line-Of-Sight (LOS) scalar displacement projected onto the radar antenna vector",
    analogy: "Like measuring whether an object is getting closer or further from a flashlight beam",
  },
  'temporal_recurrence': {
    plain: "A pattern that repeatedly returns over time (e.g. seasonal warming/cooling)",
    technical: "Periodic sinusoidal phase variation correlated with annual or cyclic environmental forcing",
    analogy: "Like a bridge that gently sways in summer and contracts in winter without being damaged",
  },
  'consensus_penalty': {
    plain: "The system lowers confidence when its independent analyses disagree",
    technical: "Cross-model confidence modulation where divergent interpretations trigger an uncertainty penalty",
    analogy: "Like two expert doctors disagreeing on an X-ray; instead of guessing, they order monitoring",
  },
  'atmospheric_contamination': {
    plain: "Radar signal distortion caused by moisture/clouds in the atmosphere",
    technical: "Tropospheric water-vapor phase delay causing apparent non-structural displacement artifacts",
    analogy: "Like looking at a pool coin through rippling water; the coin looks like it moves, but it is still",
  },
  'coherence': {
    plain: "Radar reflection clarity and measurement reliability",
    technical: "Interferometric coherence γ (0.0 to 1.0) quantifying phase stability across radar epochs",
    analogy: "Like optical camera focus: high coherence is a sharp photo, low coherence is a blurry photo",
  },
  'baseline_guard': {
    plain: "Safety check ensuring normal small vibrations are not mistaken for damage",
    technical: "Historical noise envelope guard requiring cumulative displacement to exceed ±1σ to ±2σ baseline",
    analogy: "Checking whether a sound is just normal traffic rumble or an actual crack",
  },
  'evidence_index': {
    plain: "Diagnostic rating (0-100) reflecting evidence strength for structural attention",
    technical: "Evidence Characterization Index: multi-factorial weighted score of kinematics, quality, and context",
    analogy: "A doctor's priority triage index, NOT a failure forecast or remaining-lifespan calculation",
  },
  'hash_chronology': {
    plain: "Tamper-evident digital audit log where records are locked with cryptographic seals",
    technical: "SHA-256 canonical hash chain linking consecutive analytical records for provenance audit",
    analogy: "Like wax seals on historical letters: if any past record is altered, the chain seal breaks",
  },
}

interface FacultyModeContextType {
  facultyMode: boolean
  setFacultyMode: (enabled: boolean) => void
  toggleFacultyMode: () => void
  translate: (key: string, defaultText: string) => string
  getTermDetails: (key: string) => TermDefinition | undefined
}

const FacultyModeContext = createContext<FacultyModeContextType>({
  facultyMode: false,
  setFacultyMode: () => {},
  toggleFacultyMode: () => {},
  translate: (_key, defaultText) => defaultText,
  getTermDetails: () => undefined,
})

export const FacultyModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [facultyMode, setFacultyMode] = useState(false)

  const value = useMemo(
    () => ({
      facultyMode,
      setFacultyMode,
      toggleFacultyMode: () => setFacultyMode((prev) => !prev),
      translate: (key: string, defaultText: string) => {
        if (!facultyMode) return defaultText
        return DICTIONARY[key]?.plain || defaultText
      },
      getTermDetails: (key: string) => DICTIONARY[key],
    }),
    [facultyMode]
  )

  return <FacultyModeContext.Provider value={value}>{children}</FacultyModeContext.Provider>
}

export const useFacultyMode = () => useContext(FacultyModeContext)

export const FacultyModeToggle: React.FC = () => {
  const { facultyMode, toggleFacultyMode } = useFacultyMode()

  return (
    <button
      onClick={toggleFacultyMode}
      className={`btn btn-sm ${facultyMode ? 'btn-primary' : 'btn-secondary'}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.45rem',
        padding: '0.3rem 0.65rem',
        borderRadius: '5px',
        fontSize: '0.75rem',
        fontFamily: 'var(--font-sans)',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        boxShadow: facultyMode ? '0 0 10px rgba(56, 189, 248, 0.35)' : 'none',
        borderColor: facultyMode ? 'var(--accent-cyan)' : 'var(--border-medium)',
      }}
      title="Toggle between Academic/Faculty plain-language explanations and scientific terminology"
    >
      <span
        style={{
          width: '7px',
          height: '7px',
          borderRadius: '50%',
          backgroundColor: facultyMode ? 'var(--accent-cyan)' : 'var(--text-muted)',
          display: 'inline-block',
        }}
      />
      <span style={{ fontWeight: 600 }}>
        {facultyMode ? 'Faculty Mode (Plain English)' : 'Technical Mode (InSAR Scientific)'}
      </span>
    </button>
  )
}
