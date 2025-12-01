'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import {
  Monitor,
  Smartphone,
  Globe,
  Shield,
  AlertTriangle,
  Clock,
  MapPin,
  User,
  Power,
  Lock,
  Unlock,
  RefreshCw
} from 'lucide-react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { sessionsApi } from '@/lib/api';

interface Session {
  id: string;
  user_id: string;
  session_id: string;
  device_info: any;
  ip_address: string;
  user_agent: string;
  location: any;
  is_active: boolean;
  created_at: string;
  last_activity: string;
  expires_at: string;
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeOnly, setActiveOnly] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadSessions();
  }, [currentPage, activeOnly]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        size: '10',
        active_only: activeOnly.toString()
      });

      const response = await sessionsApi.getSessions(params);
      setSessions(response.items || []);
      setTotal(response.total || 0);
      setTotalPages(Math.ceil((response.total || 0) / 10));
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const terminateSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to terminate this session?')) return;

    try {
      await sessionsApi.terminateSession(sessionId);
      loadSessions(); // Refresh the list
    } catch (error) {
      console.error('Error terminating session:', error);
    }
  };

  const terminateAllSessions = async () => {
    if (!confirm('Are you sure you want to terminate ALL sessions? This will log out all users.')) return;

    try {
      await sessionsApi.terminateAllSessions();
      loadSessions(); // Refresh the list
    } catch (error) {
      console.error('Error terminating all sessions:', error);
    }
  };

  const refreshSession = async (sessionId: string) => {
    try {
      await sessionsApi.refreshSession(sessionId);
      loadSessions(); // Refresh the list
    } catch (error) {
      console.error('Error refreshing session:', error);
    }
  };

  const lockSession = async (sessionId: string) => {
    try {
      await sessionsApi.lockSession(sessionId);
      loadSessions(); // Refresh the list
    } catch (error) {
      console.error('Error locking session:', error);
    }
  };

  const unlockSession = async (sessionId: string) => {
    try {
      await sessionsApi.unlockSession(sessionId);
      loadSessions(); // Refresh the list
    } catch (error) {
      console.error('Error unlocking session:', error);
    }
  };

  const getDeviceIcon = (deviceInfo: any) => {
    if (!deviceInfo) return <Monitor size={20} />;

    const userAgent = deviceInfo.user_agent?.toLowerCase() || '';
    if (userAgent.includes('mobile') || userAgent.includes('android') || userAgent.includes('iphone')) {
      return <Smartphone size={20} />;
    }
    return <Monitor size={20} />;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const isExpired = (expiresAt: string) => {
    return new Date(expiresAt) < new Date();
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">Active Sessions</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Monitor and manage user sessions across devices</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label htmlFor="activeOnly" className="text-sm font-medium">Active only</label>
              <Switch
                id="activeOnly"
                checked={activeOnly}
                onCheckedChange={setActiveOnly}
              />
            </div>
            <Button variant="destructive" onClick={terminateAllSessions}>
              <Power size={16} className="mr-2" />
              Terminate All
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Sessions</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{total}</p>
                </div>
                <Shield className="text-blue-500" size={24} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Sessions</p>
                  <p className="text-3xl font-bold text-green-600">
                    {sessions.filter(s => s.is_active && !isExpired(s.expires_at)).length}
                  </p>
                </div>
                <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Expired Sessions</p>
                  <p className="text-3xl font-bold text-red-600">
                    {sessions.filter(s => isExpired(s.expires_at)).length}
                  </p>
                </div>
                <AlertTriangle className="text-red-500" size={24} />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sessions List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Monitor size={20} />
              <span>Sessions ({total})</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {Array(5).fill(0).map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                  </div>
                ))}
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-12">
                <Monitor size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No sessions found</h3>
                <p className="text-gray-600 dark:text-gray-400">No active sessions match your criteria.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {sessions.map((session) => (
                  <div key={session.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                        {getDeviceIcon(session.device_info)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="font-medium text-gray-900 dark:text-gray-50 truncate">
                            Session {session.session_id.slice(-8)}
                          </h3>
                          <Badge variant={session.is_active && !isExpired(session.expires_at) ? 'success' : 'destructive'}>
                            {session.is_active && !isExpired(session.expires_at) ? 'Active' : 'Inactive'}
                          </Badge>
                          {isExpired(session.expires_at) && (
                            <Badge variant="destructive">Expired</Badge>
                          )}
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                          <div className="flex items-center space-x-1">
                            <Globe size={14} />
                            <span>{session.ip_address}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock size={14} />
                            <span>Last: {formatDate(session.last_activity)}</span>
                          </div>
                          {session.location?.country && (
                            <div className="flex items-center space-x-1">
                              <MapPin size={14} />
                              <span>{session.location.country}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        Expires: {formatDate(session.expires_at)}
                      </span>
                      <div className="flex space-x-1">
                        <Button variant="ghost" size="sm" onClick={() => refreshSession(session.id)} title="Refresh session">
                          <RefreshCw size={16} />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => lockSession(session.id)} title="Lock session">
                          <Lock size={16} />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => unlockSession(session.id)} title="Unlock session">
                          <Unlock size={16} />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => terminateSession(session.id)} className="text-red-600 hover:text-red-700">
                          <Power size={16} />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Showing {((currentPage - 1) * 10) + 1} to {Math.min(currentPage * 10, total)} of {total} sessions
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(currentPage - 1)}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage(currentPage + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}