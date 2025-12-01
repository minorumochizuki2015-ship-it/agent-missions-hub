'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export default function ComponentsPage() {
  return (
    <section className="min-h-screen bg-gray-50 p-6" aria-label="Components showcase">
      <div className="max-w-3xl mx-auto space-y-6">
        <nav aria-label="Breadcrumb" className="mb-2">
          <a href="/" className="underline">Home</a>
          <span className="mx-1">/</span>
          <span>Components</span>
        </nav>
        <h1 className="text-2xl font-bold mb-4">Components</h1>
        <header role="banner" aria-label="Components header">
          <h1 className="text-2xl font-bold">shadcn/ui Showcase</h1>
          <p className="text-sm text-gray-600">Card / Badge / Button の最小使用例</p>
        </header>

        <Card aria-labelledby="card-title">
          <CardHeader>
            <CardTitle id="card-title" className="text-sm font-medium">Card Example</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700">Card は KPI ボックスやセクション枠に利用します。</p>
            <div className="mt-2">
              <Badge variant="success" aria-label="Status badge">success</Badge>
            </div>
            <div className="mt-4">
              <Button variant="outline" aria-label="Go to basic forms">
                <Link href="/forms/basic" aria-label="Navigate to Basic Forms">Basic Formsへ</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
