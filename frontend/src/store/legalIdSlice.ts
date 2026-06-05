import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { LegalIdState, LegalIdType, LegalIdGuidance, IdApplication, ChecklistItem } from '../types'
import { apiClient } from '../services/api'

// ─── Async Thunks ─────────────────────────────────────────────────────────

export const fetchIdTypes = createAsyncThunk(
  'legalId/fetchTypes',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ id_types: LegalIdType[] }>('/legal-id')
      return response.data.id_types
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load ID types')
    }
  }
)

export const fetchIdGuidance = createAsyncThunk(
  'legalId/fetchGuidance',
  async (idType: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ guidance: LegalIdGuidance }>(`/legal-id/${idType}`)
      return response.data.guidance
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load guidance')
    }
  }
)

export const createApplication = createAsyncThunk(
  'legalId/createApplication',
  async (data: { id_type: string; service: string; notes?: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<IdApplication>('/legal-id/applications', data)
      return response.data
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to create application')
    }
  }
)

export const fetchApplications = createAsyncThunk(
  'legalId/fetchApplications',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ applications: IdApplication[] }>('/legal-id/applications')
      return response.data.applications
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load applications')
    }
  }
)

export const updateApplication = createAsyncThunk(
  'legalId/updateApplication',
  async (data: { app_id: string; status?: string; notes?: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.patch<IdApplication>(`/legal-id/applications/${data.app_id}`, {
        status: data.status,
        notes: data.notes,
      })
      return response.data
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to update application')
    }
  }
)

export const deleteApplication = createAsyncThunk(
  'legalId/deleteApplication',
  async (app_id: string, { rejectWithValue }) => {
    try {
      await apiClient.delete(`/legal-id/applications/${app_id}`)
      return app_id
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete application')
    }
  }
)

export const fetchChecklist = createAsyncThunk(
  'legalId/fetchChecklist',
  async (app_id: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ items: ChecklistItem[] }>(`/legal-id/applications/${app_id}/checklist`)
      return response.data.items
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load checklist')
    }
  }
)

export const saveChecklist = createAsyncThunk(
  'legalId/saveChecklist',
  async (data: { app_id: string; items: { item_text: string; is_done: boolean }[] }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<{ items: ChecklistItem[] }>(`/legal-id/applications/${data.app_id}/checklist`, {
        items: data.items,
      })
      return response.data.items
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to save checklist')
    }
  }
)

// ─── Initial State ────────────────────────────────────────────────────────

const initialState: LegalIdState = {
  idTypes: [],
  currentGuidance: null,
  applications: [],
  currentChecklist: [],
  isLoading: false,
  error: null,
}

// ─── Slice ────────────────────────────────────────────────────────────────

const legalIdSlice = createSlice({
  name: 'legalId',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null
    },
    clearCurrentGuidance(state) {
      state.currentGuidance = null
    },
    clearCurrentChecklist(state) {
      state.currentChecklist = []
    },
  },
  extraReducers: (builder) => {
    // fetchIdTypes
    builder
      .addCase(fetchIdTypes.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchIdTypes.fulfilled, (state, action: PayloadAction<LegalIdType[]>) => {
        state.isLoading = false
        state.idTypes = action.payload
      })
      .addCase(fetchIdTypes.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // fetchIdGuidance
    builder
      .addCase(fetchIdGuidance.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchIdGuidance.fulfilled, (state, action: PayloadAction<LegalIdGuidance>) => {
        state.isLoading = false
        state.currentGuidance = action.payload
      })
      .addCase(fetchIdGuidance.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // createApplication
    builder
      .addCase(createApplication.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(createApplication.fulfilled, (state, action: PayloadAction<IdApplication>) => {
        state.isLoading = false
        state.applications.push(action.payload)
      })
      .addCase(createApplication.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // fetchApplications
    builder
      .addCase(fetchApplications.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchApplications.fulfilled, (state, action: PayloadAction<IdApplication[]>) => {
        state.isLoading = false
        state.applications = action.payload
      })
      .addCase(fetchApplications.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // updateApplication
    builder
      .addCase(updateApplication.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(updateApplication.fulfilled, (state, action: PayloadAction<IdApplication>) => {
        state.isLoading = false
        const index = state.applications.findIndex((app) => app.id === action.payload.id)
        if (index !== -1) {
          state.applications[index] = action.payload
        }
      })
      .addCase(updateApplication.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // deleteApplication
    builder
      .addCase(deleteApplication.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(deleteApplication.fulfilled, (state, action: PayloadAction<string>) => {
        state.isLoading = false
        state.applications = state.applications.filter((app) => app.id !== action.payload)
      })
      .addCase(deleteApplication.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // fetchChecklist
    builder
      .addCase(fetchChecklist.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchChecklist.fulfilled, (state, action: PayloadAction<ChecklistItem[]>) => {
        state.isLoading = false
        state.currentChecklist = action.payload
      })
      .addCase(fetchChecklist.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // saveChecklist
    builder
      .addCase(saveChecklist.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(saveChecklist.fulfilled, (state, action: PayloadAction<ChecklistItem[]>) => {
        state.isLoading = false
        state.currentChecklist = action.payload
      })
      .addCase(saveChecklist.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  },
})

export const { clearError, clearCurrentGuidance, clearCurrentChecklist } = legalIdSlice.actions
export default legalIdSlice.reducer
