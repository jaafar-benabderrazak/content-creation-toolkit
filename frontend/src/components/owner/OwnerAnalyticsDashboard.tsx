import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, DollarSign, Users, Star, Calendar, Trophy } from 'lucide-react';

interface AnalyticsData {
  revenue: { day: string; amount: number }[];
  reservations: { day: string; count: number }[];
  spaceUtilization: { name: string; value: number }[];
  topSpaces: { name: string; bookings: number; revenue: number }[];
  customerStats: {
    total: number;
    returning: number;
    new: number;
    avgVisits: number;
  };
  revenueStats: {
    total: number;
    thisWeek: number;
    lastWeek: number;
    change: number;
  };
  ratingStats: {
    average: number;
    total: number;
    distribution: { rating: number; count: number }[];
  };
}

interface OwnerAnalyticsDashboardProps {
  establishmentId: string;
}

export function OwnerAnalyticsDashboard({ establishmentId }: OwnerAnalyticsDashboardProps) {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('week');

  useEffect(() => {
    loadAnalytics();
  }, [establishmentId, timeRange]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the backend
      // For now, we'll use mock data
      const mockData: AnalyticsData = {
        revenue: [
          { day: 'Mon', amount: 120 },
          { day: 'Tue', amount: 150 },
          { day: 'Wed', amount: 90 },
          { day: 'Thu', amount: 180 },
          { day: 'Fri', amount: 220 },
          { day: 'Sat', amount: 200 },
          { day: 'Sun', amount: 140 }
        ],
        reservations: [
          { day: 'Mon', count: 12 },
          { day: 'Tue', count: 19 },
          { day: 'Wed', count: 15 },
          { day: 'Thu', count: 22 },
          { day: 'Fri', count: 28 },
          { day: 'Sat', count: 24 },
          { day: 'Sun', count: 18 }
        ],
        spaceUtilization: [
          { name: 'Tables', value: 65 },
          { name: 'Desks', value: 45 },
          { name: 'Rooms', value: 80 }
        ],
        topSpaces: [
          { name: 'Table 1', bookings: 45, revenue: 180 },
          { name: 'Study Room A', bookings: 38, revenue: 152 },
          { name: 'Desk 3', bookings: 32, revenue: 96 },
          { name: 'Table 5', bookings: 28, revenue: 112 }
        ],
        customerStats: {
          total: 156,
          returning: 89,
          new: 67,
          avgVisits: 3.2
        },
        revenueStats: {
          total: 1100,
          thisWeek: 1100,
          lastWeek: 950,
          change: 15.8
        },
        ratingStats: {
          average: 4.6,
          total: 89,
          distribution: [
            { rating: 5, count: 56 },
            { rating: 4, count: 22 },
            { rating: 3, count: 8 },
            { rating: 2, count: 2 },
            { rating: 1, count: 1 }
          ]
        }
      };

      setAnalytics(mockData);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !analytics) {
    return <div className="flex items-center justify-center p-8">Loading analytics...</div>;
  }

  const COLORS = ['#F9AB18', '#10B981', '#3B82F6', '#EF4444'];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-gray-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{analytics.revenueStats.total}</div>
            <p className="text-xs text-gray-500">
              <span className={analytics.revenueStats.change >= 0 ? 'text-green-600' : 'text-red-600'}>
                {analytics.revenueStats.change >= 0 ? '+' : ''}{analytics.revenueStats.change}%
              </span> from last week
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Total Customers</CardTitle>
            <Users className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{analytics.customerStats.total}</div>
            <p className="text-xs text-gray-500">
              {analytics.customerStats.new} new this week
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Avg. Rating</CardTitle>
            <Star className="h-4 w-4 text-[#F9AB18]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{analytics.ratingStats.average}</div>
            <p className="text-xs text-gray-500">
              {analytics.ratingStats.total} reviews
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Returning Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">
              {Math.round((analytics.customerStats.returning / analytics.customerStats.total) * 100)}%
            </div>
            <p className="text-xs text-gray-500">
              {analytics.customerStats.returning} returning customers
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-gray-900">Revenue Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analytics.revenue}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="day" stroke="#6B7280" />
                <YAxis stroke="#6B7280" />
                <Tooltip />
                <Line type="monotone" dataKey="amount" stroke="#F9AB18" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-gray-900">Reservations</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.reservations}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="day" stroke="#6B7280" />
                <YAxis stroke="#6B7280" />
                <Tooltip />
                <Bar dataKey="count" fill="#10B981" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-gray-900">Space Utilization</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analytics.spaceUtilization}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {analytics.spaceUtilization.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-gray-900">Top Performing Spaces</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.topSpaces.map((space, index) => (
                <div key={space.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                      index === 0 ? 'bg-[#F9AB18]' : index === 1 ? 'bg-gray-400' : index === 2 ? 'bg-[#CD7F32]' : 'bg-gray-300'
                    }`}>
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{space.name}</div>
                      <div className="text-sm text-gray-500">{space.bookings} bookings</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-gray-900">{space.revenue}</div>
                    <div className="text-xs text-gray-500">credits</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Rating Distribution */}
      <Card className="border-gray-200">
        <CardHeader>
          <CardTitle className="text-gray-900">Rating Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analytics.ratingStats.distribution.sort((a, b) => b.rating - a.rating).map((item) => {
              const percentage = (item.count / analytics.ratingStats.total) * 100;
              return (
                <div key={item.rating} className="flex items-center gap-4">
                  <div className="flex items-center gap-1 w-16">
                    <span className="font-medium">{item.rating}</span>
                    <Star className="h-4 w-4 text-[#F9AB18] fill-[#F9AB18]" />
                  </div>
                  <div className="flex-1">
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-[#F9AB18] h-3 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="w-16 text-right text-sm text-gray-600">
                    {item.count} ({Math.round(percentage)}%)
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

