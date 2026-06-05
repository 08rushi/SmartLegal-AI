import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit'
import type { BusinessState, BusinessType, BusinessGuidance, BusinessApplication, ChecklistItem } from '../types'
import { apiClient } from '../services/api'

// ─── Async Thunks ─────────────────────────────────────────────────────────

export const fetchBusinessTypes = createAsyncThunk(
  'business/fetchTypes',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ business_types: BusinessType[] }>('/business')
      return response.data.business_types
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load business types')
    }
  }
)

export const fetchBusinessGuidance = createAsyncThunk(
  'business/fetchGuidance',
  async (businessType: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ guidance: BusinessGuidance }>(`/business/${businessType}`)
      return response.data.guidance
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load guidance')
    }
  }
)

export const createApplication = createAsyncThunk(
  'business/createApplication',
  async (data: { business_type: string; service: string; notes?: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<BusinessApplication>('/business/applications', data)
      return response.data
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to create application')
    }
  }
)

export const fetchBusinessApplications = createAsyncThunk(
  'business/fetchApplications',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ applications: BusinessApplication[] }>('/business/applications')
      return response.data.applications
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load applications')
    }
  }
)

export const updateApplication = createAsyncThunk(
  'business/updateApplication',
  async (data: { app_id: string; status?: string; notes?: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.patch<BusinessApplication>(`/business/applications/${data.app_id}`, {
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
  'business/deleteApplication',
  async (app_id: string, { rejectWithValue }) => {
    try {
      await apiClient.delete(`/business/applications/${app_id}`)
      return app_id
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete application')
    }
  }
)

export const fetchChecklist = createAsyncThunk(
  'business/fetchChecklist',
  async (app_id: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ items: ChecklistItem[] }>(`/business/applications/${app_id}/checklist`)
      return response.data.items
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load checklist')
    }
  }
)

export const saveBusinessChecklist = createAsyncThunk(
  'business/saveChecklist',
  async (data: { app_id: string; items: { id?: string; item_text: string; is_done: boolean }[] }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<{ items: ChecklistItem[] }>(`/business/applications/${data.app_id}/checklist`, {
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

const initialState: BusinessState = {
  businessTypes: [],
  currentGuidance: null,
  applications: [],
  currentChecklist: [],
  isLoading: false,
  error: null,
}

// ─── Slice ───────────────────────────────────────────────────────────────

const businessSlice = createSlice({
  name: 'business',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    clearGuidance: (state) => {
      state.currentGuidance = null
    },
  },
  extraReducers: (builder) => {
    // fetchBusinessTypes
    builder
      .addCase(fetchBusinessTypes.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchBusinessTypes.fulfilled, (state, action: PayloadAction<BusinessType[]>) => {
        state.isLoading = false
        state.businessTypes = action.payload
      })
      .addCase(fetchBusinessTypes.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // fetchBusinessGuidance
    builder
      .addCase(fetchBusinessGuidance.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchBusinessGuidance.fulfilled, (state, action: PayloadAction<BusinessGuidance>) => {
        state.isLoading = false
        state.currentGuidance = action.payload
      })
      .addCase(fetchBusinessGuidance.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // createApplication
    builder
      .addCase(createApplication.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(createApplication.fulfilled, (state, action: PayloadAction<BusinessApplication>) => {
        state.isLoading = false
        state.applications.push(action.payload)
      })
      .addCase(createApplication.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // fetchBusinessApplications
    builder
      .addCase(fetchBusinessApplications.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchBusinessApplications.fulfilled, (state, action: PayloadAction<BusinessApplication[]>) => {
        state.isLoading = false
        state.applications = action.payload
      })
      .addCase(fetchBusinessApplications.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // updateApplication
    builder
      .addCase(updateApplication.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(updateApplication.fulfilled, (state, action: PayloadAction<BusinessApplication>) => {
        state.isLoading = false
        const idx = state.applications.findIndex((a) => a.id === action.payload.id)
        if (idx !== -1) {
          state.applications[idx] = action.payload
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
      .addCase(deleteApplication.fulfilled, (state, action) => {
        state.isLoading = false
        state.applications = state.applications.filter((a) => a.id !== action.payload)
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
      .addCase(fetchChecklist.fulfilled, (state, action) => {
        state.isLoading = false
        state.currentChecklist = action.payload
      })
      .addCase(fetchChecklist.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // saveBusinessChecklist
    builder
      .addCase(saveBusinessChecklist.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(saveBusinessChecklist.fulfilled, (state, action) => {
        state.isLoading = false
        state.currentChecklist = action.payload
      })
      .addCase(saveBusinessChecklist.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  },
})

export const { clearError, clearGuidance } = businessSlice.actions
export default businessSlice.reducer
