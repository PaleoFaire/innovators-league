// ═══════════════════════════════════════════════════════════════════════
// OPTI — Batch Embedding Generator Edge Function
// Used by the Python ingestion script to generate gte-small embeddings.
// Deploy via Supabase Dashboard alongside opti-chat.
// Set "Verify JWT" to OFF.
// ═══════════════════════════════════════════════════════════════════════

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { texts, chunks } = await req.json();

    // Mode 1: Just generate embeddings for a list of texts
    if (texts && Array.isArray(texts)) {
      const session = new Supabase.ai.Session("gte-small");
      const embeddings: number[][] = [];

      for (const text of texts) {
        const emb = await session.run(text, {
          mean_pool: true,
          normalize: true,
        });
        embeddings.push(Array.from(emb));
      }

      return new Response(
        JSON.stringify({ embeddings, count: embeddings.length }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Mode 2: Generate embeddings AND insert into opti_documents
    if (chunks && Array.isArray(chunks)) {
      const session = new Supabase.ai.Session("gte-small");
      const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
      const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
      const supabase = createClient(supabaseUrl, supabaseServiceKey);

      let inserted = 0;
      const errors: string[] = [];

      // Process in mini-batches for memory safety
      for (let i = 0; i < chunks.length; i++) {
        const chunk = chunks[i];
        try {
          const emb = await session.run(chunk.content, {
            mean_pool: true,
            normalize: true,
          });

          const { error } = await supabase.table("opti_documents").insert({
            content: chunk.content,
            embedding: Array.from(emb),
            metadata: chunk.metadata || {},
            source_file: chunk.source_file,
            source_type: chunk.source_type,
            chunk_index: chunk.chunk_index || 0,
            token_count: chunk.token_count || 0,
          });

          if (error) {
            errors.push(`Row ${i}: ${error.message}`);
          } else {
            inserted++;
          }
        } catch (e) {
          errors.push(`Row ${i}: ${e.message}`);
        }
      }

      return new Response(
        JSON.stringify({
          inserted,
          total: chunks.length,
          errors: errors.length > 0 ? errors.slice(0, 10) : [],
        }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    return new Response(
      JSON.stringify({
        error:
          'Provide "texts" (array of strings) or "chunks" (array of {content, source_file, source_type, ...})',
      }),
      {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (err) {
    console.error("Embed function error:", err);
    return new Response(
      JSON.stringify({ error: err.message }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
