/**
 * Typed API Layer (SL-036).
 * Single HTTP Client wrapper grouping Auth, Documents, Analysis, Chat, Advisor,
 * Services, and Yojana endpoints.
 */

import { apiClient } from './api'
import type { UploadedDocument, UploadResponse } from '../types'

export const authApi = {
  login: async (formData: FormData) => {
    const res = await apiClient.post('/auth/login', formData)
    return res.data
  },
  register: async (payload: { name: string; email: string; password: string }) => {
    const res = await apiClient.post('/auth/register', payload)
    return res.data
  },
  logout: async () => {
    const res = await apiClient.post('/auth/logout')
    return res.data
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me')
    return res.data
  },
}

export const documentApi = {
  upload: async (file: File, onProgress?: (pct: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiClient.post<UploadResponse>('/upload', formData, {
      onUploadProgress: (evt) => {
        if (onProgress) {
          const pct = Math.round((evt.loaded * 100) / (evt.total || 1))
          onProgress(pct)
        }
      },
    })
    return res.data.document
  },
  getHistory: async () => {
    const res = await apiClient.get<{ documents: UploadedDocument[] }>('/upload/history')
    return res.data.documents
  },
  getById: async (documentId: string) => {
    const res = await apiClient.get<UploadedDocument>(`/upload/${documentId}`)
    return res.data
  },
  delete: async (documentId: string) => {
    const res = await apiClient.delete(`/upload/${documentId}`)
    return res.data
  },

}

export const analysisApi = {
  analyze: async (documentId: string, forceReanalyze = false) => {
    const res = await apiClient.post('/analyze', {
      document_id: documentId,
      force_reanalyze: forceReanalyze,
    })
    return res.data
  },
  getStatus: async (documentId: string) => {
    const res = await apiClient.get(`/analyze/${documentId}/status`)
    return res.data
  },
  clearCache: async (documentId: string) => {
    const res = await apiClient.delete(`/analyze/${documentId}/cache`)
    return res.data
  },
}

export const chatApi = {
  sendMessage: async (documentId: string, question: string) => {
    const res = await apiClient.post('/chat', {
      document_id: documentId,
      question,
    })
    return res.data
  },
  getHistory: async (documentId: string) => {
    const res = await apiClient.get(`/chat/history/${documentId}`)
    return res.data
  },
}

export const advisorApi = {
  ask: async (message: string) => {
    const res = await apiClient.post('/advisor', { message })
    return res.data
  },
}

export const yojanaApi = {
  getSchemes: async (category?: string) => {
    const res = await apiClient.get('/yojana/schemes', { params: { category } })
    return res.data
  },
  matchEligibility: async (profile: any) => {
    const res = await apiClient.post('/yojana/match', profile)
    return res.data
  },
  getBlogs: async () => {
    const res = await apiClient.get('/yojana/blogs')
    return res.data
  },
}
