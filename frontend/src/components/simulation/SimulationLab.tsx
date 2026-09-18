import React, { useState } from 'react'
import {
  Sparkles,
  BookOpen,
  Camera,
  ArrowLeft,
} from 'lucide-react'
import { FacultyModeProvider, FacultyModeToggle, useFacultyMode } from './FacultyModeContext'
import { SimulationScenarioCard, type ScenarioCardData } from './SimulationScenarioCard'
import { SarInSarSimulation } from './SarInSarSimulation'
import { WaterResponseSimulation } from './WaterResponseSimulation'
import { SeasonalCycleSimulation } from './SeasonalCycleSimulation'
import { AtmosphericSimulation } from './AtmosphericSimulation'
import { StructuralDeformationSimulation } from './StructuralDeformationSimulation'
import { ConsensusConflictSimulation } from './ConsensusConflictSimulation'
import { EvidenceFusionDiagram } from './EvidenceFusionDiagram'
import { PatentFigureMode } from './PatentFigureMode'
import { GlossaryModal } from './GlossaryModal'
import { ThreeMinuteDemoModal } from './ThreeMinuteDemoModal'

const SCENARIO_CARDS: ScenarioCardData[] = [
  {
    id: 'module_01',
    moduleNum: 'MODULE 01',
    title: 'SAR / InSAR Fundamentals',
    plainQuestion: 'How does satellite radar measure millimeters without optical photos?',
    description: 'Explore microwave pulses, Line-Of-Sight (LOS) slant range, phase shift Δϕ, and geometric projection into true vertical deformation.',
    category: 'PHYSICS & GEOMETRY',
  },
  {
    id: 'module_02',
    moduleNum: 'MODULE 02',
    title: 'Environmental Water Response',
    plainQuestion: 'Why does heavy rain cause reversible ground settlement?',
    description: 'Simulate rainfall, soil pore-pressure saturation, and transient water loading. See how STRATA detects cyclic recovery and suppresses false alarms.',
    category: 'HYDROLOGY SAFEGUARD',
  },
  {
    id: 'module_03',
    moduleNum: 'MODULE 03',
    title: 'Seasonal Thermal Dynamics',
    plainQuestion: 'Why do summer heat and winter cold trigger false alarms?',
    description: 'Inspect 12-month thermal expansion cycles. Watch STRATA’s temporal engine identify zero crossings and suppress monotonic alarms.',
    category: 'SEASONAL PATTERNS',
  },
  {
    id: 'module_04',
    moduleNum: 'MODULE 04',
    title: 'Atmospheric Disturbance',
    plainQuestion: 'Can clouds and water vapor fake a bridge collapse signal?',
    description: 'See a concrete bridge remain completely static (0.0 mm) while passing water vapor creates a fake 14 mm spike that STRATA rejects.',
    category: 'ARTIFACT FILTERING',
  },
  {
    id: 'module_05',
    moduleNum: 'MODULE 05',
    title: 'Progressive Structural Deformation',
    plainQuestion: 'How does true structural damage emerge across multiple visits?',
    description: 'Step through 8 observation epochs under Stable, Monotonic, and Accelerating patterns with synchronized ML, Physics, and Consensus meters.',
    category: 'MULTI-EPOCH KINEMATICS',
  },
  {
    id: 'module_06',
    moduleNum: 'MODULE 06',
    title: 'Cross-Model Consensus & Conflict',
    plainQuestion: 'Why does STRATA lower confidence when AI and Physics disagree?',
    description: 'Split-screen analysis comparing statistical pattern recognition against kinematic laws. See how disagreement triggers an uncertainty penalty.',
    category: 'CONSENSUS FUSION',
  },
]

export const SimulationLabContent: React.FC = () => {
  const { facultyMode } = useFacultyMode()
  const [activeModuleId, setActiveModuleId] = useState<string | null>(null)
  const [isPatentMode, setIsPatentMode] = useState<boolean>(false)
  const [isGlossaryOpen, setIsGlossaryOpen] = useState<boolean>(false)
  const [isDemoWalkthroughOpen, setIsDemoWalkthroughOpen] = useState<boolean>(false)

  if (isPatentMode) {
    return <PatentFigureMode onExit={() => setIsPatentMode(false)} />
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Top Banner & Quick Actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
            <span className="badge badge-cyan">SIMULATION LAB</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              TECHNICAL EXPLAINABILITY &amp; PATENT VISUALIZATION
            </span>
          </div>
          <h1 style={{ fontSize: '1.7rem', margin: '0 0 0.35rem 0', color: 'var(--text-primary)' }}>
            STRATA Simulation &amp; Explainability Lab
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0, maxWidth: '820px' }}>
            {facultyMode
              ? 'Explore how satellites measure bridges, why weather creates false alarms, and how STRATA’s independent AI and physics engines collaborate without needing prior radar knowledge.'
              : 'Interactive scientific simulation environment demonstrating InSAR geometry, environmental recurrence discrimination, cross-model consensus confidence modulation, and multi-epoch temporal evidence accumulation.'}
          </p>
        </div>

        {/* Global Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          <FacultyModeToggle />

          <button
            onClick={() => setIsDemoWalkthroughOpen(true)}
            className="btn btn-secondary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <Sparkles size={14} color="var(--accent-cyan)" />
            <span>Explain in 3 Min</span>
          </button>

          <button
            onClick={() => setIsGlossaryOpen(true)}
            className="btn btn-secondary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <BookOpen size={14} />
            <span>Glossary</span>
          </button>

          <button
            onClick={() => setIsPatentMode(true)}
            className="btn btn-primary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <Camera size={14} />
            <span>Patent Figures</span>
          </button>
        </div>
      </div>

      {/* Persistent Scientific Boundary Disclaimer */}
      <div
        style={{
          backgroundColor: 'rgba(56, 189, 248, 0.03)',
          border: '1px solid rgba(56, 189, 248, 0.15)',
          borderRadius: '6px',
          padding: '0.65rem 1rem',
          fontSize: '0.75rem',
          color: 'var(--text-secondary)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <strong style={{ color: 'var(--accent-cyan)' }}>Conceptual Simulation Notice:</strong> Interactive simulations are explanatory visualizations demonstrating physical and analytical principles. They do not modify frozen STRATA v1.0.0 analytical pipeline calculations.
        </div>
        <span className="badge badge-secondary" style={{ fontSize: '0.62rem' }}>
          EDUCATIONAL AID
        </span>
      </div>

      {/* VIEW A: LANDING PAGE CARDS & ARCHITECTURE OVERVIEW */}
      {!activeModuleId && (
        <>
          {/* 6 Scenario Cards Grid */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.15rem', margin: 0, color: 'var(--text-primary)' }}>
                Interactive Physical &amp; Analytical Scenarios
              </h2>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                6 Interactive Educational Modules
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
                gap: '1.25rem',
              }}
            >
              {SCENARIO_CARDS.map((card) => (
                <SimulationScenarioCard
                  key={card.id}
                  card={card}
                  onSelect={(id) => setActiveModuleId(id)}
                />
              ))}
            </div>
          </div>

          {/* Interactive Evidence Fusion Diagram */}
          <EvidenceFusionDiagram />
        </>
      )}

      {/* VIEW B: ACTIVE MODULE DETAIL VIEW */}
      {activeModuleId && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Sub-navigation bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              onClick={() => setActiveModuleId(null)}
              className="btn btn-secondary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <ArrowLeft size={14} />
              <span>All Simulation Modules</span>
            </button>

            {/* Quick Switch Pills */}
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              {SCENARIO_CARDS.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveModuleId(c.id)}
                  className={`btn btn-sm ${activeModuleId === c.id ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ fontSize: '0.7rem', padding: '0.25rem 0.55rem' }}
                >
                  {c.moduleNum}
                </button>
              ))}
            </div>
          </div>

          {/* Active Module Container */}
          {activeModuleId === 'module_01' && <SarInSarSimulation />}
          {activeModuleId === 'module_02' && <WaterResponseSimulation />}
          {activeModuleId === 'module_03' && <SeasonalCycleSimulation />}
          {activeModuleId === 'module_04' && <AtmosphericSimulation />}
          {activeModuleId === 'module_05' && <StructuralDeformationSimulation />}
          {activeModuleId === 'module_06' && <ConsensusConflictSimulation />}
        </div>
      )}

      {/* Modals */}
      <GlossaryModal isOpen={isGlossaryOpen} onClose={() => setIsGlossaryOpen(false)} />
      <ThreeMinuteDemoModal isOpen={isDemoWalkthroughOpen} onClose={() => setIsDemoWalkthroughOpen(false)} />
    </div>
  )
}

export const SimulationLab: React.FC = () => {
  return (
    <FacultyModeProvider>
      <SimulationLabContent />
    </FacultyModeProvider>
  )
}
