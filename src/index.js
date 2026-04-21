import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "perplexity-polza",
  version: "0.1.0",
});

const API_KEY = process.env.POLZA_API_KEY;
const BASE_URL = (process.env.POLZA_BASE_URL || "https://polza.ai/api/v1").replace(/\/+$/, "");
const DEFAULT_MODEL = process.env.PERPLEXITY_MODEL || "perplexity/sonar";

function requireApiKey() {
  if (!API_KEY) {
    throw new Error(
      "POLZA_API_KEY is not set. Add it to your Claude MCP config environment."
    );
  }
}

async function polzaFetch(path, options = {}) {
  requireApiKey();

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  const data = text ? safeJsonParse(text) : null;

  if (!response.ok) {
    const message =
      data?.error?.message ||
      data?.message ||
      `Polza API error ${response.status}: ${response.statusText}`;
    throw new Error(message);
  }

  return data;
}

function safeJsonParse(value) {
  try {
    return JSON.parse(value);
  } catch {
    return { raw: value };
  }
}

function normalizeContent(content) {
  if (typeof content === "string") {
    return content;
  }

  if (Array.isArray(content)) {
    return content
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (item?.type === "text") {
          return item.text || "";
        }

        if (item?.type) {
          return `[${item.type}]`;
        }

        return "";
      })
      .filter(Boolean)
      .join("\n");
  }

  if (content == null) {
    return "";
  }

  return JSON.stringify(content, null, 2);
}

function formatAnnotations(message) {
  if (!Array.isArray(message?.annotations) || message.annotations.length === 0) {
    return "";
  }

  const lines = message.annotations.map((annotation, index) => {
    const citation = annotation?.url_citation || {};
    const title =
      annotation?.title ||
      annotation?.name ||
      citation?.title ||
      `Source ${index + 1}`;
    const url =
      annotation?.url ||
      annotation?.uri ||
      annotation?.source ||
      citation?.url ||
      "";
    return url ? `${index + 1}. ${title} — ${url}` : `${index + 1}. ${title}`;
  });

  return `\n\nSources:\n${lines.join("\n")}`;
}

function formatUsage(usage) {
  if (!usage) {
    return "";
  }

  const details = [
    usage.prompt_tokens != null ? `prompt_tokens=${usage.prompt_tokens}` : null,
    usage.completion_tokens != null ? `completion_tokens=${usage.completion_tokens}` : null,
    usage.total_tokens != null ? `total_tokens=${usage.total_tokens}` : null,
    usage.cost_rub != null ? `cost_rub=${usage.cost_rub}` : null,
    usage.server_tool_use?.web_search_requests != null
      ? `web_search_requests=${usage.server_tool_use.web_search_requests}`
      : null,
  ].filter(Boolean);

  return details.length ? `\n\nUsage: ${details.join(", ")}` : "";
}

function buildToolResult(response) {
  const choice = response?.choices?.[0];
  const message = choice?.message || {};
  const answer = normalizeContent(message.content) || "(empty response)";
  const annotations = formatAnnotations(message);
  const usage = formatUsage(response.usage);

  const toolCalls =
    Array.isArray(message.tool_calls) && message.tool_calls.length > 0
      ? `\n\nTool calls:\n${JSON.stringify(message.tool_calls, null, 2)}`
      : "";

  const reasoning =
    message.reasoning != null
      ? `\n\nReasoning:\n${normalizeContent(message.reasoning)}`
      : "";

  return {
    content: [
      {
        type: "text",
        text:
          answer +
          annotations +
          usage +
          toolCalls +
          reasoning,
      },
    ],
  };
}

server.tool(
  "perplexity_ask",
  {
    prompt: z.string().min(1).describe("User question or task for Perplexity."),
    model: z
      .string()
      .default(DEFAULT_MODEL)
      .describe("Polza model id. Default: perplexity/sonar"),
    system: z
      .string()
      .optional()
      .describe("Optional system instruction."),
    temperature: z
      .number()
      .min(0)
      .max(2)
      .optional()
      .describe("Sampling temperature."),
    max_tokens: z
      .number()
      .int()
      .positive()
      .optional()
      .describe("Maximum completion tokens."),
    search_context_size: z
      .enum(["low", "medium", "high"])
      .optional()
      .describe("Perplexity web search depth."),
    reasoning_effort: z
      .enum(["xhigh", "high", "medium", "low", "minimal", "none"])
      .optional()
      .describe("Reasoning effort for models that support it."),
    include_reasoning: z
      .boolean()
      .optional()
      .describe("Ask the provider to include reasoning in the response when supported."),
  },
  async ({
    prompt,
    model,
    system,
    temperature,
    max_tokens,
    search_context_size,
    reasoning_effort,
    include_reasoning,
  }) => {
    const messages = [];

    if (system) {
      messages.push({ role: "system", content: system });
    }

    messages.push({ role: "user", content: prompt });

    const body = {
      model,
      messages,
    };

    if (temperature != null) {
      body.temperature = temperature;
    }

    if (max_tokens != null) {
      body.max_tokens = max_tokens;
    }

    if (search_context_size) {
      body.web_search_options = { search_context_size };
    }

    if (reasoning_effort || include_reasoning != null) {
      body.reasoning = {};
      if (reasoning_effort) {
        body.reasoning.effort = reasoning_effort;
      }
      if (include_reasoning != null) {
        body.reasoning.exclude = !include_reasoning;
      }
    }

    const response = await polzaFetch("/chat/completions", {
      method: "POST",
      body: JSON.stringify(body),
    });

    return buildToolResult(response);
  }
);

server.tool(
  "perplexity_research",
  {
    topic: z.string().min(1).describe("Research topic or question."),
    model: z
      .string()
      .default("perplexity/sonar-deep-research")
      .describe("Research-focused Perplexity model."),
    system: z
      .string()
      .optional()
      .describe("Optional system instruction."),
    max_tokens: z
      .number()
      .int()
      .positive()
      .optional()
      .describe("Maximum completion tokens."),
    search_context_size: z
      .enum(["low", "medium", "high"])
      .default("high")
      .describe("Search depth for research."),
  },
  async ({ topic, model, system, max_tokens, search_context_size }) => {
    const prompt =
      `Conduct a thorough research pass on the following topic.\n\n` +
      `Topic: ${topic}\n\n` +
      `Return a useful synthesis with key facts, caveats, and direct source references.`;

    const body = {
      model,
      messages: [
        ...(system ? [{ role: "system", content: system }] : []),
        { role: "user", content: prompt },
      ],
      web_search_options: { search_context_size },
    };

    if (max_tokens != null) {
      body.max_tokens = max_tokens;
    }

    const response = await polzaFetch("/chat/completions", {
      method: "POST",
      body: JSON.stringify(body),
    });

    return buildToolResult(response);
  }
);

server.tool(
  "list_perplexity_models",
  {
    include_providers: z
      .boolean()
      .default(true)
      .describe("Include provider details from Polza catalog."),
  },
  async ({ include_providers }) => {
    const query = new URLSearchParams({
      type: "chat",
      search: "perplexity",
      limit: "100",
    });

    const response = await polzaFetch(`/models/catalog?${query.toString()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const models = (response?.data || [])
      .filter((model) => String(model.id || "").startsWith("perplexity/"))
      .map((model) => ({
        id: model.id,
        name: model.name,
        description: model.short_description || null,
        context_length: model.top_provider?.context_length ?? null,
        max_completion_tokens: model.top_provider?.max_completion_tokens ?? null,
        pricing: model.top_provider?.pricing ?? null,
        supported_parameters: model.top_provider?.supported_parameters ?? [],
        providers: include_providers ? model.providers ?? [] : undefined,
      }));

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(models, null, 2),
        },
      ],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
