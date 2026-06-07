import type { ConsulateMessageData, ConsulateStage } from "@/types/chat";

/** Model lifecycle statuses that mean no further council response is expected. */
export const TERMINAL_MODEL_STATUSES = new Set([
  "complete",
  "completed",
  "error",
  "failed",
  "timeout",
]);

const STAGE_RANK: Record<ConsulateStage, number> = {
  initializing: 0,
  receiving: 1,
  analyzing: 2,
  synthesizing: 3,
  complete: 4,
  deadlock: 4,
  error: 4,
};

export function isTerminalModelStatus(status: string): boolean {
  return TERMINAL_MODEL_STATUSES.has(status);
}

export function allCouncilMembersTerminal(
  responses: ConsulateMessageData["individualResponses"]
): boolean {
  if (responses.length === 0) return false;
  return responses.every((response) => isTerminalModelStatus(response.status));
}

/** Promote receiving → analyzing once every council member has finished. */
export function advanceStageWhenCouncilComplete(
  data: ConsulateMessageData
): boolean {
  if (data.currentStage !== "receiving") return false;
  if (!allCouncilMembersTerminal(data.individualResponses)) return false;

  data.currentStage = "analyzing";
  if (!data.stages.includes("analyzing")) {
    data.stages.push("analyzing");
  }
  return true;
}

/**
 * Effective stage for display — never regress below backend stage, but advance
 * from receiving once all models are terminal even if analyzing SSE is delayed.
 */
export function deriveDisplayStage(data: ConsulateMessageData): ConsulateStage {
  const backendStage = data.currentStage ?? "initializing";

  if (backendStage !== "receiving") {
    return backendStage;
  }

  if (allCouncilMembersTerminal(data.individualResponses)) {
    return "analyzing";
  }

  return backendStage;
}

export function isStageAtLeast(
  stage: ConsulateStage,
  minimum: ConsulateStage
): boolean {
  return STAGE_RANK[stage] >= STAGE_RANK[minimum];
}
