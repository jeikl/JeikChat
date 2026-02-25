import toast from 'react-hot-toast';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

type ToastType = 'success' | 'error' | 'empty';

const toastConfig = {
  success: {
    icon: <CheckCircle className="w-5 h-5 text-green-500" />,
    style: { borderLeftColor: '#22c55e' },
    duration: 2000,
  },
  error: {
    icon: <XCircle className="w-5 h-5 text-red-500" />,
    style: { borderLeftColor: '#ef4444' },
    duration: 4000,
  },
  empty: {
    icon: <AlertCircle className="w-5 h-5 text-gray-400" />,
    style: { borderLeftColor: '#9ca3af' },
    duration: 4000,
  },
};

export const showToast = (message: string, type: ToastType = 'success') => {
  const config = toastConfig[type];
  toast(message, {
    icon: config.icon,
    style: config.style,
    duration: config.duration,
    position: 'top-center',
  });
};
