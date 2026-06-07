"use client";

import { cn } from "@/lib/utils";
import {
  formatModelMeta,
  getDefaultCouncilModelIds,
  useModels,
  type ModelInfo,
} from "@/hooks/use-models";
import { useChatStore } from "@/stores/chat-store";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, Check, ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";

function ModelItem({
  model,
  selected,
  onSelect,
}: {
  model: ModelInfo;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        "w-full flex items-start gap-3 px-3 py-3 text-left rounded-lg transition-colors hover:bg-surface-overlay cursor-pointer",
        selected && "bg-surface-overlay"
      )}
    >
      <div
        className={cn(
          "mt-1 w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors",
          selected
            ? "bg-accent border-accent text-[var(--bg-base)]"
            : "border-border"
        )}
      >
        {selected && <Check className="w-3 h-3" />}
      </div>
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium block truncate">
          {model.displayName}
        </span>
        <p className="text-xs text-muted mt-0.5">{formatModelMeta(model)}</p>
      </div>
    </button>
  );
}

function ModelPickerSkeleton() {
  return (
    <div className="flex items-center gap-3 px-3 py-2">
      <div className="w-28 h-4 rounded skeleton" />
    </div>
  );
}

export function ModelPicker() {
  const { models, loading, error, usingFallback, reload } = useModels();
  const {
    mode,
    selectedModelId,
    selectedModelIds,
    setSelectedModelId,
    setSelectedModelIds,
    toggleModelId,
    isGenerating,
  } = useChatStore();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (models.length === 0) return;

    if (!selectedModelId) {
      setSelectedModelId(models[0].id);
    }

    if (selectedModelIds.length === 0) {
      const defaultIds = getDefaultCouncilModelIds(models);
      if (defaultIds.length > 0) {
        setSelectedModelIds(defaultIds);
      }
    }
  }, [
    models,
    selectedModelId,
    selectedModelIds.length,
    setSelectedModelId,
    setSelectedModelIds,
  ]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const displayModels =
    mode === "consulate"
      ? (models.filter((m) => m.consulateEligible).length > 0
          ? models.filter((m) => m.consulateEligible)
          : models)
      : models;

  const selectedModel = models.find((m) => m.id === selectedModelId);

  if (loading) return <ModelPickerSkeleton />;

  const hasModels = models.length > 0;

  if (!hasModels) {
    return (
      <button
        type="button"
        onClick={reload}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-overlay/60 text-sm text-muted hover:text-foreground"
      >
        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
        <span>Retry loading models</span>
      </button>
    );
  }

  const label =
    mode === "direct"
      ? selectedModel?.displayName ?? models[0]?.displayName ?? "Select model"
      : `${Math.max(selectedModelIds.length, 1)} models selected`;

  return (
    <div ref={ref} className="relative min-w-0">
      {error && (
        <p className="sr-only">{error}</p>
      )}
      <button
        onClick={() => setOpen(!open)}
        disabled={isGenerating}
        aria-expanded={open}
        aria-haspopup="listbox"
        title={error ?? undefined}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-overlay/60 text-sm hover:bg-surface-overlay transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed max-w-full"
      >
        <span className="truncate max-w-[12rem] sm:max-w-[14rem] md:max-w-[16rem]">
          {label}
        </span>
        {usingFallback && (
          <span className="text-[10px] uppercase tracking-wider text-amber-600 dark:text-amber-400 shrink-0">
            Fallback
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-3.5 h-3.5 text-muted transition-transform shrink-0",
            open && "rotate-180"
          )}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            role="listbox"
            className="absolute top-full left-0 mt-2 w-80 max-h-80 overflow-y-auto scrollbar-thin z-50 rounded-xl bg-surface shadow-lg p-1.5 ring-1 ring-border-subtle"
          >
            {mode === "consulate" && (
              <p className="px-3 py-2 text-[11px] uppercase tracking-wider text-muted/70">
                Select council models
              </p>
            )}
            {displayModels.length === 0 ? (
              <div className="px-3 py-4 text-sm text-muted space-y-2">
                <p>No models matched this mode.</p>
                <button
                  type="button"
                  onClick={reload}
                  className="text-accent hover:underline"
                >
                  Refresh model list
                </button>
              </div>
            ) : (
              displayModels.map((model) => (
                <ModelItem
                  key={model.id}
                  model={model}
                  selected={
                    mode === "direct"
                      ? selectedModelId === model.id
                      : selectedModelIds.includes(model.id)
                  }
                  onSelect={() => {
                    if (mode === "direct") {
                      setSelectedModelId(model.id);
                      setOpen(false);
                    } else {
                      toggleModelId(model.id);
                    }
                  }}
                />
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
