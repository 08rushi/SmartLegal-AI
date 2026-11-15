import { useParams } from 'react-router-dom'
import HubDetailView from '../components/HubDetailView'

export default function LegalIdDetail() {
  const { idType } = useParams<{ idType: string }>()
  return <HubDetailView hub="legal-id" typeKey={idType || ''} />
}
