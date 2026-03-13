import api from './api'

export default {
  getAll() {
    return api.get('/api/visualizations')
  },

  getRecent() {
    return api.get('/api/visualizations/recent')
  },

  getById(vizId) {
    return api.get(`/api/visualizations/${vizId}`)
  },

  create(title, description) {
    return api.post('/api/visualizations', { title, description })
  },

  publish(vizId) {
    return api.post(`/api/visualizations/${vizId}/publish`)
  },

  publishVersion(vizId, versionNumber) {
    return api.post(`/api/visualizations/${vizId}/publish-version/${versionNumber}`)
  },

  unpublish(vizId) {
    return api.post(`/api/visualizations/${vizId}/unpublish`)
  },

  getPublished(slug) {
    return api.get(`/api/visualizations/public/${slug}`)
  },

  getVersion(vizId, versionNumber) {
    return api.get(`/api/visualizations/${vizId}/versions/${versionNumber}`)
  },

  getChat(vizId) {
    return api.get(`/api/visualizations/${vizId}/chat`)
  },

  delete(vizId) {
    return api.delete(`/api/visualizations/${vizId}`)
  },
}
