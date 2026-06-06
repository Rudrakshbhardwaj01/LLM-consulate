"use client";

import { Button } from "@/components/ui/button";
import { cn, formatRelativeTime } from "@/lib/utils";
import { useChatStore } from "@/stores/chat-store";
import { useUIStore } from "@/stores/ui-store";
import { AnimatePresence, motion } from "framer-motion";
import { MessageSquarePlus, PanelLeftClose, PanelLeft, Trash2, Pencil } from "lucide-react";
import { useState } from "react";

function ConversationItem({
  id,
  title,
  updatedAt,
  isActive,
}: {
  id: string;
  title: string;
  updatedAt: number;
  isActive: boolean;
}) {
  const { setActiveConversation, deleteConversation, renameConversation } =
    useChatStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(title);

  const handleRename = () => {
    if (editTitle.trim()) {
      renameConversation(id, editTitle.trim());
    }
    setIsEditing(false);
  };

  return (
    <div
      className={cn(
        "group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm",
        isActive
          ? "bg-surface-overlay text-foreground"
          : "text-muted hover:bg-surface-overlay/50 hover:text-foreground"
      )}
      onClick={() => !isEditing && setActiveConversation(id)}
    >
      {isEditing ? (
        <input
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={(e) => e.key === "Enter" && handleRename()}
          className="flex-1 bg-transparent border-b border-accent text-sm focus:outline-none"
          autoFocus
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <>
          <div className="flex-1 min-w-0">
            <p className="truncate font-medium">{title}</p>
            <p className="text-[11px] text-muted/60 mt-0.5">
              {formatRelativeTime(updatedAt)}
            </p>
          </div>
          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(true);
                setEditTitle(title);
              }}
              className="p-1 rounded hover:bg-surface cursor-pointer"
            >
              <Pencil className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteConversation(id);
              }}
              className="p-1 rounded hover:bg-surface hover:text-red-500 cursor-pointer"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export function Sidebar() {
  const { conversations, activeConversationId, createConversation } =
    useChatStore();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <>
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={{ type: "spring", duration: 0.4, bounce: 0.1 }}
            className="fixed md:relative z-30 w-[280px] h-full min-h-0 border-r border-border bg-surface flex flex-col shrink-0"
          >
            <div className="flex items-center justify-between p-4 border-b border-border-subtle">
              <Button
                variant="outline"
                size="sm"
                className="flex-1 gap-2"
                onClick={() => createConversation()}
              >
                <MessageSquarePlus className="w-4 h-4" />
                New Chat
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="ml-2 md:hidden"
                onClick={toggleSidebar}
              >
                <PanelLeftClose className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin p-2">
              {conversations.length === 0 ? (
                <p className="text-xs text-muted text-center py-8 px-4">
                  No conversations yet. Start a new chat to begin.
                </p>
              ) : (
                <div className="space-y-0.5">
                  {conversations.map((conv) => (
                    <ConversationItem
                      key={conv.id}
                      id={conv.id}
                      title={conv.title}
                      updatedAt={conv.updatedAt}
                      isActive={conv.id === activeConversationId}
                    />
                  ))}
                </div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {!sidebarOpen && (
        <Button
          variant="ghost"
          size="icon"
          className="fixed top-4 left-4 z-30 md:relative md:top-0 md:left-0"
          onClick={toggleSidebar}
        >
          <PanelLeft className="w-4 h-4" />
        </Button>
      )}
    </>
  );
}
