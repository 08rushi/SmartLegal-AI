import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useAppDispatch, useAppSelector } from './hooks/redux'
import { fetchCurrentUser } from './store/authSlice'
import { fetchDocumentHistory } from './store/documentSlice'

import Home from './pages/Home'
import Upload from './pages/Upload'
import Analysis from './pages/Analysis'
import Chat from './pages/Chat'
import Compare from './pages/Compare'
import ServicesHub from './pages/ServicesHub'
import LegalIdHub from './pages/LegalIdHub'
import LegalIdDetail from './pages/LegalIdDetail'
import PropertyHub from './pages/PropertyHub'
import PropertyDetail from './pages/PropertyDetail'
import BusinessHub from './pages/BusinessHub'
import BusinessDetail from './pages/BusinessDetail'
import ServiceTracker from './pages/ServiceTracker'
import Login from './pages/Login'
import Register from './pages/Register'
import MyDocuments from './pages/MyDocuments'
import NotFound from './pages/NotFound'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  const dispatch = useAppDispatch()
  const { token, user } = useAppSelector((s) => s.auth)
  const currentDocument = useAppSelector((s) => s.document.current)

  // Step 1: Restore session JWT → fetch user profile
  useEffect(() => {
    if (token) {
      dispatch(fetchCurrentUser())
    }
  }, [dispatch, token])

  // Step 2: Once user is confirmed, load their document history from DB
  useEffect(() => {
    if (user && token) {
      dispatch(fetchDocumentHistory())
    }
  }, [dispatch, user, token])

  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* Public routes */}
          <Route index element={<Home />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />

          {/* Public service hub routes (no auth required) */}
          <Route path="services" element={<ServicesHub />} />
          <Route path="legal-id" element={<LegalIdHub />} />
          <Route path="legal-id/:idType" element={<LegalIdDetail />} />
          <Route path="property-hub" element={<PropertyHub />} />
          <Route path="property-hub/:propertyType" element={<PropertyDetail />} />
          <Route path="business-hub" element={<BusinessHub />} />
          <Route path="business-hub/:businessType" element={<BusinessDetail />} />

          {/* Protected routes (requires auth) */}
          <Route
            path="upload"
            element={
              <ProtectedRoute>
                <Upload />
              </ProtectedRoute>
            }
          />
          <Route
            path="analysis"
            element={
              <ProtectedRoute>
                {currentDocument ? (
                  <Navigate to={`/analysis/${currentDocument.id}`} replace />
                ) : (
                  <Analysis />
                )}
              </ProtectedRoute>
            }
          />
          <Route
            path="analysis/:documentId"
            element={
              <ProtectedRoute>
                <Analysis />
              </ProtectedRoute>
            }
          />
          <Route
            path="chat"
            element={
              <ProtectedRoute>
                <Chat />
              </ProtectedRoute>
            }
          />
          <Route
            path="compare"
            element={
              <ProtectedRoute>
                <Compare />
              </ProtectedRoute>
            }
          />
          <Route
            path="documents"
            element={
              <ProtectedRoute>
                <MyDocuments />
              </ProtectedRoute>
            }
          />
          <Route
            path="tracker"
            element={
              <ProtectedRoute>
                <ServiceTracker />
              </ProtectedRoute>
            }
          />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
