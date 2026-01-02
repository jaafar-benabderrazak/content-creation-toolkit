import React, { useState, useEffect } from 'react';
import { ArrowLeft, Settings, BarChart3, Trophy, Calendar, Bell, Users, MapPin } from 'lucide-react';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { OwnerAnalyticsDashboard } from './OwnerAnalyticsDashboard';
import { OwnerLoyaltyManager } from './OwnerLoyaltyManager';
import { OwnerReservationsTable } from './OwnerReservationsTable';
import { OwnerDashboard } from '../OwnerDashboard';
import { OwnerAdminPage } from '../OwnerAdminPage';

interface EnhancedOwnerDashboardProps {
  onNavigate: (page: string) => void;
}

interface Establishment {
  id: string;
  name: string;
  address: string;
  city: string;
}

export function EnhancedOwnerDashboard({ onNavigate }: EnhancedOwnerDashboardProps) {
  const [establishments, setEstablishments] = useState<Establishment[]>([]);
  const [selectedEstablishment, setSelectedEstablishment] = useState<Establishment | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<'overview' | 'management'>('overview');

  useEffect(() => {
    loadEstablishments();
  }, []);

  const loadEstablishments = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/owner/establishments', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setEstablishments(data);
        if (data.length > 0) {
          setSelectedEstablishment(data[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load establishments:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#F9AB18] mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (establishments.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="text-center py-12">
            <MapPin className="mx-auto h-12 w-12 text-gray-400" />
            <h2 className="mt-4 text-xl font-semibold text-gray-900">No Establishments Yet</h2>
            <p className="mt-2 text-gray-600">Create your first establishment to get started</p>
            <Button 
              onClick={() => onNavigate('create-establishment')} 
              className="mt-6 bg-[#F9AB18] hover:bg-[#F8A015]"
            >
              Create Establishment
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // If user wants to switch between old and new view
  if (activeView === 'management') {
    return <OwnerAdminPage onNavigate={(page) => {
      if (page === 'owner-dashboard') {
        setActiveView('overview');
      } else {
        onNavigate(page);
      }
    }} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-4">
            <Button
              variant="ghost"
              onClick={() => onNavigate('home')}
              className="text-gray-700"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setActiveView('management')}
                className="border-gray-300"
              >
                <Settings className="mr-2 h-4 w-4" />
                Manage Spaces
              </Button>
            </div>
          </div>

          {/* Establishment Selector */}
          {establishments.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {establishments.map((est) => (
                <Button
                  key={est.id}
                  variant={selectedEstablishment?.id === est.id ? 'default' : 'outline'}
                  onClick={() => setSelectedEstablishment(est)}
                  className={selectedEstablishment?.id === est.id ? 'bg-[#F9AB18] hover:bg-[#F8A015]' : ''}
                >
                  {est.name}
                </Button>
              ))}
            </div>
          )}

          {/* Current Establishment Info */}
          {selectedEstablishment && (
            <div className="mt-4">
              <h1 className="text-2xl font-bold text-gray-900">{selectedEstablishment.name}</h1>
              <p className="text-gray-600">{selectedEstablishment.address}, {selectedEstablishment.city}</p>
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {selectedEstablishment && (
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="reservations" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Reservations
              </TabsTrigger>
              <TabsTrigger value="loyalty" className="flex items-center gap-2">
                <Trophy className="h-4 w-4" />
                Loyalty Program
              </TabsTrigger>
              <TabsTrigger value="analytics" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Analytics
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <OwnerDashboard onNavigate={(page) => {
                if (page === 'owner-admin') {
                  setActiveView('management');
                } else {
                  onNavigate(page);
                }
              }} />
            </TabsContent>

            <TabsContent value="reservations">
              <OwnerReservationsTable establishmentId={selectedEstablishment.id} />
            </TabsContent>

            <TabsContent value="loyalty">
              <OwnerLoyaltyManager establishmentId={selectedEstablishment.id} />
            </TabsContent>

            <TabsContent value="analytics">
              <OwnerAnalyticsDashboard establishmentId={selectedEstablishment.id} />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}

