'use client';

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Pagination } from '@/components/ui/pagination';
import {
  CreditCard,
  Plus,
  Edit,
  Trash2,
  Search,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronRight,
  Settings,
  RefreshCw
} from 'lucide-react';
import { subscriptionApi } from '@/lib/api';
import { toast } from '@/lib/toast';
import SubscriptionForm from '@/components/forms/SubscriptionForm';
import SubscriptionEntitlementForm from '@/components/forms/SubscriptionEntitlementForm';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface Subscription {
  id: string;
  tenant_id: string;
  tenant_name?: string;
  plan_id: string;
  plan_name?: string;
  status: string;
  start_date: string;
  issue_date?: string;
  end_date?: string;
  auto_renew: boolean;
  payment_provider_id?: string;
  validity_days?: number;
}

interface SubscriptionEntitlement {
  subscription_id: string;
  feature_id: string;
  feature_key?: string;
  effective_value: any;
  overridden: boolean;
}

export default function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
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
  const [showEntitlementModal, setShowEntitlementModal] = useState(false);
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [selectedEntitlement, setSelectedEntitlement] = useState<SubscriptionEntitlement | null>(null);

  // Entitlements state
  const [expandedSubscriptions, setExpandedSubscriptions] = useState<Set<string>>(new Set());
  const [subscriptionEntitlements, setSubscriptionEntitlements] = useState<Record<string, SubscriptionEntitlement[]>>({});

  useEffect(() => {
    loadSubscriptions();
  }, []);

  const loadSubscriptions = async (page = 1, size = pageSize) => {
    try {
      setLoading(true);
      setCurrentPage(page);
      setPageSize(size);

      const response = await subscriptionApi.getSubscriptions(page, size);
      setSubscriptions(response.items || []);
      setTotalItems(response.total || 0);
      setTotalPages(Math.ceil((response.total || 0) / size));
    } catch (error) {
      console.error('Error loading subscriptions:', error);
      toast.error('Failed to load subscriptions');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    loadSubscriptions(page);
  };

  const handlePageSizeChange = (size: number) => {
    loadSubscriptions(1, size); // Reset to first page when changing page size
  };

  const loadSubscriptionEntitlements = async (subscriptionId: string) => {
    try {
      const response = await subscriptionApi.getSubscriptionEntitlements(subscriptionId);
      setSubscriptionEntitlements(prev => ({
        ...prev,
        [subscriptionId]: response.items || []
      }));
    } catch (error) {
      console.error('Error loading entitlements:', error);
      toast.error('Failed to load entitlements');
    }
  };

  const filteredSubscriptions = subscriptions.filter(subscription =>
    subscription.tenant_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    subscription.plan_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    subscription.status.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleRefresh = () => {
    loadSubscriptions(currentPage);
    // Clear cached entitlements
    setSubscriptionEntitlements({});
    setExpandedSubscriptions(new Set());
  };

  const handleCreate = () => {
    setSelectedSubscription(null);
    setShowCreateModal(true);
  };

  const handleEdit = (subscription: Subscription) => {
    setSelectedSubscription(subscription);
    setShowEditModal(true);
  };

  const handleDelete = (subscription: Subscription) => {
    setSelectedSubscription(subscription);
    setShowDeleteModal(true);
  };

  const handleToggleEntitlements = async (subscriptionId: string) => {
    const newExpanded = new Set(expandedSubscriptions);
    if (newExpanded.has(subscriptionId)) {
      newExpanded.delete(subscriptionId);
    } else {
      newExpanded.add(subscriptionId);
      // Load entitlements if not already loaded
      if (!subscriptionEntitlements[subscriptionId]) {
        await loadSubscriptionEntitlements(subscriptionId);
      }
    }
    setExpandedSubscriptions(newExpanded);
  };

  const handleCreateEntitlement = (subscription: Subscription) => {
    setSelectedSubscription(subscription);
    setSelectedEntitlement(null);
    setShowEntitlementModal(true);
  };

  const handleEditEntitlement = (subscription: Subscription, entitlement: SubscriptionEntitlement) => {
    setSelectedSubscription(subscription);
    setSelectedEntitlement(entitlement);
    setShowEntitlementModal(true);
  };

  const handleDeleteEntitlement = async (subscriptionId: string, featureId: string) => {
    if (!confirm('Are you sure you want to delete this entitlement?')) return;

    try {
      await subscriptionApi.deleteSubscriptionEntitlement(subscriptionId, featureId);
      toast.success('Entitlement deleted successfully');
      // Reload entitlements
      await loadSubscriptionEntitlements(subscriptionId);
    } catch (error) {
      console.error('Error deleting entitlement:', error);
      toast.error('Failed to delete entitlement');
    }
  };

  const confirmDelete = async () => {
    if (!selectedSubscription) return;

    try {
      await subscriptionApi.deleteSubscription(selectedSubscription.id);
      toast.success(`Subscription deleted successfully`);
      setShowDeleteModal(false);
      loadSubscriptions(currentPage);
    } catch (error) {
      console.error('Error deleting subscription:', error);
    }
  };

  const handleFormSuccess = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setShowEntitlementModal(false);
    setTimeout(() => loadSubscriptions(currentPage), 500);
  };

  const handleEntitlementFormSuccess = () => {
    setShowEntitlementModal(false);
    if (selectedSubscription) {
      loadSubscriptionEntitlements(selectedSubscription.id);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'trialing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'past_due':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'canceled':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">Subscriptions</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Manage tenant subscriptions and their feature entitlements</p>
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
              <span>Add Subscription</span>
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <Card className="p-4">
          <div className="flex items-center">
            <div className="relative flex-1">
              <Input
                type="text"
                placeholder="Search subscriptions..."
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

        {/* Subscriptions Table */}
        <Card>
          <div className="overflow-x-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
                <span className="text-gray-600 dark:text-gray-400">Loading subscriptions...</span>
              </div>
            ) : filteredSubscriptions.length === 0 ? (
              <div className="text-center py-12">
                <CreditCard className="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No subscriptions found</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {searchQuery ? 'Try adjusting your search terms.' : 'Get started by creating your first subscription.'}
                </p>
                {!searchQuery && (
                  <Button className="flex items-center space-x-2 mx-auto">
                    <Plus size={18} />
                    <span>Create Subscription</span>
                  </Button>
                )}
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Expand
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Tenant
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Plan
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Start Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Validity Days
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Auto Renew
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredSubscriptions.map((subscription) => (
                    <>
                      <tr key={subscription.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleEntitlements(subscription.id)}
                            className="p-1"
                          >
                            {expandedSubscriptions.has(subscription.id) ? (
                              <ChevronDown size={16} />
                            ) : (
                              <ChevronRight size={16} />
                            )}
                          </Button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900 dark:text-gray-50">
                            {subscription.tenant_name || subscription.tenant_id}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900 dark:text-gray-50">
                            {subscription.plan_name || subscription.plan_id}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(subscription.status)}`}>
                            {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                          {new Date(subscription.start_date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                          {subscription.validity_days || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {subscription.auto_renew ? (
                            <CheckCircle size={16} className="text-green-500" />
                          ) : (
                            <XCircle size={16} className="text-red-500" />
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-gray-400 hover:text-blue-500"
                              title="Manage entitlements"
                              onClick={() => handleCreateEntitlement(subscription)}
                            >
                              <Settings size={16} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-gray-400 hover:text-blue-500"
                              title="Edit subscription"
                              onClick={() => handleEdit(subscription)}
                            >
                              <Edit size={16} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-gray-400 hover:text-red-500"
                              title="Delete subscription"
                              onClick={() => handleDelete(subscription)}
                            >
                              <Trash2 size={16} />
                            </Button>
                          </div>
                        </td>
                      </tr>
                      {expandedSubscriptions.has(subscription.id) && (
                        <tr key={`${subscription.id}-entitlements`}>
                          <td colSpan={8} className="px-6 py-4 bg-gray-50 dark:bg-gray-800">
                            <div className="space-y-3">
                              <div className="flex items-center justify-between">
                                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-50">
                                  Feature Entitlements
                                </h4>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleCreateEntitlement(subscription)}
                                >
                                  <Plus size={14} className="mr-1" />
                                  Add Entitlement
                                </Button>
                              </div>
                              {subscriptionEntitlements[subscription.id]?.length > 0 ? (
                                <div className="overflow-x-auto">
                                  <table className="w-full text-sm">
                                    <thead className="bg-gray-100 dark:bg-gray-700">
                                      <tr>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                          Feature
                                        </th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                          Value
                                        </th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                          Overridden
                                        </th>
                                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                          Actions
                                        </th>
                                      </tr>
                                    </thead>
                                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                                      {subscriptionEntitlements[subscription.id].map((entitlement) => (
                                        <tr key={`${subscription.id}-${entitlement.feature_id}`} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                                          <td className="px-4 py-2 whitespace-nowrap font-medium text-gray-900 dark:text-gray-50">
                                            {entitlement.feature_key || entitlement.feature_id}
                                          </td>
                                          <td className="px-4 py-2 whitespace-nowrap text-gray-600 dark:text-gray-400 max-w-xs truncate">
                                            {entitlement.effective_value ? JSON.stringify(entitlement.effective_value) : 'null'}
                                          </td>
                                          <td className="px-4 py-2 whitespace-nowrap">
                                            {entitlement.overridden ? (
                                              <CheckCircle size={14} className="text-green-500" />
                                            ) : (
                                              <XCircle size={14} className="text-gray-400" />
                                            )}
                                          </td>
                                          <td className="px-4 py-2 whitespace-nowrap text-right">
                                            <div className="flex items-center justify-end space-x-1">
                                              <Button
                                                variant="ghost"
                                                size="sm"
                                                className="text-gray-400 hover:text-blue-500 p-1"
                                                title="Edit entitlement"
                                                onClick={() => handleEditEntitlement(subscription, entitlement)}
                                              >
                                                <Edit size={12} />
                                              </Button>
                                              <Button
                                                variant="ghost"
                                                size="sm"
                                                className="text-gray-400 hover:text-red-500 p-1"
                                                title="Delete entitlement"
                                                onClick={() => handleDeleteEntitlement(subscription.id, entitlement.feature_id)}
                                              >
                                                <Trash2 size={12} />
                                              </Button>
                                            </div>
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              ) : (
                                <div className="text-center py-6 text-gray-500 dark:text-gray-400">
                                  <Settings size={24} className="mx-auto mb-2 opacity-50" />
                                  <p className="text-sm">No entitlements configured</p>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="mt-2"
                                    onClick={() => handleCreateEntitlement(subscription)}
                                  >
                                    <Plus size={14} className="mr-1" />
                                    Add First Entitlement
                                  </Button>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
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

        {/* Create Subscription Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Subscription</DialogTitle>
              <DialogDescription>
                Add a new subscription for a tenant with a specific plan.
              </DialogDescription>
            </DialogHeader>
            <SubscriptionForm
              onSuccess={handleFormSuccess}
              onCancel={() => setShowCreateModal(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Edit Subscription Modal */}
        <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Subscription</DialogTitle>
              <DialogDescription>
                Update subscription information.
              </DialogDescription>
            </DialogHeader>
            <SubscriptionForm
              subscription={selectedSubscription}
              onSuccess={handleFormSuccess}
              onCancel={() => setShowEditModal(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Modal */}
        <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Subscription</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this subscription?
                This action cannot be undone and will remove all associated entitlements.
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
                      This will permanently delete the subscription and all its feature entitlements.
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
                Delete Subscription
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Entitlement Modal */}
        <Dialog open={showEntitlementModal} onOpenChange={setShowEntitlementModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {selectedEntitlement ? 'Edit Entitlement' : 'Create Entitlement'}
              </DialogTitle>
              <DialogDescription>
                {selectedEntitlement
                  ? 'Update the entitlement value for this feature.'
                  : 'Add a new feature entitlement to this subscription.'
                }
              </DialogDescription>
            </DialogHeader>
            {selectedSubscription && (
              <SubscriptionEntitlementForm
                subscriptionId={selectedSubscription.id}
                entitlement={selectedEntitlement}
                onSuccess={handleEntitlementFormSuccess}
                onCancel={() => setShowEntitlementModal(false)}
              />
            )}
          </DialogContent>
        </Dialog>
      </div>
    </ProtectedRoute>
  );
}