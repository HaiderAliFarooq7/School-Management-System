import axios from 'axios'

// In local dev this stays '/api' and is handled by Vite's dev-server proxy
// (see vite.config.ts) straight to the local backend. That proxy doesn't
// exist in production — when the frontend (Vercel) and backend (Render) are
// on different domains, VITE_API_URL must point at the deployed backend
// (e.g. https://your-backend.onrender.com/api), set as a Vercel build-time
// env var. Vite only inlines import.meta.env.* at build time, so changing
// this requires a redeploy, not just an env var update.
const baseURL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({ baseURL })

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
