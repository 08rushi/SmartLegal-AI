import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'
import { useAppDispatch, useAppSelector } from './hooks/redux'
import { fetchCurrentUser } from './store/authSlice'
import { fetchDocumentHistory } from './store/documentSlice'

const Home = lazy(() => import('./pages/Home'))
const Upload = lazy(() => import('./pages/Upload'))
const Analysis = lazy(() => import('./pages/Analysis'))
const Chat = lazy(() => import('./pages/Chat'))
const Advisor = lazy(() => import('./pages/Advisor'))
const Compare = lazy(() => import('./pages/Compare'))
const KnowledgeBase = lazy(() => import('./pages/KnowledgeBase'))
const ServicesHub = lazy(() => import('./pages/ServicesHub'))
const LegalIdHub = lazy(() => import('./pages/LegalIdHub'))
const LegalIdDetail = lazy(() => import('./pages/LegalIdDetail'))
const PropertyHub = lazy(() => import('./pages/PropertyHub'))
const PropertyDetail = lazy(() => import('./pages/PropertyDetail'))
const BusinessHub = lazy(() => import('./pages/BusinessHub'))
const BusinessDetail = lazy(() => import('./pages/BusinessDetail'))
const YojanaHub = lazy(() => import('./pages/YojanaHub'))
const YojanaBlogList = lazy(() => import('./pages/YojanaBlogList'))
const YojanaBlogDetail = lazy(() => import('./pages/YojanaBlogDetail'))
const ServiceTracker = lazy(() => import('./pages/ServiceTracker'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const MyDocuments = lazy(() => import('./pages/MyDocuments'))
const WhatsAppChannelPage = lazy(() => import('./pages/WhatsAppChannelPage'))
const NotFound = lazy(() => import('./pages/NotFound'))

import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

function PageFallback() {
  return (
    <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center p-8">
      <div className="space-y-4 text-center">
        <div className="w-12 h-12 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-400 text-sm font-medium">Loading SmartLegal AI...</p>
      </div>
    </div>
  )
}


function App() {
  const dispatch = useAppDispatch()
  const { token, user } = useAppSelector((s) => s.auth)

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
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/" element={<Layout />}>
            {/* Public routes */}
            <Route index element={<Home />} />
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Register />} />
            <Route path="forgot-password" element={<ForgotPassword />} />
            <Route path="reset-password" element={<ResetPassword />} />

            {/* Public service hub routes (no auth required) */}
            <Route path="services" element={<ServicesHub />} />
            <Route path="legal-id" element={<LegalIdHub />} />
            <Route path="legal-id/:idType" element={<LegalIdDetail />} />
            <Route path="property-hub" element={<PropertyHub />} />
            <Route path="property-hub/:propertyType" element={<PropertyDetail />} />
            <Route path="business-hub" element={<BusinessHub />} />
            <Route path="business-hub/:businessType" element={<BusinessDetail />} />
            <Route path="yojana" element={<YojanaHub />} />
            <Route path="yojana/blogs" element={<YojanaBlogList />} />
            <Route path="yojana/blogs/:slug" element={<YojanaBlogDetail />} />

            {/* Protected routes */}
            <Route
              path="upload"
              element={
                <ProtectedRoute
                  title="Sign in to analyze"
                  message="Please sign in to upload and analyze your legal documents. It only takes a moment."
                >
                  <Upload />
                </ProtectedRoute>
              }
            />
            <Route path="analysis" element={<Analysis isDemo />} />
            <Route path="analysis/demo" element={<Analysis isDemo />} />

            <Route
              path="analysis/:documentId"
              element={
                <ProtectedRoute
                  title="Sign in to view this analysis"
                  message="Please sign in to open your document analysis."
                >
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
              path="advisor"
              element={
                <ProtectedRoute>
                  <Advisor />
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
            <Route path="knowledge-base" element={<KnowledgeBase />} />

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
            <Route
              path="channels/whatsapp"
              element={
                <ProtectedRoute>
                  <WhatsAppChannelPage />
                </ProtectedRoute>
              }
            />

            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )

}

export default App
