import api from './api'

export default {
  getSession(vizId) {
    return api.get(`/api/visualizations/${vizId}/chat`)
  },
}
