import { useState } from 'react'
import { API_BASE } from '../config'

const CATEGORIES = [
  { value: 'top', label: 'Top' },
  { value: 'bottom', label: 'Bottom' },
  { value: 'shoes', label: 'Shoes' },
  { value: 'outerwear', label: 'Outerwear' },
  { value: 'other', label: 'Other' },
]

function Upload({ onSuccess }) {
  const [category, setCategory] = useState('top')
  const [file, setFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    if (!file) {
      setError('Choose an image file.')
      return
    }
    const body = new FormData()
    body.append('file', file)
    body.append('category', category)
    setSubmitting(true)
    try {
      const res = await fetch(`${API_BASE}/upload-item`, {
        method: 'POST',
        body,
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const msg =
          typeof data.detail === 'string'
            ? data.detail
            : Array.isArray(data.detail)
              ? data.detail.map((d) => d.msg).join(' ')
              : res.statusText
        throw new Error(msg || 'Upload failed')
      }
      setFile(null)
      e.target.reset()
      setCategory('top')
      onSuccess?.()
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="self-center w-full py-8">
      <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900">Add an item</h2>
      <p className="text-center mt-1 text-sm text-gray-500">Choose a category and upload a clothing photo.</p>

      <div className="mt-4">
        <label htmlFor="category" className="block text-sm font-medium text-gray-700">
          Category
        </label>
        <select
          id="category"
          name="category"
          value={category}
          onChange={(ev) => setCategory(ev.target.value)}
          className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-6 flex justify-center rounded-lg border border-dashed border-gray-900/25 px-6 py-10">
        <div className="text-center">
          <svg
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
            className="mx-auto size-12 text-gray-300"
          >
            <path
              fillRule="evenodd"
              d="M1.5 6a2.25 2.25 0 0 1 2.25-2.25h16.5A2.25 2.25 0 0 1 22.5 6v12a2.25 2.25 0 0 1-2.25 2.25H3.75A2.25 2.25 0 0 1 1.5 18V6ZM3 16.06V18c0 .414.336.75.75.75h16.5A.75.75 0 0 0 21 18v-1.94l-2.69-2.689a1.5 1.5 0 0 0-2.12 0l-.88.879.97.97a.75.75 0 1 1-1.06 1.06l-5.16-5.159a1.5 1.5 0 0 0-2.12 0L3 16.061Zm10.125-7.81a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Z"
              clipRule="evenodd"
            />
          </svg>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-1 text-sm text-gray-600">
            <label
              htmlFor="file-upload"
              className="relative cursor-pointer rounded-md font-semibold text-indigo-600 hover:text-indigo-500 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-indigo-600"
            >
              <span>Upload a file</span>
              <input
                id="file-upload"
                name="file-upload"
                type="file"
                accept="image/png,image/jpeg,image/gif,image/webp"
                className="sr-only"
                onChange={(ev) => setFile(ev.target.files?.[0] ?? null)}
              />
            </label>
            <span className="pl-1">or drag and drop below</span>
          </div>
          <p className="mt-2 text-xs text-gray-500">PNG, JPG, GIF, WebP up to your storage limit</p>
          {file && (
            <p className="mt-2 text-sm text-gray-700">
              Selected: <span className="font-medium">{file.name}</span>
            </p>
          )}
        </div>
      </div>

      {error && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      <div className="mt-6 flex justify-center">
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? 'Uploading…' : 'Upload'}
        </button>
      </div>

    </form>
  )
}

export default Upload
