export type StructureType =
  | 'BRIDGE'
  | 'DAM'
  | 'TUNNEL'
  | 'BUILDING'
  | 'RETAINING_STRUCTURE'
  | 'RETAINING_WALL'
  | 'EMBANKMENT'
  | 'PIPELINE'
  | 'OTHER'

export type MaterialType =
  | 'CONCRETE'
  | 'STEEL'
  | 'MASONRY'
  | 'EARTH'
  | 'ROCK'
  | 'COMPOSITE'
  | 'UNKNOWN'

export type CriticalityLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | 'UNKNOWN'

export type RiskCharacterizationState =
  | 'INSUFFICIENT_EVIDENCE'
  | 'BASELINE'
  | 'ENVIRONMENTAL_PATTERN'
  | 'MONITOR'
  | 'ELEVATED_ATTENTION'
  | 'HIGH_ATTENTION'

export type ConsensusCategory =
  | 'STRUCTURAL'
  | 'ENVIRONMENTAL'
  | 'ATMOSPHERIC'
  | 'LOW_QUALITY'
  | 'CONFLICTED'
  | 'INSUFFICIENT_EVIDENCE'
  | 'STABLE'

export type TemporalStatus =
  | 'INSUFFICIENT_HISTORY'
  | 'BASELINE'
  | 'PERSISTENT_LINEAR'
  | 'ACCELERATING'
  | 'ENVIRONMENTAL_PATTERN'
  | 'ATMOSPHERIC_EVENT'
  | 'CONFLICTED'

export interface CriticalZone {
  zone_id: string
  zone_name: string
  zone_type: string
  importance_weight: number
  notes?: string
}

export interface HistoricalBaseline {
  baseline_mean_mm: number
  baseline_std_mm: number
  baseline_min_mm?: number
  baseline_max_mm?: number
  baseline_period_days?: number
}

export interface Infrastructure {
  id: string
  name: string
  structure_type: StructureType
  material: MaterialType
  criticality: CriticalityLevel
  latitude: number
  longitude: number
  description?: string
  critical_zones?: CriticalZone[]
  historical_baseline?: HistoricalBaseline
  baseline?: HistoricalBaseline
  profile_version?: string
  created_at?: string
  observations_count?: number
  // Computed client-side display fields
  latest_displacement?: number
  latest_trend?: number
  evidence_state?: RiskCharacterizationState
  confidence?: number
  latest_observation_date?: string
}

export interface Observation {
  id: string
  infrastructure_id: string
  acquisition_timestamp: string
  epoch_date?: string
  deformation_mm: number
  displacement_vertical_mm?: number
  displacement_los_mm?: number
  los_displacement_mm?: number
  velocity_mm_per_year?: number
  coherence: number
  phase_quality?: number
  incidence_angle?: number
  look_angle?: number
  heading_angle?: number
  source?: string
  atmospheric_indicator?: string
  metadata?: Record<string, any>
}

export interface MLResult {
  predicted_class: string
  confidence: number
  probabilities: Record<string, number>
  entropy?: number
  model_version?: string
}

export interface PhysicsEvidence {
  classification: string
  is_physically_consistent?: boolean
  consistency_score?: number
  evidence_factors?: Record<string, any>
  evidence_strength?: number
}

export interface ConsensusAssessment {
  consensus_class: ConsensusCategory | string
  consensus_category?: ConsensusCategory | string
  consensus_confidence: number
  confidence?: number
  agreement_ratio?: number
  agreement_score: number
  disagreement_penalty: number
  flags?: string[]
  explanation?: string
}

export interface TemporalSummary {
  temporal_status: TemporalStatus
  status?: string
  trend_rate_mm_per_year?: number
  apparent_acceleration_mm_per_year2?: number
  acceleration_supported: boolean
  persistence_score?: number
  persistence_streak?: number
  coverage_duration_days?: number
}

export interface EnvironmentalDiscrimination {
  is_environmental: boolean
  temperature_correlation?: number
  seasonal_amplitude_mm?: number
  dominant_period_days?: number
}

export interface RiskCharacterization {
  characterization_state: RiskCharacterizationState
  evidence_state?: RiskCharacterizationState
  prototype_risk_index: number
  evidence_characterization_index?: number
  confidence: number
  analytical_confidence?: number
  explanation: string
  justification?: string
  supporting_factors?: string[]
  suppressing_factors?: string[]
  uncertainty_factors?: string[]
  disclaimer?: string
}

export interface ChronologyRecord {
  id?: string
  record_id?: string
  infrastructure_id?: string
  sequence_number?: number
  observation_id?: string
  analysis_result_id?: string
  analysis_state?: string
  record_index?: number
  payload?: Record<string, any>
  payload_summary?: Record<string, any>
  payload_hash: string
  previous_hash: string
  current_hash: string
  timestamp: string
}

export interface StageTimings {
  validation_ms: number
  normalization_ms: number
  ml_ms: number
  physics_ms: number
  consensus_ms: number
  temporal_ms: number
  characterization_ms: number
  chronology_ms: number
  total_ms: number
}

export interface PipelineResult {
  analysis_id: string
  observation_id: string
  infrastructure_id: string
  processing_status: string
  execution_timestamp: string
  normalized_observation?: {
    observation_id: string
    infrastructure_id: string
    acquisition_timestamp: string
    normalized_deformation_mm: number
    normalized_los_displacement_mm?: number
    coherence?: number
    phase_quality?: number
    incidence_angle?: number
    geometry_available: boolean
    normalization_flags: string[]
  }
  ml_result?: MLResult
  ml_classification?: MLResult
  physics_evidence: PhysicsEvidence
  consensus_assessment?: ConsensusAssessment
  consensus?: ConsensusAssessment
  temporal_summary?: TemporalSummary
  temporal_evidence?: TemporalSummary
  environmental_discrimination?: EnvironmentalDiscrimination
  risk_characterization: RiskCharacterization
  chronology_record: {
    record_id: string
    record_index: number
    current_hash: string
    previous_hash: string
    payload_hash: string
    timestamp: string
  }
  stage_timings: StageTimings
  system_versions: Record<string, string>
  idempotent_replay: boolean
}

export type ViewTab =
  | 'dashboard'
  | 'infrastructure'
  | 'detail'
  | 'temporal'
  | 'chronology'
  | 'demo'
  | 'about'

export interface DemoScenario {
  id: string
  name: string
  code: string
  structure_name: string
  structure_type: StructureType
  material: MaterialType
  criticality: CriticalityLevel
  description: string
  expected_state: RiskCharacterizationState
  expected_index: number
  displacements: number[]
  narrative: string
  validation_status?: string
  dataset_provenance?: string
}
