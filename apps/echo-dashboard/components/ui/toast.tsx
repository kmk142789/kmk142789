import * as React from "react";

type ToastContextValue = {
  toasts: ToastProps[];
  onDismiss?: (id: string) => void;
};

const ToastContext = React.createContext<ToastContextValue | undefined>(
  undefined
);

type ToastItemContextValue = {
  id?: string;
  onOpenChange?: (open: boolean) => void;
};

const ToastItemContext = React.createContext<ToastItemContextValue | null>(
  null
);

export interface ToastProps extends React.ComponentPropsWithoutRef<"div"> {
  id?: string;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: ToastActionElement;
}

export type ToastActionElement = React.ReactElement<ToastActionProps>;

interface ToastActionProps extends React.ComponentPropsWithoutRef<"button"> {
  altText?: string;
}

const ToastProvider = ({
  children,
  toasts = [],
  onDismiss,
}: React.PropsWithChildren<{
  toasts?: ToastProps[];
  onDismiss?: (id: string) => void;
}>) => {
  const value = React.useMemo(
    () => ({
      toasts,
      onDismiss,
    }),
    [toasts, onDismiss]
  );

  return (
    <ToastContext.Provider value={value}>{children}</ToastContext.Provider>
  );
};

const useToastContext = () => {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("Toast components must be used within a <ToastProvider />");
  }
  return context;
};

const useToastItemContext = () => React.useContext(ToastItemContext);

const ToastViewport = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<"div">
>(function ToastViewport({ className, children, ...props }, ref) {
  return (
    <div
      ref={ref}
      role="region"
      aria-live="polite"
      aria-label="Notifications"
      className={className}
      {...props}
    >
      {children}
    </div>
  );
});

const Toast = React.forwardRef<HTMLDivElement, ToastProps>(function Toast(
  {
    id,
    open = true,
    onOpenChange,
    title,
    description,
    action,
    className,
    children,
    ...props
  },
  ref
) {
  const hasCustomContent = React.useMemo(
    () => React.Children.count(children) > 0,
    [children]
  );

  React.useEffect(() => {
    if (!open && onOpenChange) {
      onOpenChange(false);
    }
  }, [open, onOpenChange]);

  if (!open) {
    return null;
  }

  return (
    <ToastItemContext.Provider value={{ id, onOpenChange }}>
      <div
        ref={ref}
        role="status"
        className={className}
        data-toast-id={id}
        {...props}
      >
        {hasCustomContent ? (
          children
        ) : (
          <>
            {title ? <ToastTitle>{title}</ToastTitle> : null}
            {description ? <ToastDescription>{description}</ToastDescription> : null}
            {action ?? null}
            <ToastClose />
          </>
        )}
      </div>
    </ToastItemContext.Provider>
  );
});

const ToastTitle = React.forwardRef<
  HTMLParagraphElement,
  React.ComponentPropsWithoutRef<"p">
>(function ToastTitle({ className, ...props }, ref) {
  return <p ref={ref} className={className} {...props} />;
});

const ToastDescription = React.forwardRef<
  HTMLParagraphElement,
  React.ComponentPropsWithoutRef<"p">
>(function ToastDescription({ className, ...props }, ref) {
  return <p ref={ref} className={className} {...props} />;
});

const ToastAction = React.forwardRef<HTMLButtonElement, ToastActionProps>(
  function ToastAction({ className, altText, ...props }, ref) {
    return (
      <button ref={ref} className={className} aria-label={altText} {...props} />
    );
  }
);

const ToastClose = React.forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<"button">
>(function ToastClose({ children = "Close", onClick, ...props }, ref) {
  const itemContext = useToastItemContext();
  const toastContext = useToastContext();

  return (
    <button
      type="button"
      ref={ref}
      onClick={(event) => {
        onClick?.(event);
        if (event.defaultPrevented) {
          return;
        }
        itemContext?.onOpenChange?.(false);
        if (itemContext?.id) {
          toastContext.onDismiss?.(itemContext.id);
        }
      }}
      {...props}
    >
      {children}
    </button>
  );
});

const useToastRenderer = () => {
  const context = useToastContext();
  return context.toasts;
};

export {
  ToastProvider,
  ToastViewport,
  Toast,
  ToastTitle,
  ToastDescription,
  ToastClose,
  ToastAction,
  useToastRenderer,
};
