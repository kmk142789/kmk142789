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
      <ToastViewport className={className}>
        {toasts.map(({ id, title, description, action, ...props }) => (
          <Toast key={id} id={id} {...props}>
            <div className="grid gap-1">
              {title ? <ToastTitle>{title}</ToastTitle> : null}
              {description ? (
                <ToastDescription>{description}</ToastDescription>
              ) : null}
            </div>
            {action}
            <ToastClose />
          </Toast>
        ))}
      </ToastViewport>
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
