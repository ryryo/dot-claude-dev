import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-indigo-900 mb-2">
            Tarot Demo App
          </h1>
          <p className="text-gray-600 text-lg">
            Tailwind CSS Styling Verification
          </p>
        </header>

        {/* Card Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Card 1: Colors */}
          <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-shadow">
            <h2 className="text-xl font-semibold text-indigo-700 mb-3">
              Colors
            </h2>
            <div className="space-y-2">
              <div className="h-8 bg-blue-500 rounded"></div>
              <div className="h-8 bg-green-500 rounded"></div>
              <div className="h-8 bg-purple-500 rounded"></div>
            </div>
          </div>

          {/* Card 2: Typography */}
          <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-shadow">
            <h2 className="text-xl font-semibold text-indigo-700 mb-3">
              Typography
            </h2>
            <p className="text-sm text-gray-500">Small text</p>
            <p className="text-base text-gray-700">Base text</p>
            <p className="text-lg font-medium text-gray-900">Large text</p>
          </div>

          {/* Card 3: Interactive */}
          <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-shadow">
            <h2 className="text-xl font-semibold text-indigo-700 mb-3">
              Interactive
            </h2>
            <button
              onClick={() => setCount(count + 1)}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded transition-colors"
            >
              Count: {count}
            </button>
          </div>
        </div>

        {/* Responsive Grid */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold text-indigo-900 mb-4">
            Responsive Layout
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {[1, 2, 3, 4, 5, 6].map((num) => (
              <div
                key={num}
                className="bg-indigo-100 text-indigo-800 font-bold text-center py-4 rounded"
              >
                {num}
              </div>
            ))}
          </div>
        </div>

        {/* Spacing & Flexbox */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Left Column</h3>
            <p className="text-gray-600">Flexbox layout with responsive direction</p>
          </div>
          <div className="flex-1 bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Right Column</h3>
            <p className="text-gray-600">Stacks vertically on mobile, side-by-side on desktop</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
