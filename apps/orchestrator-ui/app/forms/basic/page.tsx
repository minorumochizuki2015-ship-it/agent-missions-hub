'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function BasicFormPage() {
  const [values, setValues] = useState({ name: '', email: '', agree: false })
  const [errors, setErrors] = useState<{ name?: string; email?: string }>({})
  const [submitted, setSubmitted] = useState(false)

  const validate = () => {
    const e: any = {}
    if (!values.name.trim()) e.name = '氏名は必須です'
    if (!values.email.match(/^[^@\s]+@[^@\s]+\.[^@\s]+$/)) e.email = '有効なメール形式で入力してください'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  return (
    <section className="min-h-screen bg-gray-50 p-6" aria-label="Basic forms">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Basic Forms</h1>
        <Card aria-labelledby="form-title">
          <CardHeader>
            <CardTitle id="form-title" className="text-sm font-medium">Basic Accessible Form</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              role="form"
              aria-describedby="form-desc"
              onSubmit={(e) => {
                e.preventDefault()
                if (validate()) setSubmitted(true)
              }}
              noValidate
            >
              <p id="form-desc" className="sr-only">氏名とメールを入力し、同意チェック後に送信します。</p>

              <div className="mb-4">
                <label htmlFor="name" className="block text-sm font-medium">氏名 <span aria-hidden="true">*</span></label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  aria-required="true"
                  aria-invalid={Boolean(errors.name)}
                  aria-describedby={errors.name ? 'name-error' : undefined}
                  className="mt-1 w-full border rounded p-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={values.name}
                  onChange={(e) => setValues({ ...values, name: e.target.value })}
                />
                {errors.name && (
                  <p id="name-error" role="alert" className="mt-1 text-xs text-danger-600">{errors.name}</p>
                )}
              </div>

              <div className="mb-4">
                <label htmlFor="email" className="block text-sm font-medium">メール <span aria-hidden="true">*</span></label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  aria-required="true"
                  aria-invalid={Boolean(errors.email)}
                  aria-describedby={errors.email ? 'email-error' : 'email-help'}
                  className="mt-1 w-full border rounded p-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={values.email}
                  onChange={(e) => setValues({ ...values, email: e.target.value })}
                />
                <p id="email-help" className="mt-1 text-xs text-gray-500">例: user@example.com</p>
                {errors.email && (
                  <p id="email-error" role="alert" className="mt-1 text-xs text-danger-600">{errors.email}</p>
                )}
              </div>

              <div className="mb-4">
                <input
                  id="agree"
                  name="agree"
                  type="checkbox"
                  aria-checked={values.agree}
                  className="mr-2 align-middle"
                  checked={values.agree}
                  onChange={(e) => setValues({ ...values, agree: e.target.checked })}
                />
                <label htmlFor="agree" className="text-sm">利用規約に同意します</label>
              </div>

              <Button type="submit" variant="default" aria-label="フォーム送信">
                送信
              </Button>

              <div className="mt-4" aria-live="polite">
                {submitted && <p className="text-sm text-success-600">送信しました</p>}
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
