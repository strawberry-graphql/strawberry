import SyntaxHighlighter from "react-syntax-highlighter";
import { dracula } from "react-syntax-highlighter/dist/esm/styles/hljs";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import data from "@/data/benchmarks.json";

interface BenchmarkTabsProps {
  data: typeof data;
}

export function BenchmarkTabs({ data }: BenchmarkTabsProps) {
  return (
    <Tabs defaultValue={data[0].id} className="w-full">
      <TabsList className="border-b rounded-none w-full justify-start h-auto p-0">
        {data.map((benchmark) => (
          <TabsTrigger
            key={benchmark.id}
            value={benchmark.id}
            className="px-6 py-3 rounded-none data-[state=active]:text-[#FF3366] data-[state=active]:border-b-2 data-[state=active]:border-[#FF3366]"
          >
            {benchmark.title}
          </TabsTrigger>
        ))}
      </TabsList>
      {data.map((benchmark) => (
        <TabsContent key={benchmark.id} value={benchmark.id}>
          <Card className="border rounded-lg mt-6">
            <CardHeader>
              <CardTitle className="text-xl font-mono text-[#FF3366]">
                {benchmark.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {benchmark.results.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b">
                        <th className="py-3 px-4 font-medium">Version</th>
                        <th className="py-3 px-4 font-medium">Time</th>
                        <th className="py-3 px-4 font-medium">Speed Ratio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmark.results.map((result, index) => (
                        <tr key={index} className="border-b">
                          <td className="py-3 px-4">{result.version}</td>
                          <td className="py-3 px-4 font-mono">{result.time}</td>
                          <td
                            className={`py-3 px-4 font-mono ${
                              result.speedRatio !== "1.00x"
                                ? "text-[#FF3366]"
                                : ""
                            }`}
                          >
                            {result.speedRatio}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-600">Results will be displayed here.</p>
              )}
            </CardContent>
          </Card>
          <Card className="border rounded-lg mt-6 bg-[#1E1E1E]">
            <CardHeader>
              <CardTitle className="text-lg font-mono text-white">
                Jitted code
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SyntaxHighlighter
                language="python"
                style={dracula}
                customStyle={{
                  background: "none",
                  fontSize: "14px",
                  padding: "0",
                }}
              >
                {benchmark.code}
              </SyntaxHighlighter>
            </CardContent>
          </Card>
          <Card className="border rounded-lg mt-6 bg-[#1E1E1E]">
            <CardHeader>
              <CardTitle className="text-lg font-mono text-white">
                Benchmark Query
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SyntaxHighlighter
                language="graphql"
                style={dracula}
                customStyle={{
                  background: "none",
                  fontSize: "14px",
                  padding: "0",
                }}
              >
                {benchmark.query}
              </SyntaxHighlighter>
            </CardContent>
          </Card>
        </TabsContent>
      ))}
    </Tabs>
  );
}
