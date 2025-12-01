'use client';

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Pagination } from '@/components/ui/pagination';
import {
  Key,
  Plus,
  Edit,
  Trash2,
  Search,
  CheckCircle,
  XCircle,
  Download,
  RefreshCw,
  Eye
} from 'lucide-react';
import { licenseApi } from '@/lib/api';
import { toast } from '@/lib/toast';
import LicenseForm from '@/components/forms/LicenseForm';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface License {
  id: number;
  license_key: string;
  tenant_id: number;
  tenant_name: string;
  template_id?: number;
  linked_subscription?: string;
  issued_at?: string;
  validity_days?: number;
  payload: any;
  created_at: string;
}

export default function LicensesPage() {
  const [licenses, setLicenses] = useState<License[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedLicense, setSelectedLicense] = useState<any>(null);

  useEffect(() => {
    loadLicenses();
  }, []);

  const loadLicenses = async (page = 1, size = pageSize) => {
    try {
      setLoading(true);
      setCurrentPage(page);
      setPageSize(size);

      const response = await licenseApi.getLicenses(page, size);
      setLicenses(response.items || []);
      setTotalItems(response.total || 0);
      setTotalPages(Math.ceil((response.total || 0) / size));
    } catch (error) {
      console.error('Error loading licenses:', error);
      toast.error('Failed to load licenses');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    loadLicenses(page);
  };

  const handlePageSizeChange = (size: number) => {
    loadLicenses(1, size); // Reset to first page when changing page size
  };

  const filteredLicenses = licenses.filter(license =>
    license.id.toString().includes(searchQuery) ||
    license.tenant_id.toString().includes(searchQuery)
  );

  const handleRefresh = () => {
    loadLicenses(currentPage);
  };

  const handleCreate = () => {
    setSelectedLicense(null);
    setShowCreateModal(true);
  };

  const handleEdit = (license: any) => {
    setSelectedLicense(license);
    setShowEditModal(true);
  };

  const handleDelete = (license: any) => {
    setSelectedLicense(license);
    setShowDeleteModal(true);
  };

  const handleView = (license: any) => {
    setSelectedLicense(license);
    setShowViewModal(true);
  };

  const handleDownload = async (license: any) => {
    try {
      await licenseApi.downloadLicense(license.license_key);
    } catch (error) {
      console.error('Error downloading license:', error);
      toast.error('Failed to download license');
    }
  };

  const confirmDelete = async () => {
    if (!selectedLicense) return;

    try {
      await licenseApi.deleteLicense(selectedLicense.id.toString());
      toast.success(`License deleted successfully`);
      setShowDeleteModal(false);
      loadLicenses(currentPage);
    } catch (error) {
      console.error('Error deleting license:', error);
    }
  };

  const handleFormSuccess = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setTimeout(() => loadLicenses(currentPage), 500);
  };

  const getLicenseType = (license: License): string => {
    // Try to get type from payload
    if (license.payload?.license_type) {
      return license.payload.license_type;
    }
    // Try to infer from template or payload content
    if (license.payload?.features?.includes('user_management')) {
      return 'Business';
    }
    if (license.payload?.features?.includes('basic')) {
      return 'Basic';
    }
    return 'Custom';
  };

  const getExpiryInfo = (license: License): { date: string; color: string; daysRemaining: number } => {
    if (!license.issued_at || !license.validity_days) {
      return {
        date: 'N/A',
        color: 'text-gray-500',
        daysRemaining: 0
      };
    }

    const issuedDate = new Date(license.issued_at);
    const expiryDate = new Date(issuedDate);
    expiryDate.setDate(expiryDate.getDate() + license.validity_days - 1);
    const now = new Date();
    const daysRemaining = Math.ceil((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    let color = 'text-green-600';
    if (daysRemaining <= 10) {
      color = 'text-red-600';
    } else if (daysRemaining <= 20) {
      color = 'text-yellow-600';
    }

    return {
      date: expiryDate.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }),
      color,
      daysRemaining
    };
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">Licenses</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Manage license keys and their distribution</p>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              title="Refresh"
            >
              <RefreshCw size={18} />
            </Button>
            <Button className="flex items-center space-x-2" onClick={handleCreate}>
              <Plus size={18} />
              <span>Issue License</span>
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <Card className="p-4">
          <div className="flex items-center">
            <div className="relative flex-1">
              <Input
                type="text"
                placeholder="Search licenses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pr-10"
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <Search size={18} className="text-gray-400" />
              </div>
            </div>
          </div>
        </Card>

        {/* Licenses Table */}
        <Card>
          <div className="overflow-x-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
                <span className="text-gray-600 dark:text-gray-400">Loading licenses...</span>
              </div>
            ) : filteredLicenses.length === 0 ? (
              <div className="text-center py-12">
                <Key className="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No licenses found</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {searchQuery ? 'Try adjusting your search terms.' : 'Get started by issuing your first license.'}
                </p>
                {!searchQuery && (
                  <Button className="flex items-center space-x-2 mx-auto">
                    <Plus size={18} />
                    <span>Issue License</span>
                  </Button>
                )}
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      License ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Tenant
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Subscription
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Issued
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Expires
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredLicenses.map((license) => (
                    <tr key={license.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-sm text-gray-800 dark:text-gray-200">
                          {license.id.toString().substring(0, 8)}
                        </code>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-900 dark:text-gray-50">
                        {license.tenant_name || `Tenant ${license.tenant_id}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-900 dark:text-gray-50">
                        {getLicenseType(license)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {license.linked_subscription ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                            {license.linked_subscription.substring(0, 8)}...
                          </span>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-500">None</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                          {license.issued_at ? new Date(license.issued_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          getExpiryInfo(license).daysRemaining <= 10
                            ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                            : getExpiryInfo(license).daysRemaining <= 20
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                            : 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                        }`}>
                          {getExpiryInfo(license).date}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-purple-500"
                            title="View license details"
                            onClick={() => handleView(license)}
                          >
                            <Eye size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-green-500"
                            title="Download license"
                            onClick={() => handleDownload(license)}
                          >
                            <Download size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-blue-500"
                            title="Edit license"
                            onClick={() => handleEdit(license)}
                          >
                            <Edit size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-red-500"
                            title="Delete license"
                            onClick={() => handleDelete(license)}
                          >
                            <Trash2 size={16} />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>

        {/* Pagination */}
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          pageSize={pageSize}
          totalItems={totalItems}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />

        {/* Create License Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Issue New License</DialogTitle>
              <DialogDescription>
                Create a new license for a tenant with optional template validation.
              </DialogDescription>
            </DialogHeader>
            <LicenseForm
              onSuccess={handleFormSuccess}
              onCancel={() => setShowCreateModal(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Edit License Modal */}
        <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit License</DialogTitle>
              <DialogDescription>
                Update license information and settings.
              </DialogDescription>
            </DialogHeader>
            <LicenseForm
              license={selectedLicense}
              onSuccess={handleFormSuccess}
              onCancel={() => setShowEditModal(false)}
            />
          </DialogContent>
        </Dialog>

        {/* View License Modal */}
        <Dialog open={showViewModal} onOpenChange={setShowViewModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>License Details</DialogTitle>
              <DialogDescription>
                Detailed information about the selected license.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">License ID</h3>
                  <p className="text-lg font-mono font-medium text-gray-900 dark:text-gray-50">{selectedLicense?.id}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Tenant</h3>
                  <p className="text-lg font-medium text-gray-900 dark:text-gray-50">{selectedLicense?.tenant_name || 'Unknown'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Linked Subscription</h3>
                  <p className="text-lg font-medium text-gray-900 dark:text-gray-50">
                    {selectedLicense?.linked_subscription ? (
                      <span className="font-mono">{selectedLicense.linked_subscription}</span>
                    ) : (
                      'None'
                    )}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Issued Date</h3>
                  <p className="text-lg text-gray-900 dark:text-gray-50">{selectedLicense?.issued_at ? new Date(selectedLicense.issued_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Validity Days</h3>
                  <p className="text-lg text-gray-900 dark:text-gray-50">{selectedLicense?.validity_days ? `${selectedLicense.validity_days} days` : 'N/A'}</p>
                </div>
              </div>

              {selectedLicense?.license_key && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-3">License Key</h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    <p className="text-sm font-mono text-gray-800 dark:text-gray-200 break-all">{selectedLicense.license_key}</p>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    This key should be shared with the customer for offline license validation.
                  </p>
                </div>
              )}

              {selectedLicense?.payload && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-3">License Payload</h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    <pre className="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto"><code>{JSON.stringify(selectedLicense.payload, null, 2)}</code></pre>
                  </div>
                </div>
              )}
            </div>
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => setShowViewModal(false)}>
                Close
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Modal */}
        <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete License</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this license?
                This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                    <Trash2 className="text-red-600 dark:text-red-400" size={20} />
                  </div>
                </div>
                <div className="flex-1">
                  <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                      The license will be permanently removed and cannot be recovered.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={confirmDelete}>
                Delete License
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </ProtectedRoute>
  );
}