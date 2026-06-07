export type ChatMode = "direct" | "consulate";



export type ConsulateStage =

  | "initializing"

  | "receiving"

  | "analyzing"

  | "synthesizing"

  | "complete"

  | "deadlock"

  | "error";



export type ModelStatus =

  | "pending"

  | "running"

  | "streaming"

  | "completed"

  | "complete"

  | "failed"

  | "error"

  | "timeout";



export type SynthesisStatus = "ok" | "degraded";



export interface ConsulateStreamEventPayload {

  type: string;

  stage?: ConsulateStage;

  modelId?: string;

  modelStatus?: ModelStatus;

  synthesisStatus?: SynthesisStatus;

  /** @deprecated Use modelStatus or synthesisStatus */
  status?: ModelStatus | SynthesisStatus;

  content?: string;

  answer?: string;

  synthesisDegraded?: boolean;

  deadlock?: boolean;

}



export interface MinorityReport {

  model: string;

  modelId: string;

  role: string;

  response: string;

  reasoning?: string;

}



export interface ConsulateMessageData {

  individualResponses: {

    modelId: string;

    modelName: string;

    role?: string;

    content: string;

    reasoning?: string;

    status: ModelStatus | string;

    error?: string;

    supportsReasoning?: boolean;

  }[];

  synthesisModel: string;

  stages: ConsulateStage[];

  currentStage?: ConsulateStage;

  modelStatuses?: Record<string, ModelStatus | string>;

  synthesisStatus?: SynthesisStatus;

  agreementScore?: number;

  isDeadlock?: boolean;

  isConsensus?: boolean;

  consensusOutcome?: string;

  outcomeLabel?: string;

  confidenceLevel?: string;

  majoritySupport?: number;

  minoritySupport?: number;

  supportingModels?: string[];

  minorityModels?: string[];

  disagreement?: {

    disputedConcept: string;

    majorityPosition: string;

    minorityPosition: string;

    majoritySupport: number;

    minoritySupport: number;

    explanation: string;

  };

  majorityPosition?: string;

  minorityPosition?: string;

  primaryDisagreement?: string;

  minorityReports?: MinorityReport[];

  councilTotal?: number;

  councilResponded?: number;

  synthesisDegraded?: boolean;

}



export interface Message {

  id: string;

  role: "user" | "assistant";

  content: string;

  mode: ChatMode;

  modelId?: string;

  consulateData?: ConsulateMessageData;

  isStreaming?: boolean;

  error?: string;

  createdAt: number;

}



export interface Conversation {

  id: string;

  title: string;

  mode: ChatMode;

  modelId?: string;

  modelIds?: string[];

  messages: Message[];

  createdAt: number;

  updatedAt: number;

}


