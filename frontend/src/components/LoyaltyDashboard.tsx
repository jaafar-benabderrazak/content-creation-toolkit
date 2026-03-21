'use client';

import { useEffect, useState } from 'react';
import { Trophy, Gift, TrendingUp, Zap } from 'lucide-react';

interface LoyaltyStatus {
  points: number;
  tier_name: string;
  tier_min_points: number;
  tier_max_points: number | null;
  credits_bonus_percentage: number;
  discount_percentage: number;
  perks: string[];
  lifetime_reservations: number;
  lifetime_credits_spent: number;
  current_streak_days: number;
  longest_streak_days: number;
  points_to_next_tier: number | null;
  next_tier_name: string | null;
}

export function LoyaltyDashboard() {
  const [status, setStatus] = useState<LoyaltyStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [redeeming, setRedeeming] = useState(false);

  useEffect(() => {
    loadLoyaltyStatus();
  }, []);

  const loadLoyaltyStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/loyalty/status`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Error loading loyalty status:', error);
    } finally {
      setLoading(false);
    }
  };

  const redeemPoints = async (points: number) => {
    if (!confirm(`Redeem ${points} points for ${points / 100} credits?`)) {
      return;
    }

    setRedeeming(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/loyalty/redeem/credits?points=${points}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        alert(data.message);
        loadLoyaltyStatus(); // Reload status
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to redeem points');
      }
    } catch (error) {
      console.error('Error redeeming points:', error);
      alert('Failed to redeem points');
    } finally {
      setRedeeming(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!status) return null;

  const tierColors = {
    Bronze: 'from-amber-600 to-amber-800',
    Silver: 'from-gray-400 to-gray-600',
    Gold: 'from-yellow-400 to-yellow-600',
    Platinum: 'from-purple-500 to-purple-700'
  };

  const tierColor = tierColors[status.tier_name as keyof typeof tierColors] || 'from-gray-400 to-gray-600';
  const progressPercent = status.points_to_next_tier
    ? ((status.points - status.tier_min_points) / ((status.tier_min_points + status.points_to_next_tier) - status.tier_min_points)) * 100
    : 100;

  return (
    <div className="space-y-6">
      {/* Tier Card */}
      <div className={`bg-gradient-to-br ${tierColor} rounded-lg shadow-lg p-8 text-white`}>
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Trophy className="w-8 h-8" />
              <h2 className="text-3xl font-bold">{status.tier_name}</h2>
            </div>
            <p className="text-white/80">Member</p>
          </div>
          <div className="text-right">
            <p className="text-4xl font-bold">{status.points}</p>
            <p className="text-white/80">Points</p>
          </div>
        </div>

        {/* Progress to Next Tier */}
        {status.points_to_next_tier && (
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>{status.tier_name}</span>
              <span>{status.next_tier_name}</span>
            </div>
            <div className="w-full bg-white/20 rounded-full h-2 mb-2">
              <div
                className="bg-white rounded-full h-2 transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <p className="text-sm text-white/80">
              {status.points_to_next_tier} points to {status.next_tier_name}
            </p>
          </div>
        )}

        {/* Perks */}
        {status.perks.length > 0 && (
          <div className="mt-6 pt-6 border-t border-white/20">
            <p className="text-sm font-semibold mb-2">Your Perks:</p>
            <div className="flex flex-wrap gap-2">
              {status.perks.map((perk, i) => (
                <span key={i} className="px-3 py-1 bg-white/20 rounded-full text-sm">
                  {perk}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<TrendingUp className="w-6 h-6" />}
          title="Lifetime Reservations"
          value={status.lifetime_reservations}
          color="blue"
        />
        <StatCard
          icon={<Gift className="w-6 h-6" />}
          title="Credits Spent"
          value={status.lifetime_credits_spent}
          color="green"
        />
        <StatCard
          icon={<Zap className="w-6 h-6" />}
          title="Current Streak"
          value={`${status.current_streak_days} days`}
          color="orange"
        />
        <StatCard
          icon={<Trophy className="w-6 h-6" />}
          title="Longest Streak"
          value={`${status.longest_streak_days} days`}
          color="purple"
        />
      </div>

      {/* Bonuses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-lg mb-4">Your Benefits</h3>
          <div className="space-y-3">
            <BenefitItem
              label="Credits Bonus"
              value={`+${status.credits_bonus_percentage}%`}
            />
            <BenefitItem
              label="Discount"
              value={`${status.discount_percentage}%`}
            />
          </div>
        </div>

        {/* Redeem Points */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-lg mb-4">Redeem Points</h3>
          <p className="text-sm text-gray-600 mb-4">
            Convert your loyalty points to coffee credits (100 points = 1 credit)
          </p>
          
          <div className="space-y-2">
            {[100, 500, 1000].map((points) => (
              <button
                key={points}
                onClick={() => redeemPoints(points)}
                disabled={redeeming || status.points < points}
                className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                  status.points >= points
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                {points} Points → {points / 100} Credits
              </button>
            ))}
          </div>
        </div>
      </div>
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

function BenefitItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-700">{label}</span>
      <span className="font-semibold text-blue-600">{value}</span>
    </div>
  );
}

