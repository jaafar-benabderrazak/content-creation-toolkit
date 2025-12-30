'use client'

import { useState } from 'react'
import { Navbar } from '@/components/Navbar'
import { HomePage } from '@/components/HomePage'
import { ExplorePage } from '@/components/ExplorePage'
import { EstablishmentDetails } from '@/components/EstablishmentDetails'
import { UserDashboard } from '@/components/UserDashboard'
import { OwnerDashboard } from '@/components/OwnerDashboard'
import { OwnerAdminPage } from '@/components/OwnerAdminPage'

type Page = 'home' | 'explore' | 'details' | 'dashboard' | 'owner-dashboard' | 'owner-admin'

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>('home')
  const [selectedEstablishmentId, setSelectedEstablishmentId] = useState<string>('')

  const handleNavigate = (page: string, establishmentId?: string) => {
    setCurrentPage(page as Page)
    if (establishmentId) {
      setSelectedEstablishmentId(establishmentId)
    }
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar currentPage={currentPage} onNavigate={handleNavigate} />
      
      {currentPage === 'home' && <HomePage onNavigate={handleNavigate} />}
      {currentPage === 'explore' && <ExplorePage onNavigate={handleNavigate} />}
      {currentPage === 'details' && (
        <EstablishmentDetails
          establishmentId={selectedEstablishmentId}
          onNavigate={handleNavigate}
        />
      )}
      {currentPage === 'dashboard' && <UserDashboard onNavigate={handleNavigate} />}
      {currentPage === 'owner-dashboard' && <OwnerDashboard onNavigate={handleNavigate} />}
      {currentPage === 'owner-admin' && <OwnerAdminPage onNavigate={handleNavigate} />}
    </div>
  )
}
