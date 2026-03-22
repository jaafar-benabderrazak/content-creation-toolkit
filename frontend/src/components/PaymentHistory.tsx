'use client'

import { useEffect, useState } from 'react'
import { format, parseISO } from 'date-fns'
import { CreditCard, Receipt } from 'lucide-react'
import { Card, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { api } from '@/lib/api'

interface PaymentRecord {
  id: string
  space_name: string
  establishment_name?: string
  start_time: string
  cost_credits: number
  status: 'confirmed' | 'completed'
}

function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy')
  } catch {
    return dateStr
  }
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    confirmed: 'bg-[#10B981] text-white',
    completed: 'bg-gray-500 text-white',
  }
  return (
    <Badge className={colorMap[status] ?? 'bg-gray-200 text-gray-900'}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  )
}

export function PaymentHistory() {
  const [records, setRecords] = useState<PaymentRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get('/payments/history')
      .then((res) => {
        setRecords(res.data ?? [])
      })
      .catch((err) => {
        setError(err?.response?.data?.detail ?? 'Failed to load payment history.')
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded-lg bg-gray-100" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-gray-200">
        <CardContent className="py-10 text-center">
          <p className="text-red-500">{error}</p>
        </CardContent>
      </Card>
    )
  }

  if (records.length === 0) {
    return (
      <Card className="border-gray-200">
        <CardContent className="py-16 text-center">
          <Receipt className="mx-auto mb-3 h-10 w-10 text-gray-300" />
          <p className="text-gray-500">No payments yet</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      {records.map((record) => (
        <Card key={record.id} className="border-gray-200">
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#F9AB18]/10">
                <CreditCard className="h-5 w-5 text-[#F9AB18]" />
              </div>
              <div>
                <p className="font-medium text-gray-900">{record.space_name}</p>
                {record.establishment_name && (
                  <p className="text-sm text-gray-500">{record.establishment_name}</p>
                )}
                <p className="text-xs text-gray-400">{formatDate(record.start_time)}</p>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className="font-semibold text-gray-900">
                €{(record.cost_credits / 100).toFixed(2)}
              </span>
              <StatusBadge status={record.status} />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
