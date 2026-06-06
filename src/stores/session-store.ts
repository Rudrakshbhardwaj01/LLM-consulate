import {
  getRemainingRequests,
  isSessionExhausted,
  SESSION_REQUEST_LIMIT,
} from "@/lib/session/limits";
import { generateId } from "@/lib/utils";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SessionState {
  sessionId: string;
  requestsUsed: number;
  incrementRequest: () => boolean;
  getRemaining: () => number;
  isExhausted: () => boolean;
  reset: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      sessionId: generateId(),
      requestsUsed: 0,

      incrementRequest: () => {
        const { requestsUsed } = get();
        if (isSessionExhausted(requestsUsed)) return false;
        set({ requestsUsed: requestsUsed + 1 });
        return true;
      },

      getRemaining: () => getRemainingRequests(get().requestsUsed),

      isExhausted: () => isSessionExhausted(get().requestsUsed),

      reset: () =>
        set({
          sessionId: generateId(),
          requestsUsed: 0,
        }),
    }),
    { name: "llm-consulate-session" }
  )
);

export { SESSION_REQUEST_LIMIT };
