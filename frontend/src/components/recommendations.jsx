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

                <div className="mt-8 space-y-6">
                {recommendations.map((rec, index) => (
                    <div
                    key={index}
                    className="rounded-xl border p-4 shadow-sm bg-gray-50"
                    >
                    <p className="font-semibold text-lg">
                        Score: {rec.score}
                    </p>

                    <p className="text-sm text-gray-500 mb-4">
                        Confidence: {rec.confidence}
                    </p>

                    {/* Outfit */}
                    <div className="grid grid-cols-3 gap-4">
                        {/* Top */}
                        <div>
                        <p className="text-sm font-medium">Top</p>
                        <img
                            src={rec.outfit.top.image_url}
                            alt="top"
                            className="w-full h-40 object-cover rounded-lg"
                        />
                        </div>

                        {/* Bottom */}
                        <div>
                        <p className="text-sm font-medium">Bottom</p>
                        <img
                            src={rec.outfit.bottom.image_url}
                            alt="bottom"
                            className="w-full h-40 object-cover rounded-lg"
                        />
                        </div>

                        {/* Shoes */}
                        <div>
                        <p className="text-sm font-medium">Shoes</p>
                        <img
                            src={rec.outfit.shoes.image_url}
                            alt="shoes"
                            className="w-full h-40 object-cover rounded-lg"
                        />
                        </div>
                    </div>

                    {/* Reasons */}
                    {/* <div className="mt-4 flex flex-wrap gap-2">
                        {rec.reasons.map((reason, i) => (
                        <span
                            key={i}
                            className="text-xs bg-black text-white px-2 py-1 rounded-full"
                        >
                            {reason}
                        </span>
                        ))}
                    </div> */}
                    </div>
                ))}
                </div>

            </div>
        </div>
    )
}

export default Recommendations