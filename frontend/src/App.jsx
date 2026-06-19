import { useState } from 'react'
import Navigation from './components/navigation'

function App() {

  return (
    <div className="flex min-h-screen flex-col items-center bg-gray-50">
      <header className="mt-10 w-full text-center">
        <h1 className="text-6xl font-bold tracking-tight text-gray-900 sm:text-7xl">FitsIt</h1>
      </header>
      <Navigation/>
    </div>
  )
}

export default App
