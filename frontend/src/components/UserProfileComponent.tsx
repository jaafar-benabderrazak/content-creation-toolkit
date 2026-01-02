import React, { useState, useEffect } from 'react';
import { User, Mail, CreditCard, Calendar, Star, MapPin, Edit2, Save, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { api } from '../lib/api';

interface UserProfileProps {
  onNavigate: (page: string) => void;
}

interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  phone_number?: string;
  avatar_url?: string;
  coffee_credits: number;
  role: string;
  created_at: string;
  total_reservations: number;
  total_reviews: number;
}

interface UserStats {
  total_reservations: number;
  completed_reservations: number;
  cancelled_reservations: number;
  active_reservations: number;
  total_spent_credits: number;
  current_credits: number;
  total_reviews: number;
  average_rating_given: number | null;
  favorite_establishments: Array<{
    id: string;
    name: string;
    category: string;
    visit_count: number;
  }>;
}

interface Reservation {
  id: string;
  space_id: string;
  establishment_id: string;
  start_time: string;
  end_time: string;
  status: string;
  cost_credits: number;
  created_at: string;
}

export function UserProfileComponent({ onNavigate }: UserProfileProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [editedPhone, setEditedPhone] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch profile
      const profileResponse = await api.get('/users/me/profile');
      setProfile(profileResponse.data);
      setEditedName(profileResponse.data.full_name);
      setEditedPhone(profileResponse.data.phone_number || '');

      // Fetch stats
      const statsResponse = await api.get('/users/me/stats');
      setStats(statsResponse.data);

      // Fetch recent reservations
      const reservationsResponse = await api.get('/users/me/reservations?limit=10');
      setReservations(reservationsResponse.data.reservations);
    } catch (err: any) {
      console.error('Failed to load profile data:', err);
      setError(err.response?.data?.detail || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      await api.put('/users/me/profile', {
        full_name: editedName,
        phone_number: editedPhone || null,
      });
      setIsEditing(false);
      loadProfileData();
    } catch (err: any) {
      console.error('Failed to update profile:', err);
      alert(err.response?.data?.detail || 'Failed to update profile');
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'default';
      case 'completed':
        return 'secondary';
      case 'cancelled':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#F9AB18] mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <p className="text-red-600 text-center">{error || 'Profile not found'}</p>
            <Button
              onClick={loadProfileData}
              className="mt-4 w-full bg-[#F9AB18] hover:bg-[#F8A015]"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const initials = profile.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Profile Header */}
        <Card className="mb-6 border-gray-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-6">
              <Avatar className="h-24 w-24">
                <AvatarImage src={profile.avatar_url} alt={profile.full_name} />
                <AvatarFallback className="bg-[#F9AB18] text-white text-2xl">
                  {initials}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1">
                {isEditing ? (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="name">Full Name</Label>
                      <Input
                        id="name"
                        value={editedName}
                        onChange={(e) => setEditedName(e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="phone">Phone Number</Label>
                      <Input
                        id="phone"
                        value={editedPhone}
                        onChange={(e) => setEditedPhone(e.target.value)}
                        placeholder="Optional"
                        className="mt-1"
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleSaveProfile}
                        className="bg-[#F9AB18] hover:bg-[#F8A015]"
                        size="sm"
                      >
                        <Save className="mr-2 h-4 w-4" />
                        Save
                      </Button>
                      <Button
                        onClick={() => {
                          setIsEditing(false);
                          setEditedName(profile.full_name);
                          setEditedPhone(profile.phone_number || '');
                        }}
                        variant="outline"
                        size="sm"
                      >
                        <X className="mr-2 h-4 w-4" />
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between">
                      <div>
                        <h1 className="text-2xl font-bold text-gray-900">{profile.full_name}</h1>
                        <p className="text-gray-600 flex items-center gap-2 mt-1">
                          <Mail className="h-4 w-4" />
                          {profile.email}
                        </p>
                        {profile.phone_number && (
                          <p className="text-gray-600 mt-1">{profile.phone_number}</p>
                        )}
                      </div>
                      <Button
                        onClick={() => setIsEditing(true)}
                        variant="outline"
                        size="sm"
                      >
                        <Edit2 className="mr-2 h-4 w-4" />
                        Edit Profile
                      </Button>
                    </div>

                    <div className="flex gap-4 mt-4">
                      <div className="flex items-center gap-2">
                        <CreditCard className="h-5 w-5 text-[#F9AB18]" />
                        <span className="font-semibold">{profile.coffee_credits}</span>
                        <span className="text-sm text-gray-600">credits</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-[#F9AB18]" />
                        <span className="font-semibold">{profile.total_reservations}</span>
                        <span className="text-sm text-gray-600">reservations</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Star className="h-5 w-5 text-[#F9AB18]" />
                        <span className="font-semibold">{profile.total_reviews}</span>
                        <span className="text-sm text-gray-600">reviews</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Overview */}
        {stats && (
          <div className="grid gap-6 md:grid-cols-4 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-700">
                  Active Reservations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{stats.active_reservations}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-700">
                  Completed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{stats.completed_reservations}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-700">
                  Credits Spent
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{stats.total_spent_credits}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-700">
                  Avg. Rating Given
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.average_rating_given?.toFixed(1) || 'N/A'}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="reservations" className="space-y-6">
          <TabsList>
            <TabsTrigger value="reservations">Reservations</TabsTrigger>
            <TabsTrigger value="favorites">Favorites</TabsTrigger>
          </TabsList>

          <TabsContent value="reservations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Reservations</CardTitle>
              </CardHeader>
              <CardContent>
                {reservations.length === 0 ? (
                  <div className="text-center py-8">
                    <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No reservations yet</p>
                    <Button
                      onClick={() => onNavigate('explore')}
                      className="mt-4 bg-[#F9AB18] hover:bg-[#F8A015]"
                    >
                      Browse Spaces
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {reservations.map((reservation) => (
                      <div
                        key={reservation.id}
                        className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-gray-900">
                            {new Date(reservation.start_time).toLocaleDateString()}
                          </p>
                          <p className="text-sm text-gray-600">
                            {new Date(reservation.start_time).toLocaleTimeString()} -{' '}
                            {new Date(reservation.end_time).toLocaleTimeString()}
                          </p>
                          <p className="text-sm text-gray-600 mt-1">
                            {reservation.cost_credits} credits
                          </p>
                        </div>
                        <Badge variant={getStatusBadgeVariant(reservation.status)}>
                          {reservation.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="favorites" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Favorite Places</CardTitle>
              </CardHeader>
              <CardContent>
                {!stats || stats.favorite_establishments.length === 0 ? (
                  <div className="text-center py-8">
                    <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No favorites yet</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {stats.favorite_establishments.map((establishment) => (
                      <div
                        key={establishment.id}
                        className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-[#F9AB18] transition-colors cursor-pointer"
                        onClick={() => onNavigate('explore')}
                      >
                        <div>
                          <h3 className="font-semibold text-gray-900">{establishment.name}</h3>
                          <p className="text-sm text-gray-600">{establishment.category}</p>
                        </div>
                        <Badge variant="outline">{establishment.visit_count} visits</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

