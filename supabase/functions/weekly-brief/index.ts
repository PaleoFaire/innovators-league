// ═══════════════════════════════════════════════════════════════════════
// Weekly Intelligence Brief — Email Sender Edge Function
// Deploy: supabase functions deploy weekly-brief
// Environment Variables (set in Supabase Dashboard → Edge Functions → Secrets):
//   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (auto-set)
//   RESEND_API_KEY         — from resend.com
//   BRIEF_WEBHOOK_SECRET   — shared secret with GitHub Actions
// ═══════════════════════════════════════════════════════════════════════

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ── CORS Headers ──
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// ── Types ──
interface BriefSection {
  title: string;
  icon: string;
  count: number;
  items: any[];
}

interface WeeklyBrief {
  date: string;
  display_date: string;
  generated_at: string;
  cutoff: string;
  section_count: number;
  total_items: number;
  sections: BriefSection[];
  brief_id: string;
}

interface AlertPreference {
  user_id: string;
  email_enabled: boolean;
  email_frequency: string;
  categories: string[];
}

// ── Main Handler ──
Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // ── Step 1: Validate webhook secret ──
    const authHeader = req.headers.get("authorization") || "";
    const webhookSecret = Deno.env.get("BRIEF_WEBHOOK_SECRET");

    if (!webhookSecret) {
      return jsonResponse({ error: "BRIEF_WEBHOOK_SECRET not configured" }, 500);
    }

    const token = authHeader.replace("Bearer ", "");
    if (token !== webhookSecret) {
      return jsonResponse({ error: "Unauthorized" }, 401);
    }

    // ── Step 2: Parse the brief JSON ──
    const brief: WeeklyBrief = await req.json();

    if (!brief.sections || brief.sections.length === 0) {
      return jsonResponse({ message: "No sections in brief, skipping", emails_sent: 0 });
    }

    console.log(`Processing brief ${brief.brief_id}: ${brief.section_count} sections, ${brief.total_items} items`);

    // ── Step 3: Connect to Supabase (service role) ──
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // ── Step 4: Query opted-in subscribers ──
    const { data: subscribers, error: subError } = await supabase
      .from("alert_preferences")
      .select("user_id, email_frequency, categories")
      .eq("email_enabled", true)
      .in("email_frequency", ["weekly", "daily"]);

    if (subError) {
      console.error("Error querying subscribers:", subError);
      return jsonResponse({ error: "Failed to query subscribers" }, 500);
    }

    if (!subscribers || subscribers.length === 0) {
      console.log("No opted-in subscribers found");
      return jsonResponse({ message: "No subscribers", emails_sent: 0 });
    }

    console.log(`Found ${subscribers.length} opted-in subscribers`);

    // ── Step 5: Get email addresses from auth.users ──
    const userIds = subscribers.map((s: AlertPreference) => s.user_id);
    const { data: { users }, error: usersError } = await supabase.auth.admin.listUsers();

    if (usersError) {
      console.error("Error listing users:", usersError);
      return jsonResponse({ error: "Failed to list users" }, 500);
    }

    // Build lookup: user_id → email
    const emailLookup = new Map<string, string>();
    for (const user of users || []) {
      if (userIds.includes(user.id) && user.email) {
        emailLookup.set(user.id, user.email);
      }
    }

    // ── Step 6: Check for already-sent briefs (dedup) ──
    const { data: alreadySent } = await supabase
      .from("email_send_log")
      .select("user_id")
      .eq("brief_date", brief.date)
      .eq("status", "sent");

    const sentUserIds = new Set((alreadySent || []).map((r: any) => r.user_id));

    // ── Step 7: Send emails via Resend ──
    const resendApiKey = Deno.env.get("RESEND_API_KEY");
    if (!resendApiKey) {
      return jsonResponse({ error: "RESEND_API_KEY not configured" }, 500);
    }

    let emailsSent = 0;
    let emailsFailed = 0;
    const sectionTitles = brief.sections.map((s) => s.title);

    for (const sub of subscribers) {
      const email = emailLookup.get(sub.user_id);
      if (!email) {
        console.log(`No email found for user ${sub.user_id}, skipping`);
        continue;
      }

      // Skip if already sent this week
      if (sentUserIds.has(sub.user_id)) {
        console.log(`Brief already sent to ${email} for ${brief.date}, skipping`);
        continue;
      }

      try {
        // Render HTML email
        const html = renderEmailHtml(brief, sub.categories || []);

        // Send via Resend
        const sendResult = await fetch("https://api.resend.com/emails", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${resendApiKey}`,
          },
          body: JSON.stringify({
            from: "The Innovators League <brief@innovatorsleague.com>",
            to: [email],
            subject: `TIL Weekly Brief — ${brief.display_date}`,
            html: html,
          }),
        });

        const sendData = await sendResult.json();

        if (sendResult.ok && sendData.id) {
          // Log success
          await supabase.from("email_send_log").insert({
            user_id: sub.user_id,
            brief_date: brief.date,
            status: "sent",
            resend_id: sendData.id,
            sections_included: sectionTitles,
          });
          emailsSent++;
          console.log(`Sent to ${email} (resend_id: ${sendData.id})`);
        } else {
          // Log failure
          await supabase.from("email_send_log").insert({
            user_id: sub.user_id,
            brief_date: brief.date,
            status: "failed",
            resend_id: sendData.id || null,
            sections_included: sectionTitles,
          });
          emailsFailed++;
          console.error(`Failed to send to ${email}:`, sendData);
        }
      } catch (emailErr) {
        emailsFailed++;
        console.error(`Error sending to ${email}:`, emailErr);
      }
    }

    console.log(`Done: ${emailsSent} sent, ${emailsFailed} failed`);

    return jsonResponse({
      brief_id: brief.brief_id,
      subscribers: subscribers.length,
      emails_sent: emailsSent,
      emails_failed: emailsFailed,
      sections: sectionTitles,
    });
  } catch (err) {
    console.error("Edge function error:", err);
    return jsonResponse({ error: "Internal error", details: String(err) }, 500);
  }
});

// ── Email HTML Renderer ──
function renderEmailHtml(brief: WeeklyBrief, userCategories: string[]): string {
  const sections = brief.sections
    .map((section) => renderSection(section))
    .join("");

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TIL Weekly Brief — ${brief.display_date}</title>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <div style="max-width:640px;margin:0 auto;padding:24px 16px;">
    <!-- Header -->
    <div style="text-align:center;padding:32px 0 24px;">
      <div style="display:inline-block;background:#8b5cf6;color:white;font-weight:700;font-size:14px;padding:6px 16px;border-radius:6px;letter-spacing:1px;">ROS</div>
      <h1 style="color:#ffffff;font-size:24px;margin:16px 0 4px;font-weight:600;">Weekly Intelligence Brief</h1>
      <p style="color:#888;font-size:14px;margin:0;">${brief.display_date} &middot; ${brief.total_items} signals tracked</p>
    </div>

    <!-- Sections -->
    ${sections}

    <!-- Footer -->
    <div style="text-align:center;padding:32px 0 16px;border-top:1px solid #222;">
      <p style="color:#666;font-size:12px;margin:0 0 8px;">
        You're receiving this because you opted into email digests on The Innovators League.
      </p>
      <p style="color:#666;font-size:12px;margin:0;">
        <a href="https://innovatorsleague.com/index.html#alerts-config" style="color:#8b5cf6;text-decoration:none;">Manage preferences</a>
        &middot;
        <a href="https://innovatorsleague.com" style="color:#8b5cf6;text-decoration:none;">Visit TIL</a>
      </p>
    </div>
  </div>
</body>
</html>`;
}

function renderSection(section: BriefSection): string {
  const items = section.items
    .map((item) => renderItem(section.title, item))
    .join("");

  return `
    <div style="background:#111;border:1px solid #222;border-radius:12px;padding:20px;margin-bottom:16px;">
      <h2 style="color:#ffffff;font-size:16px;margin:0 0 12px;font-weight:600;">
        ${section.icon} ${section.title}
        <span style="color:#666;font-weight:400;font-size:13px;margin-left:8px;">${section.count} items</span>
      </h2>
      ${items}
    </div>`;
}

function renderItem(sectionTitle: string, item: any): string {
  // Different rendering based on section type
  if (sectionTitle === "Top Score Movers") {
    const changeColor = item.change > 0 ? "#10b981" : "#ef4444";
    const arrow = item.change > 0 ? "\u25B2" : "\u25BC";
    return `<div style="padding:8px 0;border-bottom:1px solid #1a1a1a;">
      <span style="color:#fff;font-weight:500;">${item.company}</span>
      <span style="color:${changeColor};font-size:13px;margin-left:8px;">${arrow} ${item.change > 0 ? "+" : ""}${item.change}</span>
      <span style="color:#666;font-size:12px;margin-left:8px;">${item.tier || ""}</span>
    </div>`;
  }

  if (sectionTitle === "New Funding Rounds") {
    return `<div style="padding:8px 0;border-bottom:1px solid #1a1a1a;">
      <span style="color:#fff;font-weight:500;">${item.company}</span>
      <span style="color:#10b981;font-size:13px;margin-left:8px;">${item.amount}</span>
      <span style="color:#888;font-size:12px;margin-left:8px;">${item.round} ${item.investor ? "— " + item.investor : ""}</span>
    </div>`;
  }

  if (sectionTitle === "SEC Activity") {
    const badge = item.isIPO ? '<span style="background:#8b5cf6;color:white;font-size:10px;padding:2px 6px;border-radius:4px;margin-left:6px;">IPO</span>' : "";
    return `<div style="padding:8px 0;border-bottom:1px solid #1a1a1a;">
      <span style="color:#fff;font-weight:500;">${item.company}</span>
      <span style="color:#f59e0b;font-size:12px;margin-left:8px;">${item.form}</span>${badge}
      <p style="color:#888;font-size:12px;margin:4px 0 0;">${item.description}</p>
    </div>`;
  }

  if (sectionTitle === "Market Signals") {
    const impactColor = item.impact === "high" ? "#ef4444" : item.impact === "medium" ? "#f59e0b" : "#666";
    return `<div style="padding:8px 0;border-bottom:1px solid #1a1a1a;">
      <span style="color:#fff;font-size:13px;">${item.title}</span>
      <div style="margin-top:4px;">
        <span style="color:#888;font-size:11px;">${item.source}</span>
        ${item.company ? `<span style="color:#8b5cf6;font-size:11px;margin-left:8px;">${item.company}</span>` : ""}
        <span style="color:${impactColor};font-size:10px;margin-left:8px;text-transform:uppercase;">${item.impact}</span>
      </div>
    </div>`;
  }

  if (sectionTitle === "Hacker News Buzz") {
    return `<div style="padding:8px 0;border-bottom:1px solid #1a1a1a;">
      <span style="color:#fff;font-size:13px;">${item.title}</span>
      <div style="margin-top:4px;">
        <span style="color:#f59e0b;font-size:11px;">\u25B2 ${item.score}</span>
        <span style="color:#888;font-size:11px;margin-left:8px;">${item.comments} comments</span>
      </div>
    </div>`;
  }

  if (sectionTitle === "Federal Register") {
    return `<div style="padding:8px 0;border-bottom:1px solid #1a1a1a;">
      <span style="color:#fff;font-size:13px;">${item.title}</span>
      <div style="margin-top:4px;">
        <span style="color:#888;font-size:11px;">${item.type}</span>
        ${item.significant ? '<span style="color:#ef4444;font-size:10px;margin-left:8px;">SIGNIFICANT</span>' : ""}
      </div>
    </div>`;
  }

  if (sectionTitle === "Insider Trading") {
    const txColor = item.transaction_type?.toLowerCase().includes("purchase") ? "#10b981" : "#ef4444";
    return `<div style="padding:8px 0;border-bottom:1px solid #1a1a1a;">
      <span style="color:#fff;font-weight:500;">${item.company}</span>
      <span style="color:${txColor};font-size:12px;margin-left:8px;">${item.transaction_type}</span>
      <p style="color:#888;font-size:12px;margin:4px 0 0;">${item.insider} — ${item.shares} shares ($${item.value})</p>
    </div>`;
  }

  // Generic fallback
  const title = item.title || item.company || item.product || "Item";
  return `<div style="padding:8px 0;border-bottom:1px solid #1a1a1a;">
    <span style="color:#fff;font-size:13px;">${title}</span>
  </div>`;
}

// ── Helper ──
function jsonResponse(data: any, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}
