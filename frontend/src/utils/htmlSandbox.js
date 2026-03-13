/**
 * Create a sandboxed iframe srcdoc from HTML content.
 * The sandbox attribute limits what the iframe can do.
 */
export function createSandboxedHtml(htmlContent) {
  return htmlContent || ''
}

/**
 * Returns the sandbox attributes for the visualization iframe.
 */
export function getSandboxAttributes() {
  return 'allow-scripts'
}
