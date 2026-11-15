import { useParams } from 'react-router-dom'
import HubDetailView from '../components/HubDetailView'

export default function PropertyDetail() {
  const { propertyType } = useParams<{ propertyType: string }>()
  return <HubDetailView hub="property" typeKey={propertyType || ''} />
}
