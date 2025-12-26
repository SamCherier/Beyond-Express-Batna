import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { LogOut, Truck } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';

const DriverLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/driver/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Simple Mobile Header */}
      <header className="bg-red-600 text-white shadow-md sticky top-0 z-50">
        <div className="px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Truck className="w-6 h-6" />
            <div>
              <h1 className="text-lg font-bold">Beyond Express</h1>
              <p className="text-xs text-red-100">Espace Livreur</p>
            </div>
          </div>
          {user && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-white hover:bg-red-700"
            >
              <LogOut className="w-5 h-5" />
            </Button>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="pb-20">
        <Outlet />
      </main>
    </div>
  );
};

export default DriverLayout;
