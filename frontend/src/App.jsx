import { useState } from 'react'
import Items from './components/items'
import Upload from './components/upload'
import Recommendations from './components/recommendations'

function App() {
  const [wardrobeKey, setWardrobeKey] = useState(0)

  return (
    <div className="flex min-h-screen flex-col items-center bg-gray-50">
      <header className="mt-10 w-full text-center">
        <h1 className="text-6xl font-bold tracking-tight text-gray-900 sm:text-7xl">FitsIt</h1>
      </header>

      <div className="flex w-full max-w-5xl flex-col items-stretch">
        <Upload onSuccess={() => setWardrobeKey((k) => k + 1)} />
        <Items refreshTrigger={wardrobeKey} />
        <Recommendations/>
      </div>
    </div>
  )
}

export default App
