import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  expandedConsulatePanels: Set<string>;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleConsulatePanel: (messageId: string) => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  sidebarOpen: true,
  expandedConsulatePanels: new Set(),

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  toggleConsulatePanel: (messageId) => {
    const current = new Set(get().expandedConsulatePanels);
    if (current.has(messageId)) {
      current.delete(messageId);
    } else {
      current.add(messageId);
    }
    set({ expandedConsulatePanels: current });
  },
}));
