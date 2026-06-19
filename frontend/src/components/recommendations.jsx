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

            setRecommendations(data.items ?? [])

        } catch (e) {
            setError(e.message || 'Failed to load recommendations')
            setItems([])
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
            </div>
        </div>
    )
}

export default Recommendations