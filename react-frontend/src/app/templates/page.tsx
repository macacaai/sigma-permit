'use client';

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Pagination } from '@/components/ui/pagination';
import {
  FileText,
  Plus,
  Edit,
  Trash2,
  Search,
  CheckCircle,
  XCircle,
  Eye,
  RefreshCw
} from 'lucide-react';
import { templateApi } from '@/lib/api';
import { toast } from '@/lib/toast';
import TemplateForm from '@/components/forms/TemplateForm';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface Template {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  payload_schema?: any;
  validation_rules?: any;
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
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
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async (page = 1, size = pageSize) => {
    try {
      setLoading(true);
      setCurrentPage(page);
      setPageSize(size);

      const response = await templateApi.getTemplates(page, size);
      setTemplates(response.items || []);
      setTotalItems(response.total || 0);
      setTotalPages(Math.ceil((response.total || 0) / size));
    } catch (error) {
      console.error('Error loading templates:', error);
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    loadTemplates(page);
  };

  const handlePageSizeChange = (size: number) => {
    loadTemplates(1, size); // Reset to first page when changing page size
  };

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleRefresh = () => {
    loadTemplates(currentPage);
  };

  const handleCreate = () => {
    setSelectedTemplate(null);
    setShowCreateModal(true);
  };

  const handleEdit = (template: Template) => {
    setSelectedTemplate(template);
    setShowEditModal(true);
  };

  const handleDelete = (template: Template) => {
    setSelectedTemplate(template);
    setShowDeleteModal(true);
  };

  const handleView = (template: Template) => {
    setSelectedTemplate(template);
    setShowViewModal(true);
  };

  const confirmDelete = async () => {
    if (!selectedTemplate) return;

    try {
      await templateApi.deleteTemplate(selectedTemplate.id.toString());
      toast.success(`Template "${selectedTemplate.name}" deleted successfully`);
      setShowDeleteModal(false);
      loadTemplates(currentPage);
    } catch (error) {
      console.error('Error deleting template:', error);
    }
  };

  const handleFormSuccess = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setTimeout(() => loadTemplates(currentPage), 500);
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">Templates</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Manage license templates with JSON schema validation</p>
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
              <span>Add Template</span>
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <Card className="p-4">
          <div className="flex items-center">
            <div className="relative flex-1">
              <Input
                type="text"
                placeholder="Search templates..."
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

        {/* Templates Table */}
        <Card>
          <div className="overflow-x-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
                <span className="text-gray-600 dark:text-gray-400">Loading templates...</span>
              </div>
            ) : filteredTemplates.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No templates found</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {searchQuery ? 'Try adjusting your search terms.' : 'Get started by creating your first template.'}
                </p>
                {!searchQuery && (
                  <Button className="flex items-center space-x-2 mx-auto">
                    <Plus size={18} />
                    <span>Create Template</span>
                  </Button>
                )}
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredTemplates.map((template) => (
                    <tr key={template.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900 dark:text-gray-50">{template.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap max-w-xs truncate text-gray-600 dark:text-gray-400" title={template.description}>
                        {template.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          template.is_active
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                        }`}>
                          {template.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                        {new Date(template.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-purple-500"
                            title="View template details"
                            onClick={() => handleView(template)}
                          >
                            <Eye size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-blue-500"
                            title="Edit template"
                            onClick={() => handleEdit(template)}
                          >
                            <Edit size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-red-500"
                            title="Delete template"
                            onClick={() => handleDelete(template)}
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

        {/* Create Template Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Template</DialogTitle>
              <DialogDescription>
                Add a new license template with JSON schema validation.
              </DialogDescription>
            </DialogHeader>
            <TemplateForm
              onSuccess={handleFormSuccess}
              onCancel={() => setShowCreateModal(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Edit Template Modal */}
        <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Template</DialogTitle>
              <DialogDescription>
                Update template information and validation rules.
              </DialogDescription>
            </DialogHeader>
            <TemplateForm
              template={selectedTemplate}
              onSuccess={handleFormSuccess}
              onCancel={() => setShowEditModal(false)}
            />
          </DialogContent>
        </Dialog>

        {/* View Template Modal */}
        <Dialog open={showViewModal} onOpenChange={setShowViewModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Template Details</DialogTitle>
              <DialogDescription>
                Detailed information about the selected template.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Template ID</h3>
                  <p className="text-lg font-mono font-medium text-gray-900 dark:text-gray-50">{selectedTemplate?.id}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Name</h3>
                  <p className="text-lg font-medium text-gray-900 dark:text-gray-50">{selectedTemplate?.name}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</h3>
                  <p className="text-lg text-gray-900 dark:text-gray-50">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${
                      selectedTemplate?.is_active
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                    }`}>
                      {selectedTemplate?.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Created Date</h3>
                  <p className="text-lg text-gray-900 dark:text-gray-50">{selectedTemplate?.created_at ? new Date(selectedTemplate.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A'}</p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-3">Description</h3>
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                  <p className="text-sm text-gray-800 dark:text-gray-200">{selectedTemplate?.description || 'No description provided.'}</p>
                </div>
              </div>

              {selectedTemplate?.payload_schema && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-3">Payload Schema</h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    <pre className="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto"><code>{JSON.stringify(selectedTemplate.payload_schema, null, 2)}</code></pre>
                  </div>
                </div>
              )}

              {selectedTemplate?.validation_rules && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-3">Validation Rules</h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    <pre className="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto"><code>{JSON.stringify(selectedTemplate.validation_rules, null, 2)}</code></pre>
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
              <DialogTitle>Delete Template</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete <strong>{selectedTemplate?.name}</strong>?
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
                      Existing licenses using this template will remain valid, but no new licenses can be created with this template.
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
                Delete Template
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </ProtectedRoute>
  );
}