'use client'

import { useState } from 'react'
import { Loader2, CreditCard, X } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { api } from '@/lib/api'
import { toast } from 'sonner'

interface ReservationCheckoutProps {
  reservationId: string
  spaceName: string
  amount: number // cost_credits
  onCancel: () => void
}

export function ReservationCheckout({
  reservationId,
  spaceName,
  amount,
  onCancel,
}: ReservationCheckoutProps) {
  const [loading, setLoading] = useState(false)

  const handlePayNow = async () => {
    setLoading(true)
    try {
      const response = await api.post('/payments/checkout-session', {
        reservation_id: reservationId,
      })
      const { checkout_url } = response.data
      if (checkout_url) {
        window.location.href = checkout_url
      } else {
        toast.error('Invalid checkout response. Please try again.')
        setLoading(false)
      }
    } catch (error: unknown) {
      const message =
        error instanceof Error
          ? error.message
          : 'Failed to create checkout session. Please try again.'
      toast.error(message)
      setLoading(false)
    }
  }

  const amountEur = (amount / 100).toFixed(2)

  return (
    <Card className="mx-auto w-full max-w-md border-gray-200 shadow-lg">
      <CardHeader className="border-b border-gray-100 pb-4">
        <CardTitle className="flex items-center gap-2 text-gray-900">
          <CreditCard className="h-5 w-5 text-[#F9AB18]" />
          Complete Payment
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="mb-6 space-y-3">
          <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
            <span className="text-gray-600">Space</span>
            <span className="font-medium text-gray-900">{spaceName}</span>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
            <span className="text-gray-600">Credits</span>
            <span className="font-medium text-gray-900">{amount} credits</span>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-[#F9AB18]/10 px-4 py-3">
            <span className="font-medium text-gray-900">Total</span>
            <span className="text-lg font-bold text-[#F9AB18]">€{amountEur}</span>
          </div>
        </div>

        <div className="flex gap-3">
          <Button
            onClick={handlePayNow}
            disabled={loading}
            className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015] disabled:opacity-60"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Redirecting...
              </>
            ) : (
              <>
                <CreditCard className="mr-2 h-4 w-4" />
                Pay Now
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={loading}
            className="border-gray-300 text-gray-700"
          >
            <X className="mr-1 h-4 w-4" />
            Cancel
          </Button>
        </div>

        <p className="mt-4 text-center text-xs text-gray-400">
          You will be redirected to Stripe&apos;s secure checkout page.
        </p>
      </CardContent>
    </Card>
  )
}
