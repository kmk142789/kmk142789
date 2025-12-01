import * as React from "react";

import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /**
   * Automatically grow the textarea height to fit its content.
   * Enabled by default.
   */
  autoExpand?: boolean;
  /**
   * Optional maximum height (in pixels) when auto expansion is enabled.
   * Once reached, the textarea will scroll instead of continuing to grow.
   */
  maxAutoExpandHeight?: number;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      autoExpand = true,
      maxAutoExpandHeight,
      onInput,
      style,
      ...props
    },
    ref,
  ) => {
    const internalRef = React.useRef<HTMLTextAreaElement | null>(null);

    const setRefs = React.useCallback(
      (node: HTMLTextAreaElement | null) => {
        internalRef.current = node;
        if (!ref) return;
        if (typeof ref === "function") {
          ref(node);
        } else {
          ref.current = node;
        }
      },
      [ref],
    );

    const resizeToContent = React.useCallback(
      (element: HTMLTextAreaElement | null) => {
        if (!autoExpand || !element) return;
        element.style.height = "auto";
        const nextHeight = element.scrollHeight;
        if (maxAutoExpandHeight) {
          const clampedHeight = Math.min(nextHeight, maxAutoExpandHeight);
          element.style.height = `${clampedHeight}px`;
          element.style.overflowY = nextHeight > maxAutoExpandHeight ? "auto" : "hidden";
        } else {
          element.style.height = `${nextHeight}px`;
          element.style.overflowY = "hidden";
        }
      },
      [autoExpand, maxAutoExpandHeight],
    );

    React.useLayoutEffect(() => {
      resizeToContent(internalRef.current);
    }, [resizeToContent, props.value]);

    const handleInput: React.FormEventHandler<HTMLTextAreaElement> = (event) => {
      resizeToContent(event.currentTarget);
      onInput?.(event);
    };

    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary focus-visible:border-primary/50 disabled:cursor-not-allowed disabled:opacity-50 transition-colors resize-none",
          className,
        )}
        ref={setRefs}
        onInput={handleInput}
        style={{ ...style, overflow: autoExpand ? "hidden" : style?.overflow }}
        {...props}
      />
    );
  },
);
Textarea.displayName = "Textarea";

export { Textarea };
