import React, { useState } from 'react';
import { ArrowLeft, Edit, Trash2, QrCode, Printer, Plus, Download } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { establishments, Space } from '../lib/mockData';

interface OwnerAdminPageProps {
  onNavigate: (page: string) => void;
}

export function OwnerAdminPage({ onNavigate }: OwnerAdminPageProps) {
  // For demo purposes, we'll use the first establishment as the owner's venue
  const [venue] = useState(establishments[0]);
  const [spaces, setSpaces] = useState(venue.spaces);
  const [showAddSpace, setShowAddSpace] = useState(false);
  const [showEditSpace, setShowEditSpace] = useState(false);
  const [showQRCode, setShowQRCode] = useState(false);
  const [selectedSpace, setSelectedSpace] = useState<Space | null>(null);

  // Form state
  const [spaceName, setSpaceName] = useState('');
  const [spaceType, setSpaceType] = useState<'table' | 'room' | 'desk'>('table');
  const [credits, setCredits] = useState('2');
  const [capacity, setCapacity] = useState('2');

  const handleAddSpace = () => {
    const newSpace: Space = {
      id: `s${Date.now()}`,
      name: spaceName,
      type: spaceType,
      creditsPerHour: parseInt(credits),
      available: true,
      occupancyRate: 0,
      capacity: parseInt(capacity),
      qrCode: `QR-${venue.name.substring(0, 2).toUpperCase()}-${spaceName.substring(0, 2).toUpperCase()}`,
    };
    setSpaces([...spaces, newSpace]);
    setShowAddSpace(false);
    resetForm();
  };

  const handleEditSpace = () => {
    if (selectedSpace) {
      const updatedSpaces = spaces.map((s) =>
        s.id === selectedSpace.id
          ? {
              ...s,
              name: spaceName,
              type: spaceType,
              creditsPerHour: parseInt(credits),
              capacity: parseInt(capacity),
            }
          : s
      );
      setSpaces(updatedSpaces);
      setShowEditSpace(false);
      resetForm();
    }
  };

  const handleDeleteSpace = (spaceId: string) => {
    if (confirm('Are you sure you want to delete this space?')) {
      setSpaces(spaces.filter((s) => s.id !== spaceId));
    }
  };

  const resetForm = () => {
    setSpaceName('');
    setSpaceType('table');
    setCredits('2');
    setCapacity('2');
    setSelectedSpace(null);
  };

  const openEditDialog = (space: Space) => {
    setSelectedSpace(space);
    setSpaceName(space.name);
    setSpaceType(space.type);
    setCredits(space.creditsPerHour.toString());
    setCapacity(space.capacity?.toString() || '1');
    setShowEditSpace(true);
  };

  const openQRDialog = (space: Space) => {
    setSelectedSpace(space);
    setShowQRCode(true);
  };

  const handlePrintQR = () => {
    window.print();
  };

  const getOccupancyColor = (rate?: number) => {
    if (!rate) return 'text-gray-500';
    if (rate >= 80) return 'text-[#EF4444]';
    if (rate >= 60) return 'text-[#F59E0B]';
    return 'text-[#10B981]';
  };

  const getOccupancyLabel = (rate?: number) => {
    if (!rate) return 'New';
    if (rate >= 80) return 'High Traffic';
    if (rate >= 60) return 'Medium Traffic';
    return 'Low Traffic';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <Button
            variant="ghost"
            onClick={() => onNavigate('owner-dashboard')}
            className="mb-4 text-gray-700"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-gray-900">Manage Spaces</h1>
              <p className="text-gray-500">{venue.name}</p>
            </div>
            <Button
              onClick={() => setShowAddSpace(true)}
              className="bg-[#F9AB18] hover:bg-[#F8A015]"
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Space
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Stats Cards */}
        <div className="mb-8 grid gap-6 md:grid-cols-4">
          <Card className="border-gray-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-gray-700">Total Spaces</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">{spaces.length}</div>
            </CardContent>
          </Card>
          <Card className="border-gray-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-gray-700">Available</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-[#10B981]">
                {spaces.filter((s) => s.available).length}
              </div>
            </CardContent>
          </Card>
          <Card className="border-gray-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-gray-700">Avg. Occupancy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">
                {Math.round(
                  spaces.reduce((sum, s) => sum + (s.occupancyRate || 0), 0) / spaces.length
                )}
                %
              </div>
            </CardContent>
          </Card>
          <Card className="border-gray-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-gray-700">Total Capacity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-gray-900">
                {spaces.reduce((sum, s) => sum + (s.capacity || 0), 0)} people
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Spaces Table */}
        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-gray-900">All Spaces</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Credits/Hour</TableHead>
                    <TableHead>Capacity</TableHead>
                    <TableHead>Traffic</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>QR Code</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {spaces.map((space) => (
                    <TableRow key={space.id}>
                      <TableCell className="text-gray-900">{space.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {space.type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-gray-700">{space.creditsPerHour}</TableCell>
                      <TableCell className="text-gray-700">
                        {space.capacity || '-'} {space.capacity && space.capacity > 1 ? 'people' : 'person'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className={getOccupancyColor(space.occupancyRate)}>
                            {space.occupancyRate || 0}%
                          </span>
                          <span className="text-gray-500">
                            ({getOccupancyLabel(space.occupancyRate)})
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            space.available
                              ? 'bg-[#10B981] text-white'
                              : 'bg-gray-500 text-white'
                          }
                        >
                          {space.available ? 'Available' : 'Unavailable'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-gray-700">{space.qrCode || '-'}</span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openQRDialog(space)}
                            disabled={!space.qrCode}
                          >
                            <QrCode className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditDialog(space)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteSpace(space.id)}
                            className="text-[#EF4444] hover:text-[#EF4444]"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add Space Dialog */}
      <Dialog open={showAddSpace} onOpenChange={setShowAddSpace}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-gray-900">Add New Space</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="spaceName">Space Name</Label>
              <Input
                id="spaceName"
                placeholder="e.g., Table 5"
                value={spaceName}
                onChange={(e) => setSpaceName(e.target.value)}
                className="border-gray-300"
              />
            </div>
            <div>
              <Label htmlFor="spaceType">Space Type</Label>
              <Select value={spaceType} onValueChange={(v: any) => setSpaceType(v)}>
                <SelectTrigger id="spaceType" className="border-gray-300">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="table">Table</SelectItem>
                  <SelectItem value="desk">Desk</SelectItem>
                  <SelectItem value="room">Room</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="credits">Credits Per Hour</Label>
              <Input
                id="credits"
                type="number"
                min="1"
                value={credits}
                onChange={(e) => setCredits(e.target.value)}
                className="border-gray-300"
              />
            </div>
            <div>
              <Label htmlFor="capacity">Capacity (People)</Label>
              <Input
                id="capacity"
                type="number"
                min="1"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
                className="border-gray-300"
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleAddSpace}
                disabled={!spaceName}
                className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015]"
              >
                Add Space
              </Button>
              <Button
                onClick={() => {
                  setShowAddSpace(false);
                  resetForm();
                }}
                variant="outline"
                className="flex-1 border-gray-300"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Space Dialog */}
      <Dialog open={showEditSpace} onOpenChange={setShowEditSpace}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-gray-900">Edit Space</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="editSpaceName">Space Name</Label>
              <Input
                id="editSpaceName"
                value={spaceName}
                onChange={(e) => setSpaceName(e.target.value)}
                className="border-gray-300"
              />
            </div>
            <div>
              <Label htmlFor="editSpaceType">Space Type</Label>
              <Select value={spaceType} onValueChange={(v: any) => setSpaceType(v)}>
                <SelectTrigger id="editSpaceType" className="border-gray-300">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="table">Table</SelectItem>
                  <SelectItem value="desk">Desk</SelectItem>
                  <SelectItem value="room">Room</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="editCredits">Credits Per Hour</Label>
              <Input
                id="editCredits"
                type="number"
                min="1"
                value={credits}
                onChange={(e) => setCredits(e.target.value)}
                className="border-gray-300"
              />
            </div>
            <div>
              <Label htmlFor="editCapacity">Capacity (People)</Label>
              <Input
                id="editCapacity"
                type="number"
                min="1"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
                className="border-gray-300"
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleEditSpace}
                disabled={!spaceName}
                className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015]"
              >
                Save Changes
              </Button>
              <Button
                onClick={() => {
                  setShowEditSpace(false);
                  resetForm();
                }}
                variant="outline"
                className="flex-1 border-gray-300"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* QR Code Dialog */}
      <Dialog open={showQRCode} onOpenChange={setShowQRCode}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-gray-900">Print QR Code</DialogTitle>
          </DialogHeader>
          {selectedSpace && (
            <div className="space-y-6">
              <div className="rounded-lg border-2 border-dashed border-gray-300 bg-white p-8 text-center">
                {/* QR Code Placeholder */}
                <div className="mb-4 flex flex-col items-center justify-center">
                  <div className="mb-4 flex h-64 w-64 items-center justify-center rounded-lg bg-gray-100">
                    <QrCode className="h-48 w-48 text-gray-400" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-gray-900">{selectedSpace.name}</h3>
                    <div className="rounded-lg bg-[#F9AB18] px-6 py-2">
                      <p className="font-mono text-white">{selectedSpace.qrCode}</p>
                    </div>
                    <p className="text-gray-500">{venue.name}</p>
                    <p className="text-gray-700">
                      {selectedSpace.creditsPerHour} credits/hour • Capacity:{' '}
                      {selectedSpace.capacity}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handlePrintQR}
                  className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015]"
                >
                  <Printer className="mr-2 h-4 w-4" />
                  Print QR Code
                </Button>
                <Button
                  variant="outline"
                  className="flex-1 border-gray-300"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </div>
              <Button
                onClick={() => setShowQRCode(false)}
                variant="ghost"
                className="w-full"
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
