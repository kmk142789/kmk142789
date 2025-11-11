import * as React from "react";

const MOBILE_BREAKPOINT = 768;

function getIsMobile() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.innerWidth < MOBILE_BREAKPOINT;
}

export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = React.useState<boolean>(getIsMobile);

  React.useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return undefined;
    }

    const mediaQuery = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);

    const handleChange = (event: MediaQueryListEvent | MediaQueryList) => {
      setIsMobile(event.matches);
    };

    // Ensure the initial state always reflects the current match
    handleChange(mediaQuery);

    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }

    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  return isMobile;
}
