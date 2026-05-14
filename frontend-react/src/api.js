import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? '/api'

const api = axios.create({ baseURL: BASE })

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/'
    }
    return Promise.reject(err)
  }
)

export default api

export const getAuthUrl    = () => api.get('/auth/google')
export const getMe         = () => api.get('/auth/me')
export const updateName    = (name) => api.put('/auth/me/name', { name })
export const deleteAccount = () => api.delete('/auth/me')

export const getStats      = () => api.get('/stats')
export const getBills      = () => api.get('/bills')
export const getBill       = (id) => api.get(`/bills/${id}`)
export const deleteBill    = (id) => api.delete(`/bills/${id}`)
export const updateBill    = (id, data) => api.patch(`/bills/${id}`, data)
export const exportCsv     = () => api.get('/bills/export/csv', { responseType: 'blob' })
export const createManual  = (data) => api.post('/bills/manual', data)

export const getBudget         = () => api.get('/budget')
export const setBudget         = (data) => api.put('/budget', data)
export const getBudgetStatus   = () => api.get('/budget/status')
export const getUpcomingDues   = () => api.get('/alerts/upcoming-dues')
export const triggerSummary    = () => api.post('/alerts/weekly-summary')
export const checkDueDates     = () => api.post('/alerts/check-due-dates')

export const getGoal   = () => api.get('/goal')
export const setGoal   = (data) => api.put('/goal', data)

export const getPredictions   = () => api.get('/ml/predictions')
export const getAnomalies     = () => api.get('/ml/anomalies')
export const getClassify      = () => api.get('/ml/classify')
export const getRecommendations = () => api.get('/ml/recommendations')
export const getClusters      = () => api.get('/ml/clusters')
export const getChangepoints  = () => api.get('/ml/changepoints')
export const getCostPrediction = () => api.get('/ml/cost-prediction')

export const downloadPdf = () => api.get('/report/pdf', { responseType: 'blob' })

export const adminStats   = () => api.get('/admin/stats')
export const adminUsers   = () => api.get('/admin/users')
export const adminBills   = () => api.get('/admin/bills')
export const adminDeleteUser = (id) => api.delete(`/admin/users/${id}`)
export const adminDeleteBill = (id) => api.delete(`/admin/bills/${id}`)

export const uploadBill = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload-bill', form, { headers: { 'Content-Type': 'multipart/form-data' } })
}
