import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useAppDispatch, useAppSelector } from './hooks/redux'
import { fetchCurrentUser } from './store/authSlice'

// Pages
import Home from './pages/Home'
import Upload from './pages/Upload'
import Analysis from './pages/Analysis'
import Chat from './pages/Chat'
import Compare from './pages/Compare'
import Login from './pages/Login'
import Register from './pages/Register'
import MyDocuments from './pages/MyDocuments'
import NotFound from './pages/NotFound'

// Components
import Layout from './components/Layout'

function App() {
  const dispatch = useAppDispatch()
  const { token } = useAppSelector((s) => s.auth)

  // Restore session on every page load — JWT is in localStorage
  useEffect(() => {
    if (token) {
      dispatch(fetchCurrentUser())
    }
  }, [dispatch, token])

  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="upload" element={<Upload />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="chat" element={<Chat />} />
          <Route path="compare" element={<Compare />} />
          <Route path="documents" element={<MyDocuments />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App