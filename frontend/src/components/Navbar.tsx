'use client';

import React, { useState } from 'react';
import { Menu, User, Play } from 'lucide-react';
import Link from 'next/link';
import { useUser } from '@stackframe/stack';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';
import { useDemoStore, DEMO_USERS } from '@/lib/demo';
import { useTranslations } from 'next-intl';
import { LanguageSwitcher } from './LanguageSwitcher';

interface NavbarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export function Navbar({ currentPage, onNavigate }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [demoOpen, setDemoOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const user = useUser();
  const { demoRole, enterDemo, exitDemo } = useDemoStore();
  const t = useTranslations('Navbar');

  const isAuthenticated = !!user || !!demoRole;
  const isOwnerOrAdmin = demoRole === 'owner' ||
    (user?.clientReadOnlyMetadata as any)?.role === 'owner' ||
    (user?.clientReadOnlyMetadata as any)?.role === 'admin';

  const displayName = demoRole
    ? DEMO_USERS[demoRole].full_name
    : user?.displayName || 'User';

  const handleLogout = () => {
    if (demoRole) {
      exitDemo();
    } else {
      user?.signOut();
    }
  };

  const navLinks = [
    { name: t('home'), id: 'home' },
    { name: t('explore'), id: 'explore' },
  ];

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <button
              onClick={() => onNavigate('home')}
              className="flex items-center space-x-2"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#F9AB18]">
                <span className="text-white font-bold">LW</span>
              </div>
              <span className="text-xl font-semibold text-gray-900">LibreWork</span>
            </button>
          </div>

          {/* Demo banner */}
          {demoRole && (
            <div className="hidden md:flex items-center gap-2 rounded-full bg-amber-50 border border-amber-200 px-3 py-1">
              <Play className="h-3 w-3 text-amber-600 fill-amber-600" />
              <span className="text-xs font-medium text-amber-700">
                {t('demoLabel')}: {demoRole === 'owner' ? t('demoOwnerShort') : t('demoCustomerShort')}
              </span>
            </div>
          )}

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:space-x-8">
            {navLinks.map((link) => (
              <button
                key={link.id}
                onClick={() => onNavigate(link.id)}
                className={`${
                  currentPage === link.id
                    ? 'text-[#F9AB18] font-medium'
                    : 'text-gray-700 hover:text-[#F9AB18]'
                } transition-colors`}
              >
                {link.name}
              </button>
            ))}
          </div>

          {/* Auth Buttons / User Menu */}
          <div className="hidden md:flex md:items-center md:space-x-4">
            {/* Language Switcher */}
            <LanguageSwitcher />

            {isAuthenticated ? (
              <>
                <Button
                  variant="ghost"
                  onClick={() => onNavigate('dashboard')}
                  className="text-gray-700"
                >
                  {t('dashboard')}
                </Button>
                <div className="relative">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="relative"
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                  >
                    <User className="h-5 w-5" />
                    {demoRole && (
                      <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-amber-400 border-2 border-white" />
                    )}
                  </Button>
                  {userMenuOpen && (
                    <div className="absolute right-0 top-full mt-2 w-48 rounded-lg border border-gray-200 bg-white p-1 shadow-lg z-50">
                      <div className="px-3 py-1.5 text-sm text-gray-500">{displayName}</div>
                      <div className="my-1 h-px bg-gray-100" />
                      <button onClick={() => { onNavigate('dashboard'); setUserMenuOpen(false); }} className="w-full text-left rounded-md px-3 py-1.5 text-sm hover:bg-gray-50 transition-colors text-gray-700">
                        {t('myDashboard')}
                      </button>
                      {isOwnerOrAdmin && (
                        <button onClick={() => { onNavigate('owner-dashboard'); setUserMenuOpen(false); }} className="w-full text-left rounded-md px-3 py-1.5 text-sm hover:bg-gray-50 transition-colors text-gray-700">
                          {t('ownerDashboard')}
                        </button>
                      )}
                      {isOwnerOrAdmin && (
                        <button onClick={() => { onNavigate('owner-admin'); setUserMenuOpen(false); }} className="w-full text-left rounded-md px-3 py-1.5 text-sm hover:bg-gray-50 transition-colors text-gray-700">
                          {t('manageSpaces')}
                        </button>
                      )}
                      <div className="my-1 h-px bg-gray-100" />
                      <button onClick={() => { handleLogout(); setUserMenuOpen(false); }} className="w-full text-left rounded-md px-3 py-1.5 text-sm hover:bg-gray-50 transition-colors text-red-500">
                        {demoRole ? t('exitDemo') : t('logout')}
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                {/* Demo buttons */}
                <div className="relative">
                  <Button
                    variant="outline"
                    className="border-amber-200 text-amber-700 hover:bg-amber-50 gap-2"
                    onClick={() => setDemoOpen(!demoOpen)}
                  >
                    <Play className="h-3.5 w-3.5 fill-amber-600" />
                    {t('demoLabel')}
                  </Button>
                  {demoOpen && (
                    <div className="absolute right-0 top-full mt-2 w-52 rounded-lg border border-gray-200 bg-white p-1 shadow-lg z-50">
                      <div className="px-3 py-1.5 text-xs text-gray-400 uppercase tracking-wider">{t('demoAs')}</div>
                      <button
                        onClick={() => { enterDemo('customer'); setDemoOpen(false); }}
                        className="w-full text-left rounded-md px-3 py-2 hover:bg-gray-50 transition-colors"
                      >
                        <div className="font-medium text-sm text-gray-900">{t('demoCustomer')}</div>
                        <div className="text-xs text-gray-400">{t('demoCustomerDesc')}</div>
                      </button>
                      <button
                        onClick={() => { enterDemo('owner'); setDemoOpen(false); }}
                        className="w-full text-left rounded-md px-3 py-2 hover:bg-gray-50 transition-colors"
                      >
                        <div className="font-medium text-sm text-gray-900">{t('demoOwner')}</div>
                        <div className="text-xs text-gray-400">{t('demoOwnerDesc')}</div>
                      </button>
                    </div>
                  )}
                </div>
                <Link href="/login">
                  <Button variant="ghost" className="text-gray-700">
                    {t('login')}
                  </Button>
                </Link>
                <Link href="/register">
                  <Button className="bg-[#F9AB18] hover:bg-[#F8A015] text-white">
                    {t('register')}
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Menu className="h-6 w-6" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[300px]">
                <div className="mt-8 flex flex-col space-y-4">
                  {demoRole && (
                    <div className="flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 mb-2">
                      <Play className="h-3 w-3 text-amber-600 fill-amber-600" />
                      <span className="text-sm font-medium text-amber-700">
                        {t('demoLabel')}: {demoRole === 'owner' ? t('demoOwnerShort') : t('demoCustomerShort')}
                      </span>
                    </div>
                  )}
                  {navLinks.map((link) => (
                    <button
                      key={link.id}
                      onClick={() => {
                        onNavigate(link.id);
                        setMobileOpen(false);
                      }}
                      className={`${
                        currentPage === link.id
                          ? 'text-[#F9AB18] font-medium'
                          : 'text-gray-700'
                      } text-left`}
                    >
                      {link.name}
                    </button>
                  ))}
                  <hr className="border-gray-200" />

                  {/* Mobile Language Switcher */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">{t('languageSwitcher')}:</span>
                    <LanguageSwitcher />
                  </div>

                  {isAuthenticated ? (
                    <>
                      <button
                        onClick={() => {
                          onNavigate('dashboard');
                          setMobileOpen(false);
                        }}
                        className="text-left text-gray-700"
                      >
                        {t('myDashboard')}
                      </button>
                      {isOwnerOrAdmin && (
                        <>
                          <button
                            onClick={() => {
                              onNavigate('owner-dashboard');
                              setMobileOpen(false);
                            }}
                            className="text-left text-gray-700"
                          >
                            {t('ownerDashboard')}
                          </button>
                          <button
                            onClick={() => {
                              onNavigate('owner-admin');
                              setMobileOpen(false);
                            }}
                            className="text-left text-gray-700"
                          >
                            {t('manageSpaces')}
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => {
                          handleLogout();
                          setMobileOpen(false);
                        }}
                        className="text-left text-red-500"
                      >
                        {demoRole ? t('exitDemo') : t('logout')}
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="text-xs text-gray-400 uppercase tracking-wider">{t('demoAs')}</div>
                      <button
                        onClick={() => { enterDemo('customer'); setMobileOpen(false); }}
                        className="text-left text-gray-700"
                      >
                        {t('demoCustomer')}
                      </button>
                      <button
                        onClick={() => { enterDemo('owner'); setMobileOpen(false); }}
                        className="text-left text-gray-700"
                      >
                        {t('demoOwner')}
                      </button>
                      <hr className="border-gray-200" />
                      <Link href="/login" onClick={() => setMobileOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start">
                          {t('login')}
                        </Button>
                      </Link>
                      <Link href="/register" onClick={() => setMobileOpen(false)}>
                        <Button className="w-full bg-[#F9AB18] hover:bg-[#F8A015]">
                          {t('register')}
                        </Button>
                      </Link>
                    </>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </nav>
  );
}
