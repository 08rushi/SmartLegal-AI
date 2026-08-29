import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { apiClient } from '../services/api'
import { YojanaState, YojanaScheme, YojanaMatchProfile, YojanaMatchResult, YojanaBlog } from '../types'

const initialProfile: YojanaMatchProfile = {
  state: 'ALL',
  district: '',
  age: 28,
  gender: 'all',
  occupation: 'farmer',
  annual_income: 180000,
  category: 'OBC',
  land_holding_acres: 1.5,
  is_pregnant_or_lactating: false,
  is_disabled: false,
}

const initialState: YojanaState = {
  schemes: [],
  matchedResults: [],
  currentScheme: null,
  blogs: [],
  currentBlog: null,
  profile: initialProfile,
  isLoading: false,
  error: null,
}

export const fetchYojanaSchemes = createAsyncThunk(
  'yojana/fetchSchemes',
  async (filters: { category?: string; state?: string; level?: string } = {}, { rejectWithValue }) => {
    try {
      const response = await apiClient.get('/yojana/schemes', { params: filters })
      return response.data.schemes as YojanaScheme[]
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to load government schemes')
    }
  }
)

export const fetchSchemeDetails = createAsyncThunk(
  'yojana/fetchSchemeDetails',
  async (schemeId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/yojana/schemes/${schemeId}`)
      return response.data.scheme as YojanaScheme
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to load scheme details')
    }
  }
)

export const matchYojanaEligibility = createAsyncThunk(
  'yojana/matchEligibility',
  async (profile: YojanaMatchProfile, { rejectWithValue }) => {
    try {
      const response = await apiClient.post('/yojana/match', profile)
      return response.data.matches as YojanaMatchResult[]
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to evaluate scheme eligibility')
    }
  }
)

export const fetchYojanaBlogs = createAsyncThunk(
  'yojana/fetchBlogs',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get('/yojana/blogs')
      return response.data.blogs as YojanaBlog[]
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to load citizen guides')
    }
  }
)

export const fetchYojanaBlogBySlug = createAsyncThunk(
  'yojana/fetchBlogBySlug',
  async (slug: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/yojana/blogs/${slug}`)
      return response.data.blog as YojanaBlog
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to load citizen guide')
    }
  }
)

export const yojanaSlice = createSlice({
  name: 'yojana',
  initialState,
  reducers: {
    setProfile(state, action: PayloadAction<Partial<YojanaMatchProfile>>) {
      state.profile = { ...state.profile, ...action.payload }
    },
    clearMatchedResults(state) {
      state.matchedResults = []
    },
    clearError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchYojanaSchemes
      .addCase(fetchYojanaSchemes.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchYojanaSchemes.fulfilled, (state, action) => {
        state.isLoading = false
        state.schemes = action.payload
      })
      .addCase(fetchYojanaSchemes.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
      // fetchSchemeDetails
      .addCase(fetchSchemeDetails.fulfilled, (state, action) => {
        state.currentScheme = action.payload
      })
      // matchYojanaEligibility
      .addCase(matchYojanaEligibility.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(matchYojanaEligibility.fulfilled, (state, action) => {
        state.isLoading = false
        state.matchedResults = action.payload
      })
      .addCase(matchYojanaEligibility.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
      // fetchYojanaBlogs
      .addCase(fetchYojanaBlogs.pending, (state) => {
        state.isLoading = true
      })
      .addCase(fetchYojanaBlogs.fulfilled, (state, action) => {
        state.isLoading = false
        state.blogs = action.payload
      })
      // fetchYojanaBlogBySlug
      .addCase(fetchYojanaBlogBySlug.fulfilled, (state, action) => {
        state.currentBlog = action.payload
      })
  },
})

export const { setProfile, clearMatchedResults, clearError } = yojanaSlice.actions
export default yojanaSlice.reducer
