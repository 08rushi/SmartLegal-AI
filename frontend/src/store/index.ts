import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'
import documentReducer from './documentSlice'
import analysisReducer from './analysisSlice'
import chatReducer from './chatSlice'
import advisorReducer from './advisorSlice'
import insightsReducer from './insightsSlice'
import legalIdReducer from './legalIdSlice'
import propertyReducer from './propertySlice'
import businessReducer from './businessSlice'
import yojanaReducer from './yojanaSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    document: documentReducer,
    analysis: analysisReducer,
    chat: chatReducer,
    advisor: advisorReducer,
    insights: insightsReducer,
    legalId: legalIdReducer,
    property: propertyReducer,
    business: businessReducer,
    yojana: yojanaReducer,
  },
})


// Infer types from store itself
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
