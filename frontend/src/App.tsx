import React, { useState, useEffect } from 'react'
import { Shell } from './components/layout/Shell'
import { DashboardView } from './components/dashboard/DashboardView'
import { InfrastructureTable } from './components/infrastructure/InfrastructureTable'
import { InfrastructureDetailView } from './components/detail/InfrastructureDetailView'
import { ChronologyView } from './components/chronology/ChronologyView'
import { DemoModeView } from './components/demo/DemoModeView'
import { PipelineExecutionModal } from './components/analysis/PipelineExecutionModal'
import { AboutModal } from './components/about/AboutModal'

import type {
  Infrastructure,
  Observation,
  PipelineResult,
  ChronologyRecord,
  ViewTab,
  DemoScenario,
} from './types'

import {
  fetchInfrastructures,
  fetchObservations,
  fetchChronologyRecords,
  runFullPipeline,
} from './services/api'

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<ViewTab>('dashboard')
  const [infrastructures, setInfrastructures] = useState<Infrastructure[]>([])
  const [selectedInfrastructure, setSelectedInfrastructure] = useState<Infrastructure | null>(null)
  const [observations, setObservations] = useState<Observation[]>([])
  const [chronologyRecords, setChronologyRecords] = useState<ChronologyRecord[]>([])
  const [resultsMap, setResultsMap] = useState<Record<string, PipelineResult>>({})

  // Modals & Mode
  const [isAboutOpen, setIsAboutOpen] = useState(false)
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false)
  const [targetAnalysisInfra, setTargetAnalysisInfra] = useState<Infrastructure | null>(null)
  const [isDemoMode, setIsDemoMode] = useState(false)

  // Initial Load
  useEffect(() => {
    fetchInfrastructures().then((infras) => {
      setInfrastructures(infras)
      if (infras.length > 0) {
        setSelectedInfrastructure(infras[0])
        fetchObservations(infras[0].id).then(setObservations)
      }
    })

    fetchChronologyRecords().then(setChronologyRecords)
  }, [])

  // Update observations when selected asset changes
  const handleSelectInfrastructure = (infra: Infrastructure) => {
    setSelectedInfrastructure(infra)
    fetchObservations(infra.id).then(setObservations)
    setCurrentTab('detail')
  }

  // Trigger pipeline analysis modal
  const handleOpenPipeline = (infraId?: string) => {
    const target = infraId
      ? infrastructures.find((i) => i.id === infraId) || selectedInfrastructure
      : selectedInfrastructure || infrastructures[0]

    setTargetAnalysisInfra(target || null)
    setIsAnalysisOpen(true)
  }

  // Handle pipeline completion
  const handlePipelineComplete = (result: PipelineResult) => {
    if (targetAnalysisInfra) {
      setResultsMap((prev) => ({
        ...prev,
        [targetAnalysisInfra.id]: result,
      }))
      fetchChronologyRecords().then(setChronologyRecords)
      setSelectedInfrastructure(targetAnalysisInfra)
      fetchObservations(targetAnalysisInfra.id).then(setObservations)
      setCurrentTab('detail')
    }
  }

  // Handle Inspect Scenario from Demo Mode
  const handleSelectScenarioForInspection = (scen: DemoScenario) => {
    // Find matching or create proxy asset
    let matching = infrastructures.find(
      (i) => i.structure_type === scen.structure_type && i.criticality === scen.criticality
    )
    if (!matching && infrastructures.length > 0) {
      matching = infrastructures[0]
    }

    if (matching) {
      handleSelectInfrastructure(matching)
    }
  }

  return (
    <Shell
      currentTab={currentTab}
      onSelectTab={(tab) => {
        if (tab === 'demo') {
          setIsDemoMode(true)
          setCurrentTab('demo')
        } else {
          setIsDemoMode(false)
          setCurrentTab(tab)
        }
      }}
      onOpenAbout={() => setIsAboutOpen(true)}
      onOpenAnalysis={() => handleOpenPipeline()}
      onToggleDemo={() => {
        setIsDemoMode((prev) => !prev)
        setCurrentTab((prev) => (prev === 'demo' ? 'dashboard' : 'demo'))
      }}
      isDemoMode={isDemoMode || currentTab === 'demo'}
    >
      {/* 1. DASHBOARD VIEW */}
      {currentTab === 'dashboard' && (
        <DashboardView
          infrastructures={infrastructures}
          onSelectInfrastructure={handleSelectInfrastructure}
          onRunPipeline={handleOpenPipeline}
          onStartDemo={() => {
            setIsDemoMode(true)
            setCurrentTab('demo')
          }}
          resultsMap={resultsMap}
        />
      )}

      {/* 2. INFRASTRUCTURE ASSETS TABLE */}
      {currentTab === 'infrastructure' && (
        <InfrastructureTable
          infrastructures={infrastructures}
          resultsMap={resultsMap}
          onSelectInfrastructure={handleSelectInfrastructure}
          onRunPipeline={handleOpenPipeline}
        />
      )}

      {/* 3. CENTERPIECE INFRASTRUCTURE DETAIL VIEW */}
      {currentTab === 'detail' && selectedInfrastructure && (
        <InfrastructureDetailView
          infrastructure={selectedInfrastructure}
          pipelineResult={resultsMap[selectedInfrastructure.id]}
          observations={observations}
          onBack={() => setCurrentTab('infrastructure')}
          onRunPipeline={handleOpenPipeline}
        />
      )}

      {/* 4. TEMPORAL HISTORY (DIRECT TIMELINE AUDIT) */}
      {currentTab === 'temporal' && selectedInfrastructure && (
        <InfrastructureDetailView
          infrastructure={selectedInfrastructure}
          pipelineResult={resultsMap[selectedInfrastructure.id]}
          observations={observations}
          onBack={() => setCurrentTab('dashboard')}
          onRunPipeline={handleOpenPipeline}
        />
      )}

      {/* 5. EVIDENCE CHRONOLOGY CHAIN */}
      {currentTab === 'chronology' && (
        <ChronologyView records={chronologyRecords} />
      )}

      {/* 6. CURATED PRESENTATION DEMO MODE */}
      {currentTab === 'demo' && (
        <DemoModeView
          onSelectScenarioForInspection={handleSelectScenarioForInspection}
        />
      )}

      {/* PIPELINE EXECUTION MODAL (9-STAGE ANIMATED) */}
      <PipelineExecutionModal
        isOpen={isAnalysisOpen}
        infrastructure={targetAnalysisInfra}
        onClose={() => setIsAnalysisOpen(false)}
        onComplete={handlePipelineComplete}
        executePipeline={runFullPipeline}
      />

      {/* ABOUT / SCIENTIFIC METHODOLOGY MODAL */}
      <AboutModal
        isOpen={isAboutOpen}
        onClose={() => setIsAboutOpen(false)}
      />
    </Shell>
  )
}

export default App
