/**
 * Rabbit SDK — Memory infrastructure for the world.
 *
 * Usage:
 *   import { Rabbit } from '@reattend/rabbit';
 *   const rab = new Rabbit('rab_test_YOUR_KEY');
 *   await rab.remember('Sarah delayed the launch to March 15.', { source: 'meeting' });
 *   const answer = await rab.ask('When is the launch?');
 *   console.log(answer.text);
 */

// ── Types ─────────────────────────────────────────────────────────────────

export interface RabbitMemory {
  id: string;
  summary: string;
  triage_type: string;
  tags: string[];
  extraction: {
    people: string[];
    organizations: string[];
    decisions: string[];
    action_items: Array<Record<string, string>>;
    dates: string[];
    topics: string[];
  };
  sentiment: string;
  importance: number;
  importance_reason: string;
  links: Array<{ target_id: string; kind: string; weight: number }>;
  latency_ms: number;
}

export interface RabbitAnswer {
  text: string;
  sources: Array<Record<string, string>>;
  followups: string[];
  intent: string;
  expanded_query: string;
  memories_used: number;
  latency_ms: number;
}

export interface RabbitAlert {
  show: boolean;
  reason: string;
  context: string;
  memory_indices: number[];
}

export interface RememberOptions {
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface AskOptions {
  limit?: number;
  reasoning?: boolean;
}

// ── Errors ────────────────────────────────────────────────────────────────

export class RabbitAPIError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "RabbitAPIError";
    this.status = status;
  }
}

export class RabbitAuthError extends RabbitAPIError {
  constructor(message: string) {
    super(message, 401);
    this.name = "RabbitAuthError";
  }
}

export class RabbitRateLimitError extends RabbitAPIError {
  constructor(message: string) {
    super(message, 429);
    this.name = "RabbitRateLimitError";
  }
}

// ── Client ────────────────────────────────────────────────────────────────

export class Rabbit {
  private apiKey: string;
  private baseUrl: string;

  /**
   * Create a Rabbit client.
   * @param apiKey - Your Rabbit API key (rab_test_* or rab_live_*).
   * @param baseUrl - API base URL. Defaults to api.rabbit.reattend.com.
   */
  constructor(
    apiKey: string,
    baseUrl: string = "http://api.rabbit.reattend.com:8000"
  ) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  private async request(
    method: string,
    path: string,
    body?: unknown
  ): Promise<Record<string, unknown>> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
    };

    const resp = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (resp.status === 401) throw new RabbitAuthError("Invalid API key");
    if (resp.status === 429) {
      const data = await resp.json();
      throw new RabbitRateLimitError(data.detail || "Rate limit exceeded");
    }
    if (!resp.ok) {
      const text = await resp.text();
      throw new RabbitAPIError(`API error ${resp.status}: ${text}`, resp.status);
    }

    return resp.json();
  }

  // ── Core Operations ───────────────────────────────────────────────────

  /**
   * Ingest content into memory.
   * Runs: triage → extract → summarize → sentiment → importance → embed → store → link.
   */
  async remember(
    content: string,
    options: RememberOptions = {}
  ): Promise<RabbitMemory> {
    const data = await this.request("POST", "/v1/remember", {
      content,
      source: options.source || "unknown",
      metadata: options.metadata || {},
    });
    return data as unknown as RabbitMemory;
  }

  /**
   * Ask a question over stored memories.
   * Runs: intent → expand → retrieve → rerank → graph walk → answer.
   */
  async ask(question: string, options: AskOptions = {}): Promise<RabbitAnswer> {
    const data = await this.request("POST", "/v1/ask", {
      question,
      limit: options.limit || 5,
      reasoning: options.reasoning || false,
    });
    return data as unknown as RabbitAnswer;
  }

  /**
   * Check for contradictions or forgotten commitments.
   */
  async check(context: string): Promise<RabbitAlert> {
    const data = await this.request("POST", "/v1/check", { context });
    return data as unknown as RabbitAlert;
  }

  // ── Knowledge Base ────────────────────────────────────────────────────

  /** Compile a wiki page for an entity. */
  async compile(entity: string): Promise<string> {
    const data = await this.request("POST", `/v1/compile/${encodeURIComponent(entity)}`);
    return (data.content as string) || "";
  }

  /** Run a health audit on memories. */
  async lint(): Promise<Record<string, unknown>> {
    return this.request("POST", "/v1/lint");
  }

  // ── Memory Management ─────────────────────────────────────────────────

  /** List stored memories. */
  async memories(
    options: { limit?: number; source?: string } = {}
  ): Promise<Record<string, unknown>[]> {
    const params = new URLSearchParams();
    if (options.limit) params.set("limit", String(options.limit));
    if (options.source) params.set("source", options.source);
    const query = params.toString() ? `?${params.toString()}` : "";
    const data = await this.request("GET", `/v1/memories${query}`);
    return (data.memories as Record<string, unknown>[]) || [];
  }

  /** Get a specific memory. */
  async getMemory(memoryId: string): Promise<Record<string, unknown>> {
    return this.request("GET", `/v1/memories/${memoryId}`);
  }

  /** Delete a memory. */
  async forget(memoryId: string): Promise<boolean> {
    await this.request("DELETE", `/v1/memories/${memoryId}`);
    return true;
  }

  /** Get a memory's connections. */
  async graph(
    memoryId: string,
    hops: number = 2
  ): Promise<Record<string, unknown>> {
    return this.request("GET", `/v1/graph/${memoryId}?hops=${hops}`);
  }

  /** Get usage and memory statistics. */
  async stats(): Promise<Record<string, unknown>> {
    return this.request("GET", "/v1/stats");
  }
}

export default Rabbit;
