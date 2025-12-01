import { toast as sonnerToast } from 'sonner';
import { CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react';
import React from 'react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastOptions {
  description?: string;
  duration?: number;
}

const createToastWithIcon = (type: ToastType, message: string, options?: ToastOptions) => {
  const iconMap = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
    info: Info,
  };

  const colorMap = {
    success: 'text-green-600',
    error: 'text-red-600',
    warning: 'text-yellow-600',
    info: 'text-blue-600',
  };

  const Icon = iconMap[type];

  return sonnerToast(message, {
    ...options,
    icon: React.createElement(Icon, { className: `h-5 w-5 ${colorMap[type]}` }),
  });
};

export const toast = {
  success: (message: string, options?: ToastOptions) =>
    createToastWithIcon('success', message, options),

  error: (message: string, options?: ToastOptions) =>
    createToastWithIcon('error', message, options),

  warning: (message: string, options?: ToastOptions) =>
    createToastWithIcon('warning', message, options),

  info: (message: string, options?: ToastOptions) =>
    createToastWithIcon('info', message, options),

  // Keep the original sonner toast for custom cases
  custom: sonnerToast,
};