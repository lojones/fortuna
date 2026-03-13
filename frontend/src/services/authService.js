import api from './api'

export default {
  login(username, password) {
    return api.post('/api/auth/login', { username, password })
  },

  register(username, email, password) {
    return api.post('/api/auth/register', { username, email, password })
  },

  getMe() {
    return api.get('/api/users/me')
  },
}
