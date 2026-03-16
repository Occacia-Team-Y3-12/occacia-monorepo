// frontend/src/app/admin/pending-requests/page.tsx

'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2,
  User,
  Clock,
  CheckCircle,
  XCircle,
  Search,
  Filter,
  MoreHorizontal,
  Calendar,
  Mail,
  Phone,
  MapPin,
  FileText,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { adminService } from '@/services/adminService';
import {
  Vendor,
  Organization,
  VendorStatus,
  OrganizationStatus,
  VendorType,
} from '@/types/vendor';
import { formatDate } from '@/lib/formatters';
import { toast } from 'react-hot-toast';

type TabType = 'vendors' | 'organizations';
type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => void;
  type: 'approve' | 'reject';
  itemName: string;
}

const ApprovalModal: React.FC<ApprovalModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  type,
  itemName,
}) => {
  const [reason, setReason] = useState('');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
      >
        <h3 className="mb-4 text-xl font-bold text-gray-900">
          {type === 'approve' ? 'Approve' : 'Reject'} {itemName}
        </h3>
        
        <p className="mb-4 text-gray-600">
          {type === 'approve'
            ? 'Are you sure you want to approve this request?'
            : 'Please provide a reason for rejection:'}
        </p>

        {type === 'reject' && (
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Enter rejection reason..."
            className="mb-4 w-full rounded-xl border border-gray-200 p-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            rows={3}
          />
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-xl border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(reason)}
            className={`flex-1 rounded-xl px-4 py-2 text-sm font-medium text-white transition-colors ${
              type === 'approve'
                ? 'bg-green-600 hover:bg-green-700'
                : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            {type === 'approve' ? 'Approve' : 'Reject'}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

interface DetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: Vendor | Organization | null;
  type: TabType;
}

const DetailModal: React.FC<DetailModalProps> = ({ isOpen, onClose, item, type }) => {
  if (!isOpen || !item) return null;

  const isVendor = type === 'vendors';
  const vendor = item as Vendor;
  const org = item as Organization;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-2xl"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-100 bg-white px-6 py-4">
          <h3 className="text-xl font-bold text-gray-900">
            {isVendor ? vendor.business_name : org.name}
          </h3>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Close details modal"
            title="Close"
          >
            <XCircle className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Status Badge */}
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
                item.status === 'pending'
                  ? 'bg-amber-100 text-amber-700'
                  : item.status === 'approved'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-red-100 text-red-700'
              }`}
            >
              {item.status === 'pending' && <Clock className="h-3.5 w-3.5" />}
              {item.status === 'approved' && <CheckCircle className="h-3.5 w-3.5" />}
              {item.status === 'rejected' && <XCircle className="h-3.5 w-3.5" />}
              {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
            </span>
            {item.status_reason && (
              <span className="text-sm text-gray-500">Reason: {item.status_reason}</span>
            )}
          </div>

          {/* Basic Info */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-4">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                Contact Information
              </h4>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <span className="text-gray-900">
                    {isVendor ? vendor.business_email : org.email}
                  </span>
                </div>
                {(isVendor ? vendor.business_phone : org.phone) && (
                  <div className="flex items-center gap-3 text-sm">
                    <Phone className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-900">
                      {isVendor ? vendor.business_phone : org.phone}
                    </span>
                  </div>
                )}
                {(isVendor ? vendor.business_address : org.address) && (
                  <div className="flex items-start gap-3 text-sm">
                    <MapPin className="h-4 w-4 text-gray-400 mt-0.5" />
                    <span className="text-gray-900">
                      {isVendor ? vendor.business_address : org.address}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                Business Details
              </h4>
              <div className="space-y-3">
                {isVendor ? (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Business Type</span>
                      <span className="font-medium text-gray-900">
                        {vendor.business_type || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Vendor Type</span>
                      <span className="font-medium text-gray-900">
                        {vendor.vendor_type === VendorType.INDIVIDUAL
                          ? 'Individual'
                          : 'Organization'}
                      </span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Legal Name</span>
                      <span className="font-medium text-gray-900">{org.legal_name}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Registration</span>
                      <span className="font-medium text-gray-900">
                        {org.registration_number || 'N/A'}
                      </span>
                    </div>
                    {org.tax_id && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Tax ID</span>
                        <span className="font-medium text-gray-900">{org.tax_id}</span>
                      </div>
                    )}
                    {org.website && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Website</span>
                        <a
                          href={org.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-blue-600 hover:underline flex items-center gap-1"
                        >
                          Visit <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Description */}
          {(isVendor ? vendor.description : org.description) && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                Description
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed">
                {isVendor ? vendor.description : org.description}
              </p>
            </div>
          )}

          {/* Documents for Organizations */}
          {!isVendor && (org.business_license_url || org.tax_certificate_url) && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                Documents
              </h4>
              <div className="flex gap-3">
                {org.business_license_url && (
                  <a
                    href={org.business_license_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
                  >
                    <FileText className="h-4 w-4" />
                    Business License
                  </a>
                )}
                {org.tax_certificate_url && (
                  <a
                    href={org.tax_certificate_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
                  >
                    <FileText className="h-4 w-4" />
                    Tax Certificate
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="border-t border-gray-100 pt-4">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <div className="flex items-center gap-2">
                <Calendar className="h-3.5 w-3.5" />
                <span>Submitted on {formatDate(item.created_at)}</span>
              </div>
              {item.reviewed_at && (
                <span>Reviewed on {formatDate(item.reviewed_at)}</span>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default function PendingRequestsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('vendors');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('pending');
  const [searchQuery, setSearchQuery] = useState('');
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    total: 0,
    pageSize: 10,
  });

  // Modal states
  const [selectedItem, setSelectedItem] = useState<Vendor | Organization | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [approvalAction, setApprovalAction] = useState<'approve' | 'reject'>('approve');

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'vendors') {
        const params = {
          page: pagination.page,
          limit: pagination.pageSize,
          status:
            statusFilter === 'all'
              ? undefined
              : statusFilter === 'pending'
              ? VendorStatus.PENDING
              : statusFilter === 'approved'
              ? VendorStatus.APPROVED
              : VendorStatus.REJECTED,
          search: searchQuery || undefined,
        };

        const response = await adminService.getVendors(params);
        setVendors(response.items);
        setPagination((prev) => ({ ...prev, total: response.total }));
      } else {
        const params = {
          page: pagination.page,
          limit: pagination.pageSize,
          status:
            statusFilter === 'all'
              ? undefined
              : statusFilter === 'pending'
              ? OrganizationStatus.PENDING
              : statusFilter === 'approved'
              ? OrganizationStatus.APPROVED
              : OrganizationStatus.REJECTED,
          search: searchQuery || undefined,
        };

        const response = await adminService.getOrganizations(params);
        setOrganizations(response.items);
        setPagination((prev) => ({ ...prev, total: response.total }));
      }
    } catch (error) {
      toast.error('Failed to fetch data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab, statusFilter, pagination.page, searchQuery]);

  const handleStatusUpdate = async (reason?: string) => {
    if (!selectedItem) return;

    try {
      const status =
        approvalAction === 'approve'
          ? activeTab === 'vendors'
            ? VendorStatus.APPROVED
            : OrganizationStatus.APPROVED
          : activeTab === 'vendors'
          ? VendorStatus.REJECTED
          : OrganizationStatus.REJECTED;

      if (activeTab === 'vendors') {
        await adminService.updateVendorStatus(selectedItem.id, {
          status,
          status_reason: reason,
        });
      } else {
        await adminService.updateOrganizationStatus(selectedItem.id, {
          status,
          status_reason: reason,
        });
      }

      toast.success(
        `${activeTab === 'vendors' ? 'Vendor' : 'Organization'} ${
          approvalAction === 'approve' ? 'approved' : 'rejected'
        } successfully`
      );
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
      console.error(error);
    } finally {
      setApprovalModalOpen(false);
      setSelectedItem(null);
    }
  };

  const openApprovalModal = (
    item: Vendor | Organization,
    action: 'approve' | 'reject'
  ) => {
    setSelectedItem(item);
    setApprovalAction(action);
    setApprovalModalOpen(true);
  };

  const openDetailModal = (item: Vendor | Organization) => {
    setSelectedItem(item);
    setDetailModalOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'approved':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const currentItems = activeTab === 'vendors' ? vendors : organizations;

  return (
    <div className="min-h-screen bg-gray-50/50 p-6">
      {/* Header */}
      <div className="mb-8">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-bold text-gray-900"
        >
          Pending Requests
        </motion.h1>
        <p className="mt-2 text-gray-600">
          Manage and approve vendor and organization requests
        </p>
      </div>

      {/* Main Tabs - Vendors vs Organizations */}
      <div className="mb-6">
        <div className="flex items-center justify-between border-b border-gray-200">
          <div className="flex gap-8">
            <button
              onClick={() => {
                setActiveTab('vendors');
                setPagination((prev) => ({ ...prev, page: 1 }));
              }}
              className={`relative pb-4 text-sm font-medium transition-colors ${
                activeTab === 'vendors'
                  ? 'text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="flex items-center gap-2">
                <User className="h-4 w-4" />
                Individual Vendors
              </span>
              {activeTab === 'vendors' && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
                />
              )}
            </button>
            <button
              onClick={() => {
                setActiveTab('organizations');
                setPagination((prev) => ({ ...prev, page: 1 }));
              }}
              className={`relative pb-4 text-sm font-medium transition-colors ${
                activeTab === 'organizations'
                  ? 'text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                Organizations
              </span>
              {activeTab === 'organizations' && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
                />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Sub-tabs for Status - Like the screenshot */}
      <div className="mb-6">
        <h2 className="mb-4 text-lg font-semibold text-blue-600">
          {activeTab === 'vendors' ? 'Vendor' : 'Organization'} Pending Requests
        </h2>
        <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 pb-4">
          {(['all', 'pending', 'approved', 'rejected'] as StatusFilter[]).map(
            (status) => (
              <button
                key={status}
                onClick={() => {
                  setStatusFilter(status);
                  setPagination((prev) => ({ ...prev, page: 1 }));
                }}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                  statusFilter === status
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-200'
                    : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
                }`}
              >
                {status === 'all' && 'All Requests'}
                {status === 'pending' && 'Awaiting Review'}
                {status === 'approved' && 'Approved'}
                {status === 'rejected' && 'Rejected'}
              </button>
            )
          )}
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder={`Search ${activeTab}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Filter className="h-4 w-4" />
          <span>
            Showing {currentItems.length} of {pagination.total} results
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex h-96 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        ) : currentItems.length === 0 ? (
          <div className="flex h-96 flex-col items-center justify-center text-center">
            <div className="mb-4 rounded-full bg-gray-100 p-4">
              {activeTab === 'vendors' ? (
                <User className="h-8 w-8 text-gray-400" />
              ) : (
                <Building2 className="h-8 w-8 text-gray-400" />
              )}
            </div>
            <h3 className="text-lg font-semibold text-gray-900">No requests found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {statusFilter === 'pending'
                ? `No pending ${activeTab} requests at the moment.`
                : `No ${statusFilter} ${activeTab} found.`}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    {activeTab === 'vendors' ? 'Business Name' : 'Organization'}
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Contact
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Type
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Submitted
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <AnimatePresence>
                  {currentItems.map((item, index) => (
                    <motion.tr
                      key={item.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ delay: index * 0.05 }}
                      className="group hover:bg-gray-50/50"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center text-blue-700 font-semibold">
                            {activeTab === 'vendors'
                              ? (item as Vendor).business_name.charAt(0).toUpperCase()
                              : (item as Organization).name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">
                              {activeTab === 'vendors'
                                ? (item as Vendor).business_name
                                : (item as Organization).name}
                            </p>
                            <p className="text-xs text-gray-500">
                              {activeTab === 'vendors'
                                ? (item as Vendor).business_type || 'Individual'
                                : (item as Organization).legal_name}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          {activeTab === 'vendors'
                            ? (item as Vendor).business_email
                            : (item as Organization).email}
                        </div>
                        <div className="text-xs text-gray-500">
                          {activeTab === 'vendors'
                            ? (item as Vendor).business_phone || 'No phone'
                            : (item as Organization).phone || 'No phone'}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                          {activeTab === 'vendors'
                            ? (item as Vendor).vendor_type === VendorType.INDIVIDUAL
                              ? 'Individual'
                              : 'Organization Vendor'
                            : 'Organization'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium ${getStatusColor(
                            item.status
                          )}`}
                        >
                          {item.status === 'pending' && (
                            <Clock className="h-3 w-3" />
                          )}
                          {item.status === 'approved' && (
                            <CheckCircle className="h-3 w-3" />
                          )}
                          {item.status === 'rejected' && (
                            <XCircle className="h-3 w-3" />
                          )}
                          {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDate(item.created_at)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openDetailModal(item)}
                            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                            title="View Details"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </button>
                          
                          {item.status === 'pending' && (
                            <>
                              <button
                                onClick={() => openApprovalModal(item, 'approve')}
                                className="rounded-lg bg-green-50 p-2 text-green-600 hover:bg-green-100"
                                title="Approve"
                              >
                                <CheckCircle className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => openApprovalModal(item, 'reject')}
                                className="rounded-lg bg-red-50 p-2 text-red-600 hover:bg-red-100"
                                title="Reject"
                              >
                                <XCircle className="h-4 w-4" />
                              </button>
                            </>
                          )}
                          
                          <button
                            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                            aria-label="More actions"
                            title="More actions"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && currentItems.length > 0 && (
          <div className="flex items-center justify-between border-t border-gray-200 px-6 py-4">
            <div className="text-sm text-gray-500">
              Page {pagination.page} of{' '}
              {Math.ceil(pagination.total / pagination.pageSize)}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() =>
                  setPagination((prev) => ({
                    ...prev,
                    page: Math.max(1, prev.page - 1),
                  }))
                }
                disabled={pagination.page === 1}
                className="flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </button>
              <button
                onClick={() =>
                  setPagination((prev) => ({
                    ...prev,
                    page: prev.page + 1,
                  }))
                }
                disabled={
                  pagination.page >=
                  Math.ceil(pagination.total / pagination.pageSize)
                }
                className="flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <ApprovalModal
        isOpen={approvalModalOpen}
        onClose={() => {
          setApprovalModalOpen(false);
          setSelectedItem(null);
        }}
        onConfirm={handleStatusUpdate}
        type={approvalAction}
        itemName={
          selectedItem
            ? activeTab === 'vendors'
              ? (selectedItem as Vendor).business_name
              : (selectedItem as Organization).name
            : ''
        }
      />

      <DetailModal
        isOpen={detailModalOpen}
        onClose={() => {
          setDetailModalOpen(false);
          setSelectedItem(null);
        }}
        item={selectedItem}
        type={activeTab}
      />
    </div>
  );
}