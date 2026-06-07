"use client";

import { apiUrl, getSessionHeaders } from "@/lib/api-client";
import { generateId } from "@/lib/utils";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";
import type { ConsulateMessageData, Message } from "@/types/chat";
import { useCallback } from "react";

type ModelInfoEntry = {
  name: string;
  role: string;
  supportsReasoning: boolean;
};

let modelInfoCache: Record<string, ModelInfoEntry> | null = null;

async function getModelInfo(): Promise<Record<string, ModelInfoEntry>> {
  if (modelInfoCache) {
    return modelInfoCache;
  }

  const res = await fetch(apiUrl("/models"));
  if (!res.ok) {
    throw new Error("Failed to fetch models");
  }

  const data = await res.json();
  modelInfoCache = Object.fromEntries(
    data.models.map(
      (m: {
        id: string;
        display_name?: string;
        displayName?: string;
        role: string;
        supports_reasoning?: boolean;
        supportsReasoning?: boolean;
      }) => [
        m.id,
        {
          name: m.display_name ?? m.displayName ?? m.id,
          role: m.role,
          supportsReasoning:
            m.supports_reasoning ?? m.supportsReasoning ?? false,
        },
      ]
    )
  );
  return modelInfoCache;
}

function parseSSELine(
  line: string,
  onEvent: (event: Record<string, unknown>) => void
) {
  const trimmed = line.trim();
  if (!trimmed.startsWith("data: ")) return;
  const data = trimmed.slice(6);
  if (data === "[DONE]") return;
  try {
    onEvent(JSON.parse(data));
  } catch {
    // skip malformed
  }
}

async function consumeSSE(
  response: Response,
  onEvent: (event: Record<string, unknown>) => void
) {
  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";
  let done = false;

  while (!done) {
    const result = await reader.read();
    done = result.done ?? false;

    if (result.value) {
      buffer += decoder.decode(result.value, { stream: !done });
    }

    const lines = buffer.split("\n");
    buffer = done ? "" : (lines.pop() ?? "");

    for (const line of lines) {
      parseSSELine(line, onEvent);
    }
  }

  if (buffer.trim()) {
    parseSSELine(buffer, onEvent);
  }
}

function resolveCouncilIds(
  selectedModelIds: string[],
  modelInfo: Record<string, ModelInfoEntry>
): string[] {
  if (selectedModelIds.length >= 2) {
    return selectedModelIds;
  }
  return Object.keys(modelInfo);
}

function ensureCouncilMember(
  consulateData: ConsulateMessageData,
  modelId: string,
  modelInfo: Record<string, ModelInfoEntry>
) {
  const existing = consulateData.individualResponses.find(
    (r) => r.modelId === modelId
  );
  if (existing) return existing;

  const entry: ConsulateMessageData["individualResponses"][number] = {
    modelId,
    modelName: modelInfo[modelId]?.name ?? modelId,
    role: modelInfo[modelId]?.role,
    supportsReasoning: modelInfo[modelId]?.supportsReasoning,
    content: "",
    status: "pending",
  };
  consulateData.individualResponses.push(entry);
  return entry;
}

export function useChat() {
  const {
    mode,
    selectedModelId,
    selectedModelIds,
    activeConversationId,
    createConversation,
    addMessage,
    updateMessage,
    setIsGenerating,
    getActiveConversation,
  } = useChatStore();

  const { incrementRequest, isExhausted, sessionId } = useSessionStore();

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isExhausted()) return;

      let conversationId = activeConversationId;
      if (!conversationId) {
        conversationId = createConversation();
      }

      let modelInfo: Record<string, ModelInfoEntry> = {};
      if (mode === "consulate") {
        try {
          modelInfo = await getModelInfo();
        } catch (err) {
          const assistantId = generateId();
          addMessage(conversationId, {
            id: generateId(),
            role: "user",
            content: content.trim(),
            mode,
            createdAt: Date.now(),
          });
          addMessage(conversationId, {
            id: assistantId,
            role: "assistant",
            content: "",
            mode,
            isStreaming: false,
            error:
              err instanceof Error
                ? err.message
                : "Failed to load council models",
            createdAt: Date.now(),
          });
          return;
        }

        const councilIds = resolveCouncilIds(selectedModelIds, modelInfo);
        if (councilIds.length < 2) {
          const assistantId = generateId();
          addMessage(conversationId, {
            id: generateId(),
            role: "user",
            content: content.trim(),
            mode,
            createdAt: Date.now(),
          });
          addMessage(conversationId, {
            id: assistantId,
            role: "assistant",
            content: "",
            mode,
            isStreaming: false,
            error: "Consulate mode requires at least 2 council members.",
            createdAt: Date.now(),
          });
          return;
        }
      }

      if (!incrementRequest()) return;

      const userMessage: Message = {
        id: generateId(),
        role: "user",
        content: content.trim(),
        mode,
        createdAt: Date.now(),
      };

      addMessage(conversationId, userMessage);
      setIsGenerating(true);

      const assistantId = generateId();
      const councilIds =
        mode === "consulate"
          ? resolveCouncilIds(selectedModelIds, modelInfo)
          : [];

      const assistantMessage: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        mode,
        modelId: mode === "direct" ? selectedModelId ?? undefined : undefined,
        isStreaming: true,
        consulateData:
          mode === "consulate"
            ? {
                individualResponses: councilIds.map((id) => ({
                  modelId: id,
                  modelName: modelInfo[id]?.name ?? id,
                  role: modelInfo[id]?.role,
                  supportsReasoning: modelInfo[id]?.supportsReasoning,
                  content: "",
                  status: "pending",
                })),
                synthesisModel: "gpt-oss-120b",
                stages: [],
                currentStage: "initializing",
                modelStatuses: {},
                minorityReports: [],
              }
            : undefined,
        createdAt: Date.now(),
      };

      addMessage(conversationId, assistantMessage);

      const conversation = getActiveConversation();
      const history =
        conversation?.messages
          .filter((m) => m.id !== assistantId)
          .map((m) => ({ role: m.role, content: m.content })) ?? [];

      try {
        if (mode === "direct") {
          if (!selectedModelId) {
            updateMessage(conversationId, assistantId, {
              content: "Please select a model.",
              isStreaming: false,
              error: "No model selected",
            });
            return;
          }

          const response = await fetch(apiUrl("/chat"), {
            method: "POST",
            headers: getSessionHeaders(sessionId),
            body: JSON.stringify({
              modelId: selectedModelId,
              messages: history,
            }),
          });

          if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail ?? err.error ?? "Chat request failed");
          }

          let fullContent = "";
          await consumeSSE(response, (event) => {
            if (event.type === "chunk" && typeof event.content === "string") {
              fullContent += event.content;
              updateMessage(conversationId!, assistantId, {
                content: fullContent,
              });
            }
          });

          updateMessage(conversationId, assistantId, {
            content: fullContent,
            isStreaming: false,
          });
        } else {
          const response = await fetch(apiUrl("/consulate"), {
            method: "POST",
            headers: getSessionHeaders(sessionId),
            body: JSON.stringify({
              modelIds: councilIds,
              messages: history.slice(0, -1),
              prompt: content.trim(),
            }),
          });

          if (!response.ok) {
            const err = await response.json();
            throw new Error(
              err.detail ?? err.error ?? "Consulate request failed"
            );
          }

          let synthesisContent = "";
          const consulateData = assistantMessage.consulateData!;
          let flushRaf: number | null = null;

          const flushConsulateUpdate = () => {
            flushRaf = null;
            updateMessage(conversationId!, assistantId, {
              content: synthesisContent,
              consulateData: { ...consulateData },
            });
          };

          const scheduleConsulateUpdate = (immediate = false) => {
            if (immediate) {
              if (flushRaf !== null) {
                cancelAnimationFrame(flushRaf);
                flushRaf = null;
              }
              flushConsulateUpdate();
              return;
            }
            if (flushRaf !== null) return;
            flushRaf = requestAnimationFrame(flushConsulateUpdate);
          };

          await consumeSSE(response, (event) => {
            const type = event.type as string;
            let immediate = false;

            if (type === "stage") {
              consulateData.currentStage = event.stage as typeof consulateData.currentStage;
              consulateData.stages = [
                ...consulateData.stages,
                event.stage as typeof consulateData.currentStage,
              ].filter(Boolean) as typeof consulateData.stages;
              immediate = true;
            }

            if (type === "model_status") {
              const modelId = event.modelId as string;
              consulateData.modelStatuses = {
                ...consulateData.modelStatuses,
                [modelId]: event.status as string,
              };
              const resp = ensureCouncilMember(
                consulateData,
                modelId,
                modelInfo
              );
              resp.status = event.status as string;
              immediate = true;
            }

            if (type === "model_chunk") {
              const modelId = event.modelId as string;
              const resp = ensureCouncilMember(
                consulateData,
                modelId,
                modelInfo
              );
              if (event.reasoning) {
                resp.reasoning =
                  (resp.reasoning ?? "") + (event.reasoning as string);
              } else if (event.content) {
                resp.content += event.content as string;
              }
            }

            if (type === "model_complete") {
              const modelId = event.modelId as string;
              const resp = ensureCouncilMember(
                consulateData,
                modelId,
                modelInfo
              );
              resp.content = event.content as string;
              if (event.reasoning) {
                resp.reasoning = event.reasoning as string;
              }
              resp.status = "complete";
              immediate = true;
            }

            if (type === "model_error") {
              const modelId = event.modelId as string;
              const resp = ensureCouncilMember(
                consulateData,
                modelId,
                modelInfo
              );
              resp.error = event.error as string;
              if (resp.status !== "timeout") {
                resp.status = "error";
              }
              immediate = true;
            }

            if (type === "synthesis_chunk") {
              synthesisContent += event.content as string;
            }

            if (type === "synthesis_complete") {
              synthesisContent = event.content as string;
              if (event.status === "degraded" || event.synthesisDegraded) {
                consulateData.synthesisDegraded = true;
              }
              immediate = true;
            }

            if (type === "agreement_analysis") {
              consulateData.agreementScore = event.agreementScore as number;
              consulateData.isConsensus = event.isConsensus as boolean;
              consulateData.isDeadlock = event.consensusOutcome === "deadlock";
              consulateData.consensusOutcome = event.consensusOutcome as string;
              consulateData.outcomeLabel = event.outcomeLabel as string;
              consulateData.confidenceLevel = event.confidenceLevel as string;
              consulateData.majoritySupport = event.majoritySupport as number;
              consulateData.minoritySupport = event.minoritySupport as number;
              consulateData.supportingModels = event.supportingModels as string[];
              consulateData.minorityModels = event.minorityModels as string[];
              consulateData.primaryDisagreement =
                event.primaryDisagreement as string;
              if (event.disagreement) {
                consulateData.disagreement = event.disagreement as ConsulateMessageData["disagreement"];
              }
              immediate = true;
            }

            if (type === "council_summary") {
              consulateData.councilTotal = event.councilTotal as number;
              consulateData.councilResponded = event.councilResponded as number;
              immediate = true;
            }

            if (type === "deadlock") {
              consulateData.isDeadlock = true;
              consulateData.isConsensus = false;
              consulateData.consensusOutcome = "deadlock";
              consulateData.outcomeLabel =
                (event.outcomeLabel as string) || "Council Deadlocked";
              consulateData.agreementScore = event.agreementScore as number;
              consulateData.majorityPosition = event.majorityPosition as string;
              consulateData.minorityPosition = event.minorityPosition as string;
              consulateData.primaryDisagreement =
                event.primaryDisagreement as string;
              consulateData.majoritySupport = event.majoritySupport as number;
              consulateData.minoritySupport = event.minoritySupport as number;
              consulateData.supportingModels = event.supportingModels as string[];
              consulateData.minorityModels = event.minorityModels as string[];
              if (event.disagreement) {
                consulateData.disagreement = event.disagreement as ConsulateMessageData["disagreement"];
              }
              consulateData.currentStage = "deadlock";
              immediate = true;
            }

            if (type === "minority_report") {
              const report = event.minorityReport as {
                model: string;
                modelId: string;
                role: string;
                response: string;
                reasoning?: string;
              };
              if (report) {
                consulateData.minorityReports = [
                  ...(consulateData.minorityReports ?? []),
                  report,
                ];
              }
              immediate = true;
            }

            if (type === "error") {
              updateMessage(conversationId!, assistantId, {
                error: event.message as string,
              });
              return;
            }

            scheduleConsulateUpdate(immediate);
          });

          if (flushRaf !== null) {
            cancelAnimationFrame(flushRaf);
            flushConsulateUpdate();
          }

          updateMessage(conversationId, assistantId, {
            content: synthesisContent,
            isStreaming: false,
            consulateData: {
              ...consulateData,
              currentStage: consulateData.isDeadlock ? "deadlock" : "complete",
            },
          });
        }
      } catch (err) {
        updateMessage(conversationId, assistantId, {
          content: "",
          isStreaming: false,
          error: err instanceof Error ? err.message : "An error occurred",
        });
      } finally {
        setIsGenerating(false);
      }
    },
    [
      mode,
      selectedModelId,
      selectedModelIds,
      activeConversationId,
      createConversation,
      addMessage,
      updateMessage,
      setIsGenerating,
      getActiveConversation,
      incrementRequest,
      isExhausted,
      sessionId,
    ]
  );

  const regenerate = useCallback(
    async (messageId: string) => {
      const conversation = getActiveConversation();
      if (!conversation) return;

      const msgIndex = conversation.messages.findIndex(
        (m) => m.id === messageId
      );
      if (msgIndex < 1) return;

      const userMsg = conversation.messages[msgIndex - 1];
      if (userMsg.role !== "user") return;

      const store = useChatStore.getState();
      const filteredMessages = conversation.messages.slice(0, msgIndex);
      useChatStore.setState({
        conversations: store.conversations.map((c) =>
          c.id === conversation.id
            ? { ...c, messages: filteredMessages }
            : c
        ),
      });

      await sendMessage(userMsg.content);
    },
    [getActiveConversation, sendMessage]
  );

  return { sendMessage, regenerate };
}
