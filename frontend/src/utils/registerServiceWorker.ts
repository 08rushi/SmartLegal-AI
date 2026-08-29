export function registerServiceWorker() {
  if ('serviceWorker' in navigator && import.meta.env.PROD) {

    window.addEventListener('load', () => {
      navigator.serviceWorker
        .register('/sw.js')
        .then((reg) => console.log('[PWA] ServiceWorker registered:', reg.scope))
        .catch((err) => console.error('[PWA] ServiceWorker registration failed:', err))
    })
  }
}
