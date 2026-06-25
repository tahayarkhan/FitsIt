import { useCallback, useEffect, useState } from 'react'
import { API_BASE } from '../config'
import { FaHeart, FaRegHeart } from "react-icons/fa";
import { motion } from "framer-motion"



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


    const toggleLike = useCallback(async (rec) => {
        const newLiked = !rec.liked

        try {
            const res = await fetch(`${API_BASE}/recommendations/${rec.id}?liked=${newLiked}`, { method: 'PATCH'})
            const data = await res.json()

            if (!res.ok) {
                throw new Error(data.detail || res.statusText || 'Failed to update like')
            }

            setRecommendations((prev) => 
                prev.map((item) => 
                    item.id === rec.id ? {...item, liked:newLiked} : item
                )
            )

        } catch (e) {
            setError(e.message || 'Failed to update like')
        }

    }, [])


    useEffect(() => {
        load()
    }, [load, refreshTrigger])








    
    return (
        <div className="w-full">
            <div className="mx-5 max-w-7xl px-4 py-12 sm:px-6 lg:px-8">

                
                {!loading && !error && (
                    <motion.h2 
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-2xl font-bold tracking-tight text-gray-900"
                    >
                        Your Recommendations
                    </motion.h2>
                )}
                

                
                {error && (
                <p className="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                    {error}
                </p>
                )}

                <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:gap-6">                
                    
                    {recommendations.map((rec, index) => (
                    
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.1, delay: index * 0.1}}
                        key={index}
                        className="relative rounded-xl border p-4 shadow-sm bg-white w-full"                    
                    >

                        {/* <FaHeart/> */}

                        <button
                            type="button"
                            onClick={() => toggleLike(rec)}
                            className="absolute top-4 right-4"
                        >

                            {rec.liked ? (
                                <FaHeart className="text-red-500 cursor-pointer" />
                            ) : (
                                <FaRegHeart className='text-gray-400 hover:text-red-500 cursor-pointer'/>
                            )}

                        </button>
                        
                    
                        <p className="font-semibold text-lg">
                            Score: {rec.score}
                        </p>

                        <p className="text-sm text-gray-500 mb-4">
                            Confidence: {rec.confidence}
                        </p>

                        {/* Outfit */}
                        <div className="grid grid-rows-3 gap-4">
                            {/* Top */}
                            
                            <div>
                            <img
                                src={rec.outfit.top.image_url}
                                alt="top"
                                className="w-40 h-40 object-cover rounded-lg"
                            />
                            </div>

                            {/* Bottom */}
                            <div>
                            <img
                                src={rec.outfit.bottom.image_url}
                                alt="bottom"
                                className="w-40 h-40 object-cover rounded-lg"
                            />
                            </div>

                            {/* Shoes */}
                            <div>
                            <img
                                src={rec.outfit.shoes.image_url}
                                alt="shoes"
                                className="w-40 h-40 object-cover rounded-lg"
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

                    </motion.div>
                ))}
                </div>

            </div>
        </div>
    )
}

export default Recommendations