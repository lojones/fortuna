class WebSocketService {
  constructor() {
    this.ws = null
    this.handlers = {}
  }

  connect(vizId, token, handlers) {
    this.handlers = handlers
    const wsBase = import.meta.env.VITE_WS_BASE_URL || `ws://${window.location.host}`
    const url = `${wsBase}/api/chat/ws/${vizId}?token=${token}`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      if (handlers.onOpen) handlers.onOpen()
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        switch (data.type) {
          case 'init':
            if (handlers.onInit) handlers.onInit(data.session)
            break
          case 'chunk':
            if (handlers.onChunk) handlers.onChunk(data.content)
            break
          case 'complete':
            if (handlers.onComplete) handlers.onComplete(data.usage || null)
            break
          case 'spec_streaming':
            if (handlers.onSpecStreaming) handlers.onSpecStreaming()
            break
          case 'spec_chunk':
            if (handlers.onSpecChunk) handlers.onSpecChunk(data.content)
            break
          case 'status':
            if (handlers.onStatus) handlers.onStatus(data.message)
            break
          case 'html_chunk':
            if (handlers.onHtmlChunk) handlers.onHtmlChunk(data.content)
            break
          case 'visualization_ready':
            if (handlers.onVisualizationReady) handlers.onVisualizationReady(data.html, data.spec || '', data.viz_id, data.usage || null)
            break
          case 'error':
            if (handlers.onError) handlers.onError(data.message)
            break
          default:
            console.warn('Unknown WebSocket message type:', data.type)
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    this.ws.onclose = (event) => {
      if (handlers.onClose) handlers.onClose(event.code)
    }

    this.ws.onerror = () => {
      if (handlers.onError) handlers.onError('WebSocket connection error')
    }
  }

  sendMessage(content) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ content }))
    } else {
      throw new Error('WebSocket not connected')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'User navigated away')
      this.ws = null
    }
  }
}

export default new WebSocketService()
