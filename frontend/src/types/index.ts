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
  risk_level: RiskLevel
  risk_score: number        // 1–10
  risk_reason: string       // why it's risky
  clause_type: string       // e.g. "Termination", "Rent", "Notice Period"
}

export interface DocumentSummary {
  document_type: string
  parties: string[]
  key_dates: { label: string; date: string }[]
  overall_risk: RiskLevel
  risk_summary: string
  total_clauses: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
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
