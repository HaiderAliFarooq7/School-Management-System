import axios from 'axios'

export const apiClient = axios.create({ baseURL: '/api' })

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
    if (error.response?.status === 401) {
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
