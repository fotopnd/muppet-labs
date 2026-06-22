import { Outlet } from 'react-router-dom'
import ConferenceNav from '@/components/ConferenceNav'

export default function ConferenceLayout() {
  return (
    <>
      <ConferenceNav />
      <Outlet />
    </>
  )
}
