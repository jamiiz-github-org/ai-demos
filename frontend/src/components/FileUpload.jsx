import { useState, useRef } from 'react'
import { uploadDocument } from '../api'

export default function FileUpload({ onUploaded }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  async function handleFile(file) {
    if (!file) return
    const allowed = ['.pdf', '.docx', '.txt', '.md']
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) {
      setError(`Unsupported file type. Please upload: ${allowed.join(', ')}`)
      return
    }
    setError(null)
    setUploading(true)
    try {
      const result = await uploadDocument(file)
      setUploadedFile({ name: file.name, chunks: result.chunks })
      onUploaded?.({ name: file.name, ...result })
    } catch (err) {
      setError('Upload failed. Make sure the backend is running.')
    } finally {
      setUploading(false)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  return (
    <div className="file-upload-section">
      <div
        className={`dropzone ${dragging ? 'dragging' : ''} ${uploadedFile ? 'uploaded' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
        />

        {uploading ? (
          <div className="upload-status">
            <div className="upload-spinner" />
            <p>Processing document…</p>
          </div>
        ) : uploadedFile ? (
          <div className="upload-status success">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <p><strong>{uploadedFile.name}</strong></p>
            <p className="upload-meta">{uploadedFile.chunks} chunks indexed — ready to ask questions</p>
            <button className="upload-replace" onClick={(e) => { e.stopPropagation(); setUploadedFile(null) }}>
              Upload a different file
            </button>
          </div>
        ) : (
          <div className="upload-prompt">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p><strong>Drop your document here</strong></p>
            <p className="upload-meta">or click to browse — PDF, DOCX, TXT, MD · Max 20MB</p>
          </div>
        )}
      </div>

      {error && <p className="upload-error">{error}</p>}
    </div>
  )
}
