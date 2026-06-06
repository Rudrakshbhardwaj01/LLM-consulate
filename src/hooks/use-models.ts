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
  id: string;
  display_name?: string;
  displayName?: string;
  provider: string;
  role: string;
  description: string;
  context_limit?: number;
  contextLimit?: number;
  capabilities: string[];
  consulate_eligible?: boolean;
  consulateEligible?: boolean;
  family: string;
  tags?: string[];
  open_source?: boolean;
  openSource?: boolean;
  supports_reasoning?: boolean;
  supportsReasoning?: boolean;
};

function mapModel(m: ApiModel): ModelInfo {
  return {
    id: m.id,
    displayName: m.display_name ?? m.displayName ?? m.id,
    provider: m.provider,
    role: m.role,
    description: m.description,
    contextLimit: m.context_limit ?? m.contextLimit ?? 4096,
    capabilities: m.capabilities,
    consulateEligible: m.consulate_eligible ?? m.consulateEligible ?? false,
    family: m.family,
    tags: m.tags ?? [],
    openSource: m.open_source ?? m.openSource ?? true,
    supportsReasoning: m.supports_reasoning ?? m.supportsReasoning ?? false,
  };
}

export function useModels() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(apiUrl("/models"))
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch models");
        return res.json();
      })
      .then((data: { models: ApiModel[] }) => {
        setModels(data.models.map(mapModel));
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const consulateModels = models.filter((m) => m.consulateEligible);

  return { models, consulateModels, loading, error };
}

export function formatModelMeta(model: ModelInfo): string {
  const parts = [model.family, ...model.tags].filter(Boolean);
  return parts.join(" • ");
}

export function getDefaultCouncilModelIds(models: ModelInfo[]): string[] {
  return models.filter((m) => m.consulateEligible).map((m) => m.id);
}
