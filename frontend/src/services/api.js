const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

let authToken = localStorage.getItem('moneyrun_token') || ''

export function setAuthToken(token) {
  authToken = token || ''
  if (authToken) localStorage.setItem('moneyrun_token', authToken)
  else localStorage.removeItem('moneyrun_token')
}

export function getAuthToken() {
  return authToken
}

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(authToken ? { Authorization: `Token ${authToken}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'API 요청 실패' }))
    const firstValue = Object.values(error)[0]
    throw new Error(error.detail || (Array.isArray(firstValue) ? firstValue[0] : firstValue) || 'API 요청 실패')
  }

  if (response.status === 204) return null
  return response.json()
}

export const api = {
  signup: (payload) => request('/auth/signup/', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload) => request('/auth/login/', { method: 'POST', body: JSON.stringify(payload) }),
  logout: () => request('/auth/logout/', { method: 'POST' }),
  me: () => request('/auth/me/'),
  uploadAvatar: (file) => {
    const formData = new FormData()
    formData.append('avatar', file)
    return request('/auth/avatar/', { method: 'POST', body: formData })
  },
  dashboard: (groupId) => request(`/dashboard/${groupId ? `?group=${groupId}` : ''}`),
  coach: (groupId) => request(`/coach/${groupId ? `?group=${groupId}` : ''}`),
  groups: () => request('/groups/'),
  createGroup: (payload) => request('/groups/', { method: 'POST', body: JSON.stringify(payload) }),
  createGoal: (payload) => request('/goals/', { method: 'POST', body: JSON.stringify(payload) }),
  invitePreview: (code) => request(`/invitations/${code}/`),
  joinInvite: (code, payload = {}) => request(`/invitations/${code}/join/`, { method: 'POST', body: JSON.stringify(payload) }),
  completeMission: (payload) => request('/mission-complete/', { method: 'POST', body: JSON.stringify(payload) }),
  createExpense: (payload) => request('/expenses/', { method: 'POST', body: JSON.stringify(payload) }),
  pokeMember: (payload) => request('/pokes/', { method: 'POST', body: JSON.stringify(payload) }),
  notifications: () => request('/notifications/'),
  readNotifications: (payload = {}) => request('/notifications/read/', { method: 'POST', body: JSON.stringify(payload) }),
  bankStatus: () => request('/bank/status/'),
  connectBank: (payload = {}) => request('/bank/connect/', { method: 'POST', body: JSON.stringify(payload) }),
  transferFromBank: (payload = {}) => request('/bank/transfer/', { method: 'POST', body: JSON.stringify(payload) }),
  gameReward: (payload) => request('/game-reward/', { method: 'POST', body: JSON.stringify(payload) }),
}
