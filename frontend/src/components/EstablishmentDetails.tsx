import React, { useState } from 'react';
import { ArrowLeft, Star } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { establishments, Space } from '../lib/mockData';

interface EstablishmentDetailsProps {
  establishmentId: string;
  onNavigate: (page: string) => void;
}

export function EstablishmentDetails({ establishmentId, onNavigate }: EstablishmentDetailsProps) {
  const establishment = establishments.find((e) => e.id === establishmentId);
  const [selectedSpace, setSelectedSpace] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [duration, setDuration] = useState('2');
  const [showConfirmation, setShowConfirmation] = useState(false);

  if (!establishment) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <p className="text-gray-700">Establishment not found</p>
      </div>
    );
  }

  const selectedSpaceData = establishment.spaces.find((s) => s.id === selectedSpace);
  const totalCredits = selectedSpaceData ? selectedSpaceData.creditsPerHour * parseInt(duration || '0') : 0;

  const handleConfirmReservation = () => {
    setShowConfirmation(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back Button */}
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <Button
            variant="ghost"
            onClick={() => onNavigate('explore')}
            className="text-gray-700"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Explore
          </Button>
        </div>
      </div>

      {/* Hero Image Gallery */}
      <div className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="grid gap-2 md:grid-cols-4 md:grid-rows-2">
            <div className="md:col-span-2 md:row-span-2">
              <img
                src={establishment.image}
                alt={establishment.name}
                className="h-full w-full rounded-lg object-cover"
              />
            </div>
            <div className="hidden md:block">
              <img
                src={establishment.image}
                alt={establishment.name}
                className="h-full w-full rounded-lg object-cover opacity-80"
              />
            </div>
            <div className="hidden md:block">
              <img
                src={establishment.image}
                alt={establishment.name}
                className="h-full w-full rounded-lg object-cover opacity-60"
              />
            </div>
            <div className="hidden md:block">
              <img
                src={establishment.image}
                alt={establishment.name}
                className="h-full w-full rounded-lg object-cover opacity-80"
              />
            </div>
            <div className="hidden md:block">
              <img
                src={establishment.image}
                alt={establishment.name}
                className="h-full w-full rounded-lg object-cover opacity-60"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Column - Details */}
          <div className="lg:col-span-2">
            {/* Header */}
            <div className="mb-6">
              <div className="mb-2 flex items-center justify-between">
                <h1 className="text-gray-900">{establishment.name}</h1>
                <div className="flex items-center">
                  <Star className="h-5 w-5 fill-[#F9AB18] text-[#F9AB18]" />
                  <span className="ml-1 text-gray-900">{establishment.rating}</span>
                </div>
              </div>
              <p className="text-gray-500">{establishment.address}</p>
            </div>

            {/* Description */}
            <div className="mb-8">
              <h3 className="mb-2 text-gray-900">About</h3>
              <p className="text-gray-700">{establishment.description}</p>
            </div>

            {/* Amenities */}
            <div className="mb-8">
              <h3 className="mb-4 text-gray-900">Amenities</h3>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                {establishment.amenities.map((amenity, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span>
                      {amenity === 'WiFi' && '📶'}
                      {amenity === 'Power Outlets' && '🔌'}
                      {amenity === 'Coffee' && '☕'}
                      {amenity === 'Snacks' && '🍪'}
                      {amenity === 'Quiet Zone' && '🔇'}
                      {amenity === 'Meeting Rooms' && '👥'}
                      {amenity === 'Printing' && '🖨️'}
                      {amenity === 'Silent Rooms' && '🤫'}
                      {amenity === 'Study Rooms' && '📚'}
                      {amenity === 'Standing Desks' && '🪑'}
                      {amenity === 'Event Space' && '🎪'}
                      {amenity === 'Lounge' && '🛋️'}
                      {amenity === 'Outdoor Seating' && '🌳'}
                      {amenity === 'Pastries' && '🥐'}
                      {amenity === 'Phone Booths' && '📞'}
                      {amenity === 'Printer' && '🖨️'}
                    </span>
                    <span className="text-gray-700">{amenity}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Reviews */}
            <div>
              <h3 className="mb-4 text-gray-900">Reviews</h3>
              <div className="space-y-4">
                {establishment.reviews.map((review) => (
                  <Card key={review.id} className="border-gray-200">
                    <CardContent className="pt-6">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-gray-900">{review.userName}</span>
                        <div className="flex items-center">
                          <Star className="h-4 w-4 fill-[#F9AB18] text-[#F9AB18]" />
                          <span className="ml-1 text-gray-700">{review.rating}</span>
                        </div>
                      </div>
                      <p className="mb-2 text-gray-700">{review.comment}</p>
                      <p className="text-gray-500">{review.date}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Booking Card */}
          <div className="lg:col-span-1">
            <Card className="sticky top-20 border-gray-200">
              <CardHeader>
                <CardTitle className="text-gray-900">Book a Space</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="space">Select a Space</Label>
                  <Select value={selectedSpace} onValueChange={setSelectedSpace}>
                    <SelectTrigger id="space" className="border-gray-300">
                      <SelectValue placeholder="Choose a space" />
                    </SelectTrigger>
                    <SelectContent>
                      {establishment.spaces.map((space) => (
                        <SelectItem key={space.id} value={space.id} disabled={!space.available}>
                          {space.name} ({space.creditsPerHour} credits/hr)
                          {space.occupancyRate && ` - ${space.occupancyRate}% booked`}
                          {!space.available && ' - Unavailable'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="date">Date</Label>
                  <Input
                    id="date"
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className="border-gray-300"
                  />
                </div>

                <div>
                  <Label htmlFor="time">Time</Label>
                  <Input
                    id="time"
                    type="time"
                    value={selectedTime}
                    onChange={(e) => setSelectedTime(e.target.value)}
                    className="border-gray-300"
                  />
                </div>

                <div>
                  <Label htmlFor="duration">Duration (hours)</Label>
                  <Select value={duration} onValueChange={setDuration}>
                    <SelectTrigger id="duration" className="border-gray-300">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 hour</SelectItem>
                      <SelectItem value="2">2 hours</SelectItem>
                      <SelectItem value="3">3 hours</SelectItem>
                      <SelectItem value="4">4 hours</SelectItem>
                      <SelectItem value="6">6 hours</SelectItem>
                      <SelectItem value="8">8 hours</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <div className="mb-4 flex items-center justify-between">
                    <span className="text-gray-700">Total Credits:</span>
                    <span className="text-gray-900">{totalCredits}</span>
                  </div>
                  <Button
                    onClick={handleConfirmReservation}
                    disabled={!selectedSpace || !selectedDate || !selectedTime}
                    className="w-full bg-[#F9AB18] hover:bg-[#F8A015]"
                  >
                    Confirm Reservation
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-gray-900">Reservation Confirmed!</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="rounded-lg bg-[#10B981]/10 p-4 text-center">
              <p className="mb-2 text-[#10B981]">✓ Success!</p>
              <p className="text-gray-700">You used {totalCredits} credits.</p>
            </div>
            <div className="space-y-2 text-gray-700">
              <p><strong>Venue:</strong> {establishment.name}</p>
              <p><strong>Space:</strong> {selectedSpaceData?.name}</p>
              <p><strong>Date:</strong> {selectedDate}</p>
              <p><strong>Time:</strong> {selectedTime}</p>
              <p><strong>Duration:</strong> {duration} hour(s)</p>
            </div>
            <Button
              onClick={() => {
                setShowConfirmation(false);
                onNavigate('dashboard');
              }}
              className="w-full bg-[#F9AB18] hover:bg-[#F8A015]"
            >
              View in Dashboard
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}