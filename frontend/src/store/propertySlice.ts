import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { PropertyState, PropertyType, PropertyGuidance, PropertyApplication, ChecklistItem, ChecklistSaveItem } from '../types'
import { apiClient } from '../services/api'

// ─── Async Thunks ─────────────────────────────────────────────────────────

export const fetchPropertyTypes = createAsyncThunk(
  'property/fetchTypes',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ property_types: PropertyType[] }>('/property')
      return response.data.property_types
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load property types')
    }
  }
)

export const fetchPropertyGuidance = createAsyncThunk(
  'property/fetchGuidance',
  async (propertyType: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ guidance: PropertyGuidance }>(`/property/${propertyType}`)
      return response.data.guidance
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load guidance')
    }
  }
)

export const createPropertyApplication = createAsyncThunk(
  'property/createApplication',
  async (data: { property_type: string; service: string; notes?: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<PropertyApplication>('/property/applications', data)
      return response.data
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to create application')
    }
  }
)

export const fetchPropertyApplications = createAsyncThunk(
  'property/fetchApplications',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ applications: PropertyApplication[] }>('/property/applications')
      return response.data.applications
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load applications')
    }
  }
)

export const updatePropertyApplication = createAsyncThunk(
  'property/updateApplication',
  async (data: { app_id: string; status?: string; notes?: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.patch<PropertyApplication>(`/property/applications/${data.app_id}`, {
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

export const deletePropertyApplication = createAsyncThunk(
  'property/deleteApplication',
  async (app_id: string, { rejectWithValue }) => {
    try {
      await apiClient.delete(`/property/applications/${app_id}`)
      return app_id
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete application')
    }
  }
)

export const fetchPropertyChecklist = createAsyncThunk(
  'property/fetchChecklist',
  async (app_id: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ items: ChecklistItem[] }>(`/property/applications/${app_id}/checklist`)
      return response.data.items
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load checklist')
    }
  }
)

export const savePropertyChecklist = createAsyncThunk(
  'property/saveChecklist',
  async (data: { app_id: string; items: ChecklistSaveItem[] }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<{ items: ChecklistItem[] }>(`/property/applications/${data.app_id}/checklist`, {
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

const initialState: PropertyState = {
  propertyTypes: [],
  currentGuidance: null,
  applications: [],
  currentChecklist: [],
  isLoading: false,
  error: null,
}

// ─── Slice ────────────────────────────────────────────────────────────────

const propertySlice = createSlice({
  name: 'property',
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
    // fetchPropertyTypes
    builder
      .addCase(fetchPropertyTypes.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchPropertyTypes.fulfilled, (state, action: PayloadAction<PropertyType[]>) => {
        state.isLoading = false
        state.propertyTypes = action.payload
      })
      .addCase(fetchPropertyTypes.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // fetchPropertyGuidance
    builder
      .addCase(fetchPropertyGuidance.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchPropertyGuidance.fulfilled, (state, action: PayloadAction<PropertyGuidance>) => {
        state.isLoading = false
        state.currentGuidance = action.payload
      })
      .addCase(fetchPropertyGuidance.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // createPropertyApplication
    builder
      .addCase(createPropertyApplication.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(createPropertyApplication.fulfilled, (state, action: PayloadAction<PropertyApplication>) => {
        state.isLoading = false
        state.applications.push(action.payload)
      })
      .addCase(createPropertyApplication.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // fetchPropertyApplications
    builder
      .addCase(fetchPropertyApplications.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchPropertyApplications.fulfilled, (state, action: PayloadAction<PropertyApplication[]>) => {
        state.isLoading = false
        state.applications = action.payload
      })
      .addCase(fetchPropertyApplications.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // updatePropertyApplication
    builder
      .addCase(updatePropertyApplication.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(updatePropertyApplication.fulfilled, (state, action: PayloadAction<PropertyApplication>) => {
        state.isLoading = false
        const index = state.applications.findIndex((app) => app.id === action.payload.id)
        if (index !== -1) {
          state.applications[index] = action.payload
        }
      })
      .addCase(updatePropertyApplication.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // deletePropertyApplication
    builder
      .addCase(deletePropertyApplication.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(deletePropertyApplication.fulfilled, (state, action: PayloadAction<string>) => {
        state.isLoading = false
        state.applications = state.applications.filter((app) => app.id !== action.payload)
      })
      .addCase(deletePropertyApplication.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // fetchPropertyChecklist
    builder
      .addCase(fetchPropertyChecklist.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchPropertyChecklist.fulfilled, (state, action: PayloadAction<ChecklistItem[]>) => {
        state.isLoading = false
        state.currentChecklist = action.payload
      })
      .addCase(fetchPropertyChecklist.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // savePropertyChecklist
    builder
      .addCase(savePropertyChecklist.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(savePropertyChecklist.fulfilled, (state, action: PayloadAction<ChecklistItem[]>) => {
        state.isLoading = false
        state.currentChecklist = action.payload
      })
      .addCase(savePropertyChecklist.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  },
})

export const { clearError, clearCurrentGuidance, clearCurrentChecklist } = propertySlice.actions
export default propertySlice.reducer
