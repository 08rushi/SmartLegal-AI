// ─── Auth ───────────────────────────────────────────────────────────────────

export interface User {
  id: string
  email: string
  name: string
  created_at: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null
}

// ─── Documents ──────────────────────────────────────────────────────────────

export type DocumentStatus = 'idle' | 'uploading' | 'processing' | 'ready' | 'error'

export interface UploadedDocument {
  id: string
  filename: string
  file_url: string
  file_size: number
  document_type: string   // e.g. "Rental Agreement", "Employment Contract"
  uploaded_at: string
  status: DocumentStatus
  analyzed?: boolean       // true once a saved analysis exists for this document
}

export interface DocumentState {
  current: UploadedDocument | null
  comparison: UploadedDocument | null   // for comparison mode
  history: UploadedDocument[]
  uploadProgress: number
  status: DocumentStatus
  error: string | null
}

// ─── Analysis ───────────────────────────────────────────────────────────────

export type RiskLevel = 'low' | 'medium' | 'high'

export interface Clause {
  id: string
  title: string
  original_text: string
  plain_english: string
  plain_hindi: string
  plain_source?: string       // explanation in the document's own language
  source_language?: string    // e.g. "Marathi", "Telugu", "English"
  risk_level: RiskLevel
  risk_score: number        // 1–10
  risk_reason: string       // why it's risky
  clause_type: string       // e.g. "Termination", "Rent", "Notice Period"
  clause_number?: string
  page_number?: number
  beneficial_to_user?: boolean
}

export interface DocumentSummary {
  document_type: string
  language?: string           // detected document language, e.g. "Marathi"
  parties: string[]
  key_dates: { label: string; date: string }[]
  overall_risk: RiskLevel
  risk_summary: string
  total_clauses: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  high_risk_clauses?: string[]
  beneficial_clauses?: string[]
  your_obligations?: string[]
  other_party_rights?: string[]
}

export interface AnalysisResult {
  document_id: string
  summary: DocumentSummary
  clauses: Clause[]
  analyzed_at: string
}

export interface AnalysisState {
  result: AnalysisResult | null
  comparisonResult: AnalysisResult | null
  isLoading: boolean
  error: string | null
}

// ─── Insights: "What happens if I sign?" + Negotiation helper ────────────────

export interface ConsequenceScenario {
  id: string
  category: string
  title: string
  trigger: string
  outcome: string
  worst_case: string
  severity: RiskLevel
  likelihood: RiskLevel
  plain_english: string
  plain_hindi: string
  related_clause: string
}

export interface ConsequenceResult {
  overview: string
  overall_exposure: RiskLevel
  scenarios: ConsequenceScenario[]
}

export interface NegotiationItem {
  id: string
  clause_title: string
  risk_level: RiskLevel
  current_problem: string
  suggested_change: string
  counter_text: string
  talking_point: string
  plain_hindi: string
}

export interface NegotiationResult {
  summary: string
  items: NegotiationItem[]
}

export type InsightStatus = 'idle' | 'loading' | 'ready' | 'error'

export interface InsightsState {
  documentId: string | null
  consequences: ConsequenceResult | null
  negotiation: NegotiationResult | null
  consequencesStatus: InsightStatus
  negotiationStatus: InsightStatus
  error: string | null
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export type MessageRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: string
  cited_clause_ids?: string[]   // which clauses the AI referenced
}

export interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  document_id: string | null
}

// ─── API responses ───────────────────────────────────────────────────────────

export interface ApiError {
  detail: string
  status_code: number
}

export interface UploadResponse {
  document: UploadedDocument
  message: string
}

export interface AnalyzeResponse {
  analysis: AnalysisResult
}

export interface ChatResponse {
  message: ChatMessage
}

export interface LoginResponse {
  user: User
  access_token: string
  token_type: string
}

// ─── Legal ID Hub ───────────────────────────────────────────────────────────

export interface LegalIdType {
  key: string
  display_name: string
  icon: string
  authority: string
  official_portal: string
}

export interface LegalIdService {
  service: string
  description?: string
  where: string
  documents_required: string[]
  fee: string
  timeline: string
  official_link: string
}

export interface LegalIdGuidance {
  key: string
  display_name: string
  icon: string
  authority: string
  governing_law: string
  official_portal: string
  overview?: string
  services: LegalIdService[]
  faqs: { q: string; a: string }[]
  common_issues?: string[]
  legal_protections: string[]
  disclaimer: string
}

export interface IdApplication {
  id: string
  id_type: string
  service: string
  status: 'in_progress' | 'submitted' | 'received' | 'completed'
  notes: string
  created_at: string
  updated_at: string
}

export interface ChecklistItem {
  id: string
  item_text: string
  is_done: boolean
  updated_at: string
}

/** Shape sent to the checklist save endpoints (id optional for new items). */
export interface ChecklistSaveItem {
  id?: string
  item_text: string
  is_done: boolean
}

export interface LegalIdState {
  idTypes: LegalIdType[]
  currentGuidance: LegalIdGuidance | null
  applications: IdApplication[]
  currentChecklist: ChecklistItem[]
  isLoading: boolean
  error: string | null
}

// ─── Property Hub ───────────────────────────────────────────────────────────

export interface PropertyType {
  key: string
  display_name: string
  icon: string
  authority: string
  official_portal: string
}

export interface PropertyService {
  service: string
  description?: string
  where: string
  documents_required: string[]
  fee: string
  timeline: string
  official_link: string
}

export interface PropertyGuidance {
  key: string
  display_name: string
  icon: string
  authority: string
  governing_law: string
  official_portal: string
  overview?: string
  services: PropertyService[]
  faqs: { q: string; a: string }[]
  common_issues?: string[]
  legal_protections: string[]
  disclaimer: string
}

export interface PropertyApplication {
  id: string
  property_type: string
  service: string
  status: 'in_progress' | 'submitted' | 'received' | 'completed'
  notes: string
  created_at: string
  updated_at: string
}

export interface PropertyState {
  propertyTypes: PropertyType[]
  currentGuidance: PropertyGuidance | null
  applications: PropertyApplication[]
  currentChecklist: ChecklistItem[]
  isLoading: boolean
  error: string | null
}

// ─── Business License Hub ────────────────────────────────────────────────────

export interface BusinessType {
  key: string
  display_name: string
  icon: string
  authority: string
  official_portal: string
}

export interface BusinessService {
  service: string
  description?: string
  where: string
  documents_required: string[]
  fee: string
  timeline: string
  official_link: string
}

export interface BusinessGuidance {
  key: string
  display_name: string
  icon: string
  authority: string
  governing_law: string
  official_portal: string
  overview?: string
  services: BusinessService[]
  faqs: { q: string; a: string }[]
  common_issues?: string[]
  legal_protections: string[]
  disclaimer: string
}

export interface BusinessApplication {
  id: string
  business_type: string
  service: string
  status: 'in_progress' | 'submitted' | 'received' | 'completed'
  notes: string
  created_at: string
  updated_at: string
}

export interface BusinessState {
  businessTypes: BusinessType[]
  currentGuidance: BusinessGuidance | null
  applications: BusinessApplication[]
  currentChecklist: ChecklistItem[]
  isLoading: boolean
  error: string | null
}

// ─── Jan-Yojana Central & State Schemes ────────────────────────────────────────

export interface YojanaScheme {
  id: string
  scheme_code: string
  title: string
  government_level: 'central' | 'state'
  state_name: string
  category: string
  summary_english: string
  summary_hindi: string
  benefits: string[]
  eligibility: {
    occupations?: string[]
    income_max?: number
    min_age?: number
    max_age?: number
    gender?: string
    states?: string[]
    requires_landholding?: boolean
    max_land_acres?: number
    requires_bpl_or_secc?: boolean
  }
  required_docs: string[]
  official_portal_url: string
  last_updated_at: string
}

export interface YojanaMatchProfile {
  state: string
  district?: string
  age: number
  gender: 'male' | 'female' | 'all'
  occupation: string
  annual_income: number
  category: string
  land_holding_acres: number
  is_pregnant_or_lactating: boolean
  is_disabled: boolean
}

export interface YojanaMatchResult {
  scheme: YojanaScheme
  match_score: number
  status: 'eligible' | 'partial' | 'ineligible'
  gap_analysis: string[]
  benefits: string[]
  required_docs: string[]
  official_portal_url: string
}

export interface YojanaBlog {
  id: string
  scheme_id?: string
  title: string
  slug: string
  summary: string
  content_markdown: string
  image_url: string
  official_links: { label: string; url: string }[]
  published_at: string
}

export interface YojanaState {
  schemes: YojanaScheme[]
  matchedResults: YojanaMatchResult[]
  currentScheme: YojanaScheme | null
  blogs: YojanaBlog[]
  currentBlog: YojanaBlog | null
  profile: YojanaMatchProfile
  isLoading: boolean
  error: string | null
}

