import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Plus, Edit, Trash2, Trophy, Star } from 'lucide-react';

interface LoyaltyProgram {
  id: string;
  establishment_id: string;
  name: string;
  description: string;
  is_active: boolean;
  points_per_hour: number;
  created_at: string;
}

interface LoyaltyTier {
  id: string;
  program_id: string;
  name: string;
  min_points: number;
  discount_percentage: number;
  perks: string[];
  color: string;
}

interface OwnerLoyaltyManagerProps {
  establishmentId: string;
}

export function OwnerLoyaltyManager({ establishmentId }: OwnerLoyaltyManagerProps) {
  const [program, setProgram] = useState<LoyaltyProgram | null>(null);
  const [tiers, setTiers] = useState<LoyaltyTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateProgram, setShowCreateProgram] = useState(false);
  const [showAddTier, setShowAddTier] = useState(false);
  const [showEditTier, setShowEditTier] = useState(false);
  const [selectedTier, setSelectedTier] = useState<LoyaltyTier | null>(null);

  // Form state
  const [programName, setProgramName] = useState('');
  const [programDescription, setProgramDescription] = useState('');
  const [pointsPerHour, setPointsPerHour] = useState('10');
  
  const [tierName, setTierName] = useState('');
  const [minPoints, setMinPoints] = useState('0');
  const [discountPercentage, setDiscountPercentage] = useState('0');
  const [tierColor, setTierColor] = useState('#F9AB18');
  const [perks, setPerks] = useState('');

  useEffect(() => {
    loadProgram();
  }, [establishmentId]);

  const loadProgram = async () => {
    setLoading(true);
    try {
      // Load loyalty program
      const programRes = await fetch(`/api/v1/loyalty/programs?establishment_id=${establishmentId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (programRes.ok) {
        const programs = await programRes.json();
        if (programs.length > 0) {
          const prog = programs[0];
          setProgram(prog);
          
          // Load tiers
          const tiersRes = await fetch(`/api/v1/loyalty/programs/${prog.id}/tiers`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
          });
          
          if (tiersRes.ok) {
            const tiersData = await tiersRes.json();
            setTiers(tiersData);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load loyalty program:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProgram = async () => {
    try {
      const response = await fetch('/api/v1/loyalty/programs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          establishment_id: establishmentId,
          name: programName,
          description: programDescription,
          points_per_hour: parseInt(pointsPerHour),
          is_active: true
        })
      });

      if (response.ok) {
        const newProgram = await response.json();
        setProgram(newProgram);
        setShowCreateProgram(false);
        resetProgramForm();
      }
    } catch (error) {
      console.error('Failed to create program:', error);
    }
  };

  const handleAddTier = async () => {
    if (!program) return;

    try {
      const response = await fetch(`/api/v1/loyalty/programs/${program.id}/tiers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: tierName,
          min_points: parseInt(minPoints),
          discount_percentage: parseFloat(discountPercentage),
          perks: perks.split('\n').filter(p => p.trim()),
          color: tierColor
        })
      });

      if (response.ok) {
        const newTier = await response.json();
        setTiers([...tiers, newTier]);
        setShowAddTier(false);
        resetTierForm();
      }
    } catch (error) {
      console.error('Failed to add tier:', error);
    }
  };

  const handleUpdateTier = async () => {
    if (!selectedTier) return;

    try {
      const response = await fetch(`/api/v1/loyalty/tiers/${selectedTier.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: tierName,
          min_points: parseInt(minPoints),
          discount_percentage: parseFloat(discountPercentage),
          perks: perks.split('\n').filter(p => p.trim()),
          color: tierColor
        })
      });

      if (response.ok) {
        const updatedTier = await response.json();
        setTiers(tiers.map(t => t.id === selectedTier.id ? updatedTier : t));
        setShowEditTier(false);
        resetTierForm();
      }
    } catch (error) {
      console.error('Failed to update tier:', error);
    }
  };

  const handleDeleteTier = async (tierId: string) => {
    if (!confirm('Are you sure you want to delete this tier?')) return;

    try {
      const response = await fetch(`/api/v1/loyalty/tiers/${tierId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setTiers(tiers.filter(t => t.id !== tierId));
      }
    } catch (error) {
      console.error('Failed to delete tier:', error);
    }
  };

  const resetProgramForm = () => {
    setProgramName('');
    setProgramDescription('');
    setPointsPerHour('10');
  };

  const resetTierForm = () => {
    setTierName('');
    setMinPoints('0');
    setDiscountPercentage('0');
    setTierColor('#F9AB18');
    setPerks('');
    setSelectedTier(null);
  };

  const openEditTier = (tier: LoyaltyTier) => {
    setSelectedTier(tier);
    setTierName(tier.name);
    setMinPoints(tier.min_points.toString());
    setDiscountPercentage(tier.discount_percentage.toString());
    setTierColor(tier.color);
    setPerks(tier.perks.join('\n'));
    setShowEditTier(true);
  };

  if (loading) {
    return <div className="flex items-center justify-center p-8">Loading...</div>;
  }

  if (!program) {
    return (
      <Card className="border-gray-200">
        <CardHeader>
          <CardTitle className="text-gray-900 flex items-center gap-2">
            <Trophy className="h-5 w-5" />
            Loyalty Program
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center py-8">
          <p className="text-gray-500 mb-4">No loyalty program configured for this establishment.</p>
          <Button onClick={() => setShowCreateProgram(true)} className="bg-[#F9AB18] hover:bg-[#F8A015]">
            <Plus className="mr-2 h-4 w-4" />
            Create Loyalty Program
          </Button>
        </CardContent>

        {/* Create Program Dialog */}
        <Dialog open={showCreateProgram} onOpenChange={setShowCreateProgram}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Loyalty Program</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="programName">Program Name</Label>
                <Input
                  id="programName"
                  placeholder="e.g., VIP Rewards"
                  value={programName}
                  onChange={(e) => setProgramName(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="programDescription">Description</Label>
                <Textarea
                  id="programDescription"
                  placeholder="Describe your loyalty program"
                  value={programDescription}
                  onChange={(e) => setProgramDescription(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="pointsPerHour">Points Per Hour</Label>
                <Input
                  id="pointsPerHour"
                  type="number"
                  value={pointsPerHour}
                  onChange={(e) => setPointsPerHour(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleCreateProgram} disabled={!programName} className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015]">
                  Create Program
                </Button>
                <Button onClick={() => setShowCreateProgram(false)} variant="outline" className="flex-1">
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Program Overview */}
      <Card className="border-gray-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-gray-900 flex items-center gap-2">
              <Trophy className="h-5 w-5 text-[#F9AB18]" />
              {program.name}
            </CardTitle>
            <Badge className={program.is_active ? 'bg-green-500' : 'bg-gray-500'}>
              {program.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 mb-4">{program.description}</p>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-[#F9AB18]" />
              <span>{program.points_per_hour} points per hour</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tiers Management */}
      <Card className="border-gray-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-gray-900">Loyalty Tiers</CardTitle>
            <Button onClick={() => setShowAddTier(true)} size="sm" className="bg-[#F9AB18] hover:bg-[#F8A015]">
              <Plus className="mr-2 h-4 w-4" />
              Add Tier
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {tiers.length === 0 ? (
            <p className="text-center text-gray-500 py-4">No tiers created yet. Add your first tier to get started.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tier Name</TableHead>
                  <TableHead>Min. Points</TableHead>
                  <TableHead>Discount</TableHead>
                  <TableHead>Perks</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tiers.sort((a, b) => a.min_points - b.min_points).map((tier) => (
                  <TableRow key={tier.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: tier.color }}></div>
                        <span className="font-medium">{tier.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>{tier.min_points}</TableCell>
                    <TableCell>{tier.discount_percentage}%</TableCell>
                    <TableCell>
                      <div className="text-sm text-gray-600">
                        {tier.perks.slice(0, 2).join(', ')}
                        {tier.perks.length > 2 && ` +${tier.perks.length - 2} more`}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm" onClick={() => openEditTier(tier)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteTier(tier.id)} className="text-red-500">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add Tier Dialog */}
      <Dialog open={showAddTier} onOpenChange={setShowAddTier}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Loyalty Tier</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="tierName">Tier Name</Label>
              <Input
                id="tierName"
                placeholder="e.g., Gold"
                value={tierName}
                onChange={(e) => setTierName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="minPoints">Minimum Points</Label>
              <Input
                id="minPoints"
                type="number"
                value={minPoints}
                onChange={(e) => setMinPoints(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="discountPercentage">Discount Percentage</Label>
              <Input
                id="discountPercentage"
                type="number"
                step="0.1"
                value={discountPercentage}
                onChange={(e) => setDiscountPercentage(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="tierColor">Tier Color</Label>
              <div className="flex gap-2">
                <Input
                  id="tierColor"
                  type="color"
                  value={tierColor}
                  onChange={(e) => setTierColor(e.target.value)}
                  className="w-20 h-10"
                />
                <Input
                  value={tierColor}
                  onChange={(e) => setTierColor(e.target.value)}
                  placeholder="#F9AB18"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="perks">Perks (one per line)</Label>
              <Textarea
                id="perks"
                placeholder="Priority booking&#10;Free coffee&#10;Extended hours"
                value={perks}
                onChange={(e) => setPerks(e.target.value)}
                rows={4}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleAddTier} disabled={!tierName} className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015]">
                Add Tier
              </Button>
              <Button onClick={() => { setShowAddTier(false); resetTierForm(); }} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Tier Dialog */}
      <Dialog open={showEditTier} onOpenChange={setShowEditTier}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Loyalty Tier</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="editTierName">Tier Name</Label>
              <Input
                id="editTierName"
                value={tierName}
                onChange={(e) => setTierName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="editMinPoints">Minimum Points</Label>
              <Input
                id="editMinPoints"
                type="number"
                value={minPoints}
                onChange={(e) => setMinPoints(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="editDiscountPercentage">Discount Percentage</Label>
              <Input
                id="editDiscountPercentage"
                type="number"
                step="0.1"
                value={discountPercentage}
                onChange={(e) => setDiscountPercentage(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="editTierColor">Tier Color</Label>
              <div className="flex gap-2">
                <Input
                  id="editTierColor"
                  type="color"
                  value={tierColor}
                  onChange={(e) => setTierColor(e.target.value)}
                  className="w-20 h-10"
                />
                <Input
                  value={tierColor}
                  onChange={(e) => setTierColor(e.target.value)}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="editPerks">Perks (one per line)</Label>
              <Textarea
                id="editPerks"
                value={perks}
                onChange={(e) => setPerks(e.target.value)}
                rows={4}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleUpdateTier} disabled={!tierName} className="flex-1 bg-[#F9AB18] hover:bg-[#F8A015]">
                Save Changes
              </Button>
              <Button onClick={() => { setShowEditTier(false); resetTierForm(); }} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

