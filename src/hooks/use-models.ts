"use client";

import { apiUrl } from "@/lib/api-client";
import { useEffect, useState } from "react";

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

export function useModels() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetch(apiUrl("/models"))
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Failed to fetch models (${res.status})`);
        }
        return res.json();
      })
      .then((data: { models?: ApiModel[] }) => {
        if (cancelled) return;
        const parsed = (data?.models ?? [])
          .map(mapModel)
          .filter((model): model is ModelInfo => model !== null);
        setModels(parsed);
        setError(parsed.length === 0 ? "No models returned from API" : null);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to fetch models");
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const consulateModels = models.filter((m) => m.consulateEligible);

  return { models, consulateModels, loading, error };
}

export function formatModelMeta(model: ModelInfo): string {
  const parts = [model.family, ...model.tags].filter(Boolean);
  return parts.join(" • ");
}

export function getDefaultCouncilModelIds(models: ModelInfo[]): string[] {
  const eligible = models.filter((m) => m.consulateEligible);
  return (eligible.length > 0 ? eligible : models).map((m) => m.id);
}
