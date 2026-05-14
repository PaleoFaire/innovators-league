# Launch Hand-Off Guide

Everything you need to flip the Innovators League from GitHub Pages to a real production deployment on Cloudflare Pages, with analytics + error reporting wired in.

Estimated time end-to-end: **45–90 minutes** depending on DNS propagation.

---

## What's already done

Code-side, the site is launch-ready:

- All 36 HTML pages have standardized OG / Twitter / canonical meta tags
- Cookie consent banner wired on every page (essential + analytics consent split)
- Privacy / Terms / Manage-cookies / Contact links in every footer
- 5 OG share images (default + defense + space + nuclear + reindustrialize)
- JSON-LD structured data injected on every page (Organization + WebSite + WebPage / CollectionPage + BreadcrumbList)
- Sitemap.xml with 36 URLs, robots.txt, _headers (Cloudflare cache rules + security)
- 404.html (Cloudflare Pages serves this automatically for missing routes)
- press.html press kit
- 4 sector landing pages (/defense, /space, /nuclear, /reindustrialize) optimized for SEO + tweet sharing
- `analytics.js` already wired for Plausible + Sentry — flip via `config.js`

---

## Step 1 — Buy the domain (15 min)

Recommended registrar: **Cloudflare Registrar** (at-cost pricing, no upsells, automatic DNSSEC). If you already have one, that's fine — we'll just point the nameservers at Cloudflare.

1. Go to https://www.cloudflare.com/products/registrar/
2. Search `innovatorsleague.com` (or your alternate). Add to cart.
3. Buy. ~$10/yr for `.com`.

If buying elsewhere (Namecheap, Google Domains, etc.):
1. Buy the domain.
2. Add it as a site in Cloudflare → DNS panel → grab the assigned Cloudflare nameservers.
3. In your registrar, replace nameservers with Cloudflare's.
4. Wait 1–4 hours for propagation. Status: `green` in Cloudflare → DNS.

---

## Step 2 — Set up Cloudflare Pages (10 min)

1. Cloudflare dashboard → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**.
2. Authorize Cloudflare to access GitHub. Select `PaleoFaire/innovators-league`.
3. **Project name**: `innovators-league`. **Production branch**: `main`.
4. **Build settings**: this is a static site with no build step. Leave:
   - Framework preset: **None**
   - Build command: *(empty)*
   - Build output directory: `/`
5. Click **Save and Deploy**. First deploy completes in ~30 seconds.
6. You'll get a `.pages.dev` preview URL (e.g. `innovators-league-abc.pages.dev`) — visit it. Should look identical to today's GitHub Pages site.

### Add the custom domain
1. In the Pages project → **Custom domains** → **Set up a custom domain**.
2. Enter `innovatorsleague.com` and `www.innovatorsleague.com`.
3. Cloudflare auto-creates the CNAME records. Status flips to active in 1–5 min.
4. Browse to https://innovatorsleague.com — should serve from Cloudflare.

### Verify deployment
- HTTPS: enforced automatically by Cloudflare (Let's Encrypt cert).
- `_headers` file is honored — verify in DevTools → Network → click `data.js` → response headers should show `cache-control: public, max-age=300, s-maxage=300`.
- Push a commit. Pages auto-rebuilds in ~30s.
- The hourly cron pushes from GitHub Actions will continue working — Cloudflare just observes the new commits.

---

## Step 3 — Set up Plausible (10 min)

Plausible is the privacy-friendly Google Analytics alternative. No cookies, no PII, GDPR-compliant, beautiful dashboard. $9/mo for the entry tier.

1. https://plausible.io → **Try it free** (30-day trial).
2. **Add a site** → enter `innovatorsleague.com` exactly as the domain.
3. **Skip** the snippet step — we already have it wired.
4. Open `config.js` in this repo. Find this commented line:

   ```js
   // window.__TIL_PLAUSIBLE_DOMAIN = 'innovatorsleague.com';
   ```

   Uncomment it. Set the value to your exact Plausible site domain.

5. Commit + push. Cloudflare redeploys in 30s. Browse the site. Refresh the Plausible dashboard — you should see live visitor count.

### Custom events you'll get for free
- Page views (automatic)
- Outbound link clicks (automatic since we'll add the outbound-links script — see Plausible docs for the optional snippet)

### Optional but recommended
Plausible's **goals** feature: configure goals for `Subscribe Clicked`, `Sign Up`, etc. Fire from inline JS:
```js
window.plausible && plausible('Subscribe Clicked');
```

---

## Step 4 — Set up Sentry (10 min)

Sentry is for JavaScript error reporting. Free tier = 5,000 events/month, plenty for a soft launch.

1. https://sentry.io → **Get Started** → create org `rational-optimist-society`.
2. **Create Project** → **Browser JavaScript** → name it `innovators-league`.
3. On the next screen Sentry shows you the DSN. It looks like:
   ```
   https://abcd1234@o12345.ingest.us.sentry.io/67890
   ```
4. Open `config.js`. Find:

   ```js
   // window.__TIL_SENTRY_DSN = 'https://YOUR_KEY@oXXXXXX.ingest.sentry.io/XXXXXXX';
   // window.__TIL_SENTRY_ENV = 'production';
   ```

   Uncomment both. Paste your DSN.

5. Commit + push.
6. Verify: open https://innovatorsleague.com, run in console:
   ```js
   __TIL_ANALYTICS_STATUS()
   ```
   You should see `sentry.loaded: true`.

7. Trigger a test error:
   ```js
   setTimeout(() => { throw new Error('Sentry test from launch'); }, 0);
   ```
   Check the Sentry dashboard — should appear within ~10 seconds.

### Optional sentry config tweaks
- Trace sample rate is `0.1` (10% of page loads). Lower if you blow through events.
- `ignoreErrors` is pre-populated with common browser noise. Add to it if specific extension errors show up.

---

## Step 5 — Submit sitemap to Google + Bing (5 min)

Now that you have a real domain:

1. **Google Search Console**: https://search.google.com/search-console → add property `innovatorsleague.com` → verify via DNS TXT record (Cloudflare DNS makes this 1 click). After verification, **Sitemaps** → add `https://innovatorsleague.com/sitemap.xml`.
2. **Bing Webmaster Tools**: https://www.bing.com/webmasters → import from Google Search Console (saves a step).

You should see Google start indexing pages within 1–3 days.

---

## Step 6 — Test the social share cards (5 min)

The OG images are designed to look great when shared on Twitter, LinkedIn, Discord, Slack.

1. Twitter Card Validator: https://cards-dev.twitter.com/validator → paste each URL:
   - `https://innovatorsleague.com/` (default OG)
   - `https://innovatorsleague.com/defense.html`
   - `https://innovatorsleague.com/space.html`
   - `https://innovatorsleague.com/nuclear.html`
   - `https://innovatorsleague.com/reindustrialize.html`
2. Facebook Sharing Debugger: https://developers.facebook.com/tools/debug/ → same URLs. If image doesn't show, click **Scrape Again**.
3. LinkedIn Post Inspector: https://www.linkedin.com/post-inspector/

If any card looks wrong, the OG meta tags are in the `<head>` of each HTML file. Edit, commit, push, re-scrape.

---

## Step 7 — Update placeholder URLs

In all 36 HTML pages and the sitemap, the canonical URL is `https://innovatorsleague.com`. If you bought a different domain, find/replace:

```bash
# Replace placeholder with your real domain everywhere
find . -name "*.html" -not -path "./.venv/*" -not -path "./_archive/*" \
  -exec sed -i '' 's|https://innovatorsleague\.com|https://your-real-domain.com|g' {} \;
sed -i '' 's|https://innovatorsleague\.com|https://your-real-domain.com|g' sitemap.xml
sed -i '' 's|innovatorsleague\.com|your-real-domain.com|g' robots.txt
```

Then commit + push.

---

## Step 8 — Smoke test (5 min)

After launch:

- [ ] Homepage loads with all 870+ companies visible in the index
- [ ] Cookie banner appears on first visit
- [ ] Click "Manage cookies" in footer → banner reopens
- [ ] Sign-in modal opens from nav
- [ ] `https://innovatorsleague.com/defense.html` shows defense companies + sector OG image preview when shared
- [ ] `https://innovatorsleague.com/nonexistent` shows the 404 page (not Cloudflare default)
- [ ] `https://innovatorsleague.com/press.html` renders cleanly
- [ ] DevTools → Network → no 404s on the homepage
- [ ] DevTools → Console → no red errors (yellow warnings ok)
- [ ] Plausible shows live visitor
- [ ] Sentry shows session

---

## Maintenance after launch

- **Hourly cron** continues running via GitHub Actions. Pushes to `main` auto-deploy via Cloudflare.
- **data.js** is currently 28MB. Cloudflare's unlimited bandwidth handles this for now. Post-launch, when you have time + an engineer, split it into per-sector chunks — see DATA_AUTOMATION_PLAN.md.
- **Sentry events**: check weekly. Common patterns can be added to `ignoreErrors` in `analytics.js`.
- **Plausible**: just look at it. The dashboard is the whole product.
- **Legal pages** (privacy.html, terms.html): drafted, fit for soft launch. Get a lawyer review before any paid product launch.

---

## Things deferred to v1.1

- data.js chunking (sector-level files instead of 28MB monolith)
- Real logo/wordmark SVG (currently using the "ROS" green badge as logomark)
- Newsletter signup form on homepage (currently links to Substack)
- More OG images (per-company on company.html?c=...)
- Sentry SDK upgrade to latest (currently pinned to 7.119.0 with integrity hash)

---

## Emergency contacts

- **Domain registrar**: whoever you bought from
- **Cloudflare**: support.cloudflare.com (24/7 chat on paid plans, otherwise community forum)
- **GitHub**: dashboard.github.com → repository → actions tab for cron failures
- **Sentry**: dashboard alerts on email immediately

---

*Last updated: 2026-05-14. Maintained alongside the code.*
