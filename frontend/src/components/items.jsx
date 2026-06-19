import { useCallback, useEffect, useState } from 'react'
import { API_BASE } from '../config'

const CATEGORY_ORDER = ['top', 'bottom', 'shoes', 'outerwear', 'other']

const CATEGORY_LABELS = {
  top: 'Tops',
  bottom: 'Bottoms',
  shoes: 'Shoes',
  outerwear: 'Outerwear',
  other: 'Other',
}

function groupByCategory(items) {
  const groups = {}
  for (const key of CATEGORY_ORDER) {
    groups[key] = []
  }
  for (const item of items) {
    const c = item.category && CATEGORY_ORDER.includes(item.category) ? item.category : 'other'
    if (!groups[c]) groups[c] = []
    groups[c].push(item)
  }
  return groups
}

function Items({ refreshTrigger = 0 }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/items`)
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || res.statusText || 'Failed to load wardrobe')
      }
      setItems(data.items ?? [])
    } catch (e) {
      setError(e.message || 'Failed to load wardrobe')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load, refreshTrigger])

  const groups = groupByCategory(items)
  const hasAny = items.length > 0

  return (
    <div className="w-full">
      <div className="mx-5 max-w-7xl px-4 py-12">
        {loading && <p className="mt-8 text-sm text-gray-500">Loading…</p>}
        {error && (
          <p className="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
            {error}
          </p>
        )}
        <h2 className="text-2xl font-bold tracking-tight text-gray-900">Your Items</h2>
        <p className="mt-1 text-sm text-gray-500">Everything you have uploaded so far.</p>

        {!loading && !error && !hasAny && (
          <p className="mt-8 text-sm text-gray-500">No items yet. Upload a photo above.</p>
        )}

        {!loading &&
          !error &&
          hasAny &&
          CATEGORY_ORDER.map((cat) => {
            const list = groups[cat] || []
            if (list.length === 0) return null
            return (
              <section key={cat} className="mt-10">
                <h3 className="text-lg font-semibold text-gray-800">
                  {CATEGORY_LABELS[cat] ?? cat}
                </h3>
                <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {list.map((item) => (
                    <article
                      key={item.id}
                      className="group relative overflow-hidden rounded-lg border border-gray-100 bg-gray-50 shadow-sm"
                    >
                      <img
                        alt={item.category ? `${item.category} clothing` : 'Clothing item'}
                        src={item.image_url}
                        className="aspect-square w-50 h-50 object-cover transition group-hover:opacity-90"
                        loading="lazy"
                      />
                    </article>
                  ))}
                </div>
              </section>
            )
          })}
      </div>
    </div>
  )
}

export default Items
