import { useCallback, useEffect, useState } from 'react'
import { API_BASE } from '../config'


const Recommendations = ({ refreshTrigger = 0 }) => {
    const [recommendations, setRecommendations] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const load = useCallback(async () => {
        setLoading(true)
        setError(null)

        try {
            
            const res = await fetch(`${API_BASE}/recommendations`)
            const data = await res.json()
            if (!res.ok) {
                throw new Error(data.detail || res.statusText || 'Failed to load recommendations')
            }

            setRecommendations(data.recommendations ?? [])

        } catch (e) {
            setError(e.message || 'Failed to load recommendations')
            setRecommendations([])
        } finally {
            setLoading(false)
        }

    }, [])

    useEffect(() => {
        load()
    }, [load, refreshTrigger])


    
    return (
        <div className="w-full bg-white">
            <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
                <h2 className="text-2xl font-bold tracking-tight text-gray-900">Your Recommendations</h2>

                {loading && <p className="mt-8 text-sm text-gray-500">Loading…</p>}
                {error && (
                <p className="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                    {error}
                </p>
                )}







            </div>
        </div>
    )
}

export default Recommendations