// ═══════════════════════════════════════════════════════════════════════
// OPTI PHASE 2 — RAG Chat Edge Function
// Deploy via Supabase Dashboard: Edge Functions → Create → Paste → Deploy
// Set "Verify JWT" to OFF for anonymous access from the website
// ═══════════════════════════════════════════════════════════════════════

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ── CORS Headers ──
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// ── Constants ──
const ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages";
const CLAUDE_MODEL = "claude-haiku-4-5-20241022";
const MAX_CONTEXT_CHUNKS = 8;
const SIMILARITY_THRESHOLD = 0.4;
const MAX_CONVERSATION_TURNS = 10;

// ── System Prompt ──
const SYSTEM_PROMPT = `You are Opti, the AI intelligence assistant for The Innovators League — a frontier tech research platform run by the Rational Optimist Society (ROS). You have deep knowledge of defense tech, space, energy, biotech, robotics, AI, and other frontier technology sectors.

Your personality:
- Enthusiastic but substantive. You genuinely love frontier tech but back everything up with specifics.
- Concise. Keep responses under 200 words unless the user asks for a deep dive.
- When you reference specific companies, bold them: **Company Name**.
- When you cite information from your knowledge base, briefly note the source type (e.g., "from our podcast interview" or "from our monthly research").
- If you don't have enough context to answer well, be honest and suggest what the user could ask instead.
- Never make up company data, funding amounts, or valuations. If unsure, say so.
- Use markdown formatting: bold, bullet points, numbered lists.
- Occasionally show personality — "this one's actually wild" or "okay here's why I'm bullish on this."

You have access to a curated research corpus including podcast interview transcripts, monthly disruptor intelligence reports, investment research notes, and optimism-themed analysis written by the ROS founder. Use the provided context to give informed, specific answers grounded in real research.`;

// ── Main Handler ──
Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { message, conversationHistory = [] } = await req.json();

    if (!message || typeof message !== "string" || message.trim().length === 0) {
      return jsonResponse({ error: "Message is required" }, 400);
    }

    // ── Step 1: Generate query embedding using built-in gte-small ──
    const session = new Supabase.ai.Session("gte-small");
    const queryEmbedding = await session.run(message.trim(), {
      mean_pool: true,
      normalize: true,
    });

    // ── Step 2: Search for relevant document chunks via pgvector ──
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const { data: documents, error: searchError } = await supabase.rpc(
      "match_documents",
      {
        query_embedding: Array.from(queryEmbedding),
        match_threshold: SIMILARITY_THRESHOLD,
        match_count: MAX_CONTEXT_CHUNKS,
      }
    );

    if (searchError) {
      console.error("Document search error:", searchError);
    }

    // ── Step 3: Build context from retrieved chunks ──
    let contextBlock = "";
    const sources: Array<{ file: string; type: string; similarity: number }> =
      [];

    if (documents && documents.length > 0) {
      contextBlock = documents
        .map((doc: any, i: number) => {
          sources.push({
            file: doc.source_file,
            type: doc.source_type,
            similarity: doc.similarity,
          });
          const meta = doc.metadata || {};
          const label = meta.title || doc.source_file;
          return `[Source ${i + 1}: ${label} (${doc.source_type})]:\n${doc.content}`;
        })
        .join("\n\n---\n\n");
    }

    // ── Step 4: Build messages array for Claude ──
    const trimmedHistory = conversationHistory.slice(
      -MAX_CONVERSATION_TURNS * 2
    );

    const messages: Array<{ role: string; content: string }> = [];

    // Add conversation history
    for (const msg of trimmedHistory) {
      messages.push({
        role: msg.role === "bot" ? "assistant" : "user",
        content: msg.content,
      });
    }

    // Build the user message with context
    let userContent = "";
    if (contextBlock) {
      userContent = `<context>\nThe following are relevant excerpts from our research corpus:\n\n${contextBlock}\n</context>\n\nUser question: ${message.trim()}`;
    } else {
      userContent = `User question: ${message.trim()}\n\n(No specific documents matched this query. Answer from your general knowledge about frontier tech, or suggest a more specific question.)`;
    }

    messages.push({ role: "user", content: userContent });

    // ── Step 5: Call Claude ──
    const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
    if (!anthropicKey) {
      return jsonResponse({
        text: "I'm having trouble connecting to my brain right now. The AI service isn't configured yet — try asking me something about a specific company and I'll use local mode!",
        sources: [],
        fallback: true,
      });
    }

    const claudeResponse = await fetch(ANTHROPIC_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": anthropicKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: CLAUDE_MODEL,
        max_tokens: 1024,
        system: SYSTEM_PROMPT,
        messages: messages,
      }),
    });

    if (!claudeResponse.ok) {
      const errBody = await claudeResponse.text();
      console.error("Claude API error:", claudeResponse.status, errBody);
      return jsonResponse({
        text: "I hit a snag talking to the AI. Let me fall back to local mode.",
        sources: [],
        fallback: true,
      });
    }

    const claudeData = await claudeResponse.json();
    const responseText =
      claudeData.content?.[0]?.text ||
      "I couldn't generate a response. Try rephrasing your question!";

    // ── Step 6: Return response ──
    return jsonResponse({
      text: responseText,
      sources: sources.map((s) => ({
        file: s.file,
        type: s.type,
        similarity: Math.round(s.similarity * 100) / 100,
      })),
      model: CLAUDE_MODEL,
      chunks_used: documents?.length || 0,
      fallback: false,
    });
  } catch (err) {
    console.error("Edge function error:", err);
    return jsonResponse(
      {
        text: "Something went wrong on my end. Try again in a moment!",
        sources: [],
        fallback: true,
      },
      500
    );
  }
});

// ── Helper ──
function jsonResponse(data: any, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}
