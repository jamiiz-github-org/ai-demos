import axios from 'axios'

// In dev, Vite proxy handles requests (baseURL = '').
// In production, VITE_API_URL points to the deployed backend e.g. https://jamiiz-ai-demos.onrender.com
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '' })

export async function sendMessage({ message, assistantType, sessionId, history = [] }) {
  const { data } = await api.post('/chat', {
    message,
    assistant_type: assistantType,
    session_id: sessionId,
    history,
  })
  return data
}

export async function uploadDocument(file, namespace = 'document-demo') {
  const form = new FormData()
  form.append('file', file)
  form.append('namespace', namespace)
  const { data } = await api.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function submitLead(lead) {
  const { data } = await api.post('/leads', lead)
  return data
}
