import type { AppDispatch, RootState } from '../../store'
import type { ChecklistItem } from '../../types'
import * as legalId from '../../store/legalIdSlice'
import * as property from '../../store/propertySlice'
import * as business from '../../store/businessSlice'

export type HubId = 'legal-id' | 'property' | 'business'

export const HUB_BASE_PATH: Record<HubId, string> = {
  'legal-id': '/legal-id',
  property: '/property-hub',
  business: '/business-hub',
}

/** Values the backend PATCH accepts (VALID_STATUSES in the hub routers). */
export const HUB_STATUSES = ['in_progress', 'submitted', 'received', 'completed'] as const

/**
 * One adapter per hub hides the differences between the three Redux slices (thunk names, state field names,
 * the application's type field) so a single generic page can serve Legal ID, Property and Business.
 */

export interface HubTypeRow {
  key: string
  display_name: string
  authority: string
}

export interface HubAppRow {
  id: string
  type: string
  service: string
  status: string
  notes: string
  updated_at: string
}

export interface HubSnapshot {
  types: HubTypeRow[]
  guidance: import('../HubDetailView').HubGuidance | null
  apps: HubAppRow[]
  checklist: ChecklistItem[]
  isLoading: boolean
  error: string | null
}

export interface ActionResult {
  ok: boolean
  error?: string
}

export interface HubAdapter {
  hub: HubId
  ns: 'legalid' | 'property' | 'business'
  select: (state: RootState) => HubSnapshot
  fetchTypes: (d: AppDispatch) => void
  fetchGuidance: (d: AppDispatch, typeKey: string) => void
  fetchApps: (d: AppDispatch) => void
  fetchChecklist: (d: AppDispatch, appId: string) => Promise<ActionResult>
  saveChecklist: (d: AppDispatch, appId: string, items: ChecklistItem[]) => Promise<ActionResult>
  /** Resolves with the new application's id, or null when creating failed. */
  create: (d: AppDispatch, typeKey: string, service: string, notes: string) => Promise<string | null>
  updateStatus: (d: AppDispatch, appId: string, status: string) => Promise<ActionResult>
}

const toSave = (items: ChecklistItem[]) => items.map((i) => ({ id: i.id, item_text: i.item_text, is_done: i.is_done }))
const failMsg = (payload: unknown) => ({ ok: false, error: String(payload ?? '') })

interface Rejectable {
  rejected: { match: (a: unknown) => boolean }
  fulfilled: { match: (a: unknown) => boolean }
}
const settle = (res: { payload?: unknown }, thunk: Rejectable): ActionResult =>
  thunk.rejected.match(res) ? failMsg(res.payload) : { ok: true }

export const legalIdAdapter: HubAdapter = {
  hub: 'legal-id',
  ns: 'legalid',
  select: (s) => ({
    types: s.legalId.idTypes,
    guidance: s.legalId.currentGuidance,
    apps: s.legalId.applications.map((a) => ({ ...a, type: a.id_type })),
    checklist: s.legalId.currentChecklist,
    isLoading: s.legalId.isLoading,
    error: s.legalId.error,
  }),
  fetchTypes: (d) => void d(legalId.fetchIdTypes()),
  fetchGuidance: (d, k) => void d(legalId.fetchIdGuidance(k)),
  fetchApps: (d) => void d(legalId.fetchApplications()),
  fetchChecklist: async (d, id) => settle(await d(legalId.fetchChecklist(id)), legalId.fetchChecklist),
  saveChecklist: async (d, id, items) =>
    settle(await d(legalId.saveChecklist({ app_id: id, items: toSave(items) })), legalId.saveChecklist),
  create: async (d, k, service, notes) => {
    const res = await d(legalId.createApplication({ id_type: k, service, notes }))
    return legalId.createApplication.fulfilled.match(res) ? res.payload.id : null
  },
  updateStatus: async (d, id, status) =>
    settle(await d(legalId.updateApplication({ app_id: id, status })), legalId.updateApplication),
}

export const propertyAdapter: HubAdapter = {
  hub: 'property',
  ns: 'property',
  select: (s) => ({
    types: s.property.propertyTypes,
    guidance: s.property.currentGuidance,
    apps: s.property.applications.map((a) => ({ ...a, type: a.property_type })),
    checklist: s.property.currentChecklist,
    isLoading: s.property.isLoading,
    error: s.property.error,
  }),
  fetchTypes: (d) => void d(property.fetchPropertyTypes()),
  fetchGuidance: (d, k) => void d(property.fetchPropertyGuidance(k)),
  fetchApps: (d) => void d(property.fetchPropertyApplications()),
  fetchChecklist: async (d, id) => settle(await d(property.fetchPropertyChecklist(id)), property.fetchPropertyChecklist),
  saveChecklist: async (d, id, items) =>
    settle(await d(property.savePropertyChecklist({ app_id: id, items: toSave(items) })), property.savePropertyChecklist),
  create: async (d, k, service, notes) => {
    const res = await d(property.createPropertyApplication({ property_type: k, service, notes }))
    return property.createPropertyApplication.fulfilled.match(res) ? res.payload.id : null
  },
  updateStatus: async (d, id, status) =>
    settle(await d(property.updatePropertyApplication({ app_id: id, status })), property.updatePropertyApplication),
}

export const businessAdapter: HubAdapter = {
  hub: 'business',
  ns: 'business',
  select: (s) => ({
    types: s.business.businessTypes,
    guidance: s.business.currentGuidance,
    apps: s.business.applications.map((a) => ({ ...a, type: a.business_type })),
    checklist: s.business.currentChecklist,
    isLoading: s.business.isLoading,
    error: s.business.error,
  }),
  fetchTypes: (d) => void d(business.fetchBusinessTypes()),
  fetchGuidance: (d, k) => void d(business.fetchBusinessGuidance(k)),
  fetchApps: (d) => void d(business.fetchBusinessApplications()),
  fetchChecklist: async (d, id) => settle(await d(business.fetchChecklist(id)), business.fetchChecklist),
  saveChecklist: async (d, id, items) =>
    settle(await d(business.saveBusinessChecklist({ app_id: id, items: toSave(items) })), business.saveBusinessChecklist),
  create: async (d, k, service, notes) => {
    const res = await d(business.createApplication({ business_type: k, service, notes }))
    return business.createApplication.fulfilled.match(res) ? res.payload.id : null
  },
  updateStatus: async (d, id, status) =>
    settle(await d(business.updateApplication({ app_id: id, status })), business.updateApplication),
}

export const HUB_ADAPTERS: Record<HubId, HubAdapter> = {
  'legal-id': legalIdAdapter,
  property: propertyAdapter,
  business: businessAdapter,
}
