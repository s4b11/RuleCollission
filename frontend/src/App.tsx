import { Navigate, Route, Routes } from 'react-router-dom'
import Layout, { type Staff } from './components/Layout'
import { PageLoader } from './components/ui'
import { getToken, useLoad } from './lib/api'
import Login from './Login'
import CaseDetail from './ops/CaseDetail'
import Cases from './ops/Cases'
import Overview from './ops/Overview'
import People from './ops/People'
import Reviews from './ops/Reviews'
import Sessions from './ops/Sessions'
import Assistant from './patient/Assistant'
import CaseLookup from './patient/CaseLookup'
import Agent from './studio/Agent'
import Channels from './studio/Channels'
import Knowledge from './studio/Knowledge'
import Rules from './studio/Rules'
import Tools from './studio/Tools'

function StaffArea() {
  const { data: staff, error, reload } = useLoad<Staff>(getToken() ? '/auth/me' : null)
  if (!getToken()) return <Navigate to="/login" />
  if (!staff) return <div className="min-h-screen"><PageLoader error={error} retry={reload} /></div>
  return <Layout staff={staff} />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/a/:slug" element={<Assistant />} />
      <Route path="/case" element={<CaseLookup />} />
      <Route element={<StaffArea />}>
        <Route path="/ops" element={<Overview />} />
        <Route path="/ops/people" element={<People />} />
        <Route path="/ops/cases" element={<Cases />} />
        <Route path="/ops/cases/:id" element={<CaseDetail />} />
        <Route path="/ops/reviews" element={<Reviews />} />
        <Route path="/ops/sessions" element={<Sessions />} />
        <Route path="/studio/agent" element={<Agent />} />
        <Route path="/studio/tools" element={<Tools />} />
        <Route path="/studio/knowledge" element={<Knowledge />} />
        <Route path="/studio/rules" element={<Rules />} />
        <Route path="/studio/channels" element={<Channels />} />
      </Route>
      <Route path="*" element={<Navigate to="/ops" />} />
    </Routes>
  )
}
