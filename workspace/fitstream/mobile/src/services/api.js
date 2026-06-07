/**
 * FitStream Mobile API Client
 * Communicates with the FitStream backend via the mobile-optimized /m/ endpoints.
 */

const DEFAULT_API = 'http://localhost:8000';

class FitStreamAPI {
  constructor(baseUrl = DEFAULT_API) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async _get(path) {
    const res = await fetch(`${this.baseUrl}${path}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  }

  async _postForm(path, formData) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `API error: ${res.status}`);
    }
    return res.json();
  }

  // ─── Status ───
  async getStatus() {
    return this._get('/m/status');
  }

  // ─── Generate ───
  async generate({ imageUri, prompt, mode = 'animate', style = 'cinematic', quality = 'draft' }) {
    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('mode', mode);
    formData.append('style', style);
    formData.append('quality', quality);

    // Append image as file
    const filename = imageUri.split('/').pop();
    const ext = filename.split('.').pop();
    formData.append('image', {
      uri: imageUri,
      name: filename,
      type: `image/${ext === 'png' ? 'png' : 'jpeg'}`,
    });

    return this._postForm('/m/generate', formData);
  }

  // ─── Job Status ───
  async getJobStatus(jobId) {
    return this._get(`/m/job/${jobId}`);
  }

  async pollUntilDone(jobId, intervalMs = 2000, maxAttempts = 150) {
    for (let i = 0; i < maxAttempts; i++) {
      const status = await this.getJobStatus(jobId);
      if (status.status === 'done') return status;
      if (status.status === 'failed') throw new Error(status.error || 'Generation failed');
      await new Promise(r => setTimeout(r, intervalMs));
    }
    throw new Error('Timeout waiting for generation');
  }

  // ─── Gallery ───
  async getGallery(page = 0, size = 12) {
    return this._get(`/m/gallery?page=${page}&size=${size}`);
  }

  // ─── Styles & Templates ───
  async getStyles() {
    return this._get('/m/styles');
  }

  async getTemplates(category = null) {
    const q = category ? `?category=${category}` : '';
    return this._get(`/m/templates${q}`);
  }

  // ─── Video URL ───
  getVideoUrl(jobId) {
    return `${this.baseUrl}/api/v1/jobs/${jobId}/video`;
  }

  // ─── Health ───
  async getHealth() {
    return this._get('/health');
  }
}

export default FitStreamAPI;
export { DEFAULT_API };
