'use client';

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Pagination } from '@/components/ui/pagination';
import {
  Settings,
  Plus,
  Edit,
  Trash2,
  Search,
  RefreshCw
} from 'lucide-react';
import { featureApi } from '@/lib/api';
import { toast } from '@/lib/toast';
import FeatureForm from '@/components/forms/FeatureForm';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface Feature {
  id: string;
  product_id: string;
  product_name?: string;
  key: string;
  type: string;
  default_value?: any;
  validation_rules?: any;
}

export default function FeaturesPage() {
  const [features, setFeatures] = useState<Feature[]>([]);
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
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null);

  useEffect(() => {
    loadFeatures();
  }, []);

  const loadFeatures = async (page = 1, size = pageSize) => {
    try {
      setLoading(true);
      setCurrentPage(page);
      setPageSize(size);

      const response = await featureApi.getFeatures(page, size);
      setFeatures(response.items || []);
      setTotalItems(response.total || 0);
      setTotalPages(Math.ceil((response.total || 0) / size));
    } catch (error) {
      console.error('Error loading features:', error);
      toast.error('Failed to load features');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    loadFeatures(page);
  };

  const handlePageSizeChange = (size: number) => {
    loadFeatures(1, size); // Reset to first page when changing page size
  };

  const filteredFeatures = features.filter(feature =>
    feature.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (feature.product_name && feature.product_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    feature.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleRefresh = () => {
    loadFeatures(currentPage);
  };

  const handleCreate = () => {
    setSelectedFeature(null);
    setShowCreateModal(true);
  };

  const handleEdit = (feature: Feature) => {
    setSelectedFeature(feature);
    setShowEditModal(true);
  };

  const handleDelete = (feature: Feature) => {
    setSelectedFeature(feature);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (!selectedFeature) return;

    try {
      await featureApi.deleteFeature(selectedFeature.id);
      toast.success(`Feature "${selectedFeature.key}" deleted successfully`);
      setShowDeleteModal(false);
      loadFeatures(currentPage);
    } catch (error) {
      console.error('Error deleting feature:', error);
    }
  };

  const handleFormSuccess = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setTimeout(() => loadFeatures(currentPage), 500);
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">Features</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Manage product features and their validation rules</p>
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
              <span>Add Feature</span>
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <Card className="p-4">
          <div className="flex items-center">
            <div className="relative flex-1">
              <Input
                type="text"
                placeholder="Search features..."
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

        {/* Features Table */}
        <Card>
          <div className="overflow-x-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
                <span className="text-gray-600 dark:text-gray-400">Loading features...</span>
              </div>
            ) : filteredFeatures.length === 0 ? (
              <div className="text-center py-12">
                <Settings className="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No features found</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {searchQuery ? 'Try adjusting your search terms.' : 'Get started by creating your first feature.'}
                </p>
                {!searchQuery && (
                  <Button className="flex items-center space-x-2 mx-auto">
                    <Plus size={18} />
                    <span>Create Feature</span>
                  </Button>
                )}
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Key
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Default Value
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredFeatures.map((feature) => (
                    <tr key={feature.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-sm text-gray-600 dark:text-gray-400">
                        {feature.id.substring(0, 8)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900 dark:text-gray-50">
                          {feature.product_name || feature.product_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900 dark:text-gray-50">{feature.key}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400 capitalize">
                        {feature.type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400 max-w-xs truncate">
                        {feature.default_value ? JSON.stringify(feature.default_value) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-blue-500"
                            title="Edit feature"
                            onClick={() => handleEdit(feature)}
                          >
                            <Edit size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-red-500"
                            title="Delete feature"
                            onClick={() => handleDelete(feature)}
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

        {/* Create Feature Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Feature</DialogTitle>
              <DialogDescription>
                Add a new feature definition for a product.
              </DialogDescription>
            </DialogHeader>
            <FeatureForm
              onSuccess={handleFormSuccess}
              onCancel={() => setShowCreateModal(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Edit Feature Modal */}
        <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Feature</DialogTitle>
              <DialogDescription>
                Update feature information and validation rules.
              </DialogDescription>
            </DialogHeader>
            <FeatureForm
              feature={selectedFeature}
              onSuccess={handleFormSuccess}
              onCancel={() => setShowEditModal(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Modal */}
        <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Feature</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete <strong>{selectedFeature?.key}</strong>?
                This action cannot be undone and will affect existing subscriptions.
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
                      This will permanently delete the feature and may affect existing subscriptions and entitlements.
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
                Delete Feature
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </ProtectedRoute>
  );
}