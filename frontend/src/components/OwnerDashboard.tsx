'use client'

import React, { useState, useEffect } from 'react';
import { QrCode, Camera, Plus, TrendingUp, Users, DollarSign } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import api from '@/lib/api';

interface OwnerDashboardProps {
  onNavigate: (page: string) => void;
}

type Period = 'week' | 'month' | 'quarter';

interface RevenuePoint {
  date: string;
  revenue: number;
}

interface OccupancyPoint {
  date: string;
  occupancy: number;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export function OwnerDashboard({ onNavigate }: OwnerDashboardProps) {
  const [showScanner, setShowScanner] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [manualCode, setManualCode] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [validatedReservation, setValidatedReservation] = useState<any>(null);

  const [revenuePeriod, setRevenuePeriod] = useState<Period>('week');
  const [occupancyPeriod, setOccupancyPeriod] = useState<'week' | 'month'>('week');
  const [revenueData, setRevenueData] = useState<RevenuePoint[]>([]);
  const [occupancyData, setOccupancyData] = useState<OccupancyPoint[]>([]);
  const [revenueLoading, setRevenueLoading] = useState(false);
  const [occupancyLoading, setOccupancyLoading] = useState(false);
  const [revenueError, setRevenueError] = useState(false);
  const [occupancyError, setOccupancyError] = useState(false);

  // Fetch revenue data
  useEffect(() => {
    setRevenueLoading(true);
    setRevenueError(false);
    api
      .get<RevenuePoint[]>(`/owner/analytics/revenue?period=${revenuePeriod}`)
      .then((res) => setRevenueData(res.data))
      .catch(() => setRevenueError(true))
      .finally(() => setRevenueLoading(false));
  }, [revenuePeriod]);

  // Fetch occupancy data
  useEffect(() => {
    setOccupancyLoading(true);
    setOccupancyError(false);
    api
      .get<OccupancyPoint[]>(`/owner/analytics/occupancy?period=${occupancyPeriod}`)
      .then((res) =>
        setOccupancyData(
          res.data.map((d) => ({ ...d, occupancy: Math.round(d.occupancy * 100) }))
        )
      )
      .catch(() => setOccupancyError(true))
      .finally(() => setOccupancyLoading(false));
  }, [occupancyPeriod]);

  const formattedRevenue = revenueData.map((d) => ({ ...d, date: formatDate(d.date) }));
  const formattedOccupancy = occupancyData.map((d) => ({ ...d, date: formatDate(d.date) }));

  const stats = {
    todayReservations: 8,
    activeUsers: 45,
    revenue: 280,
  };

  const handleManualValidation = () => {
    if (manualCode.trim()) {
      setValidatedReservation({
        userName: 'John Doe',
        spaceName: 'Table 4',
        time: '14:00 - 16:00',
      });
      setShowManualEntry(false);
      setShowSuccess(true);
      setManualCode('');
    }
  };

  const handleScannerOpen = () => {
    setShowScanner(true);
    setTimeout(() => {
      setValidatedReservation({
        userName: 'Jane Smith',
        spaceName: 'Study Room A',
        time: '10:00 - 12:00',
      });
      setShowScanner(false);
      setShowSuccess(true);
    }, 2000);
  };

  const PERIOD_LABELS: Record<Period, string> = {
    week: 'Week',
    month: 'Month',
    quarter: 'Quarter',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-gray-900">Owner Dashboard</h1>
          <div className="flex gap-2">
            <Button
              onClick={handleScannerOpen}
              className="bg-[#F9AB18] hover:bg-[#F8A015]"
            >
              <QrCode className="mr-2 h-4 w-4" />
              Scan QR
            </Button>
            <Button
              variant="outline"
              className="border-gray-300"
              onClick={() => onNavigate('owner-admin')}
            >
              <Plus className="mr-2 h-4 w-4" />
              Manage Spaces
            </Button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="mb-8 grid gap-6 md:grid-cols-3">
          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-gray-700">Today's Reservations</CardTitle>
              <Users className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">{stats.todayReservations}</div>
              <p className="text-gray-500">Active bookings</p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-gray-700">Active Users</CardTitle>
              <TrendingUp className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">{stats.activeUsers}</div>
              <p className="text-gray-500">This month</p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-gray-700">Revenue (Credits)</CardTitle>
              <DollarSign className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">{stats.revenue}</div>
              <p className="text-gray-500">This week</p>
            </CardContent>
          </Card>
        </div>

        {/* Analytics Charts */}
        <div className="mb-8 grid gap-6 grid-cols-1 lg:grid-cols-2">

          {/* Revenue Trend Chart */}
          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-gray-900">Revenue Trend</CardTitle>
              <div className="flex gap-1">
                {(['week', 'month', 'quarter'] as Period[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setRevenuePeriod(p)}
                    className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
                      revenuePeriod === p
                        ? 'bg-[#F9AB18] text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {PERIOD_LABELS[p]}
                  </button>
                ))}
              </div>
            </CardHeader>
            <CardContent>
              {revenueLoading && (
                <div className="flex h-[250px] items-center justify-center">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#F9AB18] border-t-transparent" />
                </div>
              )}
              {!revenueLoading && revenueError && (
                <div className="flex h-[250px] items-center justify-center text-sm text-gray-400">
                  Unable to load revenue data
                </div>
              )}
              {!revenueLoading && !revenueError && formattedRevenue.length === 0 && (
                <div className="flex h-[250px] items-center justify-center text-sm text-gray-400">
                  No data for this period
                </div>
              )}
              {!revenueLoading && !revenueError && formattedRevenue.length > 0 && (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={formattedRevenue}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="date" stroke="#6B7280" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#fff',
                        border: '1px solid #E5E7EB',
                        borderRadius: '8px',
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke="#F9AB18"
                      strokeWidth={2}
                      dot={false}
                      name="Revenue (credits)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Occupancy Rate Chart */}
          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-gray-900">Occupancy Rate (%)</CardTitle>
              <div className="flex gap-1">
                {(['week', 'month'] as ('week' | 'month')[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setOccupancyPeriod(p)}
                    className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
                      occupancyPeriod === p
                        ? 'bg-[#F9AB18] text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {PERIOD_LABELS[p]}
                  </button>
                ))}
              </div>
            </CardHeader>
            <CardContent>
              {occupancyLoading && (
                <div className="flex h-[250px] items-center justify-center">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#F9AB18] border-t-transparent" />
                </div>
              )}
              {!occupancyLoading && occupancyError && (
                <div className="flex h-[250px] items-center justify-center text-sm text-gray-400">
                  Unable to load occupancy data
                </div>
              )}
              {!occupancyLoading && !occupancyError && formattedOccupancy.length === 0 && (
                <div className="flex h-[250px] items-center justify-center text-sm text-gray-400">
                  No data for this period
                </div>
              )}
              {!occupancyLoading && !occupancyError && formattedOccupancy.length > 0 && (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={formattedOccupancy}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="date" stroke="#6B7280" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#fff',
                        border: '1px solid #E5E7EB',
                        borderRadius: '8px',
                      }}
                      formatter={(value: number) => [`${value}%`, 'Occupancy']}
                    />
                    <Bar dataKey="occupancy" fill="#F9AB18" radius={[4, 4, 0, 0]} name="Occupancy %" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-gray-900">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              onClick={handleScannerOpen}
              variant="outline"
              className="w-full justify-start border-gray-300"
            >
              <QrCode className="mr-2 h-4 w-4" />
              Scan QR Code
            </Button>
            <Button
              onClick={() => setShowManualEntry(true)}
              variant="outline"
              className="w-full justify-start border-gray-300"
            >
              <Camera className="mr-2 h-4 w-4" />
              Manual Code Entry
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start border-gray-300"
              onClick={() => onNavigate('owner-admin')}
            >
              <Plus className="mr-2 h-4 w-4" />
              Manage Spaces
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* QR Scanner Modal */}
      <Dialog open={showScanner} onOpenChange={setShowScanner}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-gray-900">Scan QR Code</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="relative aspect-square overflow-hidden rounded-lg bg-gray-900">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="h-48 w-48 border-4 border-[#F9AB18] rounded-lg animate-pulse" />
              </div>
              <Camera className="absolute left-1/2 top-1/2 h-16 w-16 -translate-x-1/2 -translate-y-1/2 text-white/50" />
            </div>
            <p className="text-center text-gray-700">Position QR code within the frame</p>
            <Button
              onClick={() => setShowManualEntry(true)}
              variant="outline"
              className="w-full border-gray-300"
            >
              Enter Code Manually
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Manual Entry Modal */}
      <Dialog open={showManualEntry} onOpenChange={setShowManualEntry}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-gray-900">Manual Code Entry</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="code">Reservation Code</Label>
              <Input
                id="code"
                placeholder="e.g., A7-B2-99"
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value)}
                className="border-gray-300"
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleManualValidation}
                className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015]"
              >
                Validate
              </Button>
              <Button
                onClick={() => setShowManualEntry(false)}
                variant="outline"
                className="flex-1 border-gray-300"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Success Modal */}
      <Dialog open={showSuccess} onOpenChange={setShowSuccess}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-gray-900">Check-in Successful!</DialogTitle>
          </DialogHeader>
          {validatedReservation && (
            <div className="space-y-6">
              <div className="flex items-center justify-center">
                <div className="flex h-24 w-24 items-center justify-center rounded-full bg-[#10B981]/10">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#10B981]">
                    <svg
                      className="h-8 w-8 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                </div>
              </div>
              <div className="space-y-2 text-center text-gray-700">
                <p className="text-[#10B981]">Reservation Validated</p>
                <p><strong>Guest:</strong> {validatedReservation.userName}</p>
                <p><strong>Space:</strong> {validatedReservation.spaceName}</p>
                <p><strong>Time:</strong> {validatedReservation.time}</p>
              </div>
              <Button
                onClick={() => setShowSuccess(false)}
                className="w-full bg-[#F9AB18] hover:bg-[#F8A015]"
              >
                Done
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
