import axios from 'axios'

// Production-only: the frontend (Vercel) and backend (Render) are always on
// different domains, so every request needs the full backend origin.
// VITE_API_URL must be set to that origin (e.g.
// https://school-management-backend-1t21.onrender.com — no trailing slash,
// no /api suffix) as a Vercel build-time env var. Vite only inlines
// import.meta.env.* at build time, so changing it requires a redeploy, not
// just an env var update.
const apiOrigin = import.meta.env.VITE_API_URL
if (!apiOrigin) {
  throw new Error(
    'VITE_API_URL is not set. Configure it in the Vercel project settings to ' +
      'the deployed Render backend origin (e.g. https://your-backend.onrender.com).',
  )
}

/** The bare backend origin (no /api suffix) — for building URLs to public,
 * non-axios resources like <img src> (e.g. the school logo). */
export const apiOriginUrl = apiOrigin.replace(/\/+$/, '')

export const apiClient = axios.create({ baseURL: `${apiOriginUrl}/api` })

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('sms_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // A 401 from /auth/login itself just means "wrong credentials" — that's
    // a normal response the login form handles inline, not an expired
    // session. Only force a redirect for 401s from every other endpoint
    // (an expired/invalid token on an already-authenticated request).
    const isLoginRequest = error.config?.url === '/auth/login'
    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem('sms_token')
      localStorage.removeItem('sms_role')
      localStorage.removeItem('sms_assigned_class')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

/** Downloads a file from an authenticated API endpoint — plain <a href> can't
 * send the JWT header, so this fetches as a blob and saves it client-side. */
export async function downloadFile(url: string, params: Record<string, unknown> = {}, fallbackFilename = 'download') {
  const response = await apiClient.get(url, { params, responseType: 'blob' })
  const contentDisposition = response.headers['content-disposition'] as string | undefined
  const match = contentDisposition?.match(/filename=([^;]+)/)
  const filename = match ? match[1].trim() : fallbackFilename

  const blobUrl = window.URL.createObjectURL(response.data as Blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(blobUrl)
}
