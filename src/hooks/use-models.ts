"use client";

import { apiUrl } from "@/lib/api-client";
import { useCallback, useEffect, useState } from "react";

export interface ModelInfo {
  id: string;
  displayName: string;
  provider: string;
  role: string;
  description: string;
  contextLimit: number;
  capabilities: string[];
  consulateEligible: boolean;
  family: string;
  tags: string[];
  openSource: boolean;
  supportsReasoning: boolean;
}

type ApiModel = {
  id?: string;
  display_name?: string;
  displayName?: string;
  provider?: string;
  role?: string;
  description?: string;
  context_limit?: number;
  contextLimit?: number;
  capabilities?: string[];
  consulate_eligible?: boolean;
  consulateEligible?: boolean;
  family?: string;
  tags?: string[];
  open_source?: boolean;
  openSource?: boolean;
  supports_reasoning?: boolean;
  supportsReasoning?: boolean;
};

const FALLBACK_MODELS: ModelInfo[] = [
  {
    id: "gpt-oss-120b",
    displayName: "GPT-OSS 120B",
    provider: "nvidia",
    role: "Chief Analyst",
    description: "Default council member",
    contextLimit: 8192,
    capabilities: ["chat"],
    consulateEligible: true,
    family: "OpenAI",
    tags: [],
    openSource: true,
    supportsReasoning: true,
  },
];

function mapModel(m: ApiModel): ModelInfo | null {
  if (!m.id) return null;

  return {
    id: m.id,
    displayName: m.display_name ?? m.displayName ?? m.id,
    provider: m.provider ?? "nvidia",
    role: m.role ?? "",
    description: m.description ?? "",
    contextLimit: m.context_limit ?? m.contextLimit ?? 4096,
    capabilities: Array.isArray(m.capabilities) ? m.capabilities : ["chat"],
    consulateEligible: m.consulate_eligible ?? m.consulateEligible ?? true,
    family: m.family ?? "",
    tags: Array.isArray(m.tags) ? m.tags : [],
    openSource: m.open_source ?? m.openSource ?? true,
    supportsReasoning: m.supports_reasoning ?? m.supportsReasoning ?? false,
  };
}

function parseModelsPayload(data: unknown): ModelInfo[] {
  const payload = data as { models?: unknown };
  const raw = Array.isArray(payload?.models) ? payload.models : [];
  return raw
    .map((entry) => mapModel(entry as ApiModel))
    .filter((model): model is ModelInfo => model !== null);
}

export function useModels() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingFallback, setUsingFallback] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    fetch(apiUrl("/models"))
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Failed to fetch models (${res.status})`);
        }
        return res.json();
      })
      .then((data: unknown) => {
        if (cancelled) return;
        const parsed = parseModelsPayload(data);
        if (parsed.length === 0) {
          setModels(FALLBACK_MODELS);
          setUsingFallback(true);
          setError("Using default council — model list was empty.");
        } else {
          setModels(parsed);
          setUsingFallback(false);
          setError(null);
        }
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setModels(FALLBACK_MODELS);
        setUsingFallback(true);
        setError(err instanceof Error ? err.message : "Failed to fetch models");
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const consulateModels = models.filter((m) => m.consulateEligible);

  return { models, consulateModels, loading, error, usingFallback, reload };
}

export function formatModelMeta(model: ModelInfo): string {
  const parts = [model.family, ...model.tags].filter(Boolean);
  return parts.join(" • ");
}

export function getDefaultCouncilModelIds(models: ModelInfo[]): string[] {
  const eligible = models.filter((m) => m.consulateEligible);
  return (eligible.length > 0 ? eligible : models).map((m) => m.id);
}
