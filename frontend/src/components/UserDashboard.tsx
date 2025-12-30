import React, { useState } from 'react';
import { Calendar, CreditCard, Star, QrCode, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { userReservations, userCredits, Reservation } from '../lib/mockData';

interface UserDashboardProps {
  onNavigate: (page: string) => void;
}

export function UserDashboard({ onNavigate }: UserDashboardProps) {
  const [selectedReservation, setSelectedReservation] = useState<Reservation | null>(null);
  const [showQRCode, setShowQRCode] = useState(false);

  const upcomingReservations = userReservations.filter((r) => r.status === 'confirmed');
  const pastReservations = userReservations.filter((r) => r.status === 'completed');
  const cancelledReservations = userReservations.filter((r) => r.status === 'cancelled');

  const activeReservationsCount = upcomingReservations.length;
  const totalReviews = 3; // Mock value

  const handleShowQRCode = (reservation: Reservation) => {
    setSelectedReservation(reservation);
    setShowQRCode(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-[#10B981] text-white';
      case 'pending':
        return 'bg-[#F59E0B] text-white';
      case 'cancelled':
        return 'bg-[#EF4444] text-white';
      case 'completed':
        return 'bg-gray-500 text-white';
      default:
        return 'bg-gray-200 text-gray-900';
    }
  };

  const ReservationCard = ({ reservation }: { reservation: Reservation }) => (
    <Card className="border-gray-200">
      <div
        className={`h-1 w-full ${
          reservation.status === 'confirmed'
            ? 'bg-[#10B981]'
            : reservation.status === 'cancelled'
            ? 'bg-[#EF4444]'
            : 'bg-gray-500'
        }`}
      />
      <CardContent className="pt-6">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="mb-1 text-gray-900">{reservation.establishmentName}</h3>
            <p className="text-gray-500">{reservation.spaceName}</p>
          </div>
          <Badge className={getStatusColor(reservation.status)}>
            {reservation.status.charAt(0).toUpperCase() + reservation.status.slice(1)}
          </Badge>
        </div>
        <div className="mb-4 space-y-2 text-gray-700">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-500" />
            <span>{reservation.date}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="ml-6">{reservation.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-gray-500" />
            <span>{reservation.totalCredits} Credits</span>
          </div>
        </div>
        {reservation.status === 'confirmed' && (
          <div className="flex gap-2">
            <Button
              onClick={() => handleShowQRCode(reservation)}
              className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015]"
            >
              <QrCode className="mr-2 h-4 w-4" />
              Get Code
            </Button>
            <Button variant="outline" className="border-gray-300 text-gray-700">
              Cancel
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="mb-8 text-gray-900">My Dashboard</h1>

        {/* Stats Row */}
        <div className="mb-8 grid gap-6 md:grid-cols-3">
          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-gray-700">Active Reservations</CardTitle>
              <Calendar className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">{activeReservationsCount}</div>
              <p className="text-gray-500">Upcoming bookings</p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-gray-700">Credits Remaining</CardTitle>
              <CreditCard className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">{userCredits}</div>
              <p className="text-gray-500">Available to use</p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-gray-700">Total Reviews</CardTitle>
              <Star className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">{totalReviews}</div>
              <p className="text-gray-500">Reviews given</p>
            </CardContent>
          </Card>
        </div>

        {/* Reservations Tabs */}
        <Tabs defaultValue="upcoming" className="space-y-4">
          <TabsList className="bg-white">
            <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
            <TabsTrigger value="past">Past</TabsTrigger>
            <TabsTrigger value="cancelled">Cancelled</TabsTrigger>
          </TabsList>

          <TabsContent value="upcoming" className="space-y-4">
            {upcomingReservations.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {upcomingReservations.map((reservation) => (
                  <ReservationCard key={reservation.id} reservation={reservation} />
                ))}
              </div>
            ) : (
              <Card className="border-gray-200">
                <CardContent className="py-16 text-center">
                  <p className="mb-4 text-gray-500">No upcoming reservations</p>
                  <Button
                    onClick={() => onNavigate('explore')}
                    className="bg-[#F9AB18] hover:bg-[#F8A015]"
                  >
                    Explore Spaces
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="past" className="space-y-4">
            {pastReservations.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {pastReservations.map((reservation) => (
                  <ReservationCard key={reservation.id} reservation={reservation} />
                ))}
              </div>
            ) : (
              <Card className="border-gray-200">
                <CardContent className="py-16 text-center">
                  <p className="text-gray-500">No past reservations</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="cancelled" className="space-y-4">
            {cancelledReservations.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {cancelledReservations.map((reservation) => (
                  <ReservationCard key={reservation.id} reservation={reservation} />
                ))}
              </div>
            ) : (
              <Card className="border-gray-200">
                <CardContent className="py-16 text-center">
                  <p className="text-gray-500">No cancelled reservations</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* QR Code Modal */}
      <Dialog open={showQRCode} onOpenChange={setShowQRCode}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-gray-900">Reservation Code</DialogTitle>
          </DialogHeader>
          {selectedReservation && (
            <div className="space-y-6">
              <div className="flex flex-col items-center justify-center rounded-lg bg-white p-8">
                {/* QR Code Placeholder */}
                <div className="mb-4 flex h-48 w-48 items-center justify-center rounded-lg bg-gray-100">
                  <QrCode className="h-32 w-32 text-gray-400" />
                </div>
                <div className="rounded-lg bg-[#F9AB18] px-6 py-3">
                  <p className="text-center text-white tracking-widest">
                    {selectedReservation.qrCode}
                  </p>
                </div>
              </div>
              <div className="space-y-2 text-center text-gray-700">
                <p><strong>{selectedReservation.establishmentName}</strong></p>
                <p>{selectedReservation.spaceName}</p>
                <p>{selectedReservation.date} • {selectedReservation.time}</p>
              </div>
              <Button
                onClick={() => setShowQRCode(false)}
                className="w-full bg-[#F9AB18] hover:bg-[#F8A015]"
              >
                Close
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
