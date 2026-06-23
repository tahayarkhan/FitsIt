import { useCallback, useEffect, useState } from 'react'
import { API_BASE } from '../config'




const Wardrobe = ({ refreshTrigger = 0 }) => {
    
    const [outfits, setOutfits] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const load = useCallback(async () => {
        setLoading(true)
        setError(null)

        try {
            const res = await fetch(`${API_BASE}/wardrobe`)
            const data = await res.json()

            if (!res.ok) {
                throw new Error(data.detail || res.statusText || 'Failed to load wardrobe')
            }

            setOutfits(data.outfits)
        } catch (e) {
            setError(e.message || 'Failed to load wardrobe')
            setOutfits([])
        } finally {
            setLoading(false)
        }

    }, [])

    useEffect(() => {
        load()
    }, [load, refreshTrigger])





    return (
        <div className="w-full">
            
            <div className="mx-5 max-w-7xl px-4 py-12 sm:px-6 lg:px-8">

                <h2 className="text-2xl font-bold tracking-tight text-gray-900">Your Wardrobe</h2>

                
                {loading && <p className="mt-8 text-sm text-gray-500">Loading…</p>}
                {error && (
                <p className="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                    {error}
                </p>
                )}


                <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:gap-6">

                    {outfits.map((outfit, index) => (
                        
                        <div
                        key={index}
                        className="relative rounded-xl border p-4 shadow-sm bg-white w-full"                    
                        >
                            
                            <p className="font-semibold text-lg">
                                Score: {outfit.score}
                            </p>

                            <p className="text-sm text-gray-500 mb-4">
                                Confidence: {outfit.confidence}
                            </p>


                            {/* Outfit */}
                            <div className="grid grid-rows-3 gap-4">
                                {/* Top */}
                                
                                <div>
                                <img
                                    src={outfit.top.image_url}
                                    alt="top"
                                    className="w-40 h-40 object-cover rounded-lg"
                                />
                                </div>

                                {/* Bottom */}
                                <div>
                                <img
                                    src={outfit.bottom.image_url}
                                    alt="bottom"
                                    className="w-40 h-40 object-cover rounded-lg"
                                />
                                </div>

                                {/* Shoes */}
                                <div>
                                <img
                                    src={outfit.shoes.image_url}
                                    alt="shoes"
                                    className="w-40 h-40 object-cover rounded-lg"
                                />
                                </div>
                            </div>


                        </div>
                    ))}

                </div>           

            </div>

        </div>
    )
}

export default Wardrobe