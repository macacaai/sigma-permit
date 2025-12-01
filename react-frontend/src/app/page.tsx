'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Building,
  FileText,
  Key,
  TrendingUp,
  Users,
  Activity
} from 'lucide-react';
import { tenantApi, templateApi, licenseApi, healthApi } from '@/lib/api';

interface Stats {
  tenants: { total: number; active: number };
  templates: { total: number; active: number };
  licenses: { total: number; recent: number };
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({
    tenants: { total: 0, active: 0 },
    templates: { total: 0, active: 0 },
    licenses: { total: 0, recent: 0 },
  });
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState({ status: 'unknown' });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load health status
      try {
        await healthApi.check();
        setHealth({ status: 'healthy' });
      } catch (error) {
        setHealth({ status: 'unhealthy' });
      }

      // Load stats in parallel (using size=1 to get totals without fetching all data)
      const [tenantsRes, templatesRes, licensesRes] = await Promise.allSettled([
        tenantApi.getTenants(1, 1),
        templateApi.getTemplates(1, 1),
        licenseApi.getLicenses(1, 1)
      ]);

      // Process tenants
      if (tenantsRes.status === 'fulfilled') {
        setStats(prev => ({
          ...prev,
          tenants: { ...prev.tenants, total: tenantsRes.value.total || 0 }
        }));
      }

      // Process templates
      if (templatesRes.status === 'fulfilled') {
        setStats(prev => ({
          ...prev,
          templates: { ...prev.templates, total: templatesRes.value.total || 0 }
        }));
      }

      // Process licenses
      if (licensesRes.status === 'fulfilled') {
        setStats(prev => ({
          ...prev,
          licenses: { ...prev.licenses, total: licensesRes.value.total || 0 }
        }));
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">Dashboard</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Welcome to Sigma Permit - Your License Management System</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
              health.status === 'healthy'
                ? 'bg-green-500/10 text-green-600'
                : 'bg-red-500/10 text-red-600'
            }`}>
              <Activity size={16} />
              <span className="capitalize">{health.status}</span>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {Array(4).fill(0).map((_, i) => (
              <Card key={i} className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2"></div>
                  <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Tenants Card */}
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Tenants</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.tenants.total}</p>
                  <p className="text-sm text-green-600">{stats.tenants.active} active</p>
                </div>
                <div className="p-3 rounded-lg bg-blue-500/10">
                  <Building className="text-blue-600" size={24} />
                </div>
              </div>
            </Card>

            {/* Templates Card */}
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Templates</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.templates.total}</p>
                  <p className="text-sm text-green-600">{stats.templates.active} active</p>
                </div>
                <div className="p-3 rounded-lg bg-purple-500/10">
                  <FileText className="text-purple-600" size={24} />
                </div>
              </div>
            </Card>

            {/* Licenses Card */}
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Licenses</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.licenses.total}</p>
                  <p className="text-sm text-blue-600">+{stats.licenses.recent} this month</p>
                </div>
                <div className="p-3 rounded-lg bg-indigo-500/10">
                  <Key className="text-indigo-600" size={24} />
                </div>
              </div>
            </Card>

            {/* System Health Card */}
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">System Status</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-50 capitalize">{health.status}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">All systems operational</p>
                </div>
                <div className={`p-3 rounded-lg ${
                  health.status === 'healthy' ? 'bg-green-500/10' : 'bg-red-500/10'
                }`}>
                  <Activity className={health.status === 'healthy' ? 'text-green-600' : 'text-red-600'} size={24} />
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Quick Actions */}
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Link href="/tenants">
                <Button variant="outline" className="h-auto p-4 flex items-center justify-start w-full hover:bg-blue-50 dark:hover:bg-blue-950/20">
                  <Building className="text-blue-500 mr-3 flex-shrink-0" size={20} />
                  <div className="text-left min-w-0 flex-1">
                    <div className="font-medium truncate">Manage Tenants</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">Create and manage tenant organizations</div>
                  </div>
                </Button>
              </Link>

              <Link href="/templates">
                <Button variant="outline" className="h-auto p-4 flex items-center justify-start w-full hover:bg-purple-50 dark:hover:bg-purple-950/20">
                  <FileText className="text-purple-500 mr-3 flex-shrink-0" size={20} />
                  <div className="text-left min-w-0 flex-1">
                    <div className="font-medium truncate">Manage Templates</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">Create license templates with validation</div>
                  </div>
                </Button>
              </Link>

              <Link href="/licenses">
                <Button variant="outline" className="h-auto p-4 flex items-center justify-start w-full hover:bg-indigo-50 dark:hover:bg-indigo-950/20">
                  <Key className="text-indigo-500 mr-3 flex-shrink-0" size={20} />
                  <div className="text-left min-w-0 flex-1">
                    <div className="font-medium truncate">Issue Licenses</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">Create and manage license keys</div>
                  </div>
                </Button>
              </Link>

              <a href="/docs" target="_blank" rel="noopener noreferrer">
                <Button variant="outline" className="h-auto p-4 flex items-center justify-start w-full hover:bg-green-50 dark:hover:bg-green-950/20">
                  <TrendingUp className="text-green-500 mr-3 flex-shrink-0" size={20} />
                  <div className="text-left min-w-0 flex-1">
                    <div className="font-medium truncate">API Documentation</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">Explore and test API endpoints</div>
                  </div>
                </Button>
              </a>
            </div>
          </CardContent>
        </Card>

        {/* Getting Started */}
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  1
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-50">Create Your First Tenant</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Start by creating a tenant organization to represent your client or department.</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  2
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-50">Set Up License Templates</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Create reusable templates with JSON schemas to standardize your license formats.</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  3
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-50">Issue Your First License</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Generate license keys for your tenants using the templates you've created.</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
