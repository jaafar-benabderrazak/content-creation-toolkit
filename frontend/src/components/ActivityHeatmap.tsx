'use client';

import { useEffect, useState } from 'react';
import { Calendar, TrendingUp, Award } from 'lucide-react';

interface HeatmapData {
  heatmap: number[][];
  days: string[];
  total_hours: number;
}

export function ActivityHeatmap() {
  const [data, setData] = useState<HeatmapData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHeatmap();
  }, []);

  const loadHeatmap = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/activity/heatmap`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
        const heatmapData = await response.json();
        setData(heatmapData);
      }
    } catch (error) {
      console.error('Error loading heatmap:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!data) return null;

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const maxValue = Math.max(...data.heatmap.flat());

  const getColor = (value: number) => {
    if (value === 0) return 'bg-gray-100';
    const intensity = value / maxValue;
    if (intensity < 0.25) return 'bg-green-200';
    if (intensity < 0.5) return 'bg-green-400';
    if (intensity < 0.75) return 'bg-green-600';
    return 'bg-green-800';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-6">
        <Calendar className="w-6 h-6 text-blue-600" />
        <h2 className="text-xl font-semibold">Your Activity Pattern</h2>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Total Hours: <span className="font-semibold">{data.total_hours}</span>
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="text-xs text-gray-500 font-normal p-1"></th>
              {hours.map((h) => (
                <th key={h} className="text-xs text-gray-500 font-normal p-1">
                  {h.toString().padStart(2, '0')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.days.map((day, dayIdx) => (
              <tr key={day}>
                <td className="text-sm font-medium text-gray-700 pr-3 py-1">
                  {day.substring(0, 3)}
                </td>
                {hours.map((hour) => {
                  const value = data.heatmap[dayIdx][hour];
                  return (
                    <td key={hour} className="p-1">
                      <div
                        className={`w-4 h-4 rounded-sm ${getColor(value)} cursor-pointer hover:ring-2 hover:ring-blue-500 transition-all`}
                        title={`${day} ${hour}:00 - ${value} visit${value !== 1 ? 's' : ''}`}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 flex items-center gap-4 text-xs text-gray-600">
        <span>Less</span>
        <div className="flex gap-1">
          <div className="w-4 h-4 rounded-sm bg-gray-100"></div>
          <div className="w-4 h-4 rounded-sm bg-green-200"></div>
          <div className="w-4 h-4 rounded-sm bg-green-400"></div>
          <div className="w-4 h-4 rounded-sm bg-green-600"></div>
          <div className="w-4 h-4 rounded-sm bg-green-800"></div>
        </div>
        <span>More</span>
      </div>
    </div>
  );
}


export function ActivityStats() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/activity/stats`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !stats) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard
        icon={<Calendar className="w-6 h-6" />}
        title="Total Reservations"
        value={stats.total_reservations}
        color="blue"
      />
      <StatCard
        icon={<TrendingUp className="w-6 h-6" />}
        title="Completed"
        value={stats.completed_reservations}
        color="green"
      />
      <StatCard
        icon={<Award className="w-6 h-6" />}
        title="Total Hours"
        value={stats.total_hours}
        color="purple"
      />
      <StatCard
        icon={<Calendar className="w-6 h-6" />}
        title="Credits Spent"
        value={stats.total_credits_spent}
        color="orange"
      />
    </div>
  );
}

function StatCard({ icon, title, value, color }: { icon: React.ReactNode; title: string; value: string | number; color: 'blue' | 'green' | 'purple' | 'orange' }) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600'
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className={`w-12 h-12 rounded-lg ${colorClasses[color]} flex items-center justify-center mb-4`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-600 mt-1">{title}</p>
    </div>
  );
}

