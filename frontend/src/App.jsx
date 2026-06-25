import { useState } from 'react'
import Navigation from './components/navigation'
import { motion } from "framer-motion"


function App() {

  return (
    <div className="flex min-h-screen flex-col items-center bg-gray-50">
      <header className="mt-10 w-full text-center">
        <motion.h1
          whileHover={{scale:1.5}}
          className="text-6xl font-bold tracking-tight text-gray-900 sm:text-7xl"
        >
          FitsIt
        </motion.h1>
      </header>
      <Navigation/>
    </div>
  )
}

export default App
