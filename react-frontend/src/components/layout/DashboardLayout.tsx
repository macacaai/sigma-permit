'use client';

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useTheme } from 'next-themes';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  Home,
  Building,
  FileText,
  Key,
  Shield,
  Users,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Package,
  CreditCard,
  Settings,
  UserCheck,
  LogOut,
  Sun,
  Moon,
  BookOpen,
  User
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  {
    name: 'Tenants',
    href: '/tenants/',
    icon: Building
  },
  {
    name: 'Licensing',
    icon: Key,
    defaultChild: '/licenses/',
    children: [
      { name: 'Templates', href: '/templates/', icon: FileText },
      { name: 'Licenses', href: '/licenses/', icon: Key },
      { name: 'Master Keys', href: '/master-keys/', icon: Shield },
      { name: 'Validation', href: '/validate/', icon: Shield }
    ]
  },
  {
    name: 'Subscriptions',
    icon: Package,
    defaultChild: '/subscriptions/',
    children: [
      { name: 'Products', href: '/products/', icon: Package },
      { name: 'Plans', href: '/plans/', icon: CreditCard },
      { name: 'Features', href: '/features/', icon: Settings },
      { name: 'Subscriptions', href: '/subscriptions/', icon: UserCheck }
    ]
  },
  {
    name: 'Identity & Access',
    icon: Users,
    defaultChild: '/users/',
    children: [
      { name: 'Users', href: '/users/', icon: Users },
      { name: 'Applications', href: '/applications/', icon: Shield },
      { name: 'Sessions', href: '/sessions/', icon: UserCheck },
      { name: 'OAuth2/OIDC', href: '/oauth/', icon: Key },
      { name: 'Providers', href: '/providers/', icon: Settings }
    ]
  }
];

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState<string[]>(() => {
    // Initialize from localStorage if available
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('expandedMenus');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  const pathname = usePathname();
  const { user, logout } = useAuth();

  // Persist expanded menus to localStorage
  const updateExpandedMenus = (newMenus: string[] | ((prev: string[]) => string[])) => {
    setExpandedMenus((prev) => {
      const updated = typeof newMenus === 'function' ? newMenus(prev) : newMenus;
      if (typeof window !== 'undefined') {
        localStorage.setItem('expandedMenus', JSON.stringify(updated));
      }
      return updated;
    });
  };

  const { theme, setTheme } = useTheme();

  const toggleMenu = (menuName: string) => {
    updateExpandedMenus(current => {
      const isExpanded = current.includes(menuName);
      if (isExpanded) {
        // Allow manual collapse
        return current.filter(name => name !== menuName);
      } else {
        // Allow manual expansion
        return [...current, menuName];
      }
    });
  };

  const isMenuExpanded = (menuName: string): boolean => {
    return expandedMenus.includes(menuName);
  };

  const isChildActive = (child: any): boolean => {
    return pathname === child.href;
  };

  const isParentActive = (item: any): boolean => {
    if (item.children) {
      return item.children.some((child: any) => pathname === child.href);
    }
    return pathname === item.href;
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden bg-black bg-opacity-50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 z-50 h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transform transition-all duration-300 ease-in-out flex flex-col ${
          sidebarCollapsed ? 'w-16' : 'w-64'
        } ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          {sidebarCollapsed ? (
            <h1 className="text-xl font-bold bg-gradient-to-r from-yellow-400 via-yellow-500 to-green-500 bg-clip-text text-transparent" style={{ fontFamily: "'XYBER-Bold', Arial, sans-serif" }}>
              SP
            </h1>
          ) : (
            <h1 className="text-xl font-bold bg-gradient-to-r from-yellow-400 via-yellow-500 to-green-500 bg-clip-text text-transparent" style={{ fontFamily: "'XYBER-Bold', Arial, sans-serif" }}>
              SIGMA PERMIT
            </h1>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden"
          >
            <X size={16} />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4">
          <ul className="space-y-2">
            {navigation.map((item) => (
              <li key={item.name}>
                {item.children ? (
                  <div>
                    <button
                      onClick={() => toggleMenu(item.name)}
                      className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors duration-200 cursor-pointer ${
                        isMenuExpanded(item.name)
                          ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50'
                          : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-50'
                      }`}
                    >
                      <item.icon size={18} className={sidebarCollapsed ? '' : 'mr-3'} />
                      {!sidebarCollapsed && (
                        <>
                          <span className="flex-1 text-left">{item.name}</span>
                          <ChevronRight
                            size={16}
                            className={`transition-transform duration-200 ${isMenuExpanded(item.name) ? 'rotate-90' : ''}`}
                          />
                        </>
                      )}
                    </button>

                    {!sidebarCollapsed && isMenuExpanded(item.name) && (
                      <ul className="ml-6 mt-1 space-y-1">
                        {item.children.map((child) => (
                          <li key={child.href}>
                            <Link
                              href={child.href}
                              onClick={() => setSidebarOpen(false)}
                              className={`flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${
                                isChildActive(child)
                                  ? 'bg-blue-600 text-white'
                                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-50'
                              }`}
                            >
                              <child.icon size={16} className="mr-3" />
                              {child.name}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : (
                  <Link
                    href={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'px-4'} py-3 text-sm font-medium rounded-lg transition-colors duration-200 ${
                      pathname === item.href
                        ? 'bg-blue-500 text-white'
                        : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-50'
                    }`}
                  >
                    <item.icon size={18} className={sidebarCollapsed ? '' : 'mr-3'} />
                    {!sidebarCollapsed && item.name}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          {!sidebarCollapsed && (
            <div className="space-y-2">
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Logged in as: {user?.username}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="w-full justify-start"
              >
                <LogOut size={16} className="mr-2" />
                Logout
              </Button>
            </div>
          )}
          {sidebarCollapsed && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="w-full justify-center"
              title="Logout"
            >
              <LogOut size={16} />
            </Button>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className={`transition-all duration-300 ease-in-out ${sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'}`}>
        {/* Top bar */}
        <div className="sticky top-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden"
              >
                <Menu size={16} />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="hidden lg:flex"
                title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
              </Button>
            </div>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Right side actions */}
            <div className="flex items-center space-x-2">
              {/* Docs link */}
              <Button
                variant="ghost"
                size="sm"
                asChild
              >
                <a href="/docs" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-1">
                  <BookOpen size={16} />
                  <span className="hidden sm:inline">Docs</span>
                </a>
              </Button>

              {/* Theme toggle */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              >
                {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              </Button>

              {/* User avatar dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-blue-500 text-white">
                        {user?.username?.charAt(0).toUpperCase() || 'U'}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <div className="flex items-center justify-start gap-2 p-2">
                    <div className="flex flex-col space-y-1 leading-none">
                      <p className="font-medium">{user?.username}</p>
                      <p className="w-[200px] truncate text-sm text-muted-foreground">
                        {user?.email || 'No email'}
                      </p>
                    </div>
                  </div>
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}