import { useParams } from 'react-router-dom'
import HubDetailView from '../components/HubDetailView'

export default function BusinessDetail() {
  const { businessType } = useParams<{ businessType: string }>()
  return <HubDetailView hub="business" typeKey={businessType || ''} />
}
