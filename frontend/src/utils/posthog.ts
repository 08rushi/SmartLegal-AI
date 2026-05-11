declare global {
  interface Window {
    posthog?: {
      init: (key: string, config?: Record<string, unknown>) => void
      capture: (event: string, properties?: Record<string, unknown>) => void
    }
  }
}

let initialized = false
let loadingPromise: Promise<void> | null = null

function loadPostHogScript(host: string) {
  if (typeof document === 'undefined') return Promise.resolve()
  if (document.querySelector('script[data-posthog-loader="true"]')) return Promise.resolve()

  return new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.async = true
    script.src = `${host.replace(/\/$/, '')}/static/array.js`
    script.dataset.posthogLoader = 'true'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load PostHog'))
    document.head.appendChild(script)
  })
}

export function initPostHog() {
  const key = import.meta.env.VITE_POSTHOG_KEY
  const host = import.meta.env.VITE_POSTHOG_HOST || 'https://us.i.posthog.com'

  if (!key || typeof window === 'undefined' || initialized) return

  if (!loadingPromise) {
    loadingPromise = loadPostHogScript(host)
      .then(() => {
        if (!window.posthog) return

        window.posthog.init(key, {
          api_host: host,
          person_profiles: 'identified_only',
          capture_pageview: false,
          capture_pageleave: true,
        })
        initialized = true
      })
      .catch(() => {
        loadingPromise = null
      })
  }
}

export function trackEvent(event: string, properties?: Record<string, unknown>) {
  window.posthog?.capture(event, properties)
}
