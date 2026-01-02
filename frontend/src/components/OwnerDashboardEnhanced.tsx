import React, { useState, useEffect } from 'react';
import { QrCode, Plus, TrendingUp, Users, DollarSign, MapPin, Star } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '../lib/api';

interface OwnerDashboardProps {
  onNavigate: (page: string) => void;
}

interface DashboardStats {
  total_establishments: number;
  total_spaces: number;
  total_reservations: number;
  total_revenue_credits: number;
  active_reservations: number;
  pending_reservations: number;
  average_rating: number | null;
  total_reviews: number;
}

interface Establishment {
  id: string;
  name: string;
  category: string;
  city: string;
  is_active: boolean;
}

export function OwnerDashboard({ onNavigate }: OwnerDashboardProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [establishments, setEstablishments] = useState<Establishment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch dashboard stats
      const statsResponse = await api.get('/owner/dashboard');
      setStats(statsResponse.data);

      // Fetch establishments
      const establishmentsResponse = await api.get('/owner/establishments');
      setEstablishments(establishmentsResponse.data);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#F9AB18] mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <p className="text-red-600 text-center">{error}</p>
            <Button 
              onClick={loadDashboardData} 
              className="mt-4 w-full bg-[#F9AB18] hover:bg-[#F8A015]"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Owner Dashboard</h1>
            <p className="mt-1 text-gray-600">Manage your establishments and reservations</p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => onNavigate('owner-admin')}
              className="bg-[#F9AB18] hover:bg-[#F8A015]"
            >
              <Plus className="mr-2 h-4 w-4" />
              Manage Spaces
            </Button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="mb-8 grid gap-6 md:grid-cols-4">
          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-700">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-[#F9AB18]" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{stats?.total_revenue_credits || 0}</div>
              <p className="text-xs text-gray-500">Credits earned</p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-700">Active Reservations</CardTitle>
              <Users className="h-4 w-4 text-[#F9AB18]" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{stats?.active_reservations || 0}</div>
              <p className="text-xs text-gray-500">{stats?.pending_reservations || 0} pending</p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-700">Total Spaces</CardTitle>
              <MapPin className="h-4 w-4 text-[#F9AB18]" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{stats?.total_spaces || 0}</div>
              <p className="text-xs text-gray-500">Across {stats?.total_establishments || 0} locations</p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-700">Average Rating</CardTitle>
              <Star className="h-4 w-4 text-[#F9AB18]" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {stats?.average_rating ? stats.average_rating.toFixed(1) : 'N/A'}
              </div>
              <p className="text-xs text-gray-500">{stats?.total_reviews || 0} reviews</p>
            </CardContent>
          </Card>
        </div>

        {/* Establishments List */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-gray-200">
            <CardHeader>
              <CardTitle className="text-gray-900">Your Establishments</CardTitle>
            </CardHeader>
            <CardContent>
              {establishments.length === 0 ? (
                <div className="text-center py-8">
                  <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">No establishments yet</p>
                  <Button
                    onClick={() => onNavigate('owner-admin')}
                    className="bg-[#F9AB18] hover:bg-[#F8A015]"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Your First Establishment
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {establishments.map((establishment) => (
                    <div
                      key={establishment.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-[#F9AB18] transition-colors cursor-pointer"
                      onClick={() => onNavigate('owner-admin')}
                    >
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{establishment.name}</h3>
                        <p className="text-sm text-gray-600">
                          {establishment.category} • {establishment.city}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            establishment.is_active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {establishment.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader>
              <CardTitle className="text-gray-900">Reservation Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={[
                    { day: 'Mon', reservations: 12 },
                    { day: 'Tue', reservations: 19 },
                    { day: 'Wed', reservations: 15 },
                    { day: 'Thu', reservations: 22 },
                    { day: 'Fri', reservations: 28 },
                    { day: 'Sat', reservations: 24 },
                    { day: 'Sun', reservations: 18 },
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="day" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                      }}
                    />
                    <Bar dataKey="reservations" fill="#F9AB18" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="mt-6 border-gray-200">
          <CardHeader>
            <CardTitle className="text-gray-900">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2 border-gray-300"
                onClick={() => onNavigate('owner-admin')}
              >
                <Plus className="h-6 w-6 text-[#F9AB18]" />
                <span>Add New Space</span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2 border-gray-300"
                onClick={() => onNavigate('owner-admin')}
              >
                <QrCode className="h-6 w-6 text-[#F9AB18]" />
                <span>Generate QR Codes</span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2 border-gray-300"
                onClick={loadDashboardData}
              >
                <TrendingUp className="h-6 w-6 text-[#F9AB18]" />
                <span>View Analytics</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

