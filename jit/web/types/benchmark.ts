export interface BenchmarkResult {
  version: string
  time: string
  speedRatio: string
}

export interface BenchmarkData {
  id: string
  title: string
  results: BenchmarkResult[]
  code: string
}

export type BenchmarkDataJSON = BenchmarkData[]

