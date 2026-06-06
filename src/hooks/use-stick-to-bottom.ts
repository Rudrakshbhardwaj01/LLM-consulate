"use client";

import { useCallback, useEffect, useRef } from "react";

const NEAR_BOTTOM_PX = 120;

/**
 * Keeps the scroll container pinned to the bottom while streaming, but only
 * when the user has not scrolled up to read earlier messages.
 */
export function useStickToBottom<T>(
  dependency: T,
  enabled = true
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stickRef = useRef(true);

  const onScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    stickRef.current = distanceFromBottom <= NEAR_BOTTOM_PX;
  }, []);

  useEffect(() => {
    if (!enabled) return;
    const el = containerRef.current;
    if (!el || !stickRef.current) return;

    el.scrollTo({ top: el.scrollHeight, behavior: "auto" });
  }, [dependency, enabled]);

  return { containerRef, onScroll };
}
