import { useToast } from "@/hooks/use-toast";
import {
  ToastProvider,
  ToastViewport,
  Toast,
  ToastAction,
  ToastClose,
  ToastDescription,
  ToastTitle,
} from "@/components/ui/toast";

export function Toaster({ className }: { className?: string }) {
  const { toasts, dismiss } = useToast();

  return (
    <ToastProvider toasts={toasts} onDismiss={dismiss}>
      <ToastViewport className={className} />
    </ToastProvider>
  );
}

export {
  Toast,
  ToastAction,
  ToastClose,
  ToastDescription,
  ToastTitle,
};
