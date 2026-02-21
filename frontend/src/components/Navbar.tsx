'use client';

import React, { useState } from 'react';
import { Menu, User } from 'lucide-react';
import Link from 'next/link';
import { useUser } from '@stackframe/stack';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';

interface NavbarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export function Navbar({ currentPage, onNavigate }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const user = useUser();
  const isAuthenticated = !!user;
  const isOwnerOrAdmin =
    (user?.clientReadOnlyMetadata as any)?.role === 'owner' ||
    (user?.clientReadOnlyMetadata as any)?.role === 'admin';

  const navLinks = [
    { name: 'Home', id: 'home' },
    { name: 'Explore', id: 'explore' },
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
            {isAuthenticated ? (
              <>
                <Button
                  variant="ghost"
                  onClick={() => onNavigate('dashboard')}
                  className="text-gray-700"
                >
                  Dashboard
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <User className="h-5 w-5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onNavigate('dashboard')}>
                      My Dashboard
                    </DropdownMenuItem>
                    {isOwnerOrAdmin && (
                      <DropdownMenuItem onClick={() => onNavigate('owner-dashboard')}>
                        Owner Dashboard
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem>Settings</DropdownMenuItem>
                    <DropdownMenuItem onClick={() => user.signOut()}>
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <>
                <Link href="/handler/sign-in">
                  <Button variant="ghost" className="text-gray-700">
                    Log in
                  </Button>
                </Link>
                <Link href="/handler/sign-up">
                  <Button className="bg-[#F9AB18] hover:bg-[#F8A015] text-white">
                    Sign up
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
                  
                  {isAuthenticated ? (
                    <>
                      <button
                        onClick={() => {
                          onNavigate('dashboard');
                          setMobileOpen(false);
                        }}
                        className="text-left text-gray-700"
                      >
                        My Dashboard
                      </button>
                      {isOwnerOrAdmin && (
                        <button
                          onClick={() => {
                            onNavigate('owner-dashboard');
                            setMobileOpen(false);
                          }}
                          className="text-left text-gray-700"
                        >
                          Owner Dashboard
                        </button>
                      )}
                      <button className="text-left text-gray-700">Settings</button>
                      <button
                        onClick={() => user.signOut()}
                        className="text-left text-gray-700"
                      >
                        Logout
                      </button>
                    </>
                  ) : (
                    <>
                      <Link href="/handler/sign-in" onClick={() => setMobileOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start">
                          Log in
                        </Button>
                      </Link>
                      <Link href="/handler/sign-up" onClick={() => setMobileOpen(false)}>
                        <Button className="w-full bg-[#F9AB18] hover:bg-[#F8A015]">
                          Sign up
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
