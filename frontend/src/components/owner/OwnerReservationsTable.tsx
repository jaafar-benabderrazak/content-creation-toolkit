import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Calendar, Users, CheckCircle, XCircle, Clock } from 'lucide-react';

interface Reservation {
  id: string;
  user_id: string;
  space_id: string;
  establishment_id: string;
  start_time: string;
  end_time: string;
  status: 'pending' | 'confirmed' | 'checked_in' | 'completed' | 'cancelled';
  cost_credits: number;
  qr_code: string;
  users: { full_name: string; email: string };
  spaces: { name: string; establishment_id: string };
  is_group?: boolean;
  group_size?: number;
}

interface OwnerReservationsTableProps {
  establishmentId?: string;
}

export function OwnerReservationsTable({ establishmentId }: OwnerReservationsTableProps) {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    loadReservations();
  }, [establishmentId]);

  const loadReservations = async () => {
    setLoading(true);
    try {
      const endpoint = establishmentId 
        ? `/api/v1/reservations/establishment/${establishmentId}`
        : '/api/v1/owner/reservations';
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setReservations(data);
      }
    } catch (error) {
      console.error('Failed to load reservations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckIn = async (reservationId: string) => {
    try {
      const response = await fetch(`/api/v1/reservations/${reservationId}/check-in`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        loadReservations();
      }
    } catch (error) {
      console.error('Failed to check in:', error);
    }
  };

  const handleCancel = async (reservationId: string) => {
    if (!confirm('Are you sure you want to cancel this reservation?')) return;

    try {
      const response = await fetch(`/api/v1/reservations/${reservationId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        loadReservations();
      }
    } catch (error) {
      console.error('Failed to cancel:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-500', label: 'Pending' },
      confirmed: { color: 'bg-blue-500', label: 'Confirmed' },
      checked_in: { color: 'bg-green-500', label: 'Checked In' },
      completed: { color: 'bg-gray-500', label: 'Completed' },
      cancelled: { color: 'bg-red-500', label: 'Cancelled' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return <Badge className={`${config.color} text-white`}>{config.label}</Badge>;
  };

  const filterReservations = (status?: string) => {
    if (!status || status === 'all') return reservations;
    return reservations.filter(r => r.status === status);
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (loading) {
    return <div className="flex items-center justify-center p-8">Loading reservations...</div>;
  }

  return (
    <Card className="border-gray-200">
      <CardHeader>
        <CardTitle className="text-gray-900 flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Reservations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5 mb-4">
            <TabsTrigger value="all">All ({reservations.length})</TabsTrigger>
            <TabsTrigger value="pending">Pending ({filterReservations('pending').length})</TabsTrigger>
            <TabsTrigger value="confirmed">Confirmed ({filterReservations('confirmed').length})</TabsTrigger>
            <TabsTrigger value="checked_in">Checked In ({filterReservations('checked_in').length})</TabsTrigger>
            <TabsTrigger value="completed">Completed ({filterReservations('completed').length})</TabsTrigger>
          </TabsList>

          {['all', 'pending', 'confirmed', 'checked_in', 'completed'].map((status) => (
            <TabsContent key={status} value={status}>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Guest</TableHead>
                      <TableHead>Space</TableHead>
                      <TableHead>Date & Time</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Credits</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filterReservations(status === 'all' ? undefined : status).length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                          No reservations found
                        </TableCell>
                      </TableRow>
                    ) : (
                      filterReservations(status === 'all' ? undefined : status).map((reservation) => {
                        const startTime = new Date(reservation.start_time);
                        const endTime = new Date(reservation.end_time);
                        const durationHours = (endTime.getTime() - startTime.getTime()) / (1000 * 60 * 60);

                        return (
                          <TableRow key={reservation.id}>
                            <TableCell>
                              <div>
                                <div className="font-medium">{reservation.users.full_name}</div>
                                <div className="text-sm text-gray-500">{reservation.users.email}</div>
                              </div>
                            </TableCell>
                            <TableCell className="font-medium">{reservation.spaces.name}</TableCell>
                            <TableCell>
                              <div className="text-sm">
                                <div>{formatDateTime(reservation.start_time)}</div>
                                <div className="text-gray-500">to {formatDateTime(reservation.end_time)}</div>
                              </div>
                            </TableCell>
                            <TableCell>{durationHours.toFixed(1)}h</TableCell>
                            <TableCell>
                              {reservation.is_group ? (
                                <Badge variant="outline" className="flex items-center gap-1 w-fit">
                                  <Users className="h-3 w-3" />
                                  Group ({reservation.group_size})
                                </Badge>
                              ) : (
                                <Badge variant="outline">Individual</Badge>
                              )}
                            </TableCell>
                            <TableCell>{getStatusBadge(reservation.status)}</TableCell>
                            <TableCell className="font-medium">{reservation.cost_credits}</TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
                                {reservation.status === 'confirmed' && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleCheckIn(reservation.id)}
                                    className="text-green-600 border-green-600 hover:bg-green-50"
                                  >
                                    <CheckCircle className="h-4 w-4 mr-1" />
                                    Check In
                                  </Button>
                                )}
                                {['pending', 'confirmed'].includes(reservation.status) && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleCancel(reservation.id)}
                                    className="text-red-600 border-red-600 hover:bg-red-50"
                                  >
                                    <XCircle className="h-4 w-4 mr-1" />
                                    Cancel
                                  </Button>
                                )}
                                {reservation.status === 'completed' && (
                                  <span className="text-sm text-gray-500 flex items-center gap-1">
                                    <Clock className="h-4 w-4" />
                                    Done
                                  </span>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  );
}

