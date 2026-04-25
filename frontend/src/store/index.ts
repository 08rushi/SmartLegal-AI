import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'
import documentReducer from './documentSlice'
import analysisReducer from './analysisSlice'
import chatReducer from './chatSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    document: documentReducer,
    analysis: analysisReducer,
    chat: chatReducer,
  },
})

// Infer types from store itself
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
