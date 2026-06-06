import { generateId } from "@/lib/utils";
import type { ChatMode, Conversation, Message } from "@/types/chat";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  mode: ChatMode;
  selectedModelId: string | null;
  selectedModelIds: string[];
  isGenerating: boolean;

  createConversation: () => string;
  setActiveConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, title: string) => void;
  setMode: (mode: ChatMode) => void;
  setSelectedModelId: (id: string) => void;
  setSelectedModelIds: (ids: string[]) => void;
  toggleModelId: (id: string) => void;
  addMessage: (conversationId: string, message: Message) => void;
  updateMessage: (
    conversationId: string,
    messageId: string,
    updates: Partial<Message>
  ) => void;
  setIsGenerating: (value: boolean) => void;
  getActiveConversation: () => Conversation | null;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeConversationId: null,
      mode: "direct",
      selectedModelId: null,
      selectedModelIds: [],
      isGenerating: false,

      createConversation: () => {
        const id = generateId();
        const conversation: Conversation = {
          id,
          title: "New Conversation",
          mode: get().mode,
          modelId: get().selectedModelId ?? undefined,
          modelIds: get().selectedModelIds.length
            ? get().selectedModelIds
            : undefined,
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };

        set((state) => ({
          conversations: [conversation, ...state.conversations],
          activeConversationId: id,
        }));

        return id;
      },

      setActiveConversation: (id) => {
        const conv = get().conversations.find((c) => c.id === id);
        if (conv) {
          set({
            activeConversationId: id,
            mode: conv.mode,
            selectedModelId: conv.modelId ?? null,
            selectedModelIds: conv.modelIds ?? [],
          });
        }
      },

      deleteConversation: (id) => {
        set((state) => {
          const filtered = state.conversations.filter((c) => c.id !== id);
          const newActive =
            state.activeConversationId === id
              ? filtered[0]?.id ?? null
              : state.activeConversationId;
          return {
            conversations: filtered,
            activeConversationId: newActive,
          };
        });
      },

      renameConversation: (id, title) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, title, updatedAt: Date.now() } : c
          ),
        }));
      },

      setMode: (mode) => set({ mode }),

      setSelectedModelId: (id) =>
        set((state) =>
          state.selectedModelId === id ? state : { selectedModelId: id }
        ),

      setSelectedModelIds: (ids) =>
        set((state) => {
          const current = state.selectedModelIds;
          if (
            current.length === ids.length &&
            current.every((id, index) => id === ids[index])
          ) {
            return state;
          }
          return { selectedModelIds: ids };
        }),

      toggleModelId: (id) => {
        set((state) => {
          const current = state.selectedModelIds;
          const exists = current.includes(id);
          return {
            selectedModelIds: exists
              ? current.filter((m) => m !== id)
              : [...current, id],
          };
        });
      },

      addMessage: (conversationId, message) => {
        set((state) => ({
          conversations: state.conversations.map((c) => {
            if (c.id !== conversationId) return c;
            const updated = {
              ...c,
              messages: [...c.messages, message],
              updatedAt: Date.now(),
            };
            if (c.title === "New Conversation" && message.role === "user") {
              updated.title =
                message.content.slice(0, 50) +
                (message.content.length > 50 ? "…" : "");
            }
            return updated;
          }),
        }));
      },

      updateMessage: (conversationId, messageId, updates) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === messageId ? { ...m, ...updates } : m
                  ),
                  updatedAt: Date.now(),
                }
              : c
          ),
        }));
      },

      setIsGenerating: (value) => set({ isGenerating: value }),

      getActiveConversation: () => {
        const { conversations, activeConversationId } = get();
        return (
          conversations.find((c) => c.id === activeConversationId) ?? null
        );
      },
    }),
    {
      name: "llm-consulate-chat",
      partialize: (state) => ({
        conversations: state.conversations,
        activeConversationId: state.activeConversationId,
        mode: state.mode,
        selectedModelId: state.selectedModelId,
        selectedModelIds: state.selectedModelIds,
      }),
    }
  )
);
