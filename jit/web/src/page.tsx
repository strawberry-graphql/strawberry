import Image from 'next/image'
import { BenchmarkTabs } from './components/benchmark-tabs'
import benchmarks from './data/benchmarks.json'
import { BenchmarkDataJSON } from './types/benchmark'

export default function Home() {
  const benchmarkData: BenchmarkDataJSON = benchmarks

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <Image
            src="https://github.com/strawberry-graphql/strawberry/raw/main/.github/logo.png"
            alt="Strawberry GraphQL"
            width={48}
            height={48}
            className="w-12 h-auto"
          />
          <h1 className="text-4xl font-bold">Benchmark Results</h1>
        </div>
        
        <BenchmarkTabs data={benchmarkData} />
      </div>
    </main>
  )
}

