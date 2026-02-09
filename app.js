// ─── COUNTRY MAPPING ───
// US state codes
const US_STATES = new Set([
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID',
  'IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS',
  'MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK',
  'OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'
]);

// State code to full name mapping
const STATE_NAMES = {
  'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
  'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
  'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
  'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
  'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
  'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
  'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
  'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
  'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
  'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
  'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
  'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
  'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'Washington D.C.'
};

// Unambiguous international codes (no US state conflict)
const INTL_CODES = {
  'UK': 'United Kingdom', 'GB': 'United Kingdom',
  'FR': 'France', 'SE': 'Sweden', 'FI': 'Finland',
  'CH': 'Switzerland', 'DK': 'Denmark', 'NO': 'Norway', 'NL': 'Netherlands',
  'ES': 'Spain', 'IT': 'Italy', 'EE': 'Estonia', 'PL': 'Poland',
  'JP': 'Japan', 'KR': 'South Korea',
  'AU': 'Australia', 'SG': 'Singapore',
  'NZ': 'New Zealand', 'ZA': 'South Africa', 'BR': 'Brazil',
  'IE': 'Ireland', 'CA-CAN': 'Canada',
  'PT': 'Portugal', 'CZ': 'Czech Republic'
};

// Countries found in location strings — used to disambiguate shared codes
const LOCATION_COUNTRIES = {
  'Germany': 'Germany', 'Israel': 'Israel', 'India': 'India',
  'Argentina': 'Argentina', 'Ireland': 'Ireland'
};

function getCountry(stateCode, location) {
  // Check unambiguous international codes first
  if (INTL_CODES[stateCode]) return INTL_CODES[stateCode];

  // For ambiguous codes (DE, IL, IN, AR, GA), use the location string
  if (location) {
    for (const [keyword, country] of Object.entries(LOCATION_COUNTRIES)) {
      if (location.includes(keyword)) return country;
    }
  }

  // Default: US state
  return 'United States';
}

// ─── COMPANY WEBSITE DIRECTORY ───
const COMPANY_WEBSITES = {
  "Anduril Industries": "https://www.anduril.com",
  "Shield AI": "https://www.shield.ai",
  "Epirus": "https://www.epirusinc.com",
  "Saronic": "https://www.saronic.com",
  "SpaceX": "https://www.spacex.com",
  "Boom Supersonic": "https://boomsupersonic.com",
  "Hermeus": "https://www.hermeus.com",
  "Venus Aerospace": "https://www.venusaero.com",
  "Castelion": "https://www.castelion.com",
  "Hadrian": "https://www.hadrian.co",
  "Palantir": "https://www.palantir.com",
  "Scale AI": "https://scale.com",
  "Relativity Space": "https://www.relativityspace.com",
  "Rocket Lab": "https://www.rocketlabusa.com",
  "Impulse Space": "https://www.impulsespace.com",
  "Varda Space Industries": "https://www.varda.com",
  "Astranis": "https://www.astranis.com",
  "Planet Labs": "https://www.planet.com",
  "Joby Aviation": "https://www.jobyaviation.com",
  "Archer Aviation": "https://www.archer.com",
  "Lilium": "https://www.lilium.com",
  "Skydio": "https://www.skydio.com",
  "Zipline": "https://www.flyzipline.com",
  "Saildrone": "https://www.saildrone.com",
  "Figure": "https://www.figure.ai",
  "Physical Intelligence": "https://www.physicalintelligence.company",
  "Agility Robotics": "https://www.agilityrobotics.com",
  "Apptronik": "https://www.apptronik.com",
  "Covariant": "https://covariant.ai",
  "Boston Dynamics": "https://www.bostondynamics.com",
  "Commonwealth Fusion Systems": "https://cfs.energy",
  "Helion": "https://www.helionenergy.com",
  "Oklo": "https://oklo.com",
  "Radiant": "https://www.radiantnuclear.com",
  "Kairos Power": "https://kairospower.com",
  "TerraPower": "https://www.terrapower.com",
  "NuScale Power": "https://www.nuscalepower.com",
  "Fervo Energy": "https://fervoenergy.com",
  "Solugen": "https://www.solugen.com",
  "KoBold Metals": "https://www.koboldmetals.com",
  "Heirloom Carbon": "https://www.heirloomcarbon.com",
  "Terraform Industries": "https://www.terraformindustries.com",
  "Cerebras": "https://www.cerebras.net",
  "Groq": "https://groq.com",
  "Lightmatter": "https://lightmatter.co",
  "Etched": "https://www.etched.com",
  "OpenAI": "https://openai.com",
  "Anthropic": "https://www.anthropic.com",
  "Neuralink": "https://neuralink.com",
  "Waymo": "https://waymo.com",
  "Zoox": "https://zoox.com",
  "Applied Intuition": "https://www.appliedintuition.com",
  "Flexport": "https://www.flexport.com",
  "Gecko Robotics": "https://www.geckorobotics.com",
  "Machina Labs": "https://www.machinalabs.ai",
  "Bedrock Robotics": "https://www.bedrockrobotics.ai",
  "GrayMatter Robotics": "https://www.graymatter-robotics.com",
  "Collaborative Robotics": "https://www.collaborativerobotics.com",
  "Pano AI": "https://www.pano.ai",
  "AiDash": "https://www.aidash.com",
  "Multiply Labs": "https://www.multiplylabs.com",
  "Cobod": "https://cobod.com",
  "Mighty Buildings": "https://www.mightybuildings.com",
  "ICON Technology": "https://www.iconbuild.com",
  "AstroForge": "https://www.astroforge.io",
  "Muon Space": "https://www.muonspace.com",
  "Axiom Space": "https://www.axiomspace.com",
  "Sierra Space": "https://www.sierraspace.com",
  "Valar Atomics": "https://www.valaratomics.com",
  "Deep Fission": "https://www.deepfission.com",
  "Pacific Fusion": "https://www.pacificfusion.com",
  "Xcimer Energy": "https://www.xcimer.com",
  "Zap Energy": "https://www.zapenergy.com",
  "PsiQuantum": "https://www.psiquantum.com",
  "IonQ": "https://ionq.com",
  "Rigetti Computing": "https://www.rigetti.com",
  "Colossal Biosciences": "https://colossal.com",
  "Retro Biosciences": "https://retro.bio",
  "NewLimit": "https://www.newlimit.com",
  "Neros": "https://www.neros.tech",
  "Chaos Industries": "https://www.chaosindustries.com",
  "Picogrid": "https://picogrid.com",
  "Skild AI": "https://www.skild.ai",
  "Gecko Robotics": "https://www.geckorobotics.com",
  "Antora Energy": "https://www.antoraenergy.com",
  "Koloma": "https://www.koloma.com",
  "Crusoe Energy": "https://www.crusoeenergy.com",
  "Form Energy": "https://formenergy.com",
  "Helion Energy": "https://www.helionenergy.com",
  "Orangewood Labs": "https://www.orangewood.co",
  "Trilobio": "https://www.trilobio.com",
  "Starpath Robotics": "https://www.starpathrobotics.com",
  "SafeAI": "https://www.safeai.ai",
  "RIOS Intelligent Machines": "https://www.rios.ai",
  "Orbital Composites": "https://www.orbitalcomposites.com"
};

function getCompanyWebsite(companyName) {
  return COMPANY_WEBSITES[companyName] || '';
}

// ─── MAFIA LOOKUP ───
function getCompanyMafias(companyName) {
  if (typeof FOUNDER_MAFIAS === 'undefined') return [];
  const results = [];
  for (const [mafiaName, data] of Object.entries(FOUNDER_MAFIAS)) {
    const match = data.companies.find(c => c.company === companyName);
    if (match) {
      results.push({
        mafia: mafiaName,
        icon: data.icon,
        color: data.color,
        detail: match.founders
      });
    }
  }
  return results;
}

// ─── SIGNAL HELPERS ───
const SIGNAL_CONFIG = {
  hot:         { label: 'HOT', icon: '🔥', class: 'signal-hot' },
  rising:      { label: 'RISING', icon: '⚡', class: 'signal-rising' },
  stealth:     { label: 'STEALTH', icon: '👀', class: 'signal-stealth' },
  watch:       { label: 'WATCH', icon: '🔭', class: 'signal-watch' },
  established: { label: 'EST.', icon: '✓', class: 'signal-established' }
};

const SIGNAL_PRIORITY = { hot: 0, rising: 1, stealth: 2, watch: 3, established: 4 };

function renderSignalBadge(signal) {
  if (!signal || !SIGNAL_CONFIG[signal]) return '';
  const s = SIGNAL_CONFIG[signal];
  return `<span class="signal-badge ${s.class}">${s.icon} ${s.label}</span>`;
}

// ─── INNOVATOR SCORE™ (World-Class Mosaic-Style Scoring) ───
// Uses the new INNOVATOR_SCORES object with 0-1000 scale

function getInnovatorScore(companyName) {
  if (typeof INNOVATOR_SCORES === 'undefined') return null;
  return INNOVATOR_SCORES[companyName] || null;
}

function getInnovatorScoreLabel(score) {
  if (!score) return { label: 'Unrated', class: 'unrated' };
  const total = score.total || 0;
  if (total >= 900) return { label: 'Elite', class: 'elite', icon: '👑' };
  if (total >= 800) return { label: 'Exceptional', class: 'exceptional', icon: '🔥' };
  if (total >= 700) return { label: 'Strong', class: 'strong', icon: '⚡' };
  if (total >= 600) return { label: 'Promising', class: 'promising', icon: '📈' };
  if (total >= 500) return { label: 'Developing', class: 'developing', icon: '🌱' };
  return { label: 'Nascent', class: 'nascent', icon: '🔬' };
}

function renderInnovatorScoreBadge(companyName) {
  const score = getInnovatorScore(companyName);
  if (!score) {
    // Fallback to old scoring system
    return renderLegacyScoreBadge(companyName);
  }
  const { label, class: cls, icon } = getInnovatorScoreLabel(score);
  const trendIcon = score.trend === 'accelerating' ? '↑' : score.trend === 'decelerating' ? '↓' : '→';
  return `
    <span class="innovator-score-badge ${cls}" title="${label}: ${score.total}/1000 | Momentum: ${score.momentum} | Market: ${score.market} | Tech: ${score.technology} | Team: ${score.team}">
      ${icon} ${score.total} <span class="score-trend ${score.trend}">${trendIcon}</span>
    </span>
  `;
}

function renderInnovatorScoreDetail(companyName) {
  const score = getInnovatorScore(companyName);
  if (!score) return '';

  const { label, class: cls } = getInnovatorScoreLabel(score);
  const change = score.total - (score.priorScore || score.total);
  const changeIcon = change > 0 ? '↑' : change < 0 ? '↓' : '→';
  const changeClass = change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral';

  return `
    <div class="innovator-score-detail">
      <div class="score-header">
        <span class="score-total ${cls}">${score.total}</span>
        <span class="score-label">${label}</span>
        <span class="score-change ${changeClass}">${changeIcon} ${Math.abs(change)} (30d)</span>
      </div>
      <div class="score-dimensions">
        <div class="score-dim" title="Growth trajectory and market activity">
          <span class="dim-label">Momentum</span>
          <div class="dim-bar"><div class="dim-fill momentum" style="width: ${score.momentum}%"></div></div>
          <span class="dim-value">${score.momentum}</span>
        </div>
        <div class="score-dim" title="Market opportunity and positioning">
          <span class="dim-label">Market</span>
          <div class="dim-bar"><div class="dim-fill market" style="width: ${score.market}%"></div></div>
          <span class="dim-value">${score.market}</span>
        </div>
        <div class="score-dim" title="Technical moat and product maturity">
          <span class="dim-label">Technology</span>
          <div class="dim-bar"><div class="dim-fill technology" style="width: ${score.technology}%"></div></div>
          <span class="dim-value">${score.technology}</span>
        </div>
        <div class="score-dim" title="Leadership quality and execution">
          <span class="dim-label">Team</span>
          <div class="dim-bar"><div class="dim-fill team" style="width: ${score.team}%"></div></div>
          <span class="dim-value">${score.team}</span>
        </div>
      </div>
      ${score.breakdown ? `<div class="score-breakdown">${score.breakdown}</div>` : ''}
    </div>
  `;
}

// Legacy scoring fallback for companies without Innovator Score
function getAverageScore(scores) {
  if (!scores) return 0;
  const vals = [scores.team, scores.traction, scores.techMoat, scores.market, scores.momentum].filter(v => v != null);
  return vals.length ? (vals.reduce((sum, v) => sum + v, 0) / vals.length) : 0;
}

function renderLegacyScoreBadge(companyName) {
  const company = typeof COMPANIES !== 'undefined' ? COMPANIES.find(c => c.name === companyName) : null;
  if (!company || !company.scores) return '';
  const avg = getAverageScore(company.scores);
  if (avg === 0) return '';
  const cls = avg >= 8 ? 'high' : avg >= 6 ? 'mid' : 'low';
  return `<span class="score-badge ${cls}">★ ${avg.toFixed(1)}</span>`;
}

function renderScoreBadge(scores) {
  if (!scores) return '';
  const avg = getAverageScore(scores);
  if (avg === 0) return '';
  const cls = avg >= 8 ? 'high' : avg >= 6 ? 'mid' : 'low';
  return `<span class="score-badge ${cls}">★ ${avg.toFixed(1)}</span>`;
}

// ─── INVESTMENT THESIS ───
function renderThesis(thesis) {
  if (!thesis) return '';
  return `
    <div class="thesis-section">
      <h4>Investment Thesis</h4>
      ${thesis.bull ? `
        <div class="thesis-item thesis-bull">
          <div class="thesis-label">Bull Case</div>
          ${thesis.bull}
        </div>
      ` : ''}
      ${thesis.bear ? `
        <div class="thesis-item thesis-bear">
          <div class="thesis-label">Bear Case</div>
          ${thesis.bear}
        </div>
      ` : ''}
      ${thesis.risks && thesis.risks.length > 0 ? `
        <div class="thesis-risks">
          <h5>Key Risks</h5>
          ${thesis.risks.map(r => `<div class="thesis-risk-item">${r}</div>`).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

// ─── DUE DILIGENCE ONE-PAGER ───
function generateOnePager(companyName) {
  const company = COMPANIES.find(c => c.name === companyName);
  if (!company) return;

  const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };
  const country = getCountry(company.state, company.location);
  const avg = getAverageScore(company.scores);

  // Find VCs backing this company
  const backers = (typeof VC_FIRMS !== 'undefined' ? VC_FIRMS : [])
    .filter(f => f.portfolioCompanies.includes(company.name))
    .map(f => f.shortName);

  const competitors = (company.competitors || [])
    .map(name => COMPANIES.find(c => c.name === name))
    .filter(Boolean);

  const w = window.open('', '_blank');
  w.document.write(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>${company.name} — Due Diligence One-Pager | Innovators League</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: #000; color: #f0f0fa; padding: 40px; max-width: 900px; margin: 0 auto; line-height: 1.6; }
        .header { border-bottom: 2px solid #FF6B2C; padding-bottom: 20px; margin-bottom: 28px; }
        .header h1 { font-size: 28px; margin-bottom: 4px; }
        .header .subtitle { color: rgba(240,240,250,0.5); font-size: 13px; }
        .sector-tag { display: inline-block; background: rgba(255,107,44,0.12); color: #FF6B2C; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; margin-bottom: 12px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
        .stat-box { background: #0a0a0a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px; }
        .stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(240,240,250,0.4); margin-bottom: 4px; }
        .stat-value { font-size: 18px; font-weight: 600; }
        .section { margin: 24px 0; }
        .section h3 { font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #FF6B2C; margin-bottom: 10px; }
        .section p { color: rgba(240,240,250,0.7); font-size: 14px; }
        .insight-box { background: #0a0a0a; border-left: 3px solid #FF6B2C; padding: 16px; border-radius: 0 8px 8px 0; margin: 12px 0; font-style: italic; color: rgba(240,240,250,0.7); font-size: 14px; }
        .tags { display: flex; flex-wrap: wrap; gap: 6px; }
        .tag { background: #111; border: 1px solid rgba(255,255,255,0.08); padding: 4px 10px; border-radius: 6px; font-size: 12px; color: rgba(240,240,250,0.6); }
        .bull { background: rgba(34,197,94,0.06); border-left: 3px solid #22C55E; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; font-size: 13px; color: rgba(240,240,250,0.7); }
        .bear { background: rgba(239,68,68,0.06); border-left: 3px solid #EF4444; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; font-size: 13px; color: rgba(240,240,250,0.7); }
        .bull-label { color: #22C55E; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
        .bear-label { color: #EF4444; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
        .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08); text-align: center; color: rgba(240,240,250,0.3); font-size: 12px; }
        .score-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }
        .score-item { background: #0a0a0a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 16px; text-align: center; }
        .score-num { font-size: 20px; font-weight: 700; color: #22C55E; }
        .score-lbl { font-size: 10px; text-transform: uppercase; letter-spacing: 0.3px; color: rgba(240,240,250,0.4); margin-top: 2px; }
        @media print {
          body { background: #fff; color: #000; padding: 20px; }
          .stat-box, .insight-box, .bull, .bear, .score-item { background: #f5f5f5; border-color: #ddd; }
          .section h3 { color: #333; }
          .stat-label, .section p, .insight-box, .bull, .bear { color: #333; }
          .header { border-color: #333; }
          .score-num { color: #22C55E; }
          .tag { background: #eee; border-color: #ccc; color: #333; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <div class="sector-tag">${sectorInfo.icon} ${company.sector}</div>
        <h1>${company.name}</h1>
        <div class="subtitle">Due Diligence One-Pager · Generated ${new Date().toLocaleDateString()} · Innovators League by ROS</div>
      </div>

      <div class="grid">
        <div class="stat-box"><div class="stat-label">Location</div><div class="stat-value">${company.location} · ${country}</div></div>
        <div class="stat-box"><div class="stat-label">Stage</div><div class="stat-value">${company.fundingStage || 'N/A'}</div></div>
        <div class="stat-box"><div class="stat-label">Total Raised</div><div class="stat-value">${company.totalRaised || 'N/A'}</div></div>
        <div class="stat-box"><div class="stat-label">Valuation</div><div class="stat-value">${company.valuation || 'N/A'}</div></div>
        ${company.founder ? `<div class="stat-box"><div class="stat-label">Founder(s)</div><div class="stat-value">${company.founder}</div></div>` : ''}
        ${avg > 0 ? `<div class="stat-box"><div class="stat-label">Innovation Score</div><div class="stat-value" style="color:#22C55E">${avg.toFixed(1)} / 10</div></div>` : ''}
      </div>

      ${company.scores ? `
        <div class="section">
          <h3>Innovation Score <span style="font-size:11px;color:var(--text-muted);font-weight:400;margin-left:8px;">Avg of 5 dimensions (1-10 scale)</span></h3>
          <div class="score-row">
            <div class="score-item"><div class="score-num">${company.scores.team}</div><div class="score-lbl">Team</div></div>
            <div class="score-item"><div class="score-num">${company.scores.traction}</div><div class="score-lbl">Traction</div></div>
            <div class="score-item"><div class="score-num">${company.scores.techMoat}</div><div class="score-lbl">Tech Moat</div></div>
            <div class="score-item"><div class="score-num">${company.scores.market}</div><div class="score-lbl">Market</div></div>
            <div class="score-item"><div class="score-num">${company.scores.momentum}</div><div class="score-lbl">Momentum</div></div>
          </div>
          <p style="font-size:11px;color:var(--text-muted);margin-top:12px;line-height:1.5;">Team = Founder pedigree & experience. Traction = Revenue, users, contracts. Tech Moat = Patents, defensibility. Market = TAM size & timing. Momentum = Recent growth signals.</p>
        </div>
      ` : ''}

      <div class="section">
        <h3>Overview</h3>
        <p>${company.description}</p>
      </div>

      ${company.insight ? `
        <div class="section">
          <h3>Analyst View</h3>
          <div class="insight-box">${company.insight}</div>
        </div>
      ` : ''}

      ${company.thesis ? `
        <div class="section">
          <h3>Investment Thesis</h3>
          ${company.thesis.bull ? `<div class="bull"><div class="bull-label">Bull Case</div>${company.thesis.bull}</div>` : ''}
          ${company.thesis.bear ? `<div class="bear"><div class="bear-label">Bear Case</div>${company.thesis.bear}</div>` : ''}
          ${company.thesis.risks ? `<div style="margin-top:12px"><div style="color:#F59E0B;font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:6px">Key Risks</div>${company.thesis.risks.map(r => `<div style="font-size:13px;color:rgba(240,240,250,0.6);padding:3px 0;">⚠ ${r}</div>`).join('')}</div>` : ''}
        </div>
      ` : ''}

      ${backers.length > 0 ? `
        <div class="section">
          <h3>VC Backers</h3>
          <div class="tags">${backers.map(b => `<span class="tag">${b}</span>`).join('')}</div>
        </div>
      ` : ''}

      ${competitors.length > 0 ? `
        <div class="section">
          <h3>Competitive Landscape</h3>
          <div class="tags">${competitors.map(c => `<span class="tag">${c.name}</span>`).join('')}</div>
        </div>
      ` : ''}

      <div class="section">
        <h3>Tags</h3>
        <div class="tags">${company.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>
      </div>

      <div class="footer">
        <p>The Innovators League by Rational Optimist Society · rationaloptimistsociety.com</p>
        <p style="margin-top:4px">This report is for informational purposes only and does not constitute investment advice.</p>
      </div>
    </body>
    </html>
  `);
  w.document.close();
}

// ─── RADAR CHART ───
function renderRadarChart(scores) {
  if (!scores) return '';
  const labels = ['Team', 'Traction', 'Tech Moat', 'Market', 'Momentum'];
  const keys = ['team', 'traction', 'techMoat', 'market', 'momentum'];
  const size = 280;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = 100;
  const levels = [0.25, 0.5, 0.75, 1.0];

  function polarToCart(angle, radius) {
    const a = (angle - 90) * Math.PI / 180;
    return [cx + radius * Math.cos(a), cy + radius * Math.sin(a)];
  }

  const angleStep = 360 / 5;

  // Grid polygons
  let gridSvg = '';
  levels.forEach(level => {
    const points = [];
    for (let i = 0; i < 5; i++) {
      const [x, y] = polarToCart(i * angleStep, maxR * level);
      points.push(`${x},${y}`);
    }
    gridSvg += `<polygon points="${points.join(' ')}" class="radar-grid"/>`;
  });

  // Axis lines
  let axisSvg = '';
  for (let i = 0; i < 5; i++) {
    const [x, y] = polarToCart(i * angleStep, maxR);
    axisSvg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" class="radar-axis"/>`;
  }

  // Data polygon
  const dataPoints = [];
  for (let i = 0; i < 5; i++) {
    const val = (scores[keys[i]] || 0) / 10;
    const [x, y] = polarToCart(i * angleStep, maxR * val);
    dataPoints.push(`${x},${y}`);
  }

  // Labels
  let labelsSvg = '';
  for (let i = 0; i < 5; i++) {
    const [x, y] = polarToCart(i * angleStep, maxR + 22);
    const val = scores[keys[i]] || 0;
    labelsSvg += `<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="middle" class="radar-label">${labels[i]}</text>`;
    const [sx, sy] = polarToCart(i * angleStep, maxR * (val / 10) + 12);
    labelsSvg += `<text x="${sx}" y="${sy}" text-anchor="middle" dominant-baseline="middle" class="radar-score">${val}</text>`;
  }

  return `
    <div class="radar-chart-container">
      <div>
        <h4>Intelligence Scores</h4>
        <div class="radar-chart">
          <svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
            ${gridSvg}
            ${axisSvg}
            <polygon points="${dataPoints.join(' ')}" class="radar-data"/>
            ${labelsSvg}
          </svg>
        </div>
      </div>
    </div>
  `;
}

// ─── BOOKMARKS ───
let bookmarks = JSON.parse(localStorage.getItem('til-bookmarks') || '[]');

function isBookmarked(name) {
  return bookmarks.includes(name);
}

function toggleBookmark(name) {
  if (isBookmarked(name)) {
    bookmarks = bookmarks.filter(b => b !== name);
  } else {
    bookmarks.push(name);
  }
  localStorage.setItem('til-bookmarks', JSON.stringify(bookmarks));
}

// ─── COMPARE ───
let compareList = [];
const MAX_COMPARE = 3;

function toggleCompare(name) {
  const idx = compareList.indexOf(name);
  if (idx > -1) {
    compareList.splice(idx, 1);
  } else if (compareList.length < MAX_COMPARE) {
    compareList.push(name);
  }
  updateCompareBar();
  // Re-render to update card states
  applyFilters();
}

function updateCompareBar() {
  const bar = document.getElementById('compare-bar');
  const items = document.getElementById('compare-items');

  if (compareList.length === 0) {
    bar.classList.remove('visible');
    return;
  }

  bar.classList.add('visible');
  items.innerHTML = compareList.map(name => {
    const c = COMPANIES.find(co => co.name === name);
    if (!c) return '';
    const sectorInfo = SECTORS[c.sector] || { color: '#6b7280', icon: '' };
    return `<div class="compare-item">
      <span style="color:${sectorInfo.color}">${sectorInfo.icon}</span> ${name}
      <button onclick="toggleCompare('${name.replace(/'/g, "\\'")}')" class="compare-remove">&times;</button>
    </div>`;
  }).join('');
}

function showComparison() {
  // Redirect to enhanced comparison modal
  openCompareView();
}

// ─── MODAL ───
function openModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

function openCompanyModal(companyName) {
  const company = COMPANIES.find(c => c.name === companyName);
  if (!company) return;

  const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };
  const saved = isBookmarked(company.name);
  const country = getCountry(company.state, company.location);

  // Related companies (same sector, different company)
  const related = COMPANIES
    .filter(c => c.sector === company.sector && c.name !== company.name)
    .sort(() => Math.random() - 0.5)
    .slice(0, 4);

  // Competitors from data
  const competitors = (company.competitors || [])
    .map(name => COMPANIES.find(c => c.name === name))
    .filter(Boolean);

  const body = document.getElementById('modal-body');
  body.innerHTML = `
    <div class="modal-sector-badge" style="background:${sectorInfo.color}15; color:${sectorInfo.color}; border: 1px solid ${sectorInfo.color}30;">
      ${sectorInfo.icon} ${company.sector}
    </div>
    <h2 class="modal-company-name">${company.name} ${renderSignalBadge(company.signal)}</h2>
    ${company.founder ? `<p class="modal-founder">${company.founder}</p>` : ''}
    ${renderFounderConnectionBadge(company.name)}
    <p class="modal-location">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
      ${company.location} &middot; ${country}
    </p>

    <div class="modal-stats">
      ${company.fundingStage ? `<div class="modal-stat"><span class="modal-stat-label">Stage</span><span class="modal-stat-value">${company.fundingStage}</span></div>` : ''}
      ${company.totalRaised ? `<div class="modal-stat"><span class="modal-stat-label">Raised</span><span class="modal-stat-value">${company.totalRaised}</span></div>` : ''}
      ${company.valuation ? `<div class="modal-stat"><span class="modal-stat-label">Valuation</span><span class="modal-stat-value">${company.valuation}</span></div>` : ''}
    </div>

    ${company.insight ? `
      <div class="modal-insight">
        <div class="modal-insight-label">ROS Intelligence</div>
        ${company.insight}
      </div>
    ` : ''}

    ${renderFounderQuote(company.name)}

    ${renderRadarChart(company.scores)}

    ${renderThesis(company.thesis)}

    <p class="modal-description">${company.description}</p>

    <div class="modal-tags">
      ${company.tags.map(t => `<span class="tag">${t}</span>`).join('')}
    </div>

    ${(() => {
      const backers = (typeof VC_FIRMS !== 'undefined' ? VC_FIRMS : [])
        .filter(f => f.portfolioCompanies.includes(company.name))
        .map(f => f.shortName);
      return backers.length > 0 ? `
        <div class="modal-competitors" style="margin-top:16px;">
          <h4>VC Backers</h4>
          <div class="competitors-grid">
            ${backers.map(b => `<a href="investors.html" class="competitor-chip">${b}</a>`).join('')}
          </div>
        </div>
      ` : '';
    })()}

    ${!company.scores && !company.insight ? '<p class="assessment-pending">⏳ Full intelligence assessment pending</p>' : ''}

    ${(() => {
      const mafias = getCompanyMafias(company.name);
      return mafias.length > 0 ? `
        <div class="modal-mafias">
          <h4>Founder Network</h4>
          <div class="mafia-badges">
            ${mafias.map(m => `
              <div class="mafia-badge" style="background:${m.color}12; border:1px solid ${m.color}30; color:${m.color};">
                <span class="mafia-icon">${m.icon}</span>
                <span class="mafia-name">${m.mafia}</span>
                <span class="mafia-detail">${m.detail}</span>
              </div>
            `).join('')}
          </div>
        </div>
      ` : '';
    })()}

    ${(() => {
      const rev = typeof REVENUE_INTEL !== 'undefined' ? REVENUE_INTEL.find(r => r.company === company.name) : null;
      return rev ? `
        <div class="modal-revenue">
          <h4>Revenue Intelligence</h4>
          <div class="revenue-grid">
            <div class="revenue-item"><span class="revenue-label">Revenue</span><span class="revenue-value">${rev.revenue}</span></div>
            <div class="revenue-item"><span class="revenue-label">Period</span><span class="revenue-value">${rev.period}</span></div>
            <div class="revenue-item"><span class="revenue-label">Growth</span><span class="revenue-value" style="color:var(--accent);">${rev.growth}</span></div>
            <div class="revenue-item"><span class="revenue-label">Source</span><span class="revenue-value" style="font-size:11px;">${rev.source}</span></div>
          </div>
        </div>
      ` : '';
    })()}

    ${(() => {
      const benchmarks = typeof VALUATION_BENCHMARKS !== 'undefined' ? VALUATION_BENCHMARKS[company.sector] : null;
      if (!benchmarks || !company.fundingStage) return '';
      const stage = company.fundingStage.toLowerCase();
      let stageData = null;
      if (stage.includes('seed') || stage.includes('pre-seed')) stageData = benchmarks.seed;
      else if (stage.includes('series a') || stage === 'early stage') stageData = benchmarks.seriesA;
      else if (stage.includes('series b')) stageData = benchmarks.seriesB;
      else if (stage.includes('series c') || stage.includes('series d')) stageData = benchmarks.seriesC;
      else if (stage.includes('growth') || stage.includes('late') || stage.includes('series e') || stage.includes('series f') || stage.includes('series g')) stageData = benchmarks.growth;
      if (!stageData) return '';
      return `
        <div class="modal-valuation-context">
          <div class="val-context-label">📊 Sector Valuation Context: ${company.sector}</div>
          <div class="val-context-text">Median ${company.fundingStage} valuation: <strong>${stageData.median}</strong> (range: ${stageData.range}, ${stageData.deals} deals tracked)</div>
          ${benchmarks.note ? `<div class="val-context-note">${benchmarks.note}</div>` : ''}
        </div>
      `;
    })()}

    ${(() => {
      const iscore = getInnovatorScore(company.name);
      if (!iscore) return '';
      const tierColors = { elite: '#22c55e', strong: '#3b82f6', promising: '#f59e0b', early: '#6b7280' };
      const tc = tierColors[iscore.tier];
      const dims = [
        { label: 'Technology Moat', value: iscore.techMoat, color: '#3b82f6', weight: '25%' },
        { label: 'Momentum', value: iscore.momentum, color: '#f59e0b', weight: '25%' },
        { label: 'Team Pedigree', value: iscore.teamPedigree, color: '#8b5cf6', weight: '15%' },
        { label: 'Market Gravity', value: iscore.marketGravity, color: '#22c55e', weight: '15%' },
        { label: 'Capital Efficiency', value: iscore.capitalEfficiency, color: '#06b6d4', weight: '10%' },
        { label: "Gov't Traction", value: iscore.govTraction, color: '#dc2626', weight: '10%' }
      ];
      return `
        <div class="modal-iscore">
          <div class="modal-iscore-header">
            <h4>Innovator Score™</h4>
            <div class="modal-iscore-total" style="border-color:${tc};">
              <span style="color:${tc}; font-size:28px; font-weight:800;">${iscore.composite.toFixed(0)}</span>
              <span class="modal-iscore-tier" style="background:${tc}15; color:${tc}; border:1px solid ${tc}40;">${iscore.tier.toUpperCase()}</span>
            </div>
          </div>
          <div class="modal-iscore-dims">
            ${dims.map(d => `
              <div class="modal-iscore-dim">
                <div class="modal-iscore-dim-label"><span style="color:${d.color};">●</span> ${d.label} <small style="color:var(--text-muted);">${d.weight}</small></div>
                <div class="modal-iscore-dim-bar"><div style="width:${d.value * 10}%; background:${d.color}; height:100%; border-radius:3px;"></div></div>
                <span class="modal-iscore-dim-val">${d.value}/10</span>
              </div>
            `).join('')}
          </div>
          ${iscore.note ? `<p class="modal-iscore-note">${iscore.note}</p>` : ''}
        </div>
      `;
    })()}

    ${(() => {
      const patent = typeof PATENT_INTEL !== 'undefined' ? PATENT_INTEL.find(p => p.company === company.name) : null;
      if (!patent) return '';
      const moatColor = patent.ipMoatScore >= 8 ? '#22c55e' : patent.ipMoatScore >= 6 ? '#f59e0b' : '#6b7280';
      return `
        <div class="modal-patent">
          <h4>Patent Intelligence</h4>
          <div class="modal-patent-stats">
            <div><span class="modal-patent-val">${patent.totalPatents}</span><span class="modal-patent-lbl">Patents</span></div>
            <div><span class="modal-patent-val">${patent.velocity}</span><span class="modal-patent-lbl">Filing Rate</span></div>
            <div><span class="modal-patent-val" style="color:${moatColor};">${patent.ipMoatScore}/10</span><span class="modal-patent-lbl">IP Moat</span></div>
          </div>
          <div class="modal-patent-areas">${(patent.techAreas || []).map(t => `<span class="patent-tech-tag">${t}</span>`).join('')}</div>
        </div>
      `;
    })()}

    ${(() => {
      const alt = typeof ALT_DATA_SIGNALS !== 'undefined' ? ALT_DATA_SIGNALS.find(a => a.company === company.name) : null;
      if (!alt) return '';
      const hc = { surging: '#22c55e', growing: '#3b82f6', stable: '#f59e0b', declining: '#ef4444' };
      return `
        <div class="modal-altdata">
          <h4>Alternative Signals</h4>
          <div class="modal-altdata-grid">
            <div><span class="modal-altdata-lbl">Hiring</span><span style="color:${hc[alt.hiringVelocity] || '#6b7280'};">${(alt.hiringVelocity || '').toUpperCase()} (${alt.headcountEstimate})</span></div>
            <div><span class="modal-altdata-lbl">Traffic</span><span>${(alt.webTraffic || '').toUpperCase()}</span></div>
            <div><span class="modal-altdata-lbl">Sentiment</span><span>${(alt.newsSentiment || '').toUpperCase()}</span></div>
            <div><span class="modal-altdata-lbl">Signal</span><span>${alt.signalStrength}/10</span></div>
          </div>
          ${alt.keySignal ? `<p class="modal-altdata-signal">${alt.keySignal}</p>` : ''}
        </div>
      `;
    })()}

    <div class="modal-actions">
      ${company.rosLink ? `<a href="${company.rosLink}" target="_blank" rel="noopener" class="modal-action-btn primary">
        Read Coverage
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
      </a>` : ''}
      ${getCompanyWebsite(company.name) ? `<a href="${getCompanyWebsite(company.name)}" target="_blank" rel="noopener" class="modal-action-btn">
        🌐 Website
      </a>` : ''}
      <button class="modal-action-btn ${saved ? 'saved' : ''}" onclick="toggleBookmark('${company.name.replace(/'/g, "\\'")}'); openCompanyModal('${company.name.replace(/'/g, "\\'")}');">
        ${saved ? '★ Saved' : '☆ Save'}
      </button>
      <button class="modal-action-btn" onclick="shareCompany('${company.name.replace(/'/g, "\\'")}')">
        ↗ Share
      </button>
      <button class="modal-action-btn" onclick="generateOnePager('${company.name.replace(/'/g, "\\'")}')">
        📋 One-Pager
      </button>
    </div>

    ${competitors.length > 0 ? `
      <div class="modal-competitors">
        <h4>Competitive Landscape</h4>
        <div class="competitors-grid">
          ${competitors.map(r => `
            <span class="competitor-chip" onclick="openCompanyModal('${r.name.replace(/'/g, "\\'")}')">
              ${r.name}
            </span>
          `).join('')}
        </div>
      </div>
    ` : ''}

    ${related.length > 0 ? `
      <div class="modal-related">
        <h4>Related Companies</h4>
        <div class="modal-related-grid">
          ${related.map(r => `
            <div class="modal-related-card" onclick="openCompanyModal('${r.name.replace(/'/g, "\\'")}')">
              <span class="modal-related-name">${r.name}</span>
              <span class="modal-related-loc">${r.location}</span>
            </div>
          `).join('')}
        </div>
      </div>
    ` : ''}
  `;

  // Update URL
  const url = new URL(window.location);
  url.searchParams.set('company', company.name);
  window.history.pushState({}, '', url);

  openModal();
}

function shareCompany(companyName, btnEl) {
  const url = new URL(window.location.origin + window.location.pathname);
  url.searchParams.set('company', companyName);
  const shareUrl = url.toString();

  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareUrl).then(() => {
      // Find the share button specifically
      const btns = document.querySelectorAll('.modal-actions .modal-action-btn');
      let btn = null;
      btns.forEach(b => { if (b.textContent.includes('Share') || b.textContent.includes('Copied')) btn = b; });
      if (btn) {
        const original = btn.innerHTML;
        btn.innerHTML = '✓ Copied!';
        setTimeout(() => { btn.innerHTML = original; }, 1500);
      }
    });
  } else {
    // Fallback: select text via prompt
    prompt('Copy this link:', shareUrl);
  }
}

// ─── APP INITIALIZATION ───
document.addEventListener('DOMContentLoaded', () => {
  // Debug: Check if data loaded
  console.log('🔍 Data check:', {
    COMPANIES: typeof COMPANIES !== 'undefined' ? COMPANIES.length : 'undefined',
    SECTORS: typeof SECTORS !== 'undefined' ? Object.keys(SECTORS).length : 'undefined'
  });

  try {
    initStats();
  } catch (e) {
    console.error('initStats error:', e);
  }
  initMap();
  initFilters();
  initAIQuery();
  renderCompanies(COMPANIES);
  renderSectors();
  initSearch();
  initScrollAnimations();
  initMobileMenu();
  initModal();
  initCompare();
  initKeyboard();
  initFeatured();
  initMovementTracker();
  initWeeklyDigest();
  initAnomalyAlerts();
  initLeaderboard();
  initEfficiencyLeaderboard();
  initTRLDashboard();
  initDealTracker();
  initGrowthSignals();
  initMarketMap();
  initMafiaExplorer();
  initRevenueTable();
  initRequestForStartups();
  initNewsTicker();
  initInnovator50();
  initMarketPulse();
  initFundingTracker();
  initSectorMomentum();
  initIPOPipeline();
  initInnovatorScores();
  initGovContracts();
  initPatentIntel();
  initAltData();
  initAlertsCenter();
  initIntelligenceHub();
  initPredictiveScoring();
  initNetworkGraph();
  initPortfolioBuilder();
  initAIMemo();
  initIntelFeed();
  initSectorReports();
  initCommunityIntel();
  initURLState();
  initSmoothScroll();
  updateResultsCount(COMPANIES.length);

  // Initialize world-class premium features
  initPremiumFeatures();

  // PILLAR 1: Add section timestamps for data freshness visibility
  initSectionTimestamps();

  // PILLAR 3: Initialize From the Source section
  initFromTheSource();
});

// ─── STATS COUNTER ───
function initStats() {
  const companyCount = COMPANIES.length;
  const sectorCount = Object.keys(SECTORS).length;
  const countries = new Set(COMPANIES.map(c => getCountry(c.state, c.location)));
  const countryCount = countries.size;

  // Calculate total tracked funding
  let totalFunding = 0;
  COMPANIES.forEach(c => {
    if (c.totalRaised) {
      const match = c.totalRaised.match(/([\d.]+)\s*(B|M|K)?/i);
      if (match) {
        let val = parseFloat(match[1]);
        const unit = (match[2] || '').toUpperCase();
        if (unit === 'B') val *= 1000;
        else if (unit === 'K') val *= 0.001;
        // M is the base unit
        totalFunding += val;
      }
    }
  });

  animateCounter('company-count', companyCount);
  animateCounter('sector-count', sectorCount);
  animateCounter('country-count', countryCount);

  // Format funding as $XXB+
  const fundingEl = document.getElementById('funding-count');
  if (fundingEl) {
    const fundingB = (totalFunding / 1000).toFixed(0);
    animateCounterWithPrefix('funding-count', parseInt(fundingB), '$', 'B+');
  }

  // Last updated
  const updatedEl = document.getElementById('last-updated');
  if (updatedEl && typeof LAST_UPDATED !== 'undefined') {
    updatedEl.textContent = `Last updated: ${LAST_UPDATED}`;
  }

  // Data freshness indicator
  initFreshnessIndicator();
}

function initFreshnessIndicator() {
  const freshnessEl = document.getElementById('data-freshness');
  if (!freshnessEl || typeof LAST_UPDATED === 'undefined') return;

  const lastUpdate = new Date(LAST_UPDATED);
  const now = new Date();
  const diffHours = Math.floor((now - lastUpdate) / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  let status, color, icon;
  if (diffHours < 24) {
    status = 'Live Data';
    color = '#22c55e';
    icon = '●';
  } else if (diffHours < 72) {
    status = 'Fresh';
    color = '#3b82f6';
    icon = '●';
  } else if (diffDays < 7) {
    status = `${diffDays}d ago`;
    color = '#f59e0b';
    icon = '○';
  } else {
    status = 'Updating...';
    color = '#ef4444';
    icon = '○';
  }

  freshnessEl.innerHTML = `
    <span class="freshness-dot" style="color: ${color};">${icon}</span>
    <span class="freshness-status" style="color: ${color};">${status}</span>
  `;
  freshnessEl.title = `Data pipeline runs daily. Last update: ${LAST_UPDATED}`;

  // Add detailed data sources tooltip
  if (typeof DATA_SOURCES !== 'undefined') {
    const tooltip = Object.entries(DATA_SOURCES)
      .map(([key, data]) => `${key}: ${data.lastUpdated} (${data.frequency})`)
      .join('\n');
    freshnessEl.title = tooltip;
  }
}

// Display section-specific timestamps
function addSectionTimestamp(sectionId, dataSourceKey) {
  if (typeof DATA_SOURCES === 'undefined') return;
  const section = document.getElementById(sectionId);
  if (!section) return;

  const source = DATA_SOURCES[dataSourceKey];
  if (!source) return;

  const header = section.querySelector('.section-header');
  if (!header) return;

  // Check if timestamp already exists
  if (header.querySelector('.section-timestamp')) return;

  const timestamp = document.createElement('div');
  timestamp.className = 'section-timestamp';
  timestamp.innerHTML = `<span class="timestamp-dot">●</span> Updated ${source.lastUpdated} · ${source.frequency}`;
  header.appendChild(timestamp);
}

// Initialize all section timestamps for data freshness visibility
function initSectionTimestamps() {
  // Map section IDs to their data source keys
  // These show when each type of data was last refreshed
  const sectionMappings = {
    // News & Signals (RSS feeds, every 4 hours)
    'intelligence-hub': 'news',
    'market-pulse': 'news',

    // Government & Regulatory (Daily automated updates)
    'gov-contracts': 'govContracts',
    'patent-intel': 'patents',

    // Funding & Deals (Daily from press releases)
    'funding-tracker': 'fundingRounds',
    'deal-tracker': 'fundingRounds',

    // Company Database (Daily + Manual enrichment)
    'companies': 'companies',
    'leaderboard': 'companies',
    'innovator-scores': 'companies'
  };

  // Apply timestamps to each section that has a .section-header
  Object.entries(sectionMappings).forEach(([sectionId, dataSourceKey]) => {
    addSectionTimestamp(sectionId, dataSourceKey);
  });

  console.log('📊 Section timestamps initialized for', Object.keys(sectionMappings).length, 'sections');
}

// ═══════════════════════════════════════════════════════
// PILLAR 3: FROM THE SOURCE — Founder Insights
// ═══════════════════════════════════════════════════════
function initFromTheSource() {
  if (typeof FROM_THE_SOURCE === 'undefined') {
    console.log('📝 FROM_THE_SOURCE data not found');
    return;
  }

  const grid = document.getElementById('from-source-grid');
  if (!grid) return;

  const typeLabels = {
    interview: '🎙️ Interview',
    insight: '💡 Insight',
    tripReport: '✈️ Trip Report'
  };

  const cards = FROM_THE_SOURCE.map(item => {
    const typeLabel = typeLabels[item.type] || '📄 Article';
    const premiumClass = item.premium ? 'premium' : '';

    return `
      <div class="from-source-card ${premiumClass}" onclick="openCompanyModal('${item.company.replace(/'/g, "\\'")}')">
        <div class="from-source-type ${item.type}">${typeLabel}</div>
        <h3 class="from-source-headline">${item.headline}</h3>
        <div class="from-source-founder">
          <span>${item.founder}, ${item.title}</span>
          <span>•</span>
          <span class="company">${item.company}</span>
        </div>
        <p class="from-source-summary">${item.summary}</p>
        ${item.pullQuote ? `<div class="from-source-quote">${item.pullQuote}</div>` : ''}
        <div class="from-source-topics">
          ${item.topics.map(t => `<span class="from-source-topic">${t}</span>`).join('')}
        </div>
        <div class="from-source-date">${item.date}</div>
      </div>
    `;
  }).join('');

  grid.innerHTML = cards;
  console.log('🎙️ From the Source initialized with', FROM_THE_SOURCE.length, 'items');
}

// Get founder connection data for a company
function getFounderConnection(companyName) {
  if (typeof FOUNDER_CONNECTIONS === 'undefined') return null;
  return FOUNDER_CONNECTIONS[companyName] || null;
}

// Render founder connection badge for company modals
function renderFounderConnectionBadge(companyName) {
  const connection = getFounderConnection(companyName);
  if (!connection) return '';

  if (connection.metFounder) {
    return `
      <div class="founder-connection-badge met">
        <span class="connection-icon">🤝</span>
        <span>ROS has met with this founder</span>
      </div>
    `;
  }

  return '';
}

// Render exclusive founder quote for company modals
function renderFounderQuote(companyName) {
  const connection = getFounderConnection(companyName);
  if (!connection || !connection.exclusiveQuote) return '';

  return `
    <div class="founder-exclusive-quote">
      <div class="quote-label">💎 Exclusive Quote</div>
      <div class="quote-text">"${connection.exclusiveQuote}"</div>
    </div>
  `;
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = target / (duration / 16);

  function tick() {
    current += step;
    if (current >= target) {
      el.textContent = target;
      return;
    }
    el.textContent = Math.floor(current);
    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      tick();
      observer.disconnect();
    }
  });
  observer.observe(el);
}

function animateCounterWithPrefix(id, target, prefix, suffix) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = target / (duration / 16);

  function tick() {
    current += step;
    if (current >= target) {
      el.textContent = prefix + target + suffix;
      return;
    }
    el.textContent = prefix + Math.floor(current) + suffix;
    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      tick();
      observer.disconnect();
    }
  });
  observer.observe(el);
}

// ─── MAP ───
function initMap() {
  const map = L.map('innovators-map', {
    center: [25, 0],
    zoom: 2,
    minZoom: 2,
    maxZoom: 12,
    scrollWheelZoom: true,
    zoomControl: true
  });

  // Dark tile layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19
  }).addTo(map);

  COMPANIES.forEach(company => {
    if (!company.lat || !company.lng) return;

    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };

    const markerHtml = `<div class="custom-marker" style="background:${sectorInfo.color};">
      <span class="marker-icon">${sectorInfo.icon}</span>
    </div>`;

    const icon = L.divIcon({
      html: markerHtml,
      className: 'marker-container',
      iconSize: [28, 28],
      iconAnchor: [14, 14]
    });

    const marker = L.marker([company.lat, company.lng], { icon });

    const popupContent = `
      <div class="map-popup">
        <div class="popup-sector" style="color:${sectorInfo.color}">${sectorInfo.icon} ${company.sector}</div>
        <h3>${company.name}</h3>
        ${company.founder ? `<p class="popup-founder">${company.founder}</p>` : ''}
        <p class="popup-location">${company.location}</p>
        <p class="popup-desc">${company.description.substring(0, 140)}...</p>
        <button class="popup-link" onclick="openCompanyModal('${company.name.replace(/'/g, "\\'")}')">View Details &rarr;</button>
      </div>
    `;

    marker.bindPopup(popupContent, { maxWidth: 300 });
    marker.addTo(map);
  });
}

// ─── FILTERS ───
function initFilters() {
  // Sector chips
  const chipContainer = document.getElementById('filter-chips');
  const sectors = Object.keys(SECTORS);

  sectors.forEach(sector => {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.dataset.sector = sector;
    chip.textContent = sector;
    chipContainer.appendChild(chip);
  });

  chipContainer.addEventListener('click', (e) => {
    if (!e.target.classList.contains('chip')) return;

    chipContainer.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    e.target.classList.add('active');

    // Sync dropdown
    const sectorFilter = document.getElementById('sector-filter');
    sectorFilter.value = e.target.dataset.sector;

    applyFilters();
  });

  // Sector dropdown
  const sectorFilter = document.getElementById('sector-filter');
  sectors.forEach(sector => {
    const opt = document.createElement('option');
    opt.value = sector;
    opt.textContent = sector;
    sectorFilter.appendChild(opt);
  });

  sectorFilter.addEventListener('change', () => {
    // Sync chips
    const chipContainer = document.getElementById('filter-chips');
    chipContainer.querySelectorAll('.chip').forEach(c => {
      c.classList.toggle('active', c.dataset.sector === sectorFilter.value);
    });
    applyFilters();
  });

  // Country dropdown
  const countryFilter = document.getElementById('country-filter');
  const countriesSet = new Set(COMPANIES.map(c => getCountry(c.state, c.location)));
  const countriesSorted = [...countriesSet].sort();
  countriesSorted.forEach(country => {
    const opt = document.createElement('option');
    opt.value = country;
    opt.textContent = country;
    countryFilter.appendChild(opt);
  });
  countryFilter.addEventListener('change', () => {
    updateStateFilterVisibility();
    applyFilters();
  });

  // State dropdown (US only)
  const stateFilter = document.getElementById('state-filter');
  const usStatesInData = new Set();
  COMPANIES.forEach(c => {
    if (US_STATES.has(c.state) && getCountry(c.state, c.location) === 'United States') {
      usStatesInData.add(c.state);
    }
  });
  const sortedStates = [...usStatesInData].sort((a, b) =>
    (STATE_NAMES[a] || a).localeCompare(STATE_NAMES[b] || b)
  );
  sortedStates.forEach(code => {
    const opt = document.createElement('option');
    opt.value = code;
    opt.textContent = STATE_NAMES[code] || code;
    stateFilter.appendChild(opt);
  });
  stateFilter.addEventListener('change', applyFilters);
  updateStateFilterVisibility();

  // Stage dropdown
  const stageFilter = document.getElementById('stage-filter');
  const stages = [...new Set(COMPANIES.map(c => c.fundingStage).filter(Boolean))].sort();
  stages.forEach(stage => {
    const opt = document.createElement('option');
    opt.value = stage;
    opt.textContent = stage;
    stageFilter.appendChild(opt);
  });
  stageFilter.addEventListener('change', applyFilters);

  // Sort dropdown
  document.getElementById('sort-filter').addEventListener('change', applyFilters);
}

function applyFilters() {
  const sector = document.getElementById('sector-filter').value;
  const country = document.getElementById('country-filter').value;
  const stateCode = document.getElementById('state-filter')?.value;
  const stage = document.getElementById('stage-filter').value;
  const sortBy = document.getElementById('sort-filter').value;
  const searchTerm = document.getElementById('search-input').value.toLowerCase();

  let filtered = COMPANIES;

  if (sector && sector !== 'all') {
    filtered = filtered.filter(c => c.sector === sector);
  }

  if (country && country !== 'all') {
    filtered = filtered.filter(c => getCountry(c.state, c.location) === country);
  }

  if (stateCode && stateCode !== 'all') {
    filtered = filtered.filter(c =>
      c.state === stateCode && getCountry(c.state, c.location) === 'United States'
    );
  }

  if (stage && stage !== 'all') {
    filtered = filtered.filter(c => c.fundingStage === stage);
  }

  if (searchTerm) {
    filtered = filtered.filter(c =>
      c.name.toLowerCase().includes(searchTerm) ||
      c.description.toLowerCase().includes(searchTerm) ||
      (c.founder && c.founder.toLowerCase().includes(searchTerm)) ||
      c.location.toLowerCase().includes(searchTerm) ||
      c.sector.toLowerCase().includes(searchTerm) ||
      c.tags.some(t => t.toLowerCase().includes(searchTerm)) ||
      getCountry(c.state, c.location).toLowerCase().includes(searchTerm)
    );
  }

  // Sort
  filtered = [...filtered];
  if (sortBy === 'name') {
    filtered.sort((a, b) => a.name.localeCompare(b.name));
  } else if (sortBy === 'name-desc') {
    filtered.sort((a, b) => b.name.localeCompare(a.name));
  } else if (sortBy === 'sector') {
    filtered.sort((a, b) => a.sector.localeCompare(b.sector) || a.name.localeCompare(b.name));
  } else if (sortBy === 'saved') {
    filtered.sort((a, b) => {
      const aS = isBookmarked(a.name) ? 0 : 1;
      const bS = isBookmarked(b.name) ? 0 : 1;
      return aS - bS || a.name.localeCompare(b.name);
    });
  } else if (sortBy === 'signal') {
    filtered.sort((a, b) => {
      const aP = a.signal ? (SIGNAL_PRIORITY[a.signal] ?? 99) : 99;
      const bP = b.signal ? (SIGNAL_PRIORITY[b.signal] ?? 99) : 99;
      return aP - bP || a.name.localeCompare(b.name);
    });
  } else if (sortBy === 'score') {
    filtered.sort((a, b) => {
      const avg = s => {
        if (!s) return 0;
        const vals = [s.team, s.traction, s.techMoat, s.market, s.momentum].filter(v => v != null);
        return vals.length ? vals.reduce((sum, v) => sum + v, 0) / vals.length : 0;
      };
      return avg(b.scores) - avg(a.scores) || a.name.localeCompare(b.name);
    });
  } else if (sortBy === 'recent') {
    filtered.sort((a, b) => {
      const dA = a.recentEvent ? a.recentEvent.date : '0000-00';
      const dB = b.recentEvent ? b.recentEvent.date : '0000-00';
      return dB.localeCompare(dA) || a.name.localeCompare(b.name);
    });
  }

  renderCompanies(filtered);
  updateResultsCount(filtered.length);

  // Update URL with filter state
  const url = new URL(window.location);
  if (sector && sector !== 'all') url.searchParams.set('sector', sector);
  else url.searchParams.delete('sector');
  if (country && country !== 'all') url.searchParams.set('country', country);
  else url.searchParams.delete('country');
  if (stateCode && stateCode !== 'all') url.searchParams.set('state', stateCode);
  else url.searchParams.delete('state');
  if (searchTerm) url.searchParams.set('q', searchTerm);
  else url.searchParams.delete('q');
  url.searchParams.delete('company');
  window.history.replaceState({}, '', url);

  const noResults = document.getElementById('no-results');
  noResults.style.display = filtered.length === 0 ? 'block' : 'none';
}

function updateResultsCount(count) {
  const el = document.getElementById('results-count');
  if (el) {
    el.textContent = `Showing ${count} ${count === 1 ? 'company' : 'companies'}`;
  }
}

function updateStateFilterVisibility() {
  const countryFilter = document.getElementById('country-filter');
  const stateFilterContainer = document.getElementById('state-filter-container');
  const stateFilter = document.getElementById('state-filter');
  const selectedCountry = countryFilter?.value;

  if (stateFilterContainer) {
    if (selectedCountry === 'all' || selectedCountry === 'United States') {
      stateFilterContainer.style.display = 'block';
    } else {
      stateFilterContainer.style.display = 'none';
      if (stateFilter) stateFilter.value = 'all';
    }
  }
}

// ─── SEARCH ───
function initSearch() {
  const input = document.getElementById('search-input');
  let debounce;

  input.addEventListener('input', () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      applyFilters();
    }, 200);
  });
}

// ─── RENDER COMPANIES ───
function renderCompanies(companies) {
  const grid = document.getElementById('company-grid');
  grid.innerHTML = '';

  companies.forEach((company, i) => {
    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };
    const saved = isBookmarked(company.name);
    const inCompare = compareList.includes(company.name);

    const card = document.createElement('div');
    card.className = 'company-card';
    card.style.animationDelay = `${i * 0.02}s`;

    const metaItems = [];
    if (company.fundingStage) metaItems.push(`<span class="meta-stage">${company.fundingStage}</span>`);
    if (company.totalRaised) metaItems.push(`<span class="meta-raised">${company.totalRaised}</span>`);
    if (company.valuation) metaItems.push(`<span class="meta-val">${company.valuation}</span>`);

    card.innerHTML = `
      <div class="card-header">
        <div class="card-sector-badge" style="background:${sectorInfo.color}12; color:${sectorInfo.color}; border: 1px solid ${sectorInfo.color}30;">
          ${sectorInfo.icon} ${company.sector}
        </div>
        <div class="card-actions-top">
          <button class="card-bookmark ${saved ? 'active' : ''}" onclick="event.stopPropagation(); toggleBookmark('${company.name.replace(/'/g, "\\'")}'); applyFilters();" title="Save">
            ${saved ? '★' : '☆'}
          </button>
          <button class="card-compare ${inCompare ? 'active' : ''}" onclick="event.stopPropagation(); toggleCompare('${company.name.replace(/'/g, "\\'")}');" title="Compare">
            ⇔
          </button>
        </div>
      </div>
      <h3 class="card-name">${company.name}</h3>
      ${(() => {
        const iscore = getInnovatorScore(company.name);
        const hasBadges = company.signal || company.scores || iscore;
        if (!hasBadges) return '';
        const iscoreBadge = iscore ? (() => {
          const tc = { elite: '#22c55e', strong: '#3b82f6', promising: '#f59e0b', early: '#6b7280' }[iscore.tier];
          return `<span class="iscore-card-badge" style="background:${tc}15; color:${tc}; border:1px solid ${tc}30;">${iscore.composite.toFixed(0)} IS™</span>`;
        })() : '';
        return `<div class="card-badges">${iscoreBadge}${renderSignalBadge(company.signal)}${renderScoreBadge(company.scores)}</div>`;
      })()}
      ${company.founder ? `<p class="card-founder">${company.founder}</p>` : ''}
      <p class="card-location">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        ${company.location}
      </p>
      ${metaItems.length ? `<div class="card-meta">${metaItems.join('')}</div>` : ''}
      <p class="card-description">${company.description}</p>
      <div class="card-tags">
        ${company.tags.slice(0, 3).map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
      <div class="card-footer">
        ${company.rosLink ? `<a href="${company.rosLink}" target="_blank" rel="noopener" class="card-link" onclick="event.stopPropagation();">
          Read Coverage <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
        </a>` : ''}
        ${getCompanyWebsite(company.name) ? `<a href="${getCompanyWebsite(company.name)}" target="_blank" rel="noopener" class="card-link card-link-website" onclick="event.stopPropagation();">
          Website <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        </a>` : ''}
      </div>
    `;

    // Click card to open modal
    card.addEventListener('click', () => {
      openCompanyModal(company.name);
    });
    card.style.cursor = 'pointer';

    grid.appendChild(card);
  });
}

// ─── RENDER SECTORS ───
function renderSectors() {
  const grid = document.getElementById('sectors-grid');

  Object.entries(SECTORS).forEach(([name, info]) => {
    const count = COMPANIES.filter(c => c.sector === name).length;
    const card = document.createElement('div');
    card.className = 'sector-card';

    card.innerHTML = `
      <div class="sector-icon">${info.icon}</div>
      <h3>${name}</h3>
      <p>${info.description}</p>
      ${info.trend ? `<p style="font-size: 12px; color: var(--accent); margin-top: 8px; line-height: 1.5; font-style: italic;">${info.trend}</p>` : ''}
      <div class="sector-count">${count} ${count === 1 ? 'company' : 'companies'}</div>
    `;

    card.addEventListener('click', () => {
      document.getElementById('companies').scrollIntoView({ behavior: 'smooth' });
      setTimeout(() => {
        document.getElementById('sector-filter').value = name;
        const chips = document.querySelectorAll('.chip');
        chips.forEach(c => {
          c.classList.remove('active');
          if (c.dataset.sector === name) c.classList.add('active');
        });
        applyFilters();
      }, 400);
    });

    grid.appendChild(card);
  });
}

// ─── FEATURED INNOVATORS ───
function initFeatured() {
  const scroll = document.getElementById('featured-scroll');
  if (!scroll) return;

  // Pick highest-valued companies
  const featured = COMPANIES
    .filter(c => c.valuation)
    .sort((a, b) => {
      const parseVal = v => {
        const m = v.match(/([\d.]+)\s*(B|M|T)?/i);
        if (!m) return 0;
        let val = parseFloat(m[1]);
        const unit = (m[2] || '').toUpperCase();
        if (unit === 'T') val *= 1000;
        else if (unit === 'M') val *= 0.001;
        return val;
      };
      return parseVal(b.valuation) - parseVal(a.valuation);
    })
    .slice(0, 12);

  featured.forEach(company => {
    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };

    const card = document.createElement('div');
    card.className = 'featured-card';

    card.innerHTML = `
      <div class="featured-card-accent" style="background: ${sectorInfo.color};"></div>
      <div class="featured-card-body">
        <span class="featured-sector" style="color: ${sectorInfo.color};">${sectorInfo.icon} ${company.sector}</span>
        <h3 class="featured-name">${company.name}</h3>
        ${company.valuation ? `<span class="featured-val">${company.valuation}</span>` : ''}
        <p class="featured-loc">${company.location}</p>
      </div>
    `;

    card.addEventListener('click', () => openCompanyModal(company.name));
    card.style.cursor = 'pointer';
    scroll.appendChild(card);
  });
}

// ─── MODAL INIT ───
function initModal() {
  const overlay = document.getElementById('modal-overlay');
  const closeBtn = document.getElementById('modal-close');

  closeBtn.addEventListener('click', () => {
    closeModal();
    // Remove company from URL
    const url = new URL(window.location);
    url.searchParams.delete('company');
    window.history.pushState({}, '', url);
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      closeModal();
      const url = new URL(window.location);
      url.searchParams.delete('company');
      window.history.pushState({}, '', url);
    }
  });
}

// ─── COMPARE INIT ───
function initCompare() {
  document.getElementById('compare-btn').addEventListener('click', openCompareView);
  document.getElementById('compare-clear').addEventListener('click', () => {
    compareList = [];
    updateCompareBar();
    applyFilters();
  });
}

// ─── KEYBOARD NAVIGATION ───
function initKeyboard() {
  document.addEventListener('keydown', (e) => {
    // / to focus search
    if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
      const active = document.activeElement;
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        e.preventDefault();
        document.getElementById('search-input').focus();
      }
    }

    // Escape to close modal
    if (e.key === 'Escape') {
      const overlay = document.getElementById('modal-overlay');
      if (overlay.classList.contains('active')) {
        closeModal();
        const url = new URL(window.location);
        url.searchParams.delete('company');
        window.history.pushState({}, '', url);
      }
    }

    // b to bookmark in modal
    if (e.key === 'b' && !e.ctrlKey && !e.metaKey) {
      const active = document.activeElement;
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        const overlay = document.getElementById('modal-overlay');
        if (overlay.classList.contains('active')) {
          const nameEl = document.querySelector('.modal-company-name');
          if (nameEl) {
            // Get only the direct text, not signal badge text
            const companyName = nameEl.childNodes[0].textContent.trim();
            toggleBookmark(companyName);
            openCompanyModal(companyName); // refresh modal
          }
        }
      }
    }
  });
}

// ─── URL STATE ───
function initURLState() {
  const params = new URLSearchParams(window.location.search);

  // Open company modal if ?company= present
  const companyParam = params.get('company');
  if (companyParam) {
    setTimeout(() => openCompanyModal(companyParam), 500);
  }

  // Apply filters from URL
  const sectorParam = params.get('sector');
  if (sectorParam) {
    document.getElementById('sector-filter').value = sectorParam;
    const chips = document.querySelectorAll('.chip');
    chips.forEach(c => {
      c.classList.remove('active');
      if (c.dataset.sector === sectorParam) c.classList.add('active');
    });
  }

  const countryParam = params.get('country');
  if (countryParam) {
    document.getElementById('country-filter').value = countryParam;
  }

  const qParam = params.get('q');
  if (qParam) {
    document.getElementById('search-input').value = qParam;
  }

  if (sectorParam || countryParam || qParam) {
    setTimeout(() => applyFilters(), 100);
  }
}

// ─── SCROLL ANIMATIONS ───
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.section-header, .sector-card, .featured-section').forEach(el => {
    observer.observe(el);
  });

  // Re-observe dynamically added sector cards
  const gridObserver = new MutationObserver(() => {
    document.querySelectorAll('.sector-card:not(.observed)').forEach(el => {
      el.classList.add('observed');
      observer.observe(el);
    });
  });

  const sectorsGrid = document.getElementById('sectors-grid');
  if (sectorsGrid) {
    gridObserver.observe(sectorsGrid, { childList: true });
  }
}

// ─── MOBILE MENU ───
function initMobileMenu() {
  const btn = document.querySelector('.mobile-menu-btn');
  const links = document.querySelector('.nav-links');

  btn.addEventListener('click', () => {
    links.classList.toggle('open');
    btn.classList.toggle('open');
  });

  links.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      links.classList.remove('open');
      btn.classList.remove('open');
    });
  });
}

// ─── MOVEMENT TRACKER ───
function initMovementTracker() {
  const grid = document.getElementById('movement-grid');
  if (!grid) return;

  const companiesWithEvents = COMPANIES
    .filter(c => c.recentEvent)
    .sort((a, b) => b.recentEvent.date.localeCompare(a.recentEvent.date));

  function renderMovements(type) {
    const filtered = type === 'all'
      ? companiesWithEvents
      : companiesWithEvents.filter(c => c.recentEvent.type === type);

    grid.innerHTML = filtered.slice(0, 15).map(c => {
      const evType = c.recentEvent.type;
      return `
        <div class="movement-item" onclick="openCompanyModal('${c.name.replace(/'/g, "\\'")}')">
          <span class="movement-type movement-type-${evType}">${evType}</span>
          <div class="movement-info">
            <div class="movement-company">${c.name} ${renderSignalBadge(c.signal)}</div>
            <div class="movement-text">${c.recentEvent.text}</div>
          </div>
          <span class="movement-date">${c.recentEvent.date}</span>
        </div>
      `;
    }).join('');

    if (filtered.length === 0) {
      grid.innerHTML = '<p style="color: var(--text-muted); padding: 20px;">No events in this category yet.</p>';
    }
  }

  renderMovements('all');

  // Tab handling
  document.querySelectorAll('.movement-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.movement-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderMovements(tab.dataset.type);
    });
  });
}

// ─── WEEKLY DIGEST ───
function initWeeklyDigest() {
  const scroll = document.getElementById('digest-scroll');
  if (!scroll || typeof WEEKLY_DIGEST === 'undefined') return;

  WEEKLY_DIGEST.forEach(item => {
    const card = document.createElement('div');
    card.className = 'digest-card';

    const catClass = `digest-category-${item.category}`;

    card.innerHTML = `
      <div>
        <span class="digest-date">${item.date}</span>
        <span class="digest-category ${catClass}">${item.category}</span>
      </div>
      <h3 class="digest-headline">${item.headline}</h3>
      <p class="digest-summary">${item.summary}</p>
      <div class="digest-companies">
        ${item.relatedCompanies.map(name => {
          const exists = COMPANIES.find(c => c.name === name);
          return exists
            ? `<span class="portfolio-chip linked small" onclick="openCompanyModal('${name.replace(/'/g, "\\'")}')">${name}</span>`
            : `<span class="portfolio-chip small">${name}</span>`;
        }).join('')}
      </div>
    `;

    scroll.appendChild(card);
  });
}

// ─── EXPORT WATCHLIST CSV ───
function exportWatchlistCSV() {
  const savedCompanies = COMPANIES.filter(c => isBookmarked(c.name));
  if (savedCompanies.length === 0) {
    alert('No companies saved to watchlist. Save companies first using the ☆ button.');
    return;
  }

  const headers = ['Name', 'Sector', 'Location', 'Country', 'Stage', 'Total Raised', 'Valuation', 'Founder', 'Signal', 'Score', 'Description'];
  const rows = savedCompanies.map(c => {
    const country = getCountry(c.state, c.location);
    const avg = getAverageScore(c.scores);
    return [
      c.name,
      c.sector,
      c.location,
      country,
      c.fundingStage || '',
      c.totalRaised || '',
      c.valuation || '',
      c.founder || '',
      c.signal || '',
      avg > 0 ? avg.toFixed(1) : '',
      `"${(c.description || '').replace(/"/g, '""')}"`
    ].join(',');
  });

  const csv = [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `innovators-league-watchlist-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─── VALUATION LEADERBOARD ───
function parseValuation(val) {
  if (!val) return 0;
  // Extract number and unit (B/M/T) that appears immediately after
  const match = val.match(/\$?([\d,.]+)\s*([BMTbmt])/);
  if (!match) return 0;
  const num = parseFloat(match[1].replace(/,/g, ''));
  if (isNaN(num)) return 0;
  const unit = match[2].toUpperCase();
  if (unit === 'T') return num * 1000000000000;
  if (unit === 'B') return num * 1000000000;
  if (unit === 'M') return num * 1000000;
  return num;
}

function parseFunding(val) {
  if (!val) return 0;
  // Extract number and unit (B/M/T) that appears immediately after
  const match = val.match(/\$?([\d,.]+)\s*([BMTbmt])/);
  if (!match) return 0;
  const num = parseFloat(match[1].replace(/,/g, ''));
  if (isNaN(num)) return 0;
  const unit = match[2].toUpperCase();
  if (unit === 'T') return num * 1000000000000;
  if (unit === 'B') return num * 1000000000;
  if (unit === 'M') return num * 1000000;
  return num;
}

function formatValuation(num) {
  if (num >= 1000000000000) return `$${(num / 1000000000000).toFixed(1)}T`;
  if (num >= 1000000000) return `$${(num / 1000000000).toFixed(1)}B`;
  if (num >= 1000000) return `$${(num / 1000000).toFixed(0)}M`;
  return '';
}

function initLeaderboard() {
  const grid = document.getElementById('leaderboard-grid');
  if (!grid) return;

  // Populate sector dropdown
  const sectorSelect = document.getElementById('lb-sector');
  if (sectorSelect) {
    const sectors = [...new Set(COMPANIES.map(c => c.sector))].sort();
    sectors.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      sectorSelect.appendChild(opt);
    });
  }

  function renderLeaderboard() {
    grid.innerHTML = '';
    const sortBy = document.getElementById('lb-sort')?.value || 'valuation';
    const stage = document.getElementById('lb-stage')?.value || 'all';
    const sector = document.getElementById('lb-sector')?.value || 'all';
    const countVal = document.getElementById('lb-count')?.value || '25';

    // Filter
    let filtered = COMPANIES.filter(c => {
      if (stage === 'private') return c.fundingStage !== 'Public' && !c.fundingStage?.includes('Alphabet');
      if (stage === 'public') return c.fundingStage === 'Public' || c.fundingStage?.includes('Alphabet');
      if (stage === 'pre-ipo') return c.fundingStage === 'Pre-IPO' || c.fundingStage === 'Late Stage';
      return true;
    }).filter(c => {
      if (sector !== 'all') return c.sector === sector;
      return true;
    });

    // Sort
    filtered = filtered.map(c => ({
      ...c,
      _val: parseValuation(c.valuation),
      _raised: parseFunding(c.totalRaised),
      _score: c.scores ? getAverageScore(c.scores) : 0
    }));

    if (sortBy === 'valuation') {
      filtered.sort((a, b) => b._val - a._val);
      filtered = filtered.filter(c => c._val > 0);
    } else if (sortBy === 'score') {
      filtered.sort((a, b) => b._score - a._score);
      filtered = filtered.filter(c => c._score > 0);
    } else if (sortBy === 'funding') {
      filtered.sort((a, b) => b._raised - a._raised);
      filtered = filtered.filter(c => c._raised > 0);
    } else {
      filtered.sort((a, b) => a.name.localeCompare(b.name));
    }

    const totalCount = filtered.length;
    const maxCount = countVal === 'all' ? filtered.length : parseInt(countVal);
    filtered = filtered.slice(0, maxCount);

    // Stats
    const statsEl = document.getElementById('lb-stats');
    if (statsEl) {
      const totalVal = filtered.reduce((sum, c) => sum + c._val, 0);
      const totalRaised = filtered.reduce((sum, c) => sum + c._raised, 0);
      statsEl.innerHTML = `
        <span class="lb-stat"><strong>${filtered.length}</strong> of ${totalCount} companies</span>
        <span class="lb-stat">Combined Value: <strong>${formatValuation(totalVal)}</strong></span>
        <span class="lb-stat">Total Raised: <strong>${formatValuation(totalRaised)}</strong></span>
      `;
    }

    // Find max value for bar scaling
    const maxVal = filtered.length > 0 ? filtered[0]._val : 1;

    filtered.forEach((c, i) => {
      const rank = i + 1;
      const rankClass = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : 'normal';
      const rankSymbol = rank <= 3 ? ['🥇','🥈','🥉'][rank - 1] : `#${rank}`;
      const sectorInfo = SECTORS[c.sector] || { icon: '📦', color: '#6b7280' };
      const signalBadge = c.signal ? renderSignalBadge(c.signal) : '';
      const scoreBadge = c._score > 0 ? `<span class="lb-score-badge">${c._score.toFixed(1)}</span>` : '';
      const barWidth = sortBy === 'valuation' ? (maxVal > 0 ? (c._val / maxVal * 100) : 0) :
                       sortBy === 'score' ? (c._score * 10) :
                       sortBy === 'funding' ? (filtered[0]._raised > 0 ? (c._raised / filtered[0]._raised * 100) : 0) : 50;

      const valDisplay = c.valuation || '—';
      const raisedDisplay = c.totalRaised || '—';
      const stageDisplay = c.fundingStage || '';

      const row = document.createElement('div');
      row.className = 'leaderboard-row';
      row.innerHTML = `
        <div class="leaderboard-rank ${rankClass}">${rankSymbol}</div>
        <div class="leaderboard-company">
          <span class="leaderboard-name">${c.name} ${signalBadge} ${scoreBadge}</span>
          <span class="leaderboard-sector">${sectorInfo.icon} ${c.sector}</span>
        </div>
        <div class="leaderboard-valuation">${valDisplay}</div>
        <div class="leaderboard-bar">
          <div class="leaderboard-bar-fill" style="width: 0%"></div>
        </div>
        <div class="leaderboard-raised">${raisedDisplay}</div>
        <div class="leaderboard-stage">${stageDisplay}</div>
      `;

      row.addEventListener('click', () => openCompanyModal(c.name));
      grid.appendChild(row);

      // Animate bar
      setTimeout(() => {
        row.querySelector('.leaderboard-bar-fill').style.width = `${barWidth}%`;
      }, 80 + i * 40);
    });
  }

  // Attach event listeners
  ['lb-sort', 'lb-stage', 'lb-sector', 'lb-count'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', renderLeaderboard);
  });

  // Ranking tab switching
  const rankingTabs = document.querySelectorAll('.ranking-tab');
  const valuationView = document.getElementById('valuation-view');
  const efficiencyView = document.getElementById('efficiency-view');

  rankingTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      rankingTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const ranking = tab.dataset.ranking;
      if (ranking === 'valuation') {
        if (valuationView) valuationView.style.display = 'block';
        if (efficiencyView) efficiencyView.style.display = 'none';
      } else {
        if (valuationView) valuationView.style.display = 'none';
        if (efficiencyView) efficiencyView.style.display = 'block';
      }
    });
  });

  renderLeaderboard();
}

// ─── CAPITAL EFFICIENCY LEADERBOARD ───
function initEfficiencyLeaderboard() {
  const grid = document.getElementById('efficiency-grid');
  if (!grid) return;

  // Populate sector dropdown
  const sectorSelect = document.getElementById('eff-sector');
  if (sectorSelect) {
    const sectors = [...new Set(COMPANIES.map(c => c.sector))].sort();
    sectors.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      sectorSelect.appendChild(opt);
    });
  }

  function renderEfficiencyLeaderboard() {
    grid.innerHTML = '';
    const sector = document.getElementById('eff-sector')?.value || 'all';
    const countVal = document.getElementById('eff-count')?.value || '25';

    // Filter companies with both valuation and funding data
    let filtered = COMPANIES.filter(c => {
      const val = parseValuation(c.valuation);
      const raised = parseFunding(c.totalRaised);
      return val > 0 && raised > 0;
    });

    // Sector filter
    if (sector !== 'all') {
      filtered = filtered.filter(c => c.sector === sector);
    }

    // Calculate efficiency metrics
    filtered = filtered.map(c => {
      const val = parseValuation(c.valuation);
      const raised = parseFunding(c.totalRaised);
      const efficiency = raised > 0 ? val / raised : 0;
      return {
        ...c,
        _val: val,
        _raised: raised,
        _efficiency: efficiency
      };
    });

    // Sort by efficiency (valuation to funding ratio)
    filtered.sort((a, b) => b._efficiency - a._efficiency);

    const totalCount = filtered.length;
    const maxCount = countVal === 'all' ? filtered.length : parseInt(countVal);
    filtered = filtered.slice(0, maxCount);

    // Find max efficiency for bar scaling
    const maxEfficiency = filtered.length > 0 ? filtered[0]._efficiency : 1;

    filtered.forEach((c, i) => {
      const rank = i + 1;
      const rankClass = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : 'normal';
      const rankSymbol = rank <= 3 ? ['🥇','🥈','🥉'][rank - 1] : `#${rank}`;
      const sectorInfo = SECTORS[c.sector] || { icon: '📦', color: '#6b7280' };
      const barWidth = maxEfficiency > 0 ? (c._efficiency / maxEfficiency * 100) : 0;

      const row = document.createElement('div');
      row.className = 'efficiency-row';
      row.innerHTML = `
        <div class="leaderboard-rank ${rankClass}">${rankSymbol}</div>
        <div class="leaderboard-company">
          <span class="leaderboard-name">${c.name}</span>
          <span class="leaderboard-sector">${sectorInfo.icon} ${c.sector}</span>
        </div>
        <div class="efficiency-multiple">
          <span class="efficiency-value">${c._efficiency.toFixed(1)}x</span>
        </div>
        <div class="leaderboard-bar">
          <div class="leaderboard-bar-fill efficiency-bar" style="width: 0%"></div>
        </div>
        <div class="efficiency-details">
          <span class="eff-val">${formatValuation(c._val)}</span>
          <span class="eff-divider">÷</span>
          <span class="eff-raised">${formatValuation(c._raised)}</span>
        </div>
      `;

      row.addEventListener('click', () => openCompanyModal(c.name));
      grid.appendChild(row);

      // Animate bar
      setTimeout(() => {
        row.querySelector('.leaderboard-bar-fill').style.width = `${barWidth}%`;
      }, 80 + i * 40);
    });
  }

  // Attach event listeners
  ['eff-sector', 'eff-count'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', renderEfficiencyLeaderboard);
  });

  renderEfficiencyLeaderboard();
}

// ─── ENHANCED COMPARE VIEW ───
function openCompareView() {
  if (compareList.length < 2) return;

  const companies = compareList.map(name => COMPANIES.find(c => c.name === name)).filter(Boolean);
  if (companies.length < 2) return;

  const cols = companies.length + 1;
  const gridCols = `180px repeat(${companies.length}, 1fr)`;

  // Color palette for radar chart
  const chartColors = [
    { bg: 'rgba(255, 107, 44, 0.2)', border: '#ff6b2c' },
    { bg: 'rgba(34, 197, 94, 0.2)', border: '#22c55e' },
    { bg: 'rgba(96, 165, 250, 0.2)', border: '#60a5fa' },
    { bg: 'rgba(168, 85, 247, 0.2)', border: '#a855f7' },
    { bg: 'rgba(236, 72, 153, 0.2)', border: '#ec4899' }
  ];

  // Get Innovator Scores for each company
  const innovatorScores = companies.map(c => {
    if (typeof getInnovatorScore === 'function') {
      return getInnovatorScore(c.name);
    }
    return null;
  });

  // Enhanced metrics including Innovator Score
  const metrics = [
    { label: 'Sector', key: c => c.sector },
    { label: 'Location', key: c => c.location },
    { label: 'Stage', key: c => c.fundingStage || 'N/A' },
    { label: 'Total Raised', key: c => c.totalRaised || 'N/A' },
    { label: 'Valuation', key: c => c.valuation || 'N/A' },
    { label: 'Signal', key: c => c.signal ? renderSignalBadge(c.signal) : 'None' },
    { label: 'Avg Score', key: c => c.scores ? getAverageScore(c.scores).toFixed(1) + '/10' : 'N/A', highlight: true },
    { label: 'Team', key: c => c.scores ? c.scores.team + '/10' : 'N/A' },
    { label: 'Traction', key: c => c.scores ? c.scores.traction + '/10' : 'N/A' },
    { label: 'Tech Moat', key: c => c.scores ? c.scores.techMoat + '/10' : 'N/A' },
    { label: 'Market', key: c => c.scores ? c.scores.market + '/10' : 'N/A' },
    { label: 'Momentum', key: c => c.scores ? c.scores.momentum + '/10' : 'N/A' },
    { label: 'Founder', key: c => c.founder || 'N/A' },
    { label: 'Latest Event', key: c => c.recentEvent ? c.recentEvent.text : 'N/A' }
  ];

  // Generate key differentiators
  const differentiators = [];
  const valMetrics = ['team', 'traction', 'techMoat', 'market', 'momentum'];
  valMetrics.forEach(m => {
    const vals = companies.map(c => c.scores ? c.scores[m] || 0 : 0);
    const maxIdx = vals.indexOf(Math.max(...vals));
    const minIdx = vals.indexOf(Math.min(...vals));
    if (vals[maxIdx] - vals[minIdx] >= 2) {
      differentiators.push({
        metric: m.charAt(0).toUpperCase() + m.slice(1).replace(/([A-Z])/g, ' $1'),
        leader: companies[maxIdx].name,
        value: vals[maxIdx],
        diff: vals[maxIdx] - vals[minIdx]
      });
    }
  });
  differentiators.sort((a, b) => b.diff - a.diff);

  // Build Innovator Score comparison section
  const hasInnovatorScores = innovatorScores.some(s => s !== null);
  let innovatorScoreSection = '';
  if (hasInnovatorScores) {
    const tierColors = { elite: '#22c55e', strong: '#3b82f6', promising: '#f59e0b', early: '#6b7280' };
    innovatorScoreSection = `
      <div class="compare-iscore-section">
        <h3 style="font-family: var(--font-display); font-size: 16px; color: var(--text-primary); margin-bottom: 16px;">Innovator Score™ Comparison</h3>
        <div class="compare-iscore-grid" style="display: grid; grid-template-columns: repeat(${companies.length}, 1fr); gap: 16px;">
          ${companies.map((c, i) => {
            const score = innovatorScores[i];
            if (!score) {
              return `<div class="compare-iscore-card no-data"><span class="compare-iscore-name">${c.name}</span><span class="compare-iscore-na">No Score</span></div>`;
            }
            const tc = tierColors[score.tier] || '#6b7280';
            return `
              <div class="compare-iscore-card" style="border-color: ${tc}20;">
                <div class="compare-iscore-header">
                  <span class="compare-iscore-name">${c.name}</span>
                  <span class="compare-iscore-tier" style="background: ${tc}20; color: ${tc};">${score.tier.toUpperCase()}</span>
                </div>
                <div class="compare-iscore-total" style="color: ${tc};">${score.composite.toFixed(0)}</div>
                <div class="compare-iscore-dims">
                  <div class="compare-iscore-dim"><span>Tech</span><span>${score.techMoat}/10</span></div>
                  <div class="compare-iscore-dim"><span>Momentum</span><span>${score.momentum}/10</span></div>
                  <div class="compare-iscore-dim"><span>Team</span><span>${score.teamPedigree}/10</span></div>
                  <div class="compare-iscore-dim"><span>Market</span><span>${score.marketGravity}/10</span></div>
                  <div class="compare-iscore-dim"><span>Efficiency</span><span>${score.capitalEfficiency}/10</span></div>
                  <div class="compare-iscore-dim"><span>Gov</span><span>${score.govTraction}/10</span></div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  // Build Patent/Alt Data comparison if available
  let dataIntelSection = '';
  const patentData = companies.map(c => typeof PATENT_INTEL !== 'undefined' ? PATENT_INTEL.find(p => p.company === c.name) : null);
  const altData = companies.map(c => typeof ALT_DATA_SIGNALS !== 'undefined' ? ALT_DATA_SIGNALS.find(a => a.company === c.name) : null);
  const hasPatentData = patentData.some(p => p !== null);
  const hasAltData = altData.some(a => a !== null);

  if (hasPatentData || hasAltData) {
    dataIntelSection = `
      <div class="compare-intel-section">
        <h3 style="font-family: var(--font-display); font-size: 16px; color: var(--text-primary); margin-bottom: 16px;">Data Intelligence</h3>
        <div class="compare-intel-grid" style="display: grid; grid-template-columns: ${gridCols};">
          ${hasPatentData ? `
            <div class="compare-intel-row" style="display: grid; grid-template-columns: ${gridCols};">
              <div class="compare-label">Patents</div>
              ${patentData.map(p => `<div class="compare-value" style="text-align: center;">${p ? p.totalPatents : 'N/A'}</div>`).join('')}
            </div>
            <div class="compare-intel-row" style="display: grid; grid-template-columns: ${gridCols};">
              <div class="compare-label">IP Moat Score</div>
              ${patentData.map(p => {
                if (!p) return '<div class="compare-value" style="text-align: center;">N/A</div>';
                const color = p.ipMoatScore >= 8 ? '#22c55e' : p.ipMoatScore >= 6 ? '#f59e0b' : '#6b7280';
                return `<div class="compare-value" style="text-align: center; color: ${color}; font-weight: 600;">${p.ipMoatScore}/10</div>`;
              }).join('')}
            </div>
          ` : ''}
          ${hasAltData ? `
            <div class="compare-intel-row" style="display: grid; grid-template-columns: ${gridCols};">
              <div class="compare-label">Hiring Velocity</div>
              ${altData.map(a => {
                if (!a) return '<div class="compare-value" style="text-align: center;">N/A</div>';
                const hc = { surging: '#22c55e', growing: '#3b82f6', stable: '#f59e0b', declining: '#ef4444' };
                return `<div class="compare-value" style="text-align: center; color: ${hc[a.hiringVelocity] || '#6b7280'};">${(a.hiringVelocity || '').toUpperCase()}</div>`;
              }).join('')}
            </div>
            <div class="compare-intel-row" style="display: grid; grid-template-columns: ${gridCols};">
              <div class="compare-label">Signal Strength</div>
              ${altData.map(a => `<div class="compare-value" style="text-align: center;">${a ? a.signalStrength + '/10' : 'N/A'}</div>`).join('')}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  const body = document.getElementById('modal-body');
  body.innerHTML = `
    <div class="compare-modal-header">
      <span class="modal-sector-badge" style="background: linear-gradient(135deg, var(--accent-dim), rgba(96, 165, 250, 0.1)); color: var(--accent);">⚖️ COMPARISON</span>
      <h2 class="modal-company-name">Company Comparison</h2>
      <p style="color: var(--text-muted); font-size: 14px;">Side-by-side analysis of ${companies.length} companies</p>
    </div>

    <!-- Company Quick Cards -->
    <div class="compare-quick-cards" style="display: grid; grid-template-columns: repeat(${companies.length}, 1fr); gap: 16px; margin-bottom: 24px;">
      ${companies.map((c, i) => {
        const sectorInfo = SECTORS[c.sector] || { color: '#6b7280', icon: '📦' };
        return `
          <div class="compare-quick-card" style="background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 12px; padding: 16px; border-left: 3px solid ${chartColors[i % chartColors.length].border};">
            <div style="font-size: 11px; color: ${sectorInfo.color}; margin-bottom: 4px;">${sectorInfo.icon} ${c.sector}</div>
            <div style="font-family: var(--font-display); font-weight: 700; font-size: 18px; color: var(--text-primary); margin-bottom: 4px;">${c.name}</div>
            ${c.valuation ? `<div style="color: var(--accent); font-weight: 600; font-size: 14px;">${c.valuation}</div>` : ''}
            <div style="color: var(--text-muted); font-size: 12px; margin-top: 8px;">${c.location}</div>
          </div>
        `;
      }).join('')}
    </div>

    <!-- Radar Chart Section -->
    <div class="compare-radar-section">
      <h3 style="font-family: var(--font-display); font-size: 16px; color: var(--text-primary); margin-bottom: 16px;">Intelligence Score Comparison</h3>
      <div class="compare-radar-container">
        <canvas id="compare-radar-chart" width="400" height="300"></canvas>
      </div>
      <div class="compare-legend">
        ${companies.map((c, i) => `
          <div class="compare-legend-item">
            <span class="compare-legend-color" style="background: ${chartColors[i % chartColors.length].border}"></span>
            <span class="compare-legend-name">${c.name}</span>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Innovator Score Section -->
    ${innovatorScoreSection}

    <!-- Key Differentiators -->
    ${differentiators.length > 0 ? `
    <div class="compare-differentiators">
      <h3 style="font-family: var(--font-display); font-size: 16px; color: var(--text-primary); margin-bottom: 12px;">Key Differentiators</h3>
      <div class="differentiator-grid">
        ${differentiators.slice(0, 3).map(d => `
          <div class="differentiator-card">
            <span class="differentiator-metric">${d.metric}</span>
            <span class="differentiator-leader">${d.leader}</span>
            <span class="differentiator-value">${d.value}/10 (+${d.diff.toFixed(1)} lead)</span>
          </div>
        `).join('')}
      </div>
    </div>
    ` : ''}

    <!-- Data Intelligence Section -->
    ${dataIntelSection}

    <!-- Metrics Table -->
    <div class="compare-grid" style="margin-top: 24px;">
      <div class="compare-header-row" style="display: grid; grid-template-columns: ${gridCols};">
        <div class="compare-label">Metric</div>
        ${companies.map((c, i) => {
          return `<div style="text-align: center;">
            <div style="font-family: var(--font-display); font-weight: 700; font-size: 14px; color: ${chartColors[i % chartColors.length].border};">${c.name}</div>
          </div>`;
        }).join('')}
      </div>
      ${metrics.map(m => `
        <div class="compare-data-row" style="display: grid; grid-template-columns: ${gridCols};">
          <div class="compare-label">${m.label}</div>
          ${companies.map(c => `<div class="compare-value ${m.highlight ? 'highlight' : ''}" style="text-align: center;">${m.key(c)}</div>`).join('')}
        </div>
      `).join('')}
    </div>

    <!-- Share/Export -->
    <div class="compare-actions-footer">
      <button class="compare-share-btn" id="compare-share-btn">📋 Copy Link</button>
      <button class="compare-export-btn" onclick="exportComparisonPDF()">📄 Export PDF</button>
    </div>
  `;

  // Add share button functionality
  document.getElementById('compare-share-btn')?.addEventListener('click', () => {
    shareComparison();
    const btn = document.getElementById('compare-share-btn');
    if (btn) {
      const original = btn.innerHTML;
      btn.innerHTML = '✓ Copied!';
      btn.style.background = '#22c55e';
      setTimeout(() => {
        btn.innerHTML = original;
        btn.style.background = '';
      }, 2000);
    }
  });

  document.getElementById('modal-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';

  // Update URL with comparison state
  const url = new URL(window.location);
  url.searchParams.set('compare', compareList.join(','));
  window.history.replaceState({}, '', url);

  // Initialize radar chart after DOM is ready
  setTimeout(() => {
    const ctx = document.getElementById('compare-radar-chart');
    if (ctx && typeof Chart !== 'undefined') {
      new Chart(ctx, {
        type: 'radar',
        data: {
          labels: ['Team', 'Traction', 'Tech Moat', 'Market', 'Momentum'],
          datasets: companies.map((c, i) => ({
            label: c.name,
            data: c.scores ? [
              c.scores.team || 0,
              c.scores.traction || 0,
              c.scores.techMoat || 0,
              c.scores.market || 0,
              c.scores.momentum || 0
            ] : [0, 0, 0, 0, 0],
            backgroundColor: chartColors[i % chartColors.length].bg,
            borderColor: chartColors[i % chartColors.length].border,
            borderWidth: 2,
            pointBackgroundColor: chartColors[i % chartColors.length].border,
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: chartColors[i % chartColors.length].border
          }))
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              beginAtZero: true,
              max: 10,
              ticks: {
                stepSize: 2,
                color: '#9ca3af',
                backdropColor: 'transparent'
              },
              pointLabels: {
                color: '#e5e7eb',
                font: { family: "'Space Grotesk', sans-serif", size: 12, weight: 600 }
              },
              grid: { color: 'rgba(255,255,255,0.1)' },
              angleLines: { color: 'rgba(255,255,255,0.1)' }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    }
  }, 100);
}

// Share comparison URL
function shareComparison() {
  const url = new URL(window.location);
  url.searchParams.set('compare', compareList.join(','));
  navigator.clipboard.writeText(url.toString()).then(() => {
    alert('Comparison URL copied to clipboard!');
  });
}

// Export comparison to PDF
function exportComparisonPDF() {
  if (typeof jspdf === 'undefined') {
    alert('PDF export not available');
    return;
  }

  const companies = compareList.map(name => COMPANIES.find(c => c.name === name)).filter(Boolean);
  const { jsPDF } = jspdf;
  const doc = new jsPDF();

  // Title
  doc.setFontSize(20);
  doc.setTextColor(255, 107, 44);
  doc.text('Company Comparison', 20, 20);

  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text('The Innovators League', 20, 28);
  doc.text(new Date().toLocaleDateString(), 20, 34);

  // Company names
  doc.setFontSize(14);
  doc.setTextColor(0);
  let y = 50;
  companies.forEach((c, i) => {
    doc.text(`${i + 1}. ${c.name}`, 20, y);
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`${c.sector} | ${c.fundingStage || 'N/A'} | ${c.valuation || 'N/A'}`, 30, y + 6);
    doc.setFontSize(14);
    doc.setTextColor(0);
    y += 18;
  });

  // Scores table
  y += 10;
  doc.setFontSize(12);
  doc.text('Score Comparison', 20, y);
  y += 10;

  const scoreLabels = ['Team', 'Traction', 'Tech Moat', 'Market', 'Momentum', 'Average'];
  doc.setFontSize(9);
  doc.setTextColor(100);

  // Header row
  let x = 20;
  doc.text('Metric', x, y);
  companies.forEach((c, i) => {
    x += 40;
    doc.text(c.name.substring(0, 15), x, y);
  });
  y += 8;

  doc.setTextColor(0);
  scoreLabels.forEach(label => {
    x = 20;
    doc.text(label, x, y);
    companies.forEach(c => {
      x += 40;
      let val = 'N/A';
      if (c.scores) {
        if (label === 'Average') {
          val = getAverageScore(c.scores).toFixed(1);
        } else {
          const key = label.toLowerCase().replace(' ', '');
          val = c.scores[key] ? c.scores[key].toString() : 'N/A';
        }
      }
      doc.text(val, x, y);
    });
    y += 6;
  });

  doc.save('company-comparison.pdf');
}

// ─── SMOOTH SCROLL (runs after DOMContentLoaded via initSmoothScroll) ───
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(a.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

// ─── BREAKING NEWS TICKER ───
function initNewsTicker() {
  const scroll = document.getElementById('ticker-scroll');
  if (!scroll || typeof NEWS_TICKER === 'undefined') return;

  NEWS_TICKER.forEach((item, i) => {
    if (i > 0) {
      const divider = document.createElement('span');
      divider.className = 'ticker-divider';
      scroll.appendChild(divider);
    }

    const el = document.createElement('span');
    el.className = `ticker-item ticker-priority-${item.priority}`;
    el.innerHTML = `<span>${item.text}</span><span class="ticker-time">${item.time}</span>`;
    scroll.appendChild(el);
  });
}

// ─── MARKET PULSE ───
function initMarketPulse() {
  const grid = document.getElementById('market-pulse-grid');
  if (!grid || typeof MARKET_PULSE === 'undefined') return;

  MARKET_PULSE.forEach(stock => {
    const card = document.createElement('div');
    card.className = 'pulse-card';
    card.innerHTML = `
      <div class="pulse-ticker">${stock.ticker}</div>
      <div class="pulse-name">${stock.name}</div>
      <div>
        <span class="pulse-val">${stock.valuation}</span>
        <span class="pulse-change ${stock.trend}">${stock.change}</span>
      </div>
    `;
    card.addEventListener('click', () => openCompanyModal(stock.name));
    grid.appendChild(card);
  });
}

// ─── FUNDING TRACKER ───
function initFundingTracker() {
  const grid = document.getElementById('funding-tracker-grid');
  if (!grid || typeof FUNDING_TRACKER === 'undefined') return;

  // Header row
  const header = document.createElement('div');
  header.className = 'funding-row funding-row-header';
  header.innerHTML = `
    <span>Company</span>
    <span>Amount</span>
    <span>Stage</span>
    <span>Lead Investor</span>
    <span>Valuation</span>
    <span>Date</span>
  `;
  grid.appendChild(header);

  FUNDING_TRACKER.forEach(round => {
    const row = document.createElement('div');
    row.className = 'funding-row';
    row.innerHTML = `
      <span class="funding-company">${round.company}</span>
      <span class="funding-amount">${round.amount}</span>
      <span><span class="funding-stage-tag">${round.stage}</span></span>
      <span class="funding-lead">${round.lead}</span>
      <span class="funding-val">${round.valuation}</span>
      <span class="funding-date">${round.date}</span>
    `;
    row.addEventListener('click', () => openCompanyModal(round.company));
    grid.appendChild(row);
  });
}

// ─── SECTOR MOMENTUM INDEX ───
function initSectorMomentum() {
  const grid = document.getElementById('momentum-grid');
  if (!grid || typeof SECTOR_MOMENTUM === 'undefined') return;

  SECTOR_MOMENTUM.forEach((item, i) => {
    const sectorInfo = SECTORS[item.sector] || { icon: '📊' };
    const scoreClass = item.momentum >= 80 ? 'high' : item.momentum >= 60 ? 'mid' : 'low';
    const trendClass = `momentum-trend-${item.trend}`;

    const row = document.createElement('div');
    row.className = 'momentum-row';
    row.innerHTML = `
      <div class="momentum-sector-name">
        <span class="momentum-sector-icon">${sectorInfo.icon}</span>
        ${item.sector}
      </div>
      <div class="momentum-score ${scoreClass}">${item.momentum}</div>
      <div class="momentum-bar-bg">
        <div class="momentum-bar-fill ${scoreClass}" style="width: 0%"></div>
      </div>
      <div class="momentum-trend ${trendClass}">${item.trend}</div>
      <div class="momentum-funding">${item.fundingQ} Q1</div>
    `;

    grid.appendChild(row);

    // Animate bar
    setTimeout(() => {
      row.querySelector('.momentum-bar-fill').style.width = `${item.momentum}%`;
    }, 200 + i * 80);
  });
}

// ─── IPO & EXIT PIPELINE ───
function initIPOPipeline() {
  const grid = document.getElementById('ipo-grid');
  if (!grid || typeof IPO_PIPELINE === 'undefined') return;

  IPO_PIPELINE.forEach(item => {
    const card = document.createElement('div');
    card.className = 'ipo-card';

    const sectorInfo = SECTORS[item.sector] || { icon: '', color: '#6b7280' };

    card.innerHTML = `
      <div style="font-size: 11px; color: ${sectorInfo.color}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">${sectorInfo.icon} ${item.sector}</div>
      <div class="ipo-company">${item.company}</div>
      <div class="ipo-status ipo-status-${item.likelihood}">${item.status}</div>
      <div class="ipo-meta">
        <div class="ipo-meta-item">
          <div class="ipo-meta-label">Timeline</div>
          <div class="ipo-meta-value">${item.estimatedDate}</div>
        </div>
        <div class="ipo-meta-item">
          <div class="ipo-meta-label">Est. Valuation</div>
          <div class="ipo-meta-value" style="color: var(--accent);">${item.estimatedValuation}</div>
        </div>
      </div>
    `;

    card.addEventListener('click', () => openCompanyModal(item.company));
    grid.appendChild(card);
  });
}

// ─── TRL DASHBOARD ───
function initTRLDashboard() {
  const legend = document.getElementById('trl-legend');
  const grid = document.getElementById('trl-grid');
  if (!grid || typeof TRL_DEFINITIONS === 'undefined' || typeof TRL_RANKINGS === 'undefined') return;

  // Render legend
  if (legend) {
    legend.innerHTML = Object.entries(TRL_DEFINITIONS).map(([level, def]) =>
      `<div class="trl-legend-item">
        <div class="trl-level-badge" style="background:${def.color};">${level}</div>
        <div class="trl-legend-text">
          <div class="trl-legend-label">${def.label}</div>
        </div>
      </div>`
    ).join('');
  }

  // Group by TRL level (descending)
  const grouped = {};
  TRL_RANKINGS.forEach(item => {
    if (!grouped[item.trl]) grouped[item.trl] = [];
    grouped[item.trl].push(item);
  });

  Object.keys(grouped).sort((a, b) => b - a).forEach(trl => {
    const def = TRL_DEFINITIONS[trl];
    const section = document.createElement('div');
    section.className = 'trl-row';

    const companies = grouped[trl];
    section.innerHTML = `
      <div class="trl-row-header">
        <div class="trl-row-badge" style="background:${def.color};">TRL ${trl}</div>
        <div class="trl-row-info">
          <span class="trl-row-label">${def.label}</span>
          <span class="trl-row-count">${companies.length} companies</span>
        </div>
      </div>
      <div class="trl-row-companies">
        ${companies.map(c => {
          const comp = COMPANIES.find(x => x.name === c.company);
          const sectorInfo = comp ? (SECTORS[comp.sector] || { icon: '📦', color: '#6b7280' }) : { icon: '📦', color: '#6b7280' };
          return `<div class="trl-company-chip" onclick="openCompanyModal('${c.company}')" title="${c.note}">
            <span style="color:${sectorInfo.color}">${sectorInfo.icon}</span>
            <span class="trl-company-name">${c.company}</span>
            <span class="trl-company-note">${c.note.substring(0, 60)}${c.note.length > 60 ? '...' : ''}</span>
          </div>`;
        }).join('')}
      </div>
    `;

    grid.appendChild(section);
  });
}

// ─── DEAL TRACKER ───
function initDealTracker() {
  const grid = document.getElementById('deal-grid');
  if (!grid || typeof DEAL_TRACKER === 'undefined') return;

  function renderDeals(filter) {
    grid.innerHTML = '';
    const deals = filter === 'lead'
      ? DEAL_TRACKER.filter(d => d.leadOrParticipant === 'lead')
      : DEAL_TRACKER;

    // Sort by date descending
    deals.sort((a, b) => b.date.localeCompare(a.date));

    // Header
    const header = document.createElement('div');
    header.className = 'deal-row deal-header';
    header.innerHTML = `
      <div class="deal-cell deal-company-col">Company</div>
      <div class="deal-cell deal-investor-col">Investor</div>
      <div class="deal-cell deal-amount-col">Amount</div>
      <div class="deal-cell deal-round-col">Round</div>
      <div class="deal-cell deal-val-col">Valuation</div>
      <div class="deal-cell deal-date-col">Date</div>
      <div class="deal-cell deal-role-col">Role</div>
    `;
    grid.appendChild(header);

    deals.forEach((deal, i) => {
      const row = document.createElement('div');
      row.className = 'deal-row';
      row.style.animationDelay = `${i * 30}ms`;
      const isLead = deal.leadOrParticipant === 'lead';
      row.innerHTML = `
        <div class="deal-cell deal-company-col"><span class="deal-company-link" onclick="openCompanyModal('${deal.company}')">${deal.company}</span></div>
        <div class="deal-cell deal-investor-col">${deal.investor}</div>
        <div class="deal-cell deal-amount-col" style="color:var(--accent);font-weight:600;">${deal.amount}</div>
        <div class="deal-cell deal-round-col">${deal.round}</div>
        <div class="deal-cell deal-val-col">${deal.valuation || '—'}</div>
        <div class="deal-cell deal-date-col">${deal.date}</div>
        <div class="deal-cell deal-role-col"><span class="deal-role ${isLead ? 'deal-role-lead' : ''}">${isLead ? '★ Lead' : 'Participant'}</span></div>
      `;
      grid.appendChild(row);
    });
  }

  renderDeals('all');

  // Filter buttons
  document.querySelectorAll('.deal-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.deal-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderDeals(btn.dataset.filter);
    });
  });
}

// ─── GROWTH SIGNALS ───
function initGrowthSignals() {
  const grid = document.getElementById('signals-grid');
  if (!grid || typeof GROWTH_SIGNALS === 'undefined' || typeof SIGNAL_TYPES === 'undefined') return;

  // Sort by strength (strong first) then date
  const sorted = [...GROWTH_SIGNALS].sort((a, b) => {
    const strengthOrder = { strong: 0, medium: 1, weak: 2 };
    if (strengthOrder[a.strength] !== strengthOrder[b.strength]) return strengthOrder[a.strength] - strengthOrder[b.strength];
    return b.date.localeCompare(a.date);
  });

  sorted.forEach((sig, i) => {
    const type = SIGNAL_TYPES[sig.signal] || { icon: '📊', label: sig.signal };
    const card = document.createElement('div');
    card.className = `signal-card signal-${sig.strength}`;
    card.style.animationDelay = `${i * 40}ms`;

    card.innerHTML = `
      <div class="signal-card-header">
        <span class="signal-type-icon">${type.icon}</span>
        <span class="signal-type-label">${type.label}</span>
        <span class="signal-strength signal-strength-${sig.strength}">${sig.strength}</span>
      </div>
      <div class="signal-company" onclick="openCompanyModal('${sig.company}')">${sig.company}</div>
      <div class="signal-detail">${sig.detail}</div>
      <div class="signal-date">${sig.date}</div>
    `;

    grid.appendChild(card);
  });
}

// ─── MARKET MAP ───
function initMarketMap() {
  const grid = document.getElementById('market-map-grid');
  if (!grid || typeof MARKET_MAP === 'undefined') return;

  Object.entries(MARKET_MAP).forEach(([category, data]) => {
    const card = document.createElement('div');
    card.className = 'market-map-card';

    const renderCompanyList = (companies, className) =>
      companies.map(c =>
        `<span class="market-company ${className}" onclick="openCompanyModal('${c}')">${c}</span>`
      ).join('');

    card.innerHTML = `
      <div class="market-map-header">
        <h3 class="market-map-title">${category}</h3>
        <span class="market-map-tam">${data.totalTAM} TAM</span>
      </div>
      <p class="market-map-desc">${data.description}</p>
      <div class="market-map-trend">${data.keyTrend}</div>
      <div class="market-map-tiers">
        <div class="market-tier">
          <div class="market-tier-label">🏆 Leaders</div>
          <div class="market-tier-companies">${renderCompanyList(data.leaders, 'market-leader')}</div>
        </div>
        <div class="market-tier">
          <div class="market-tier-label">⚡ Challengers</div>
          <div class="market-tier-companies">${renderCompanyList(data.challengers, 'market-challenger')}</div>
        </div>
        <div class="market-tier">
          <div class="market-tier-label">🌱 Emerging</div>
          <div class="market-tier-companies">${renderCompanyList(data.emerging, 'market-emerging')}</div>
        </div>
      </div>
    `;

    grid.appendChild(card);
  });
}

// ─── MAFIA EXPLORER ───
function initMafiaExplorer() {
  const grid = document.getElementById('mafia-grid');
  if (!grid || typeof FOUNDER_MAFIAS === 'undefined') return;

  Object.entries(FOUNDER_MAFIAS).forEach(([name, data]) => {
    const card = document.createElement('div');
    card.className = 'mafia-card';

    card.innerHTML = `
      <div class="mafia-card-header" style="border-left: 3px solid ${data.color};">
        <span class="mafia-card-icon">${data.icon}</span>
        <div>
          <h3 class="mafia-card-title">${name}</h3>
          <p class="mafia-card-desc">${data.description}</p>
        </div>
        <span class="mafia-card-count">${data.companies.length}</span>
      </div>
      <div class="mafia-card-companies">
        ${data.companies.map(c => `
          <div class="mafia-company-row" onclick="openCompanyModal('${c.company}')">
            <span class="mafia-company-name">${c.company}</span>
            <span class="mafia-company-founders">${c.founders}</span>
          </div>
        `).join('')}
      </div>
    `;

    grid.appendChild(card);
  });
}

// ─── REVENUE TABLE ───
function initRevenueTable() {
  const grid = document.getElementById('revenue-grid');
  if (!grid || typeof REVENUE_INTEL === 'undefined') return;

  const sorted = [...REVENUE_INTEL].sort((a, b) => {
    const parseRev = (r) => {
      const m = r.match(/\$?([\d.]+)(B|M|T)/);
      if (!m) return 0;
      const val = parseFloat(m[1]);
      if (m[2] === 'T') return val * 1000;
      if (m[2] === 'B') return val;
      return val / 1000;
    };
    return parseRev(b.revenue) - parseRev(a.revenue);
  });

  const header = document.createElement('div');
  header.className = 'revenue-row revenue-header';
  header.innerHTML = `
    <div class="revenue-cell rev-company-col">Company</div>
    <div class="revenue-cell rev-revenue-col">Revenue</div>
    <div class="revenue-cell rev-period-col">Period</div>
    <div class="revenue-cell rev-growth-col">Growth</div>
    <div class="revenue-cell rev-source-col">Source</div>
  `;
  grid.appendChild(header);

  sorted.forEach((rev, i) => {
    const row = document.createElement('div');
    row.className = 'revenue-row';
    row.style.animationDelay = `${i * 30}ms`;
    const isPreRevenue = rev.revenue === 'Pre-Revenue';

    row.innerHTML = `
      <div class="revenue-cell rev-company-col"><span class="deal-company-link" onclick="openCompanyModal('${rev.company}')">${rev.company}</span></div>
      <div class="revenue-cell rev-revenue-col" style="color:${isPreRevenue ? 'var(--text-muted)' : 'var(--accent)'};font-weight:600;">${rev.revenue}</div>
      <div class="revenue-cell rev-period-col">${rev.period}</div>
      <div class="revenue-cell rev-growth-col" style="color:${rev.growth === 'N/A' ? 'var(--text-muted)' : '#22c55e'}">${rev.growth}</div>
      <div class="revenue-cell rev-source-col">${rev.source}</div>
    `;
    grid.appendChild(row);
  });
}

// ─── REQUEST FOR STARTUPS ───
function initRequestForStartups() {
  const grid = document.getElementById('rfs-grid');
  if (!grid || typeof REQUEST_FOR_STARTUPS === 'undefined') return;

  REQUEST_FOR_STARTUPS.forEach((rfs, i) => {
    const card = document.createElement('div');
    card.className = `rfs-card rfs-${rfs.urgency}`;
    card.style.animationDelay = `${i * 50}ms`;

    const sectorInfo = SECTORS[rfs.sector] || { icon: '📦', color: '#6b7280' };
    const urgencyLabels = { critical: '🔴 Critical', high: '🟠 High', medium: '🟡 Medium' };

    card.innerHTML = `
      <div class="rfs-header">
        <span class="rfs-sector" style="color:${sectorInfo.color}">${sectorInfo.icon} ${rfs.sector}</span>
        <span class="rfs-urgency">${urgencyLabels[rfs.urgency] || rfs.urgency}</span>
      </div>
      <h3 class="rfs-title">${rfs.title}</h3>
      <div class="rfs-requester">Requested by: <strong>${rfs.requestedBy}</strong></div>
      <p class="rfs-problem">${rfs.problem}</p>
      <div class="rfs-bounty">💰 Market Opportunity: <strong>${rfs.bounty}</strong></div>
      <div class="rfs-tags">
        ${rfs.tags.map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
      ${rfs.relatedCompanies.length > 0 ? `
        <div class="rfs-related">
          <span class="rfs-related-label">Companies working on this:</span>
          ${rfs.relatedCompanies.map(c => `<span class="rfs-related-company" onclick="openCompanyModal('${c}')">${c}</span>`).join('')}
        </div>
      ` : ''}
    `;

    grid.appendChild(card);
  });
}

// ═══════════════════════════════════════════════════════════════
// INNOVATOR SCORE™ RANKINGS
// ═══════════════════════════════════════════════════════════════
function initInnovatorScores() {
  if (typeof INNOVATOR_SCORES === 'undefined') return;
  const grid = document.getElementById('iscore-grid');
  if (!grid) return;

  // Recalculate composites and sort
  INNOVATOR_SCORES.forEach(s => {
    s.composite = s.techMoat * 2.5 + s.momentum * 2.5 + s.teamPedigree * 1.5 +
                  s.marketGravity * 1.5 + s.capitalEfficiency * 1.0 + s.govTraction * 1.0;
    s.tier = s.composite >= 90 ? 'elite' : s.composite >= 75 ? 'strong' : s.composite >= 60 ? 'promising' : 'early';
  });
  INNOVATOR_SCORES.sort((a, b) => b.composite - a.composite);

  // Populate sector filter
  const sectorSelect = document.getElementById('iscore-sector');
  if (sectorSelect) {
    const companySectors = new Set();
    INNOVATOR_SCORES.forEach(s => {
      const co = COMPANIES.find(c => c.name === s.company);
      if (co) companySectors.add(co.sector);
    });
    [...companySectors].sort().forEach(sec => {
      const opt = document.createElement('option');
      opt.value = sec;
      opt.textContent = sec;
      sectorSelect.appendChild(opt);
    });
  }

  function renderScores() {
    const sectorVal = document.getElementById('iscore-sector')?.value || 'all';
    const tierVal = document.getElementById('iscore-tier')?.value || 'all';
    let filtered = INNOVATOR_SCORES.filter(s => {
      if (tierVal !== 'all' && s.tier !== tierVal) return false;
      if (sectorVal !== 'all') {
        const co = COMPANIES.find(c => c.name === s.company);
        if (!co || co.sector !== sectorVal) return false;
      }
      return true;
    });

    grid.innerHTML = '';
    filtered.forEach((s, i) => {
      const tierColors = { elite: '#22c55e', strong: '#3b82f6', promising: '#f59e0b', early: '#6b7280' };
      const tierLabels = { elite: 'ELITE', strong: 'STRONG', promising: 'PROMISING', early: 'EARLY' };
      const tc = tierColors[s.tier];
      const row = document.createElement('div');
      row.className = 'iscore-row';
      row.style.cursor = 'pointer';
      row.onclick = () => openCompanyModal(s.company);

      const rankBadge = i < 3 ? ['🥇','🥈','🥉'][i] : `#${i + 1}`;

      row.innerHTML = `
        <div class="iscore-rank" style="${i < 3 ? 'font-size:20px;' : ''}">${rankBadge}</div>
        <div class="iscore-info">
          <div class="iscore-name">${s.company}</div>
          <div class="iscore-note">${s.note || ''}</div>
        </div>
        <div class="iscore-dimensions">
          <div class="iscore-bar" title="Tech Moat: ${s.techMoat}/10"><div class="iscore-bar-fill" style="width:${s.techMoat * 10}%; background:#3b82f6;"></div></div>
          <div class="iscore-bar" title="Momentum: ${s.momentum}/10"><div class="iscore-bar-fill" style="width:${s.momentum * 10}%; background:#f59e0b;"></div></div>
          <div class="iscore-bar" title="Team: ${s.teamPedigree}/10"><div class="iscore-bar-fill" style="width:${s.teamPedigree * 10}%; background:#8b5cf6;"></div></div>
          <div class="iscore-bar" title="Market: ${s.marketGravity}/10"><div class="iscore-bar-fill" style="width:${s.marketGravity * 10}%; background:#22c55e;"></div></div>
          <div class="iscore-bar" title="Efficiency: ${s.capitalEfficiency}/10"><div class="iscore-bar-fill" style="width:${s.capitalEfficiency * 10}%; background:#06b6d4;"></div></div>
          <div class="iscore-bar" title="Gov't: ${s.govTraction}/10"><div class="iscore-bar-fill" style="width:${s.govTraction * 10}%; background:#dc2626;"></div></div>
        </div>
        <div class="iscore-composite" style="border-color:${tc};">
          <span class="iscore-composite-value" style="color:${tc};">${s.composite.toFixed(0)}</span>
          <span class="iscore-tier-badge" style="background:${tc}15; color:${tc}; border:1px solid ${tc}40;">${tierLabels[s.tier]}</span>
        </div>
      `;
      grid.appendChild(row);
    });
  }

  renderScores();
  document.getElementById('iscore-sector')?.addEventListener('change', renderScores);
  document.getElementById('iscore-tier')?.addEventListener('change', renderScores);
}

// Helper to get innovator score for a company
function getInnovatorScore(companyName) {
  if (typeof INNOVATOR_SCORES === 'undefined') return null;
  return INNOVATOR_SCORES.find(s => s.company === companyName) || null;
}

// ═══════════════════════════════════════════════════════════════
// GOVERNMENT CONTRACT INTELLIGENCE
// ═══════════════════════════════════════════════════════════════
function initGovContracts() {
  if (typeof GOV_CONTRACTS === 'undefined') return;
  const contractsPanel = document.getElementById('gov-contracts-panel');
  const budgetPanel = document.getElementById('gov-budget-panel');
  const heatmapPanel = document.getElementById('gov-heatmap-panel');
  if (!contractsPanel) return;

  // Tab switching
  document.querySelectorAll('.gov-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.gov-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const tabName = tab.dataset.tab;
      contractsPanel.style.display = tabName === 'contracts' ? '' : 'none';
      budgetPanel.style.display = tabName === 'budget' ? '' : 'none';
      heatmapPanel.style.display = tabName === 'heatmap' ? '' : 'none';
    });
  });

  // Filter out duplicates
  const contracts = GOV_CONTRACTS.filter(c => !c.notes?.includes('DUPLICATE'));

  // Contracts Panel - sorted by total value
  const sortedContracts = [...contracts].sort((a, b) => {
    const parseGov = v => {
      if (!v) return 0;
      const m = v.match(/([\d.]+)\s*(B|M|K)?/i);
      if (!m) return 0;
      let val = parseFloat(m[1]);
      const u = (m[2] || '').toUpperCase();
      if (u === 'B') val *= 1000;
      if (u === 'K') val *= 0.001;
      return val;
    };
    return parseGov(b.totalGovValue) - parseGov(a.totalGovValue);
  });

  contractsPanel.innerHTML = sortedContracts.map(c => `
    <div class="gov-contract-row" onclick="openCompanyModal('${(c.company || '').replace(/'/g, "\\'")}')">
      <div class="gov-contract-header">
        <span class="gov-company-name">${c.company}</span>
        <span class="gov-total-value">${c.totalGovValue}</span>
      </div>
      <div class="gov-agencies">${(c.agencies || []).map(a => `<span class="gov-agency-tag">${a}</span>`).join('')}</div>
      <div class="gov-contract-details">
        ${(c.keyContracts || []).slice(0, 2).map(k => `
          <div class="gov-key-contract">
            <span class="gov-contract-agency">${k.agency}</span>
            <span class="gov-contract-program">${k.program}</span>
            <span class="gov-contract-value">${k.value}</span>
          </div>
        `).join('')}
      </div>
      <div class="gov-meta">
        ${c.sbirStatus ? `<span class="sbir-badge sbir-${(c.sbirStatus || '').toLowerCase().replace(/\s/g, '')}">${c.sbirStatus}</span>` : ''}
        ${c.clearanceLevel ? `<span class="clearance-badge cl-${(c.clearanceLevel || '').toLowerCase().replace(/[\s/]/g, '-')}">${c.clearanceLevel}</span>` : ''}
        <span class="gov-rev-pct">${c.govRevenuePercent || ''} gov revenue</span>
      </div>
    </div>
  `).join('');

  // Budget Signals Panel
  if (typeof BUDGET_SIGNALS !== 'undefined' && budgetPanel) {
    budgetPanel.innerHTML = BUDGET_SIGNALS.map(b => `
      <div class="budget-signal-card">
        <div class="budget-signal-header">
          <span class="budget-category">${b.category}</span>
          <span class="budget-change ${b.change.startsWith('+') ? 'positive' : 'negative'}">${b.change}</span>
        </div>
        <div class="budget-line-item">${b.budgetLineItem}</div>
        <div class="budget-allocation">${b.allocation} · ${b.fy}</div>
        <p class="budget-description">${b.description}</p>
        <div class="budget-beneficiaries">
          <span class="budget-beneficiaries-label">Beneficiaries:</span>
          ${b.beneficiaries.map(name => `<span class="budget-beneficiary" onclick="openCompanyModal('${name.replace(/'/g, "\\'")}')">${name}</span>`).join('')}
        </div>
      </div>
    `).join('');
  }

  // Agency Heatmap Panel
  if (heatmapPanel) {
    const allAgencies = new Set();
    contracts.forEach(c => (c.agencies || []).forEach(a => allAgencies.add(a)));
    const agencies = [...allAgencies].sort().slice(0, 12);
    const topCompanies = sortedContracts.slice(0, 20);

    let html = '<div class="gov-heatmap-wrapper"><table class="gov-heatmap-table"><thead><tr><th>Company</th>';
    agencies.forEach(a => { html += `<th class="gov-heatmap-agency">${a}</th>`; });
    html += '</tr></thead><tbody>';

    topCompanies.forEach(c => {
      html += `<tr><td class="gov-heatmap-company">${c.company}</td>`;
      agencies.forEach(a => {
        const has = (c.agencies || []).includes(a);
        html += `<td class="gov-heatmap-cell ${has ? 'gov-heatmap-active' : ''}"></td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table></div>';
    heatmapPanel.innerHTML = html;
  }
}

// ═══════════════════════════════════════════════════════════════
// PATENT INTELLIGENCE & IP MOAT
// ═══════════════════════════════════════════════════════════════
function initPatentIntel() {
  if (typeof PATENT_INTEL === 'undefined') return;
  const grid = document.getElementById('patent-grid');
  if (!grid) return;

  const sorted = [...PATENT_INTEL].sort((a, b) => (b.ipMoatScore || 0) - (a.ipMoatScore || 0));

  grid.innerHTML = sorted.map(p => {
    const moatColor = p.ipMoatScore >= 8 ? '#22c55e' : p.ipMoatScore >= 6 ? '#f59e0b' : '#6b7280';
    const moatLabel = p.ipMoatScore >= 8 ? 'HIGH' : p.ipMoatScore >= 6 ? 'MID' : 'LOW';
    return `
      <div class="patent-card" onclick="openCompanyModal('${(p.company || '').replace(/'/g, "\\'")}')">
        <div class="patent-card-header">
          <span class="patent-company">${p.company}</span>
          <span class="patent-ip-score" style="background:${moatColor}15; color:${moatColor}; border:1px solid ${moatColor}40;">
            IP: ${p.ipMoatScore}/10 · ${moatLabel}
          </span>
        </div>
        <div class="patent-stats">
          <div class="patent-stat">
            <span class="patent-stat-value">${p.totalPatents}</span>
            <span class="patent-stat-label">Patents</span>
          </div>
          <div class="patent-stat">
            <span class="patent-stat-value">${p.velocity}</span>
            <span class="patent-stat-label">Filing Rate</span>
          </div>
          <div class="patent-stat">
            <span class="patent-stat-value patent-trend-${p.velocityTrend}">${p.velocityTrend === 'accelerating' ? '↑ Accel.' : p.velocityTrend === 'steady' ? '→ Steady' : '↓ Slow'}</span>
            <span class="patent-stat-label">Trend</span>
          </div>
        </div>
        <div class="patent-tech-areas">
          ${(p.techAreas || []).map(t => `<span class="patent-tech-tag">${t}</span>`).join('')}
        </div>
        <p class="patent-note">${p.note || ''}</p>
      </div>
    `;
  }).join('');
}

// ═══════════════════════════════════════════════════════════════
// ALTERNATIVE DATA SIGNALS
// ═══════════════════════════════════════════════════════════════
function initAltData() {
  if (typeof ALT_DATA_SIGNALS === 'undefined') return;
  const grid = document.getElementById('alt-data-grid');
  if (!grid) return;

  function renderAltData() {
    const sortVal = document.getElementById('alt-sort')?.value || 'strength';
    let sorted = [...ALT_DATA_SIGNALS];

    if (sortVal === 'strength') sorted.sort((a, b) => (b.signalStrength || 0) - (a.signalStrength || 0));
    else if (sortVal === 'hiring') {
      const hiringOrder = { surging: 4, growing: 3, stable: 2, declining: 1 };
      sorted.sort((a, b) => (hiringOrder[b.hiringVelocity] || 0) - (hiringOrder[a.hiringVelocity] || 0));
    } else sorted.sort((a, b) => (a.company || '').localeCompare(b.company || ''));

    const hiringColors = { surging: '#22c55e', growing: '#3b82f6', stable: '#f59e0b', declining: '#ef4444' };
    const trafficIcons = { up: '↑', flat: '→', down: '↓' };
    const trafficColors = { up: '#22c55e', flat: '#f59e0b', down: '#ef4444' };
    const sentimentColors = { positive: '#22c55e', mixed: '#f59e0b', neutral: '#6b7280', negative: '#ef4444' };

    grid.innerHTML = sorted.map(s => `
      <div class="alt-data-row" onclick="openCompanyModal('${(s.company || '').replace(/'/g, "\\'")}')">
        <div class="alt-data-company">${s.company}</div>
        <div class="alt-data-hiring" style="color:${hiringColors[s.hiringVelocity] || '#6b7280'}">
          ${(s.hiringVelocity || 'unknown').toUpperCase()}
          <span class="alt-data-headcount">${s.headcountEstimate || ''}</span>
        </div>
        <div class="alt-data-traffic" style="color:${trafficColors[s.webTraffic] || '#6b7280'}">
          ${trafficIcons[s.webTraffic] || '?'} ${(s.webTraffic || '').toUpperCase()}
        </div>
        <div class="alt-data-sentiment" style="color:${sentimentColors[s.newsSentiment] || '#6b7280'}">
          ${(s.newsSentiment || 'unknown').toUpperCase()}
        </div>
        <div class="alt-data-signal">
          <div class="alt-signal-bar">
            <div class="alt-signal-fill" style="width:${(s.signalStrength || 0) * 10}%;"></div>
          </div>
          <span class="alt-signal-value">${s.signalStrength || 0}/10</span>
        </div>
        <div class="alt-data-key-signal">${s.keySignal || ''}</div>
      </div>
    `).join('');
  }

  renderAltData();
  document.getElementById('alt-sort')?.addEventListener('change', renderAltData);
}

// ═══════════════════════════════════════════════════════
// REAL-TIME ALERTS CENTER
// ═══════════════════════════════════════════════════════
function initAlertsCenter() {
  if (typeof ALERTS_SYSTEM === 'undefined') return;

  const feed = document.getElementById('alerts-feed');
  if (!feed) return;

  let currentCategory = 'all';
  let criticalOnly = false;

  function renderAlerts() {
    let alerts = ALERTS_SYSTEM.recentAlerts;

    // Filter by category
    if (currentCategory !== 'all') {
      alerts = alerts.filter(a => a.category === currentCategory);
    }

    // Filter by priority
    if (criticalOnly) {
      alerts = alerts.filter(a => a.priority === 'critical' || a.priority === 'high');
    }

    feed.innerHTML = alerts.map(alert => {
      const categoryIcon = {
        funding: '💰',
        contracts: '📋',
        leadership: '👤',
        regulatory: '⚖️',
        signals: '📊',
        patents: '📜'
      }[alert.category] || '📌';

      const relatedTags = (alert.relatedCompanies || []).slice(0, 3).map(c =>
        `<span class="alert-tag">${c}</span>`
      ).join('');

      return `
        <div class="alert-item priority-${alert.priority}">
          <div class="alert-header">
            <div class="alert-meta">
              <span class="alert-category ${alert.category}">${categoryIcon} ${alert.category.toUpperCase()}</span>
              <span class="alert-company">${alert.company}</span>
            </div>
            <div class="alert-timestamp">
              <div>${alert.date}</div>
              <div>${alert.time}</div>
            </div>
          </div>

          <div class="alert-title">${alert.title}</div>
          <div class="alert-summary">${alert.summary}</div>

          <div class="alert-footer">
            <div class="alert-tags">${relatedTags}</div>
            <div class="alert-source">
              Source: <a href="${alert.sourceUrl}" target="_blank" rel="noopener">${alert.source}</a>
            </div>
          </div>
        </div>
      `;
    }).join('');

    if (alerts.length === 0) {
      feed.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No alerts match your filters</div>';
    }
  }

  // Category filter buttons
  document.querySelectorAll('.alert-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.alert-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = btn.dataset.category;
      renderAlerts();
    });
  });

  // Critical only checkbox
  document.getElementById('critical-only')?.addEventListener('change', (e) => {
    criticalOnly = e.target.checked;
    renderAlerts();
  });

  renderAlerts();
}

// ═══════════════════════════════════════════════════════
// INTELLIGENCE HUB (Tab Switching)
// ═══════════════════════════════════════════════════════
function initIntelligenceHub() {
  const tabs = document.querySelectorAll('.intel-hub-tab');
  const alertsPanel = document.getElementById('intel-alerts-panel');
  const signalsPanel = document.getElementById('intel-signals-panel');
  const newsPanel = document.getElementById('intel-news-panel');

  if (!tabs.length) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Update active state
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      // Show/hide panels
      const intel = tab.dataset.intel;
      if (alertsPanel) alertsPanel.style.display = intel === 'alerts' ? 'block' : 'none';
      if (signalsPanel) signalsPanel.style.display = intel === 'signals' ? 'block' : 'none';
      if (newsPanel) newsPanel.style.display = intel === 'news' ? 'block' : 'none';
    });
  });
}

// ═══════════════════════════════════════════════════════
// PREDICTIVE SCORING
// ═══════════════════════════════════════════════════════
function initPredictiveScoring() {
  if (typeof PREDICTIVE_SCORES === 'undefined') return;

  const content = document.getElementById('predictive-content');
  if (!content) return;

  let currentTab = 'ipo';

  function getScoreClass(score) {
    if (score >= 80) return 'very-high';
    if (score >= 60) return 'high';
    if (score >= 40) return 'medium';
    if (score >= 20) return 'low';
    return 'very-low';
  }

  function getRiskClass(score) {
    if (score <= 20) return 'risk-very-low';
    if (score <= 40) return 'risk-low';
    if (score <= 60) return 'risk-moderate';
    if (score <= 80) return 'risk-elevated';
    return 'risk-high';
  }

  function renderIPOReadiness() {
    const companies = Object.entries(PREDICTIVE_SCORES.ipoReadiness.companies)
      .sort((a, b) => b[1].score - a[1].score);

    return `
      <div class="predictive-grid">
        ${companies.map(([name, data]) => {
          const factors = Object.entries(data.factors).slice(0, 6);
          return `
            <div class="predictive-card">
              <div class="predictive-header">
                <div class="predictive-company">${name}</div>
                <div class="predictive-score">
                  <div class="score-circle ${getScoreClass(data.score)}">${data.score}</div>
                  <div class="score-trend ${data.trend}">${data.trend === 'up' ? '↑ Rising' : data.trend === 'down' ? '↓ Falling' : '→ Stable'}</div>
                </div>
              </div>

              <div class="predictive-factors">
                ${factors.map(([factor, value]) => `
                  <div class="factor-row">
                    <span class="factor-name">${factor.replace(/([A-Z])/g, ' $1').trim()}</span>
                    <div class="factor-bar"><div class="factor-fill" style="width: ${value}%"></div></div>
                    <span class="factor-value">${value}</span>
                  </div>
                `).join('')}
              </div>

              <div class="predictive-analysis">${data.analysis}</div>

              <div class="predictive-footer">
                <span>Updated: ${data.lastUpdated}</span>
                <span>IPO Readiness Score</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function renderMATargets() {
    const companies = Object.entries(PREDICTIVE_SCORES.maTarget.companies)
      .sort((a, b) => b[1].score - a[1].score);

    return `
      <div class="predictive-grid">
        ${companies.map(([name, data]) => {
          const acquirers = (data.potentialAcquirers || []).map(a =>
            `<span class="acquirer-tag">${a}</span>`
          ).join('');

          return `
            <div class="predictive-card">
              <div class="predictive-header">
                <div class="predictive-company">${name}</div>
                <div class="predictive-score">
                  <div class="score-circle ${getScoreClass(data.score)}">${data.score}</div>
                  <div class="score-trend ${data.trend}">${data.trend === 'up' ? '↑ Rising' : data.trend === 'down' ? '↓ Falling' : '→ Stable'}</div>
                </div>
              </div>

              <div style="margin-bottom: 16px;">
                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">Potential Acquirers:</div>
                <div class="acquirer-list">${acquirers}</div>
              </div>

              <div class="predictive-analysis">${data.analysis}</div>

              <div class="predictive-footer">
                <span>Updated: ${data.lastUpdated}</span>
                <span>M&A Target Score</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function renderFailureRisk() {
    const companies = Object.entries(PREDICTIVE_SCORES.failureRisk.companies)
      .sort((a, b) => b[1].score - a[1].score);

    return `
      <div class="predictive-grid">
        ${companies.map(([name, data]) => {
          const riskLevel = data.score <= 20 ? 'Very Low' :
                           data.score <= 40 ? 'Low' :
                           data.score <= 60 ? 'Moderate' :
                           data.score <= 80 ? 'Elevated' : 'High';

          return `
            <div class="predictive-card">
              <div class="predictive-header">
                <div class="predictive-company">${name}</div>
                <div class="predictive-score">
                  <div class="score-circle ${getScoreClass(100 - data.score)}">${data.score}</div>
                  <div class="score-trend ${data.trend === 'up' ? 'down' : data.trend === 'down' ? 'up' : 'stable'}">
                    ${data.trend === 'up' ? '↑ Increasing' : data.trend === 'down' ? '↓ Decreasing' : '→ Stable'}
                  </div>
                </div>
              </div>

              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding: 12px; background: var(--bg-tertiary); border-radius: var(--radius-sm);">
                <div>
                  <div style="font-size: 11px; color: var(--text-muted);">RISK LEVEL</div>
                  <div class="${getRiskClass(data.score)}" style="font-size: 16px; font-weight: 600;">${riskLevel}</div>
                </div>
                <div style="text-align: right;">
                  <div style="font-size: 11px; color: var(--text-muted);">RUNWAY</div>
                  <div style="font-size: 16px; font-weight: 600; color: var(--text-primary);">${data.runway}</div>
                </div>
              </div>

              <div class="predictive-analysis">${data.analysis}</div>

              <div class="predictive-footer">
                <span>Updated: ${data.lastUpdated}</span>
                <span>Failure Risk Score</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function renderNextRound() {
    const predictions = Object.entries(PREDICTIVE_SCORES.nextRound.predictions)
      .sort((a, b) => b[1].confidence - a[1].confidence);

    return `
      <div class="predictive-grid">
        ${predictions.map(([name, data]) => {
          const confClass = data.confidence >= 70 ? 'high' : data.confidence >= 50 ? 'medium' : 'low';
          const investors = (data.likelyInvestors || []).slice(0, 3).map(i =>
            `<span class="holder-tag">${i}</span>`
          ).join('');

          return `
            <div class="predictive-card">
              <div class="predictive-header">
                <div class="predictive-company">${name}</div>
                <div class="predictive-score">
                  <span class="confidence-badge ${confClass}">${data.confidence}% Confidence</span>
                </div>
              </div>

              <div class="prediction-highlight">
                <div class="prediction-item">
                  <div class="label">Timing</div>
                  <div class="value">${data.predictedTiming}</div>
                </div>
                <div class="prediction-item">
                  <div class="label">Size</div>
                  <div class="value">${data.predictedSize}</div>
                </div>
                <div class="prediction-item">
                  <div class="label">Valuation</div>
                  <div class="value">${data.predictedValuation}</div>
                </div>
              </div>

              <div style="margin-bottom: 16px;">
                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">Likely Investors:</div>
                <div class="secondary-holders">${investors}</div>
              </div>

              <div class="predictive-analysis"><strong>Catalyst:</strong> ${data.catalyst}</div>

              <div class="predictive-footer">
                <span>Updated: ${data.lastUpdated}</span>
                <span>Next Round Prediction</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function renderTab() {
    switch (currentTab) {
      case 'ipo':
        content.innerHTML = renderIPOReadiness();
        break;
      case 'ma':
        content.innerHTML = renderMATargets();
        break;
      case 'risk':
        content.innerHTML = renderFailureRisk();
        break;
      case 'next-round':
        content.innerHTML = renderNextRound();
        break;
    }
  }

  // Tab switching
  document.querySelectorAll('.predictive-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.predictive-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentTab = tab.dataset.tab;
      renderTab();
    });
  });

  renderTab();
}

// ═══════════════════════════════════════════════════════
// PHASE 2: INTERACTIVE NETWORK GRAPH (D3.js)
// ═══════════════════════════════════════════════════════
function initNetworkGraph() {
  if (typeof NETWORK_GRAPH === 'undefined' || typeof d3 === 'undefined') return;

  const container = document.getElementById('network-canvas');
  if (!container) return;

  const width = container.clientWidth || 900;
  const height = 600;

  // Clear any existing SVG
  container.innerHTML = '';

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height]);

  // Zoom container
  const g = svg.append('g');
  svg.call(d3.zoom().scaleExtent([0.2, 5]).on('zoom', (e) => {
    g.attr('transform', e.transform);
  }));

  // Build node/edge maps
  const nodeMap = {};
  NETWORK_GRAPH.nodes.forEach(n => { nodeMap[n.id] = { ...n }; });

  // Filter edges to only include those with valid nodes
  let edges = NETWORK_GRAPH.edges.filter(e => nodeMap[e.source] && nodeMap[e.target]);
  let nodes = NETWORK_GRAPH.nodes.filter(n => {
    return edges.some(e => e.source === n.id || e.target === n.id);
  });

  // Color scheme
  const typeColors = {
    company: '#FF6B2C',
    investor: '#f59e0b',
    person: '#8b5cf6'
  };

  const edgeColors = {
    investment: 'rgba(245,158,11,0.25)',
    founder: 'rgba(139,92,246,0.3)',
    mafia: 'rgba(255,107,44,0.3)',
    'co-investor': 'rgba(34,197,94,0.15)',
    board: 'rgba(96,165,250,0.25)'
  };

  // Node sizing
  function nodeRadius(d) {
    if (d.type === 'company') return 6 + Math.min((edges.filter(e => e.source.id === d.id || e.target.id === d.id).length) * 0.8, 12);
    if (d.type === 'investor') return 5 + Math.min((edges.filter(e => e.source.id === d.id || e.target.id === d.id).length) * 0.6, 10);
    return 4;
  }

  // Simulation
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(d => {
      if (d.type === 'co-investor') return 150;
      if (d.type === 'mafia') return 100;
      return 80;
    }).strength(d => {
      if (d.type === 'co-investor') return 0.1;
      return 0.3;
    }))
    .force('charge', d3.forceManyBody().strength(-120).distanceMax(400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(18))
    .force('x', d3.forceX(width / 2).strength(0.04))
    .force('y', d3.forceY(height / 2).strength(0.04));

  // Draw links
  const link = g.append('g')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('class', d => `network-link edge-${d.type}`)
    .attr('stroke', d => edgeColors[d.type] || 'rgba(255,255,255,0.08)')
    .attr('stroke-width', d => d.type === 'co-investor' ? 0.5 : 1);

  // Draw nodes
  const node = g.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('class', 'network-node')
    .call(d3.drag()
      .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
      .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
    );

  node.append('circle')
    .attr('r', d => nodeRadius(d))
    .attr('fill', d => typeColors[d.type] || '#666');

  node.append('text')
    .attr('dx', d => nodeRadius(d) + 4)
    .attr('dy', 3)
    .text(d => d.label);

  // Tooltip
  const tooltip = document.getElementById('network-tooltip');

  node.on('mouseover', (e, d) => {
    const connected = new Set();
    edges.forEach(edge => {
      const src = typeof edge.source === 'object' ? edge.source.id : edge.source;
      const tgt = typeof edge.target === 'object' ? edge.target.id : edge.target;
      if (src === d.id) connected.add(tgt);
      if (tgt === d.id) connected.add(src);
    });
    connected.add(d.id);

    node.classed('dimmed', n => !connected.has(n.id));
    node.classed('highlighted', n => n.id === d.id);
    link.classed('dimmed', l => {
      const src = typeof l.source === 'object' ? l.source.id : l.source;
      const tgt = typeof l.target === 'object' ? l.target.id : l.target;
      return !connected.has(src) || !connected.has(tgt);
    });
    link.classed('highlight', l => {
      const src = typeof l.source === 'object' ? l.source.id : l.source;
      const tgt = typeof l.target === 'object' ? l.target.id : l.target;
      return (src === d.id || tgt === d.id);
    });

    const connections = edges.filter(edge => {
      const src = typeof edge.source === 'object' ? edge.source.id : edge.source;
      const tgt = typeof edge.target === 'object' ? edge.target.id : edge.target;
      return src === d.id || tgt === d.id;
    });

    let extra = '';
    if (d.type === 'company' && d.sector) extra = `<div class="tt-detail">Sector: ${d.sector}</div>`;
    if (d.type === 'investor' && d.investmentCount) extra = `<div class="tt-detail">${d.investmentCount} investments in dataset</div>`;
    if (d.type === 'person' && d.role) extra = `<div class="tt-detail">${d.role}${d.affiliation ? ' — ' + d.affiliation : ''}</div>`;

    tooltip.innerHTML = `
      <h5>${d.label}</h5>
      <div class="tt-type">${d.type}</div>
      ${extra}
      <div class="tt-detail">${connections.length} connection${connections.length !== 1 ? 's' : ''}</div>
    `;
    tooltip.style.display = 'block';
  })
  .on('mousemove', (e) => {
    const rect = container.getBoundingClientRect();
    tooltip.style.left = (e.clientX - rect.left + 15) + 'px';
    tooltip.style.top = (e.clientY - rect.top - 10) + 'px';
  })
  .on('mouseout', () => {
    node.classed('dimmed', false).classed('highlighted', false);
    link.classed('dimmed', false).classed('highlight', false);
    tooltip.style.display = 'none';
  })
  .on('click', (e, d) => {
    if (d.type === 'company') {
      const comp = COMPANIES.find(c => d.label.includes(c.name) || c.name.includes(d.label));
      if (comp) openCompanyModal(comp.name);
    }
  });

  // Tick
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  // Edge type filter
  document.querySelectorAll('.network-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.network-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.dataset.edge;
      link.attr('display', d => {
        if (filter === 'all') return 'inline';
        return d.type === filter ? 'inline' : 'none';
      });
    });
  });

  // Search
  const searchInput = document.getElementById('network-search');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.toLowerCase().trim();
      if (!q) {
        node.classed('dimmed', false).classed('highlighted', false);
        link.classed('dimmed', false);
        return;
      }
      const matches = new Set();
      nodes.forEach(n => {
        if (n.label.toLowerCase().includes(q)) matches.add(n.id);
      });
      if (matches.size === 0) {
        node.classed('dimmed', true).classed('highlighted', false);
        link.classed('dimmed', true);
        return;
      }
      // Also highlight direct connections
      const connected = new Set(matches);
      edges.forEach(edge => {
        const src = typeof edge.source === 'object' ? edge.source.id : edge.source;
        const tgt = typeof edge.target === 'object' ? edge.target.id : edge.target;
        if (matches.has(src)) connected.add(tgt);
        if (matches.has(tgt)) connected.add(src);
      });
      node.classed('dimmed', n => !connected.has(n.id));
      node.classed('highlighted', n => matches.has(n.id));
      link.classed('dimmed', l => {
        const src = typeof l.source === 'object' ? l.source.id : l.source;
        const tgt = typeof l.target === 'object' ? l.target.id : l.target;
        return !connected.has(src) || !connected.has(tgt);
      });
    });
  }

  // Stats
  const statsEl = document.getElementById('network-stats');
  if (statsEl) {
    statsEl.textContent = `${nodes.length} nodes \u00b7 ${edges.length} connections \u00b7 ${nodes.filter(n => n.type === 'company').length} companies \u00b7 ${nodes.filter(n => n.type === 'investor').length} investors \u00b7 ${nodes.filter(n => n.type === 'person').length} people`;
  }
}

// ═══════════════════════════════════════════════════════
// PHASE 2: PORTFOLIO BUILDER & SCENARIO SIMULATOR
// ═══════════════════════════════════════════════════════
function initPortfolioBuilder() {
  const listEl = document.getElementById('portfolio-company-list');
  const holdingsEl = document.getElementById('portfolio-holdings');
  const searchInput = document.getElementById('portfolio-search');
  if (!listEl) return;

  let portfolio = [];

  // Try loading portfolio from URL hash
  try {
    const params = new URLSearchParams(window.location.hash.slice(1));
    const p = params.get('portfolio');
    if (p) portfolio = p.split('|').filter(Boolean);
  } catch(e) {}

  // Populate company list
  const sortedCompanies = [...COMPANIES].sort((a, b) => a.name.localeCompare(b.name));

  function renderCompanyList(filter = '') {
    const q = filter.toLowerCase();
    const filtered = q ? sortedCompanies.filter(c => c.name.toLowerCase().includes(q) || (c.sector || '').toLowerCase().includes(q)) : sortedCompanies;
    listEl.innerHTML = filtered.slice(0, 80).map(c => `
      <div class="portfolio-company-item ${portfolio.includes(c.name) ? 'in-portfolio' : ''}" data-name="${c.name.replace(/"/g, '&quot;')}">
        <span>${c.name}</span>
        <span class="pci-sector">${c.sector || ''}</span>
      </div>
    `).join('');

    listEl.querySelectorAll('.portfolio-company-item').forEach(item => {
      item.addEventListener('click', () => {
        const name = item.dataset.name;
        if (portfolio.includes(name)) {
          portfolio = portfolio.filter(n => n !== name);
        } else {
          portfolio.push(name);
        }
        renderCompanyList(searchInput?.value || '');
        renderPortfolio();
      });
    });
  }

  function renderPortfolio() {
    if (portfolio.length === 0) {
      holdingsEl.innerHTML = '<div class="portfolio-empty">Click companies on the left to build your portfolio</div>';
      document.getElementById('portfolio-sector-bars').innerHTML = '';
      document.getElementById('portfolio-stage-bars').innerHTML = '';
      document.getElementById('portfolio-metrics').innerHTML = '';
      document.getElementById('scenario-results').innerHTML = '';
      return;
    }

    const companies = portfolio.map(name => COMPANIES.find(c => c.name === name)).filter(Boolean);

    // Holdings table
    holdingsEl.innerHTML = companies.map(c => {
      const iscore = getInnovatorScore(c.name);
      const score = iscore ? iscore.composite.toFixed(0) : '—';
      const tier = iscore ? iscore.tier : '';
      const tierColor = tier === 'elite' ? '#22c55e' : tier === 'strong' ? '#3b82f6' : tier === 'promising' ? '#f59e0b' : '#6b7280';
      return `
        <div class="portfolio-holding-row">
          <div>
            <div class="ph-name" onclick="openCompanyModal('${c.name.replace(/'/g, "\\'")}')">${c.name}</div>
            <div class="ph-sector">${c.sector || ''}</div>
          </div>
          <div class="ph-valuation">${c.valuation || '—'}</div>
          <div class="ph-score" style="color:${tierColor}">${score} IS\u2122</div>
          <button class="ph-remove" data-name="${c.name.replace(/"/g, '&quot;')}">\u00d7</button>
        </div>
      `;
    }).join('');

    holdingsEl.querySelectorAll('.ph-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        portfolio = portfolio.filter(n => n !== btn.dataset.name);
        renderCompanyList(searchInput?.value || '');
        renderPortfolio();
      });
    });

    // Sector exposure
    const sectorCounts = {};
    companies.forEach(c => { sectorCounts[c.sector || 'Unknown'] = (sectorCounts[c.sector || 'Unknown'] || 0) + 1; });
    const sectorBars = Object.entries(sectorCounts).sort((a, b) => b[1] - a[1]);
    const maxSec = Math.max(...sectorBars.map(s => s[1]));
    const sectorColors = ['#FF6B2C', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#ef4444'];

    document.getElementById('portfolio-sector-bars').innerHTML = sectorBars.map((s, i) => `
      <div class="portfolio-bar-item">
        <span class="portfolio-bar-label">${s[0]}</span>
        <div class="portfolio-bar-track">
          <div class="portfolio-bar-fill" style="width:${(s[1]/maxSec)*100}%; background:${sectorColors[i % sectorColors.length]}"></div>
        </div>
        <span class="portfolio-bar-pct">${((s[1]/companies.length)*100).toFixed(0)}%</span>
      </div>
    `).join('');

    // Stage distribution
    const stageCounts = {};
    companies.forEach(c => {
      const stage = c.stage || (c.valuation && c.valuation.includes('Public') ? 'Public' : 'Private');
      stageCounts[stage] = (stageCounts[stage] || 0) + 1;
    });
    const stageBars = Object.entries(stageCounts).sort((a, b) => b[1] - a[1]);
    const maxStage = Math.max(...stageBars.map(s => s[1]));

    document.getElementById('portfolio-stage-bars').innerHTML = stageBars.map((s, i) => `
      <div class="portfolio-bar-item">
        <span class="portfolio-bar-label">${s[0]}</span>
        <div class="portfolio-bar-track">
          <div class="portfolio-bar-fill" style="width:${(s[1]/maxStage)*100}%; background:${sectorColors[(i+3) % sectorColors.length]}"></div>
        </div>
        <span class="portfolio-bar-pct">${((s[1]/companies.length)*100).toFixed(0)}%</span>
      </div>
    `).join('');

    // Portfolio metrics
    const avgScore = companies.reduce((sum, c) => {
      const iscore = getInnovatorScore(c.name);
      return sum + (iscore ? iscore.composite : 0);
    }, 0) / companies.length;

    const uniqueSectors = new Set(companies.map(c => c.sector)).size;
    const diversificationScore = Math.min(100, Math.round((uniqueSectors / Math.max(companies.length, 1)) * 100 * 1.5));

    const govCompanies = typeof GOV_CONTRACTS !== 'undefined'
      ? companies.filter(c => GOV_CONTRACTS.some(g => g.company === c.name)).length
      : 0;

    document.getElementById('portfolio-metrics').innerHTML = `
      <div class="portfolio-metric-card">
        <div class="portfolio-metric-value">${companies.length}</div>
        <div class="portfolio-metric-label">Companies</div>
      </div>
      <div class="portfolio-metric-card">
        <div class="portfolio-metric-value">${avgScore.toFixed(0)}</div>
        <div class="portfolio-metric-label">Avg IS\u2122</div>
      </div>
      <div class="portfolio-metric-card">
        <div class="portfolio-metric-value" style="color:${diversificationScore > 70 ? '#22c55e' : diversificationScore > 40 ? '#f59e0b' : '#ef4444'}">${diversificationScore}</div>
        <div class="portfolio-metric-label">Diversification</div>
      </div>
      <div class="portfolio-metric-card">
        <div class="portfolio-metric-value">${govCompanies}</div>
        <div class="portfolio-metric-label">Gov Contracts</div>
      </div>
    `;

    // Update URL hash
    const hash = new URLSearchParams();
    hash.set('portfolio', portfolio.join('|'));
    window.history.replaceState({}, '', '#' + hash.toString());
  }

  // Scenario simulator
  const scenarioBtn = document.getElementById('scenario-run');
  if (scenarioBtn) {
    scenarioBtn.addEventListener('click', () => {
      const scenario = document.getElementById('scenario-select')?.value || 'defense-up';
      const companies = portfolio.map(name => COMPANIES.find(c => c.name === name)).filter(Boolean);
      if (companies.length === 0) {
        document.getElementById('scenario-results').innerHTML = '<p style="color:var(--text-muted)">Add companies to your portfolio first.</p>';
        return;
      }

      const scenarioConfig = {
        'defense-up': { label: 'Defense Budget +15%', sectors: { 'Defense & Security': 3, 'Space & Aerospace': 2, 'Advanced Manufacturing': 1, 'Cybersecurity': 2 }, default: 0 },
        'defense-down': { label: 'Defense Budget \u221210%', sectors: { 'Defense & Security': -2, 'Space & Aerospace': -1 }, default: 0 },
        'ai-boom': { label: 'AI Investment Boom', sectors: { 'Artificial Intelligence': 3, 'Robotics & Automation': 2, 'Cybersecurity': 1, 'Advanced Manufacturing': 1 }, default: 0 },
        'space-race': { label: 'Space Race Acceleration', sectors: { 'Space & Aerospace': 3, 'Defense & Security': 1, 'Advanced Manufacturing': 1 }, default: 0 },
        'climate-push': { label: 'Climate Policy Push', sectors: { 'Energy & Fusion': 3, 'Climate & Carbon': 3, 'Sustainable Materials': 2, 'Next-Gen Mobility': 1 }, default: 0 },
        'recession': { label: 'Recession Scenario', sectors: { 'Defense & Security': 1, 'Cybersecurity': 0 }, default: -2 }
      };

      const config = scenarioConfig[scenario] || scenarioConfig['defense-up'];

      const results = companies.map(c => {
        const sectorImpact = config.sectors[c.sector] !== undefined ? config.sectors[c.sector] : (config.default || 0);
        const govBonus = (typeof GOV_CONTRACTS !== 'undefined' && GOV_CONTRACTS.some(g => g.company === c.name) && sectorImpact > 0) ? 1 : 0;
        const totalImpact = sectorImpact + govBonus;
        const impactClass = totalImpact > 0 ? 'positive' : totalImpact < 0 ? 'negative' : 'neutral';
        const impactLabel = totalImpact > 0 ? `+${totalImpact} Tailwind` : totalImpact < 0 ? `${totalImpact} Headwind` : 'Neutral';
        return { name: c.name, impact: totalImpact, impactClass, impactLabel, sector: c.sector };
      }).sort((a, b) => b.impact - a.impact);

      document.getElementById('scenario-results').innerHTML = `
        <p style="margin-bottom:12px; font-size:13px; color:var(--text-muted)">Scenario: <strong style="color:var(--text-primary)">${config.label}</strong></p>
        ${results.map(r => `
          <div class="scenario-result-item">
            <span class="scenario-company">${r.name} <span style="font-size:11px;color:var(--text-muted)">${r.sector}</span></span>
            <span class="scenario-impact ${r.impactClass}">${r.impactLabel}</span>
          </div>
        `).join('')}
      `;
    });
  }

  // Share & clear buttons
  document.getElementById('portfolio-share')?.addEventListener('click', () => {
    const url = window.location.href;
    navigator.clipboard?.writeText(url).then(() => {
      const btn = document.getElementById('portfolio-share');
      btn.textContent = '\u2713 Copied!';
      setTimeout(() => { btn.textContent = '\ud83d\udccb Copy Shareable URL'; }, 1500);
    });
  });

  document.getElementById('portfolio-clear')?.addEventListener('click', () => {
    portfolio = [];
    window.history.replaceState({}, '', window.location.pathname + window.location.search);
    renderCompanyList(searchInput?.value || '');
    renderPortfolio();
  });

  // Search filter
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      renderCompanyList(searchInput.value);
    });
  }

  renderCompanyList();
  renderPortfolio();
}

// ═══════════════════════════════════════════════════════
// PHASE 2: AI INVESTMENT MEMO GENERATOR
// ═══════════════════════════════════════════════════════
function initAIMemo() {
  const companySelect = document.getElementById('memo-company');
  const generateBtn = document.getElementById('memo-generate');
  const outputEl = document.getElementById('memo-output');
  if (!companySelect || !generateBtn) return;

  // Populate company dropdown
  const sorted = [...COMPANIES].sort((a, b) => a.name.localeCompare(b.name));
  sorted.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = `${c.name} — ${c.sector || 'Unknown'}`;
    companySelect.appendChild(opt);
  });

  // Restore saved API key
  const savedKey = localStorage.getItem('til-memo-api-key') || '';
  const keyInput = document.getElementById('memo-api-key');
  if (keyInput && savedKey) keyInput.value = savedKey;

  // Build context from all our data for a company
  function buildCompanyContext(companyName) {
    const company = COMPANIES.find(c => c.name === companyName);
    if (!company) return null;

    let context = `Company: ${company.name}\n`;
    context += `Sector: ${company.sector || 'Unknown'}\n`;
    context += `Location: ${company.location || 'Unknown'}\n`;
    context += `Founded: ${company.founded || 'Unknown'}\n`;
    context += `Valuation: ${company.valuation || 'Unknown'}\n`;
    context += `Total Raised: ${company.totalRaised || 'Unknown'}\n`;
    context += `Stage: ${company.stage || 'Unknown'}\n`;
    context += `Thesis: ${company.thesis || ''}\n`;
    context += `Signal: ${company.signal || ''}\n`;
    if (company.recentEvent) context += `Recent Event: ${company.recentEvent}\n`;
    if (company.keyPeople && company.keyPeople.length) context += `Key People: ${company.keyPeople.join(', ')}\n`;
    if (company.investors && company.investors.length) context += `Investors: ${company.investors.join(', ')}\n`;
    if (company.competitors && company.competitors.length) context += `Competitors: ${company.competitors.join(', ')}\n`;

    // Innovator Score
    const iscore = typeof INNOVATOR_SCORES !== 'undefined' ? INNOVATOR_SCORES.find(s => s.company === companyName) : null;
    if (iscore) {
      context += `\nInnovator Score: ${iscore.composite.toFixed(1)}/100 (${iscore.tier})\n`;
      context += `  Tech Moat: ${iscore.techMoat}/10, Momentum: ${iscore.momentum}/10, Team: ${iscore.teamPedigree}/10\n`;
      context += `  Market Gravity: ${iscore.marketGravity}/10, Capital Efficiency: ${iscore.capitalEfficiency}/10, Gov Traction: ${iscore.govTraction}/10\n`;
      context += `  Note: ${iscore.note}\n`;
    }

    // Gov contracts
    const govData = typeof GOV_CONTRACTS !== 'undefined' ? GOV_CONTRACTS.find(g => g.company === companyName) : null;
    if (govData) {
      context += `\nGovernment Contracts: $${govData.totalGovValue} total\n`;
      context += `  Agencies: ${govData.agencies.join(', ')}\n`;
      context += `  SBIR Status: ${govData.sbirStatus || 'None'}\n`;
      context += `  Clearance: ${govData.clearanceLevel || 'None'}\n`;
      if (govData.keyContracts) context += `  Key Contracts: ${govData.keyContracts.slice(0, 3).join('; ')}\n`;
    }

    // Patent intel
    const patent = typeof PATENT_INTEL !== 'undefined' ? PATENT_INTEL.find(p => p.company === companyName) : null;
    if (patent) {
      context += `\nPatent Portfolio: ${patent.totalPatents} patents, filing ${patent.velocity} patents/year (${patent.velocityTrend})\n`;
      context += `  IP Moat Score: ${patent.ipMoatScore}/10\n`;
      context += `  Tech Areas: ${patent.techAreas.join(', ')}\n`;
    }

    // Alt data
    const altData = typeof ALT_DATA_SIGNALS !== 'undefined' ? ALT_DATA_SIGNALS.find(a => a.company === companyName) : null;
    if (altData) {
      context += `\nAlternative Data:\n`;
      context += `  Hiring Velocity: ${altData.hiringVelocity}, Headcount: ~${altData.headcountEstimate}\n`;
      context += `  Web Traffic: ${altData.webTraffic}, News Sentiment: ${altData.newsSentiment}\n`;
      context += `  Signal Strength: ${altData.signalStrength}/10\n`;
      context += `  Key Signal: ${altData.keySignal}\n`;
    }

    return { company, context };
  }

  function getMemoPrompt(companyName, memoType) {
    const data = buildCompanyContext(companyName);
    if (!data) return null;

    const prompts = {
      investment: `You are a senior analyst at a top-tier venture capital firm. Using the structured data below from The Innovators League intelligence platform, write a professional investment memo for ${companyName}.

Structure your memo with these sections:
1. **Executive Summary** — 2-3 sentence overview
2. **Company Overview** — What they do, market position, key metrics
3. **Investment Thesis** — Bull case with specific data points
4. **Key Risks** — Bear case, competitive threats, execution risks
5. **Proprietary Signals** — What our Innovator Score, alt data, patent data, and gov contract intelligence reveal
6. **Recommendation** — Investment attractiveness rating

Use specific numbers and data from the context. Be analytical, not promotional.`,

      competitive: `You are a competitive intelligence analyst. Using the data below, write a competitive analysis for ${companyName}.

Structure with:
1. **Market Position** — Where the company sits in its competitive landscape
2. **Competitive Advantages** — Moats based on patent data, gov contracts, team pedigree
3. **Key Competitors** — Direct and indirect competitors with comparison
4. **Vulnerability Assessment** — Where competitors could gain ground
5. **Strategic Outlook** — 12-24 month competitive dynamics`,

      sector: `You are a sector analyst. Using the data below for ${companyName}, write a sector brief covering the broader ${data.company.sector} landscape.

Structure with:
1. **Sector Overview** — Current state, key trends, market size
2. **Featured Company Deep-Dive** — ${companyName}'s position and metrics
3. **Sector Signals** — What hiring, patents, and government spending tell us
4. **Investment Themes** — Key themes for investors in this sector
5. **Outlook** — 12-month sector trajectory`,

      risk: `You are a risk analyst. Using the data below, write a risk assessment for ${companyName}.

Structure with:
1. **Risk Summary** — Overall risk level and key factors
2. **Technology Risk** — Based on patent portfolio and TRL
3. **Market Risk** — Competition, timing, TAM uncertainty
4. **Execution Risk** — Team, capital efficiency, scaling challenges
5. **Regulatory & Government Risk** — Based on contract data and sector
6. **Signal Warnings** — What alt data signals suggest about trajectory`
    };

    return {
      systemPrompt: 'You are a world-class technology investment analyst. Write professional, data-driven analysis. Use markdown formatting with headers, bullet points, and bold text. Reference specific data points.',
      userPrompt: `${prompts[memoType] || prompts.investment}\n\n--- DATA FROM THE INNOVATORS LEAGUE ---\n${data.context}`
    };
  }

  generateBtn.addEventListener('click', async () => {
    const companyName = companySelect.value;
    const memoType = document.getElementById('memo-type')?.value || 'investment';
    const provider = document.getElementById('memo-provider')?.value || 'anthropic';
    const apiKey = document.getElementById('memo-api-key')?.value?.trim();

    if (!companyName) { alert('Please select a company.'); return; }
    if (!apiKey) { alert('Please enter your API key.'); return; }

    // Save key to localStorage
    localStorage.setItem('til-memo-api-key', apiKey);

    const prompt = getMemoPrompt(companyName, memoType);
    if (!prompt) { alert('Company not found.'); return; }

    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    outputEl.innerHTML = '<div class="memo-content"><p style="color:var(--text-muted)">Generating investment memo...<span class="memo-streaming-cursor"></span></p></div>';

    try {
      let responseText = '';

      if (provider === 'anthropic') {
        const resp = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01',
            'anthropic-dangerous-direct-browser-access': 'true'
          },
          body: JSON.stringify({
            model: 'claude-sonnet-4-20250514',
            max_tokens: 2048,
            system: prompt.systemPrompt,
            messages: [{ role: 'user', content: prompt.userPrompt }]
          })
        });
        const data = await resp.json();
        if (data.error) throw new Error(data.error.message);
        responseText = data.content?.[0]?.text || 'No response generated.';
      } else {
        const resp = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
          },
          body: JSON.stringify({
            model: 'gpt-4o',
            max_tokens: 2048,
            messages: [
              { role: 'system', content: prompt.systemPrompt },
              { role: 'user', content: prompt.userPrompt }
            ]
          })
        });
        const data = await resp.json();
        if (data.error) throw new Error(data.error.message);
        responseText = data.choices?.[0]?.message?.content || 'No response generated.';
      }

      // Simple markdown to HTML
      const html = responseText
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h4>$1</h4>')
        .replace(/^# (.+)$/gm, '<h3>$1</h3>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

      const memoTypes = { investment: 'Investment Memo', competitive: 'Competitive Analysis', sector: 'Sector Brief', risk: 'Risk Assessment' };

      outputEl.innerHTML = `
        <div class="memo-content">
          <h3>${companyName}</h3>
          <div class="memo-subtitle">${memoTypes[memoType] || 'Investment Memo'} \u00b7 Generated ${new Date().toLocaleDateString()} \u00b7 The Innovators League</div>
          <p>${html}</p>
          <div class="memo-actions">
            <button class="memo-action-btn" onclick="navigator.clipboard?.writeText(document.querySelector('.memo-content')?.innerText || '').then(() => { this.textContent = '\u2713 Copied!'; setTimeout(() => this.textContent = '\ud83d\udccb Copy Text', 1500); })">📋 Copy Text</button>
          </div>
        </div>
      `;
    } catch (err) {
      outputEl.innerHTML = `<div class="memo-content"><p style="color:#ef4444"><strong>Error:</strong> ${err.message}</p><p style="color:var(--text-muted)">Check your API key and try again. Make sure you have credits available.</p></div>`;
    }

    generateBtn.disabled = false;
    generateBtn.textContent = '\u26a1 Generate Memo';
  });
}

// ═══════════════════════════════════════════════════════
// AI QUERY INTERFACE — NATURAL LANGUAGE SEARCH
// ═══════════════════════════════════════════════════════
function initAIQuery() {
  const queryInput = document.getElementById('ai-query-input');
  const queryBtn = document.getElementById('ai-query-btn');
  const resultDiv = document.getElementById('ai-query-result');

  if (!queryInput || !queryBtn) return;

  // Query suggestion chips
  document.querySelectorAll('.ai-suggestion').forEach(chip => {
    chip.addEventListener('click', () => {
      queryInput.value = chip.dataset.query;
      executeAIQuery(chip.dataset.query);
    });
  });

  // Search button click
  queryBtn.addEventListener('click', () => {
    const query = queryInput.value.trim();
    if (query) executeAIQuery(query);
  });

  // Enter key
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const query = queryInput.value.trim();
      if (query) executeAIQuery(query);
    }
  });

  function executeAIQuery(query) {
    // Parse the natural language query locally
    const parsed = parseNaturalLanguageQuery(query);

    // Show interpretation
    if (resultDiv) {
      resultDiv.style.display = 'block';
      resultDiv.innerHTML = `
        <div class="ai-query-interpretation">
          <span class="ai-interpretation-label">Interpreted as:</span>
          <span class="ai-interpretation-text">${parsed.explanation}</span>
        </div>
      `;
    }

    // Apply the parsed filters
    applyParsedQuery(parsed);
  }

  function parseNaturalLanguageQuery(query) {
    const q = query.toLowerCase();
    const result = {
      sector: null,
      country: null,
      state: null,
      stage: null,
      minFunding: null,
      minValuation: null,
      foundedAfter: null,
      hasGovContracts: false,
      searchTerm: null,
      explanation: ''
    };

    const explanationParts = [];

    // Sector detection
    const sectorKeywords = {
      'defense': 'Defense Technology',
      'defence': 'Defense Technology',
      'military': 'Defense Technology',
      'space': 'Space Technology',
      'aerospace': 'Aerospace & Aviation',
      'aviation': 'Aerospace & Aviation',
      'ai': 'AI Infrastructure',
      'artificial intelligence': 'AI Infrastructure',
      'robotics': 'Robotics',
      'robot': 'Robotics',
      'energy': 'Energy & Fusion',
      'fusion': 'Energy & Fusion',
      'nuclear': 'Energy & Fusion',
      'autonomous': 'Autonomous Vehicles',
      'self-driving': 'Autonomous Vehicles',
      'semiconductor': 'Semiconductors',
      'chip': 'Semiconductors',
      'climate': 'Climate Tech',
      'manufacturing': 'Advanced Manufacturing',
      'biotech': 'Biotech',
      'quantum': 'Quantum Computing'
    };

    for (const [keyword, sector] of Object.entries(sectorKeywords)) {
      if (q.includes(keyword)) {
        result.sector = sector;
        explanationParts.push(`sector: ${sector}`);
        break;
      }
    }

    // State detection (US states)
    const statePatterns = {
      'california': 'CA', 'ca': 'CA',
      'texas': 'TX', 'tx': 'TX',
      'new york': 'NY', 'ny': 'NY',
      'florida': 'FL', 'fl': 'FL',
      'washington': 'WA', 'wa': 'WA',
      'colorado': 'CO', 'co': 'CO',
      'virginia': 'VA', 'va': 'VA',
      'massachusetts': 'MA', 'ma': 'MA',
      'arizona': 'AZ', 'az': 'AZ',
      'ohio': 'OH',
      'georgia': 'GA',
      'michigan': 'MI',
      'pennsylvania': 'PA',
      'el segundo': 'CA',
      'silicon valley': 'CA',
      'san francisco': 'CA',
      'los angeles': 'CA',
      'austin': 'TX',
      'seattle': 'WA',
      'boston': 'MA',
      'denver': 'CO'
    };

    for (const [pattern, stateCode] of Object.entries(statePatterns)) {
      if (q.includes(pattern)) {
        result.state = stateCode;
        result.country = 'United States';
        explanationParts.push(`state: ${STATE_NAMES[stateCode] || stateCode}`);
        break;
      }
    }

    // Country detection
    if (!result.state) {
      const countryPatterns = {
        'united states': 'United States', 'usa': 'United States', 'us': 'United States', 'american': 'United States',
        'united kingdom': 'United Kingdom', 'uk': 'United Kingdom', 'british': 'United Kingdom',
        'germany': 'Germany', 'german': 'Germany',
        'france': 'France', 'french': 'France',
        'israel': 'Israel', 'israeli': 'Israel',
        'canada': 'Canada', 'canadian': 'Canada'
      };

      for (const [pattern, country] of Object.entries(countryPatterns)) {
        if (q.includes(pattern)) {
          result.country = country;
          explanationParts.push(`country: ${country}`);
          break;
        }
      }
    }

    // Stage detection
    const stagePatterns = {
      'seed': 'Seed',
      'series a': 'Series A',
      'series b': 'Series B',
      'series c': 'Series C',
      'series d': 'Series D+',
      'late stage': 'Late Stage',
      'pre-ipo': 'Pre-IPO',
      'public': 'Public',
      'growth stage': ['Series B', 'Series C', 'Series D+', 'Late Stage'],
      'early stage': ['Seed', 'Series A']
    };

    for (const [pattern, stage] of Object.entries(stagePatterns)) {
      if (q.includes(pattern)) {
        result.stage = stage;
        explanationParts.push(`stage: ${Array.isArray(stage) ? stage.join(' or ') : stage}`);
        break;
      }
    }

    // Funding amount detection
    const fundingMatch = q.match(/(?:over|more than|at least|>\s*)?\$?(\d+(?:\.\d+)?)\s*(billion|b|million|m)\s*(?:funding|raised)?/i);
    if (fundingMatch) {
      let amount = parseFloat(fundingMatch[1]);
      const unit = fundingMatch[2].toLowerCase();
      if (unit === 'billion' || unit === 'b') amount *= 1000000000;
      else if (unit === 'million' || unit === 'm') amount *= 1000000;
      result.minFunding = amount;
      explanationParts.push(`min funding: $${formatValuation(amount)}`);
    }

    // Valuation detection
    const valuationMatch = q.match(/(?:valuation|valued at|worth).*?(?:over|more than|at least)?\s*\$?(\d+(?:\.\d+)?)\s*(billion|b|million|m)/i);
    if (valuationMatch) {
      let amount = parseFloat(valuationMatch[1]);
      const unit = valuationMatch[2].toLowerCase();
      if (unit === 'billion' || unit === 'b') amount *= 1000000000;
      else if (unit === 'million' || unit === 'm') amount *= 1000000;
      result.minValuation = amount;
      explanationParts.push(`min valuation: $${formatValuation(amount)}`);
    }

    // Unicorn detection
    if (q.includes('unicorn')) {
      result.minValuation = 1000000000;
      explanationParts.push('valuation: $1B+ (unicorn)');
    }

    // Year founded detection
    const yearMatch = q.match(/(?:founded|started|created)\s*(?:after|since|in)\s*(\d{4})/i);
    if (yearMatch) {
      result.foundedAfter = parseInt(yearMatch[1]);
      explanationParts.push(`founded after: ${yearMatch[1]}`);
    }

    // Government contracts
    if (q.includes('government') || q.includes('gov contract') || q.includes('gov-backed') || q.includes('federal') || q.includes('dod') || q.includes('defense contract')) {
      result.hasGovContracts = true;
      explanationParts.push('has government contracts');
    }

    result.explanation = explanationParts.length > 0
      ? explanationParts.join(' | ')
      : 'Showing all companies (no specific filters detected)';

    return result;
  }

  function applyParsedQuery(parsed) {
    // Set filters
    if (parsed.sector) {
      const sectorFilter = document.getElementById('sector-filter');
      if (sectorFilter) {
        // Find the matching option
        const options = sectorFilter.options;
        for (let i = 0; i < options.length; i++) {
          if (options[i].value === parsed.sector) {
            sectorFilter.value = parsed.sector;
            break;
          }
        }
      }
      // Sync chips
      document.querySelectorAll('.chip').forEach(c => {
        c.classList.toggle('active', c.dataset.sector === parsed.sector);
      });
    }

    if (parsed.country) {
      const countryFilter = document.getElementById('country-filter');
      if (countryFilter) countryFilter.value = parsed.country;
    }

    if (parsed.state) {
      const stateFilter = document.getElementById('state-filter');
      if (stateFilter) stateFilter.value = parsed.state;
      updateStateFilterVisibility();
    }

    if (parsed.stage && !Array.isArray(parsed.stage)) {
      const stageFilter = document.getElementById('stage-filter');
      if (stageFilter) stageFilter.value = parsed.stage;
    }

    // Apply filters with additional constraints
    let filtered = COMPANIES;

    // Apply standard filters
    if (parsed.sector) {
      filtered = filtered.filter(c => c.sector === parsed.sector);
    }
    if (parsed.country) {
      filtered = filtered.filter(c => getCountry(c.state, c.location) === parsed.country);
    }
    if (parsed.state) {
      filtered = filtered.filter(c => c.state === parsed.state);
    }
    if (parsed.stage) {
      if (Array.isArray(parsed.stage)) {
        filtered = filtered.filter(c => parsed.stage.includes(c.fundingStage));
      } else {
        filtered = filtered.filter(c => c.fundingStage === parsed.stage);
      }
    }

    // Additional filters
    if (parsed.minFunding) {
      filtered = filtered.filter(c => {
        const raised = parseFunding(c.totalRaised);
        return raised >= parsed.minFunding;
      });
    }

    if (parsed.minValuation) {
      filtered = filtered.filter(c => {
        const val = parseValuation(c.valuation);
        return val >= parsed.minValuation;
      });
    }

    if (parsed.foundedAfter) {
      filtered = filtered.filter(c => {
        const founded = parseInt(c.founded);
        return founded && founded >= parsed.foundedAfter;
      });
    }

    if (parsed.hasGovContracts && typeof GOV_CONTRACTS !== 'undefined') {
      const companiesWithContracts = new Set(GOV_CONTRACTS.map(c => c.company));
      filtered = filtered.filter(c => companiesWithContracts.has(c.name));
    }

    // Render results
    renderCompanies(filtered);
    updateResultsCount(filtered.length);

    // Scroll to results
    document.getElementById('company-grid')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ═══════════════════════════════════════════════════════
// ROS INNOVATOR 50 — ANNUAL RANKING
// ═══════════════════════════════════════════════════════
function initInnovator50() {
  if (typeof INNOVATOR_50 === 'undefined' || typeof INNOVATOR_50_META === 'undefined') return;

  const previewGrid = document.getElementById('innovator50-preview');
  const fullGrid = document.getElementById('innovator50-grid');
  if (!previewGrid && !fullGrid) return;

  // Expand/collapse toggle
  const toggleBtn = document.getElementById('i50-toggle');
  const content = document.getElementById('i50-content');
  const expandText = document.getElementById('i50-expand-text');
  const chevron = toggleBtn?.querySelector('.i50-chevron');

  if (toggleBtn && content) {
    toggleBtn.addEventListener('click', () => {
      const isExpanded = content.style.display !== 'none';
      content.style.display = isExpanded ? 'none' : 'block';
      if (expandText) expandText.textContent = isExpanded ? 'View Full Top 50' : 'Show Less';
      if (chevron) chevron.style.transform = isExpanded ? '' : 'rotate(180deg)';
      toggleBtn.classList.toggle('expanded', !isExpanded);
    });
  }

  // Populate category filter
  const categoryFilter = document.getElementById('i50-category');
  if (categoryFilter) {
    const categories = [...new Set(INNOVATOR_50.map(c => c.category))].sort();
    categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      categoryFilter.appendChild(opt);
    });
  }

  function renderI50Card(item) {
    const company = COMPANIES.find(c => c.name === item.company);
    const sectorInfo = SECTORS[item.category] || { icon: '📦', color: '#6b7280' };
    const rankClass = item.rank === 1 ? 'gold' : item.rank === 2 ? 'silver' : item.rank === 3 ? 'bronze' : '';
    const rankDisplay = item.rank <= 3 ? ['🥇', '🥈', '🥉'][item.rank - 1] : `#${item.rank}`;
    const valuation = company?.valuation || '';

    // Movement indicator
    let movement = '';
    if (item.yoyChange === 'new') movement = '<span class="i50-movement new">NEW</span>';
    else if (item.yoyChange === 'up') movement = '<span class="i50-movement up">↑</span>';
    else if (item.yoyChange === 'down') movement = '<span class="i50-movement down">↓</span>';

    const badges = (item.badges || []).map(b => `<span class="i50-badge">${b}</span>`).join('');

    return `
      <div class="i50-card ${rankClass}" onclick="openCompanyModal('${item.company.replace(/'/g, "\\'")}')">
        <div class="i50-rank-section">
          <div class="i50-rank ${rankClass}">${rankDisplay}</div>
          ${movement}
        </div>
        <div class="i50-content">
          <div class="i50-header">
            <div class="i50-company-name">${item.company}</div>
            <div class="i50-category" style="color: ${sectorInfo.color}">${sectorInfo.icon} ${item.category}</div>
          </div>
          <div class="i50-badges">${badges}</div>
          <ul class="i50-highlights">
            ${item.highlights.slice(0, 2).map(h => `<li>${h}</li>`).join('')}
          </ul>
          <div class="i50-footer">
            ${valuation ? `<span class="i50-valuation">${valuation}</span>` : ''}
          </div>
        </div>
      </div>
    `;
  }

  function renderInnovator50() {
    const selectedCategory = document.getElementById('i50-category')?.value || 'all';

    let items = [...INNOVATOR_50];
    if (selectedCategory !== 'all') {
      items = items.filter(i => i.category === selectedCategory);
    }

    // Render preview (top 10)
    if (previewGrid) {
      const previewItems = items.slice(0, 10);
      previewGrid.innerHTML = previewItems.map(item => renderI50Card(item)).join('');
    }

    // Render full grid (11-50, since preview shows 1-10)
    if (fullGrid) {
      const remainingItems = items.slice(10);
      fullGrid.innerHTML = remainingItems.map(item => renderI50Card(item)).join('');
    }

    // Add animation delays
    document.querySelectorAll('.i50-card').forEach((card, i) => {
      card.style.animationDelay = `${i * 0.03}s`;
    });
  }

  // Category filter
  if (categoryFilter) {
    categoryFilter.addEventListener('change', renderInnovator50);
  }

  // Methodology button
  const methodBtn = document.getElementById('i50-methodology-btn');
  if (methodBtn) {
    methodBtn.addEventListener('click', () => showInnovator50Methodology());
  }

  // Share button
  const shareBtn = document.getElementById('i50-share-btn');
  if (shareBtn) {
    shareBtn.addEventListener('click', () => shareInnovator50());
  }

  // Nominate button
  const nominateBtn = document.getElementById('i50-nominate-btn');
  if (nominateBtn && INNOVATOR_50_META.nominateLink) {
    nominateBtn.href = INNOVATOR_50_META.nominateLink;
  }

  // Year selector functionality
  const yearBtns = document.querySelectorAll('.i50-year-btn');
  yearBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      yearBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const year = parseInt(btn.dataset.year);
      renderHistoricalRanking(year);
    });
  });

  // Render historical ranking for a specific year
  function renderHistoricalRanking(year) {
    if (year === 2025) {
      // Current year - use regular rendering
      renderInnovator50();
      return;
    }

    // Historical year - use INNOVATOR_50_HISTORY
    if (typeof INNOVATOR_50_HISTORY === 'undefined' || !INNOVATOR_50_HISTORY[year]) {
      grid.innerHTML = '<div class="i50-no-data">Historical data not available for ' + year + '</div>';
      return;
    }

    const histData = INNOVATOR_50_HISTORY[year];
    const rankings = histData.rankings;
    const selectedCategory = document.getElementById('i50-category')?.value || 'all';

    // Convert rankings object to sorted array
    let items = Object.entries(rankings)
      .filter(([company, rank]) => rank !== null)
      .map(([company, rank]) => {
        const companyData = COMPANIES.find(c => c.name === company);
        return {
          rank,
          company,
          category: companyData?.sector || 'Unknown',
          valuation: companyData?.valuation || '',
          description: companyData?.description?.substring(0, 150) || ''
        };
      })
      .sort((a, b) => a.rank - b.rank);

    if (selectedCategory !== 'all') {
      items = items.filter(i => i.category === selectedCategory);
    }

    grid.innerHTML = `
      <div class="i50-historical-header">
        <span class="i50-historical-badge">${year} ARCHIVE</span>
        <h3>${histData.title}</h3>
        <p>Released ${new Date(histData.releaseDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
      </div>
      ${items.slice(0, 50).map((item, i) => {
        const sectorInfo = SECTORS[item.category] || { icon: '📦', color: '#6b7280' };
        const rankClass = item.rank === 1 ? 'gold' : item.rank === 2 ? 'silver' : item.rank === 3 ? 'bronze' : '';
        const rankDisplay = item.rank <= 3 ? ['🥇', '🥈', '🥉'][item.rank - 1] : `#${item.rank}`;

        // Check if company is still in 2025 list
        const currentEntry = INNOVATOR_50.find(c => c.company === item.company);
        let statusBadge = '';
        if (currentEntry) {
          const change = item.rank - currentEntry.rank;
          if (change > 0) statusBadge = `<span class="i50-status-badge up">Now #${currentEntry.rank} (↑${change})</span>`;
          else if (change < 0) statusBadge = `<span class="i50-status-badge down">Now #${currentEntry.rank} (↓${Math.abs(change)})</span>`;
          else statusBadge = `<span class="i50-status-badge same">Still #${currentEntry.rank}</span>`;
        } else {
          statusBadge = `<span class="i50-status-badge dropped">Not in 2025</span>`;
        }

        return `
          <div class="i50-card historical ${rankClass}" onclick="openCompanyModal('${item.company.replace(/'/g, "\\'")}')">
            <div class="i50-rank-section">
              <div class="i50-rank ${rankClass}">${rankDisplay}</div>
            </div>
            <div class="i50-content">
              <div class="i50-header">
                <div class="i50-company-name">${item.company}</div>
                <div class="i50-category" style="color: ${sectorInfo.color}">${sectorInfo.icon} ${item.category}</div>
              </div>
              ${statusBadge}
              ${item.valuation ? `<div class="i50-valuation">${item.valuation}</div>` : ''}
            </div>
          </div>
        `;
      }).join('')}
    `;

    // Add animation delays
    document.querySelectorAll('.i50-card').forEach((card, i) => {
      card.style.animationDelay = `${i * 0.03}s`;
    });
  }

  renderInnovator50();
}

function showInnovator50Methodology() {
  const meta = INNOVATOR_50_META;
  const body = document.getElementById('modal-body');
  body.innerHTML = `
    <div class="i50-methodology-modal">
      <span class="modal-sector-badge" style="background: linear-gradient(135deg, #ffd700, #ff6b2c); color: #000;">METHODOLOGY</span>
      <h2 class="modal-company-name" style="margin-top: 12px;">${meta.title} — ${meta.year}</h2>
      <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 20px;">Released ${new Date(meta.releaseDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>

      <div style="background: var(--bg-tertiary); border-radius: 8px; padding: 20px; margin-bottom: 20px;">
        <h3 style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px;">About the Ranking</h3>
        <p style="font-size: 14px; line-height: 1.7; color: var(--text-secondary);">${meta.methodology}</p>
      </div>

      <div style="margin-bottom: 20px;">
        <h3 style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px;">Selection Criteria</h3>
        <ul style="list-style: none; padding: 0; margin: 0;">
          ${meta.selectionCriteria.map(c => `
            <li style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px;">
              <span style="color: var(--accent); font-weight: 700;">✓</span>
              <span style="font-size: 14px; color: var(--text-secondary);">${c}</span>
            </li>
          `).join('')}
        </ul>
      </div>

      <div style="text-align: center; padding-top: 20px; border-top: 1px solid var(--border);">
        <p style="font-size: 12px; color: var(--text-muted);">Questions about the methodology? Contact us at research@rationaloptimistsociety.com</p>
      </div>
    </div>
  `;

  document.getElementById('modal-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function shareInnovator50() {
  const meta = INNOVATOR_50_META;
  const text = `Check out The ROS Innovator 50 — ${meta.year} Edition. The definitive ranking of frontier technology's most promising companies.`;
  const url = window.location.origin + window.location.pathname + '#innovator50';

  if (navigator.share) {
    navigator.share({ title: meta.title, text, url });
  } else {
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
    window.open(twitterUrl, '_blank');
  }
}

function shareInnovator50Entry(rank, company) {
  const meta = INNOVATOR_50_META;
  const text = `${company} is ranked #${rank} in The ROS Innovator 50 — ${meta.year} Edition.`;
  const url = window.location.origin + window.location.pathname + `?highlight=${encodeURIComponent(company)}#innovator50`;

  if (navigator.share) {
    navigator.share({ title: `${company} — ROS Innovator 50`, text, url });
  } else {
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
    window.open(twitterUrl, '_blank');
  }
}

// ═══════════════════════════════════════════════════════
// ANOMALY ALERT CARDS - "HOT THIS WEEK"
// ═══════════════════════════════════════════════════════
function initAnomalyAlerts() {
  const grid = document.getElementById('anomaly-grid');
  if (!grid) return;

  // Detect companies with converging signals
  function detectAnomalies() {
    const anomalies = [];
    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    COMPANIES.forEach(company => {
      const signals = [];

      // Check recent news/funding
      if (typeof NEWS_FEED !== 'undefined') {
        const recentNews = NEWS_FEED.filter(n =>
          n.company === company.name &&
          new Date(n.date) > thirtyDaysAgo
        );
        recentNews.forEach(n => {
          if (n.category === 'funding') {
            signals.push({ type: 'funding', text: n.headline, impact: n.impact, date: n.date });
          } else if (n.category === 'contract') {
            signals.push({ type: 'contract', text: n.headline, impact: n.impact, date: n.date });
          } else if (n.category === 'milestone') {
            signals.push({ type: 'milestone', text: n.headline, impact: n.impact, date: n.date });
          } else if (n.category === 'partnership') {
            signals.push({ type: 'partnership', text: n.headline, impact: n.impact, date: n.date });
          }
        });
      }

      // Check alt data signals (hiring velocity)
      if (typeof ALT_DATA_SIGNALS !== 'undefined') {
        const altData = ALT_DATA_SIGNALS.find(a => a.company === company.name);
        if (altData) {
          if (altData.hiringVelocity === 'surging') {
            signals.push({ type: 'hiring', text: `Hiring velocity: ${altData.hiringVelocity}`, impact: 'high' });
          } else if (altData.hiringVelocity === 'growing') {
            signals.push({ type: 'hiring', text: `Hiring velocity: ${altData.hiringVelocity}`, impact: 'medium' });
          }
          if (altData.signalStrength >= 8) {
            signals.push({ type: 'momentum', text: `Signal strength: ${altData.signalStrength}/10`, impact: 'high' });
          }
        }
      }

      // Check government contracts
      if (typeof GOV_CONTRACTS !== 'undefined') {
        const recentContracts = GOV_CONTRACTS.filter(c =>
          c.company === company.name &&
          c.date && new Date(c.date) > thirtyDaysAgo
        );
        recentContracts.forEach(c => {
          signals.push({ type: 'govContract', text: `${c.agency}: ${c.type} - ${c.amount}`, impact: 'high', date: c.date });
        });
      }

      // Check recent events on company
      if (company.recentEvent && company.recentEvent.date) {
        const eventDate = new Date(company.recentEvent.date);
        if (eventDate > thirtyDaysAgo) {
          signals.push({ type: 'event', text: company.recentEvent.text, impact: 'medium', date: company.recentEvent.date });
        }
      }

      // Check if company has IPO signal
      if (company.signal === 'IPO Filing' || company.signal === 'IPO Candidate') {
        signals.push({ type: 'ipo', text: company.signal, impact: 'high' });
      }

      // Deduplicate signals by type
      const uniqueTypes = [...new Set(signals.map(s => s.type))];

      if (uniqueTypes.length >= 3) {
        anomalies.push({
          company,
          signals,
          uniqueSignalCount: uniqueTypes.length,
          highImpactCount: signals.filter(s => s.impact === 'high').length,
          score: uniqueTypes.length * 2 + signals.filter(s => s.impact === 'high').length
        });
      }
    });

    // Sort by score (descending)
    return anomalies.sort((a, b) => b.score - a.score).slice(0, 8);
  }

  const anomalies = detectAnomalies();

  if (anomalies.length === 0) {
    grid.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No significant signal convergence detected this period.</div>';
    return;
  }

  const signalIcons = {
    funding: { icon: '💰', label: 'Funding' },
    contract: { icon: '📄', label: 'Contract' },
    govContract: { icon: '🏛️', label: 'Gov Contract' },
    milestone: { icon: '🎯', label: 'Milestone' },
    hiring: { icon: '👥', label: 'Hiring' },
    momentum: { icon: '📈', label: 'Momentum' },
    partnership: { icon: '🤝', label: 'Partnership' },
    event: { icon: '⚡', label: 'Event' },
    ipo: { icon: '🔔', label: 'IPO Signal' }
  };

  grid.innerHTML = anomalies.map((a, i) => {
    const sectorInfo = SECTORS[a.company.sector] || { icon: '📦', color: '#6b7280' };
    const uniqueTypes = [...new Set(a.signals.map(s => s.type))];
    const signalBadges = uniqueTypes.map(t => {
      const info = signalIcons[t] || { icon: '📊', label: t };
      return `<span class="anomaly-signal-badge">${info.icon} ${info.label}</span>`;
    }).join('');

    const latestSignal = a.signals[0];

    return `
      <div class="anomaly-card ${i < 3 ? 'top-anomaly' : ''}" onclick="openCompanyModal('${a.company.name.replace(/'/g, "\\'")}')">
        <div class="anomaly-flame-badge">🔥 ${a.uniqueSignalCount} Signals</div>
        <div class="anomaly-header">
          <div class="anomaly-company">
            <span class="anomaly-company-name">${a.company.name}</span>
            <span class="anomaly-sector" style="color: ${sectorInfo.color}">${sectorInfo.icon} ${a.company.sector}</span>
          </div>
          ${a.company.valuation ? `<span class="anomaly-valuation">${a.company.valuation}</span>` : ''}
        </div>
        <div class="anomaly-signals">
          ${signalBadges}
        </div>
        <div class="anomaly-summary">
          ${latestSignal ? latestSignal.text : 'Multiple converging signals detected'}
        </div>
        <div class="anomaly-footer">
          <span class="anomaly-impact ${a.highImpactCount >= 2 ? 'high' : 'medium'}">${a.highImpactCount} high-impact signals</span>
          <span class="anomaly-action">View Details →</span>
        </div>
      </div>
    `;
  }).join('');
}

// ═══════════════════════════════════════════════════════
// PHASE 3: REAL-TIME INTELLIGENCE FEED
// ═══════════════════════════════════════════════════════
function initIntelFeed() {
  if (typeof NEWS_FEED === 'undefined') return;
  const newsPanel = document.getElementById('feed-news-panel');
  const storiesPanel = document.getElementById('feed-stories-panel');
  if (!newsPanel) return;

  // Populate sector filter
  const sectorFilter = document.getElementById('feed-sector');
  if (sectorFilter) {
    const sectors = [...new Set(NEWS_FEED.map(n => n.sector))].sort();
    sectors.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      sectorFilter.appendChild(opt);
    });
  }

  // Tab switching
  document.querySelectorAll('.feed-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.feed-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const panel = tab.dataset.feed;
      newsPanel.style.display = panel === 'news' ? '' : 'none';
      storiesPanel.style.display = panel === 'stories' ? '' : 'none';
    });
  });

  function renderNews() {
    const cat = document.getElementById('feed-category')?.value || 'all';
    const sec = document.getElementById('feed-sector')?.value || 'all';
    const imp = document.getElementById('feed-impact')?.value || 'all';

    let items = [...NEWS_FEED].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    if (cat !== 'all') items = items.filter(n => n.category === cat);
    if (sec !== 'all') items = items.filter(n => n.sector === sec);
    if (imp !== 'all') items = items.filter(n => n.impact === imp);

    newsPanel.innerHTML = items.length === 0
      ? '<div style="padding:30px; text-align:center; color:var(--text-muted)">No news items match your filters.</div>'
      : items.map(n => `
        <div class="feed-item">
          <div class="feed-date">${formatFeedDate(n.date)}</div>
          <div class="feed-content">
            <div class="feed-headline">
              <span class="feed-company-link" onclick="openCompanyModal('${(n.company || '').replace(/'/g, "\\'")}')">${n.company}</span>: ${n.headline}
            </div>
            <div class="feed-summary">${n.summary || ''}</div>
            <div class="feed-meta">
              <span class="feed-category-tag ${n.category}">${n.category}</span>
              <span class="feed-source">${n.source || ''}</span>
            </div>
          </div>
          <div class="feed-impact">
            <span class="feed-impact-badge ${n.impact}">${n.impact}</span>
          </div>
        </div>
      `).join('');
  }

  function renderStoryLeads() {
    if (typeof STORY_LEADS === 'undefined') { storiesPanel.innerHTML = ''; return; }
    storiesPanel.innerHTML = STORY_LEADS.map(s => `
      <div class="story-lead-card">
        <div class="story-lead-header">
          <div class="story-lead-title">${s.title}</div>
          <span class="story-lead-confidence ${s.confidence}">${s.confidence} confidence</span>
        </div>
        <div class="story-lead-desc">${s.description}</div>
        <div class="story-lead-signals">
          ${(s.signals || []).map(sig => `<span class="story-signal-tag">${sig}</span>`).join('')}
        </div>
        <div class="story-lead-companies">
          ${(s.companies || []).map(c => `<span class="story-company-chip" onclick="openCompanyModal('${c.replace(/'/g, "\\'")}')">${c}</span>`).join('')}
        </div>
      </div>
    `).join('');
  }

  function formatFeedDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr + 'T00:00:00');
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return `${months[d.getMonth()]} ${d.getDate()}`;
  }

  renderNews();
  renderStoryLeads();
  document.getElementById('feed-category')?.addEventListener('change', renderNews);
  document.getElementById('feed-sector')?.addEventListener('change', renderNews);
  document.getElementById('feed-impact')?.addEventListener('change', renderNews);
}

// ═══════════════════════════════════════════════════════
// PHASE 3: EXPORTABLE SECTOR REPORTS (PDF)
// ═══════════════════════════════════════════════════════
function initSectorReports() {
  const grid = document.getElementById('reports-grid');
  if (!grid) return;

  const sectorList = Object.keys(SECTORS).sort();

  grid.innerHTML = sectorList.map(sector => {
    const info = SECTORS[sector] || {};
    const companies = COMPANIES.filter(c => c.sector === sector);
    const topCompanies = companies.sort((a, b) => {
      const sa = getInnovatorScore(a.name);
      const sb = getInnovatorScore(b.name);
      return ((sb ? sb.composite : 0) - (sa ? sa.composite : 0));
    }).slice(0, 5);

    return `
      <div class="report-card" onclick="generateSectorPDF('${sector.replace(/'/g, "\\'")}')">
        <div class="report-card-icon">${info.icon || '\u{1F4CA}'}</div>
        <div class="report-card-sector">${sector}</div>
        <div class="report-card-stats">${companies.length} companies \u00b7 ${info.trend || 'Tracking'}</div>
        <button class="report-card-btn">\u{1F4C4} Generate PDF</button>
      </div>
    `;
  }).join('');
}

function generateSectorPDF(sectorName) {
  if (typeof window.jspdf === 'undefined') {
    alert('PDF library is still loading. Please try again in a moment.');
    return;
  }

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageW = doc.internal.pageSize.getWidth();
  const margin = 20;
  const contentW = pageW - margin * 2;
  let y = margin;

  const sectorInfo = SECTORS[sectorName] || {};
  const companies = COMPANIES.filter(c => c.sector === sectorName);
  const topCompanies = [...companies].sort((a, b) => {
    const sa = getInnovatorScore(a.name);
    const sb = getInnovatorScore(b.name);
    return ((sb ? sb.composite : 0) - (sa ? sa.composite : 0));
  });

  // Helper
  function addText(text, size, style, color, maxW) {
    doc.setFontSize(size);
    doc.setFont('helvetica', style || 'normal');
    doc.setTextColor(...(color || [240, 240, 250]));
    const lines = doc.splitTextToSize(text, maxW || contentW);
    if (y + lines.length * size * 0.45 > 280) { doc.addPage(); y = margin; }
    doc.text(lines, margin, y);
    y += lines.length * size * 0.45 + 2;
    return lines.length;
  }

  function addLine() {
    doc.setDrawColor(60, 60, 60);
    doc.line(margin, y, pageW - margin, y);
    y += 4;
  }

  // Page background
  doc.setFillColor(10, 10, 10);
  doc.rect(0, 0, pageW, 297, 'F');

  // Header
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(255, 107, 44);
  doc.text('THE INNOVATORS LEAGUE', margin, y);
  doc.setTextColor(120, 120, 130);
  doc.text('Sector Intelligence Report', pageW - margin, y, { align: 'right' });
  y += 8;

  addLine();

  // Sector title
  addText(`${sectorInfo.icon || ''} ${sectorName}`, 22, 'bold', [255, 255, 255]);
  y += 2;
  addText(`${companies.length} companies tracked \u00b7 Generated ${new Date().toLocaleDateString()}`, 10, 'normal', [140, 140, 150]);
  y += 4;

  // Sector overview
  if (sectorInfo.description) {
    addText('SECTOR OVERVIEW', 11, 'bold', [255, 107, 44]);
    y += 1;
    addText(sectorInfo.description, 10, 'normal', [200, 200, 210]);
    y += 4;
  }

  addText(`Trend: ${sectorInfo.trend || 'N/A'}`, 10, 'normal', [160, 160, 170]);
  y += 6;

  addLine();

  // Top companies by Innovator Score
  addText('TOP COMPANIES BY INNOVATOR SCORE\u2122', 11, 'bold', [255, 107, 44]);
  y += 3;

  topCompanies.slice(0, 10).forEach((c, i) => {
    if (y > 265) { doc.addPage(); doc.setFillColor(10, 10, 10); doc.rect(0, 0, pageW, 297, 'F'); y = margin; }
    const score = getInnovatorScore(c.name);
    const composite = score ? score.composite.toFixed(0) : '--';
    const tier = score ? score.tier : '';

    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(240, 240, 250);
    doc.text(`${i + 1}. ${c.name}`, margin, y);

    const tierColor = tier === 'elite' ? [34, 197, 94] : tier === 'strong' ? [59, 130, 246] : tier === 'promising' ? [245, 158, 11] : [150, 150, 160];
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...tierColor);
    doc.text(`${composite} IS\u2122`, pageW - margin, y, { align: 'right' });
    y += 5;

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(160, 160, 170);
    doc.text(`${c.valuation || 'N/A'} \u00b7 ${c.location || 'N/A'} \u00b7 ${c.stage || 'N/A'}`, margin + 4, y);
    y += 4;

    if (c.thesis) {
      const thesisLines = doc.splitTextToSize(c.thesis, contentW - 8);
      doc.setFontSize(8);
      doc.setTextColor(140, 140, 150);
      doc.text(thesisLines.slice(0, 2), margin + 4, y);
      y += thesisLines.slice(0, 2).length * 3.5 + 3;
    }
    y += 2;
  });

  // Funding overview
  if (y > 220) { doc.addPage(); doc.setFillColor(10, 10, 10); doc.rect(0, 0, pageW, 297, 'F'); y = margin; }
  addLine();
  addText('FUNDING LANDSCAPE', 11, 'bold', [255, 107, 44]);
  y += 2;

  const valuationBuckets = { '$10B+': 0, '$1B-$10B': 0, '$100M-$1B': 0, '<$100M': 0 };
  companies.forEach(c => {
    const val = parseValuation(c.valuation);
    if (val >= 10000) valuationBuckets['$10B+']++;
    else if (val >= 1000) valuationBuckets['$1B-$10B']++;
    else if (val >= 100) valuationBuckets['$100M-$1B']++;
    else valuationBuckets['<$100M']++;
  });

  Object.entries(valuationBuckets).forEach(([bucket, count]) => {
    addText(`${bucket}: ${count} companies`, 9, 'normal', [180, 180, 190]);
  });
  y += 4;

  // Gov contract companies in sector
  if (typeof GOV_CONTRACTS !== 'undefined') {
    const govCompanies = GOV_CONTRACTS.filter(g => {
      const comp = COMPANIES.find(c => c.name === g.company);
      return comp && comp.sector === sectorName;
    });
    if (govCompanies.length > 0) {
      addLine();
      addText('GOVERNMENT CONTRACTS', 11, 'bold', [255, 107, 44]);
      y += 2;
      addText(`${govCompanies.length} companies with federal contracts in this sector`, 9, 'normal', [180, 180, 190]);
      y += 2;
      govCompanies.slice(0, 5).forEach(g => {
        addText(`\u2022 ${g.company}: $${g.totalGovValue} \u00b7 ${g.agencies.slice(0, 3).join(', ')}`, 9, 'normal', [160, 160, 170]);
      });
      y += 4;
    }
  }

  // Footer
  if (y > 265) { doc.addPage(); doc.setFillColor(10, 10, 10); doc.rect(0, 0, pageW, 297, 'F'); y = margin; }
  y = 280;
  doc.setFontSize(8);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(80, 80, 90);
  doc.text('The Innovators League \u00b7 Rational Optimist Society \u00b7 For informational purposes only', pageW / 2, y, { align: 'center' });

  // Save
  doc.save(`TIL_${sectorName.replace(/[^a-zA-Z0-9]/g, '_')}_Report.pdf`);
}

// ═══════════════════════════════════════════════════════
// PHASE 3: COMMUNITY INTELLIGENCE LAYER
// ═══════════════════════════════════════════════════════
function initCommunityIntel() {
  // Expert takes
  const expertList = document.getElementById('expert-takes-list');
  if (expertList && typeof EXPERT_TAKES !== 'undefined') {
    expertList.innerHTML = EXPERT_TAKES.slice(0, 5).map(t => `
      <div class="expert-take">
        <div class="expert-take-author">${t.author}</div>
        <div class="expert-take-company">on ${t.company}</div>
        <div class="expert-take-text">${t.text}</div>
      </div>
    `).join('');
  } else if (expertList) {
    expertList.innerHTML = '<p style="font-size:12px; color:var(--text-muted);">Expert takes coming soon. Want to contribute? <a href="https://github.com/PaleoFaire/innovators-league/issues/new" target="_blank" style="color:var(--accent)">Submit yours</a></p>';
  }

  // Shared watchlist builder — reuses bookmarks
  const watchlistEl = document.getElementById('watchlist-companies');
  const shareBtn = document.getElementById('watchlist-share');
  if (!watchlistEl || !shareBtn) return;

  function renderWatchlist() {
    const saved = JSON.parse(localStorage.getItem('til-bookmarks') || '[]');
    if (saved.length === 0) {
      watchlistEl.innerHTML = '<span style="font-size:11px; color:var(--text-muted)">Bookmark companies to add them to your watchlist</span>';
      return;
    }
    watchlistEl.innerHTML = saved.map(name => `
      <span class="watchlist-chip">${name}</span>
    `).join('');
  }

  shareBtn.addEventListener('click', () => {
    const saved = JSON.parse(localStorage.getItem('til-bookmarks') || '[]');
    const watchlistName = document.getElementById('watchlist-name')?.value || 'My Watchlist';
    if (saved.length === 0) { alert('Bookmark some companies first!'); return; }
    const params = new URLSearchParams();
    params.set('watchlist', saved.join('|'));
    params.set('wl-name', watchlistName);
    const url = window.location.origin + window.location.pathname + '?' + params.toString();
    navigator.clipboard?.writeText(url).then(() => {
      shareBtn.textContent = '\u2713 Copied!';
      setTimeout(() => { shareBtn.textContent = '\ud83d\udccb Generate Shareable Link'; }, 1500);
    });
  });

  renderWatchlist();
}

// ═══════════════════════════════════════════════════════════════════════════
// WORLD-CLASS INTELLIGENCE PLATFORM FEATURES
// Inspired by: Bloomberg Terminal, PitchBook, S&P CapIQ, AlphaSense, Tegus
// ═══════════════════════════════════════════════════════════════════════════

// ─── BLOOMBERG-STYLE COMMAND BAR (⌘K / Ctrl+K) ───
function initCommandBar() {
  // Create command bar overlay
  const overlay = document.createElement('div');
  overlay.className = 'command-bar-overlay';
  overlay.id = 'command-bar-overlay';
  overlay.innerHTML = `
    <div class="command-bar">
      <div class="command-bar-header">
        <svg class="command-bar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
        </svg>
        <input type="text" class="command-bar-input" id="command-bar-input" placeholder="Search companies, actions, or type a command..." autocomplete="off">
        <div class="command-bar-kbd">
          <kbd>ESC</kbd>
        </div>
      </div>
      <div class="command-bar-results" id="command-bar-results"></div>
      <div class="command-bar-footer">
        <div class="command-bar-footer-tips">
          <span class="command-bar-footer-tip"><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
          <span class="command-bar-footer-tip"><kbd>↵</kbd> select</span>
          <span class="command-bar-footer-tip"><kbd>/</kbd> search</span>
        </div>
        <span>Powered by ROS Intelligence</span>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const input = document.getElementById('command-bar-input');
  const results = document.getElementById('command-bar-results');
  let selectedIndex = 0;
  let currentResults = [];

  function openCommandBar() {
    overlay.classList.add('active');
    input.value = '';
    input.focus();
    renderDefaultResults();
  }

  function closeCommandBar() {
    overlay.classList.remove('active');
    selectedIndex = 0;
  }

  function renderDefaultResults() {
    if (typeof COMMAND_BAR_ACTIONS === 'undefined') return;

    const grouped = {};
    COMMAND_BAR_ACTIONS.forEach(action => {
      if (!grouped[action.category]) grouped[action.category] = [];
      grouped[action.category].push(action);
    });

    let html = '';
    Object.entries(grouped).forEach(([category, actions]) => {
      html += `<div class="command-bar-section">
        <div class="command-bar-section-title">${category}</div>
        ${actions.map((a, i) => `
          <div class="command-bar-item" data-action="${a.id}" data-index="${i}">
            <div class="command-bar-item-icon">${a.icon}</div>
            <div class="command-bar-item-content">
              <div class="command-bar-item-title">${a.title}</div>
            </div>
            <div class="command-bar-item-action"><kbd>${a.shortcut}</kbd></div>
          </div>
        `).join('')}
      </div>`;
    });
    results.innerHTML = html;
    currentResults = COMMAND_BAR_ACTIONS;
  }

  function renderSearchResults(query) {
    if (!query) {
      renderDefaultResults();
      return;
    }

    const q = query.toLowerCase();

    // Search companies
    const matchedCompanies = COMPANIES.filter(c =>
      c.name.toLowerCase().includes(q) ||
      c.sector.toLowerCase().includes(q) ||
      (c.tags && c.tags.some(t => t.toLowerCase().includes(q)))
    ).slice(0, 8);

    // Search actions
    const matchedActions = typeof COMMAND_BAR_ACTIONS !== 'undefined'
      ? COMMAND_BAR_ACTIONS.filter(a => a.title.toLowerCase().includes(q))
      : [];

    let html = '';

    if (matchedCompanies.length > 0) {
      html += `<div class="command-bar-section">
        <div class="command-bar-section-title">Companies</div>
        ${matchedCompanies.map((c, i) => {
          const sectorInfo = SECTORS[c.sector] || { icon: '📦', color: '#6b7280' };
          return `
            <div class="command-bar-item" data-company="${c.name}" data-index="${i}">
              <div class="command-bar-item-icon" style="background: ${sectorInfo.color}20;">${sectorInfo.icon}</div>
              <div class="command-bar-item-content">
                <div class="command-bar-item-title">${c.name}</div>
                <div class="command-bar-item-meta">
                  <span>${c.sector}</span>
                  ${c.signal === 'hot' ? '<span class="command-bar-item-tag">HOT</span>' : ''}
                  ${c.valuation ? `<span>${c.valuation}</span>` : ''}
                </div>
              </div>
              <div class="command-bar-item-action">View →</div>
            </div>
          `;
        }).join('')}
      </div>`;
    }

    if (matchedActions.length > 0) {
      html += `<div class="command-bar-section">
        <div class="command-bar-section-title">Actions</div>
        ${matchedActions.map((a, i) => `
          <div class="command-bar-item" data-action="${a.id}" data-index="${i + matchedCompanies.length}">
            <div class="command-bar-item-icon">${a.icon}</div>
            <div class="command-bar-item-content">
              <div class="command-bar-item-title">${a.title}</div>
            </div>
            <div class="command-bar-item-action"><kbd>${a.shortcut}</kbd></div>
          </div>
        `).join('')}
      </div>`;
    }

    if (html === '') {
      html = '<div class="command-bar-section"><div style="padding: 20px; text-align: center; color: var(--text-muted);">No results found</div></div>';
    }

    results.innerHTML = html;
    currentResults = [...matchedCompanies, ...matchedActions];
    selectedIndex = 0;
    updateSelection();
  }

  function updateSelection() {
    const items = results.querySelectorAll('.command-bar-item');
    items.forEach((item, i) => {
      item.classList.toggle('selected', i === selectedIndex);
    });
  }

  function executeAction(actionId) {
    closeCommandBar();
    switch(actionId) {
      case 'search':
        document.getElementById('company-search')?.focus();
        break;
      case 'innovator50':
        document.getElementById('innovator50')?.scrollIntoView({ behavior: 'smooth' });
        document.getElementById('i50-toggle')?.click();
        break;
      case 'signals':
        toggleSignalsPanel();
        break;
      case 'screener':
        document.getElementById('smart-screener')?.scrollIntoView({ behavior: 'smooth' });
        break;
      case 'watchlist':
        document.getElementById('pro-watchlist')?.scrollIntoView({ behavior: 'smooth' });
        break;
      case 'map':
        document.getElementById('map')?.scrollIntoView({ behavior: 'smooth' });
        break;
      case 'investors':
        window.location.href = 'investors.html';
        break;
      case 'insights':
        window.location.href = 'visualizations.html';
        break;
      case 'export':
        exportCurrentView();
        break;
      default:
        const sector = Object.keys(SECTORS).find(s => actionId.includes(s.toLowerCase()));
        if (sector) {
          document.getElementById('sector-filter').value = sector;
          applyFilters();
        }
    }
  }

  // Event listeners
  input.addEventListener('input', (e) => {
    renderSearchResults(e.target.value);
  });

  input.addEventListener('keydown', (e) => {
    const items = results.querySelectorAll('.command-bar-item');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
      updateSelection();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      updateSelection();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const selected = items[selectedIndex];
      if (selected) {
        if (selected.dataset.company) {
          closeCommandBar();
          openCompanyModal(selected.dataset.company);
        } else if (selected.dataset.action) {
          executeAction(selected.dataset.action);
        }
      }
    } else if (e.key === 'Escape') {
      closeCommandBar();
    }
  });

  results.addEventListener('click', (e) => {
    const item = e.target.closest('.command-bar-item');
    if (item) {
      if (item.dataset.company) {
        closeCommandBar();
        openCompanyModal(item.dataset.company);
      } else if (item.dataset.action) {
        executeAction(item.dataset.action);
      }
    }
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeCommandBar();
  });

  // Global keyboard shortcut
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      openCommandBar();
    }
    // Quick shortcuts when command bar is closed
    if (!overlay.classList.contains('active')) {
      if (e.key === '/' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        openCommandBar();
      }
    }
  });

  // Expose globally
  window.openCommandBar = openCommandBar;
  window.closeCommandBar = closeCommandBar;
}

// ─── PITCHBOOK-STYLE SIGNALS PANEL ───
function initSignalsPanel() {
  if (typeof COMPANY_SIGNALS === 'undefined') return;

  // Create signals panel
  const panel = document.createElement('div');
  panel.className = 'signals-panel';
  panel.id = 'signals-panel';
  panel.innerHTML = `
    <div class="signals-panel-header">
      <div class="signals-panel-title">
        <h3>Live Signals</h3>
        <span class="signals-badge">${COMPANY_SIGNALS.filter(s => s.unread).length} NEW</span>
      </div>
      <button class="signals-panel-close" onclick="toggleSignalsPanel()">×</button>
    </div>
    <div class="signals-filters">
      <button class="signal-filter-btn active" data-filter="all">All</button>
      <button class="signal-filter-btn" data-filter="funding">💰 Funding</button>
      <button class="signal-filter-btn" data-filter="contract">📋 Contracts</button>
      <button class="signal-filter-btn" data-filter="hire">👔 Hires</button>
      <button class="signal-filter-btn" data-filter="patent">📜 Patents</button>
      <button class="signal-filter-btn" data-filter="news">📰 News</button>
    </div>
    <div class="signals-list" id="signals-list"></div>
  `;
  document.body.appendChild(panel);

  // Add toggle button to nav
  const navLinks = document.querySelector('.nav-links');
  if (navLinks) {
    const signalsBtn = document.createElement('button');
    signalsBtn.className = 'signals-toggle-btn';
    signalsBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
      Signals
      <span class="signal-count">${COMPANY_SIGNALS.filter(s => s.unread).length}</span>
    `;
    signalsBtn.onclick = toggleSignalsPanel;
    navLinks.insertBefore(signalsBtn, navLinks.querySelector('.nav-cta'));
  }

  renderSignals('all');

  // Filter buttons
  panel.querySelectorAll('.signal-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      panel.querySelectorAll('.signal-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderSignals(btn.dataset.filter);
    });
  });
}

function renderSignals(filter) {
  const list = document.getElementById('signals-list');
  if (!list || typeof COMPANY_SIGNALS === 'undefined') return;

  const signals = filter === 'all'
    ? COMPANY_SIGNALS
    : COMPANY_SIGNALS.filter(s => s.type === filter);

  const iconMap = {
    funding: '💰',
    contract: '📋',
    hire: '👔',
    patent: '📜',
    news: '📰',
    ipo: '🚀'
  };

  list.innerHTML = signals.map(s => `
    <div class="signal-item ${s.unread ? 'unread' : ''}" onclick="handleSignalClick('${s.company}')">
      <div class="signal-icon ${s.type}">${iconMap[s.type] || '📡'}</div>
      <div class="signal-content">
        <div class="signal-headline">
          <span class="signal-company">${s.company}</span>: ${s.headline}
        </div>
        <div class="signal-meta">
          <span class="signal-time">🕐 ${s.time}</span>
          <span class="signal-source">via ${s.source}</span>
          <span class="signal-impact ${s.impact}">${s.impact.toUpperCase()}</span>
        </div>
      </div>
    </div>
  `).join('');
}

function toggleSignalsPanel() {
  const panel = document.getElementById('signals-panel');
  if (panel) panel.classList.toggle('open');
}

function handleSignalClick(companyName) {
  toggleSignalsPanel();
  openCompanyModal(companyName);
}

// ─── TEGUS-STYLE EXPERT INTELLIGENCE ───
function initExpertIntel() {
  const section = document.getElementById('expert-intel-section');
  if (!section) return;

  const grid = section.querySelector('.expert-grid');
  if (!grid) return;

  // Combine EXPERT_INSIGHTS (premium) and EXPERT_TAKES (community) if available
  let allInsights = [];

  if (typeof EXPERT_INSIGHTS !== 'undefined') {
    allInsights = [...EXPERT_INSIGHTS];
  }

  // Also add EXPERT_TAKES as community insights
  if (typeof EXPERT_TAKES !== 'undefined') {
    EXPERT_TAKES.forEach(take => {
      allInsights.push({
        expert: take.author,
        role: 'Domain Expert',
        avatar: getExpertAvatar(take.company),
        company: take.company,
        topic: take.company,
        quote: take.text,
        premium: false
      });
    });
  }

  if (allInsights.length === 0) return;

  // Shuffle and pick 6 to display
  let displayInsights = shuffleArray([...allInsights]).slice(0, 6);
  let refreshCount = 0;

  function getExpertAvatar(company) {
    const companyData = COMPANIES.find(c => c.name === company);
    if (companyData) {
      const sectorInfo = SECTORS[companyData.sector];
      return sectorInfo?.icon || '💡';
    }
    return '💡';
  }

  function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  function renderInsights() {
    grid.innerHTML = displayInsights.map(e => `
      <div class="expert-card">
        <div class="expert-card-header">
          <div class="expert-avatar">${e.avatar}</div>
          <div class="expert-info">
            <h4>${e.expert}</h4>
            <div class="expert-role">${e.role}</div>
          </div>
          ${e.premium ? '<span class="expert-badge">PREMIUM</span>' : '<span class="expert-badge" style="background: linear-gradient(135deg, #22c55e, #16a34a);">ANALYST</span>'}
        </div>
        <div class="expert-quote">
          <div class="expert-quote-text">${e.quote}</div>
        </div>
        <div class="expert-meta">
          <div class="expert-topic">
            <span>Topic:</span>
            <span class="expert-topic-tag">${e.topic}</span>
          </div>
          <a href="#" class="expert-cta" onclick="openCompanyModal('${e.company}'); return false;">
            View ${e.company} →
          </a>
        </div>
      </div>
    `).join('');
  }

  // Add refresh button to section header
  const header = section.querySelector('.section-header');
  if (header && !header.querySelector('.refresh-btn')) {
    const refreshBtn = document.createElement('button');
    refreshBtn.className = 'refresh-btn';
    refreshBtn.innerHTML = '🔄 Refresh Insights';
    refreshBtn.style.cssText = 'margin-top: 12px; padding: 8px 16px; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 8px; color: var(--text-secondary); font-size: 12px; cursor: pointer; transition: all 0.15s;';
    refreshBtn.onmouseover = () => { refreshBtn.style.borderColor = 'var(--accent)'; refreshBtn.style.color = 'var(--accent)'; };
    refreshBtn.onmouseout = () => { refreshBtn.style.borderColor = 'var(--border)'; refreshBtn.style.color = 'var(--text-secondary)'; };
    refreshBtn.onclick = () => {
      displayInsights = shuffleArray([...allInsights]).slice(0, 6);
      refreshCount++;
      renderInsights();
      refreshBtn.innerHTML = `✓ Refreshed (${refreshCount})`;
      setTimeout(() => { refreshBtn.innerHTML = '🔄 Refresh Insights'; }, 1500);
    };
    header.appendChild(refreshBtn);
  }

  // Auto-refresh every 60 seconds if section is visible
  let autoRefreshInterval;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        autoRefreshInterval = setInterval(() => {
          displayInsights = shuffleArray([...allInsights]).slice(0, 6);
          renderInsights();
        }, 60000); // Refresh every 60 seconds
      } else {
        clearInterval(autoRefreshInterval);
      }
    });
  }, { threshold: 0.1 });
  observer.observe(section);

  renderInsights();
}

// ─── S&P CAPIQ-STYLE SMART SCREENER ───
function initSmartScreener() {
  const section = document.getElementById('smart-screener');
  if (!section) return;

  const activeFilters = [];

  function renderActiveFilters() {
    const container = section.querySelector('.screener-active-filters');
    if (!container) return;

    if (activeFilters.length === 0) {
      container.style.display = 'none';
      return;
    }

    container.style.display = 'flex';
    container.innerHTML = activeFilters.map((f, i) => `
      <span class="screener-active-filter">
        ${f.label}: ${f.value}
        <button onclick="removeScreenerFilter(${i})">×</button>
      </span>
    `).join('');
  }

  function applyScreenerFilters() {
    let filtered = [...COMPANIES];

    activeFilters.forEach(f => {
      switch(f.type) {
        case 'sector':
          filtered = filtered.filter(c => c.sector === f.value);
          break;
        case 'stage':
          filtered = filtered.filter(c => c.fundingStage === f.value);
          break;
        case 'signal':
          filtered = filtered.filter(c => c.signal === f.value.toLowerCase());
          break;
        case 'location':
          if (f.value === 'International') {
            filtered = filtered.filter(c => !US_STATES.has(c.state));
          } else {
            filtered = filtered.filter(c => c.location?.includes(f.value) || STATE_NAMES[c.state] === f.value);
          }
          break;
        case 'innovator50':
          if (typeof INNOVATOR_50 !== 'undefined') {
            const i50Names = INNOVATOR_50.map(i => i.company);
            filtered = filtered.filter(c => i50Names.includes(c.name));
          }
          break;
        case 'govContracts':
          if (typeof GOV_CONTRACTS !== 'undefined') {
            const govCompanies = GOV_CONTRACTS.map(g => g.company);
            filtered = filtered.filter(c => govCompanies.includes(c.name));
          }
          break;
      }
    });

    // Update results count
    const countEl = section.querySelector('.screener-results-count');
    if (countEl) {
      countEl.innerHTML = `<strong>${filtered.length}</strong> companies match your criteria`;
    }

    return filtered;
  }

  // Expose globally
  window.addScreenerFilter = (type, label, value) => {
    activeFilters.push({ type, label, value });
    renderActiveFilters();
    applyScreenerFilters();
  };

  window.removeScreenerFilter = (index) => {
    activeFilters.splice(index, 1);
    renderActiveFilters();
    applyScreenerFilters();
  };

  window.clearScreenerFilters = () => {
    activeFilters.length = 0;
    renderActiveFilters();
    applyScreenerFilters();
  };

  window.runScreener = () => {
    const results = applyScreenerFilters();
    // Apply to main company grid
    renderCompanyCards(results);
    document.getElementById('companies')?.scrollIntoView({ behavior: 'smooth' });
  };

  // Initialize filter dropdowns
  const sectorSelect = section.querySelector('#screener-sector');
  const stageSelect = section.querySelector('#screener-stage');

  if (sectorSelect) {
    sectorSelect.innerHTML = '<option value="">Any Sector</option>' +
      Object.keys(SECTORS).map(s => `<option value="${s}">${s}</option>`).join('');
    sectorSelect.onchange = (e) => {
      if (e.target.value) addScreenerFilter('sector', 'Sector', e.target.value);
      e.target.value = '';
    };
  }

  if (stageSelect && typeof SCREENER_FILTERS !== 'undefined') {
    stageSelect.innerHTML = '<option value="">Any Stage</option>' +
      SCREENER_FILTERS.stages.map(s => `<option value="${s}">${s}</option>`).join('');
    stageSelect.onchange = (e) => {
      if (e.target.value) addScreenerFilter('stage', 'Stage', e.target.value);
      e.target.value = '';
    };
  }
}

// ─── CRUNCHBASE-STYLE WATCHLIST WITH KANBAN ───
function initProWatchlist() {
  const section = document.getElementById('pro-watchlist');
  if (!section || typeof WATCHLIST_COLUMNS === 'undefined') return;

  const kanban = section.querySelector('.watchlist-kanban');
  if (!kanban) return;

  // Get watchlist from localStorage
  function getWatchlist() {
    return JSON.parse(localStorage.getItem('til-pro-watchlist') || '{}');
  }

  function saveWatchlist(data) {
    localStorage.setItem('til-pro-watchlist', JSON.stringify(data));
  }

  function renderKanban() {
    const watchlist = getWatchlist();

    kanban.innerHTML = WATCHLIST_COLUMNS.map(col => {
      const companies = watchlist[col.id] || [];
      return `
        <div class="kanban-column" data-column="${col.id}">
          <div class="kanban-column-header">
            <div class="kanban-column-title">
              <span>${col.icon}</span>
              <h4>${col.title}</h4>
              <span class="kanban-column-count">${companies.length}</span>
            </div>
          </div>
          <div class="kanban-cards" data-column="${col.id}">
            ${companies.map(name => {
              const company = COMPANIES.find(c => c.name === name);
              if (!company) return '';
              return `
                <div class="kanban-card" draggable="true" data-company="${name}">
                  <div class="kanban-card-header">
                    <span class="kanban-card-name">${name}</span>
                    <span class="kanban-card-sector">${company.sector}</span>
                  </div>
                  <div class="kanban-card-meta">
                    ${company.valuation ? `<span>💰 ${company.valuation}</span>` : ''}
                    ${company.signal === 'hot' ? '<span class="kanban-card-signal">🔥 Hot</span>' : ''}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }).join('');

    // Add drag and drop
    initKanbanDragDrop();
  }

  function initKanbanDragDrop() {
    const cards = kanban.querySelectorAll('.kanban-card');
    const columns = kanban.querySelectorAll('.kanban-cards');

    cards.forEach(card => {
      card.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', card.dataset.company);
        card.classList.add('dragging');
      });
      card.addEventListener('dragend', () => {
        card.classList.remove('dragging');
      });
      card.addEventListener('click', () => {
        openCompanyModal(card.dataset.company);
      });
    });

    columns.forEach(column => {
      column.addEventListener('dragover', (e) => {
        e.preventDefault();
        column.classList.add('drag-over');
      });
      column.addEventListener('dragleave', () => {
        column.classList.remove('drag-over');
      });
      column.addEventListener('drop', (e) => {
        e.preventDefault();
        column.classList.remove('drag-over');
        const companyName = e.dataTransfer.getData('text/plain');
        const newColumn = column.dataset.column;
        moveToColumn(companyName, newColumn);
      });
    });
  }

  function moveToColumn(companyName, columnId) {
    const watchlist = getWatchlist();

    // Remove from all columns
    WATCHLIST_COLUMNS.forEach(col => {
      if (watchlist[col.id]) {
        watchlist[col.id] = watchlist[col.id].filter(n => n !== companyName);
      }
    });

    // Add to new column
    if (!watchlist[columnId]) watchlist[columnId] = [];
    watchlist[columnId].push(companyName);

    saveWatchlist(watchlist);
    renderKanban();
  }

  // Add to watchlist function
  window.addToWatchlist = (companyName, column = 'watching') => {
    const watchlist = getWatchlist();
    if (!watchlist[column]) watchlist[column] = [];
    if (!watchlist[column].includes(companyName)) {
      watchlist[column].push(companyName);
      saveWatchlist(watchlist);
      renderKanban();
    }
  };

  // Update watchlist count in header
  function updateWatchlistCount() {
    const watchlist = getWatchlist();
    const total = Object.values(watchlist).reduce((sum, arr) => sum + arr.length, 0);
    const countEl = section.querySelector('.watchlist-count');
    if (countEl) countEl.textContent = total;
  }

  // Global function to add company from input
  window.addCompanyToWatchlist = () => {
    const input = document.getElementById('watchlist-add-input');
    if (!input || !input.value.trim()) return;

    const searchTerm = input.value.trim().toLowerCase();
    const company = COMPANIES.find(c => c.name.toLowerCase().includes(searchTerm));

    if (company) {
      const watchlist = getWatchlist();
      if (!watchlist['watching']) watchlist['watching'] = [];
      if (!watchlist['watching'].includes(company.name)) {
        watchlist['watching'].push(company.name);
        saveWatchlist(watchlist);
        renderKanban();
        updateWatchlistCount();
        input.value = '';
        // Show brief confirmation
        input.placeholder = `✓ Added ${company.name}`;
        setTimeout(() => { input.placeholder = 'Add company...'; }, 2000);
      } else {
        input.placeholder = 'Already in watchlist';
        input.value = '';
        setTimeout(() => { input.placeholder = 'Add company...'; }, 2000);
      }
    } else {
      input.placeholder = 'Company not found';
      input.value = '';
      setTimeout(() => { input.placeholder = 'Add company...'; }, 2000);
    }
  };

  // Global function to clear all watchlist
  window.clearAllWatchlist = () => {
    if (confirm('Clear all companies from your watchlist?')) {
      localStorage.removeItem('til-pro-watchlist');
      renderKanban();
      updateWatchlistCount();
    }
  };

  // Handle enter key on input
  const addInput = document.getElementById('watchlist-add-input');
  if (addInput) {
    addInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') addCompanyToWatchlist();
    });
  }

  renderKanban();
  updateWatchlistCount();
}

// ─── BLOOMBERG-STYLE STATUS BAR ───
function initNetworkStatusBar() {
  const statusBar = document.createElement('div');
  statusBar.className = 'network-status-bar';
  statusBar.innerHTML = `
    <div class="network-status-left">
      <div class="network-status-item">
        <span class="network-status-dot"></span>
        <span>Live</span>
      </div>
      <div class="network-status-item">
        <span>📊 ${typeof COMPANIES !== 'undefined' ? COMPANIES.length : 0} companies</span>
      </div>
      <div class="network-status-item">
        <span>🔄 Updated ${typeof LAST_UPDATED !== 'undefined' ? LAST_UPDATED : 'today'}</span>
      </div>
      <div class="network-status-item">
        <span>📡 ${typeof COMPANY_SIGNALS !== 'undefined' ? COMPANY_SIGNALS.length : 0} signals</span>
      </div>
    </div>
    <div class="network-status-right">
      <div class="network-kbd-hint">
        <kbd>⌘</kbd><kbd>K</kbd> Quick search
      </div>
      <div class="network-kbd-hint">
        <kbd>G</kbd> Signals
      </div>
    </div>
  `;
  document.body.appendChild(statusBar);

  // Add padding to body to account for status bar
  document.body.style.paddingBottom = '28px';
}

// ─── EXPORT CURRENT VIEW ───
function exportCurrentView() {
  const visibleCards = document.querySelectorAll('.company-card:not([style*="display: none"])');
  const companies = [];

  visibleCards.forEach(card => {
    const name = card.querySelector('.card-name')?.textContent;
    if (name) {
      const company = COMPANIES.find(c => c.name === name);
      if (company) companies.push(company);
    }
  });

  if (companies.length === 0) {
    alert('No companies to export. Apply some filters first.');
    return;
  }

  // Create CSV
  const headers = ['Name', 'Sector', 'Location', 'Funding Stage', 'Total Raised', 'Valuation', 'Signal', 'Founder'];
  const rows = companies.map(c => [
    c.name,
    c.sector,
    c.location,
    c.fundingStage || '',
    c.totalRaised || '',
    c.valuation || '',
    c.signal || '',
    c.founder || ''
  ]);

  const csv = [headers.join(','), ...rows.map(r => r.map(v => `"${v}"`).join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `innovators-league-export-${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ─── AI SEARCH ENHANCEMENT ───
function initAISearch() {
  const searchBox = document.getElementById('company-search');
  if (!searchBox) return;

  // Create AI badge
  const wrapper = searchBox.parentElement;
  if (wrapper && !wrapper.querySelector('.ai-search-badge')) {
    const badge = document.createElement('span');
    badge.className = 'ai-search-badge';
    badge.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
      </svg>
      AI
    `;
    wrapper.appendChild(badge);
  }

  // Enhanced search with natural language hints
  const originalPlaceholder = searchBox.placeholder;
  const aiPlaceholders = [
    'Try: "defense companies with government contracts"',
    'Try: "Series B+ companies in California"',
    'Try: "hot companies in nuclear energy"',
    'Try: "space companies valued over $1B"',
    originalPlaceholder
  ];

  let placeholderIndex = 0;
  setInterval(() => {
    if (document.activeElement !== searchBox) {
      placeholderIndex = (placeholderIndex + 1) % aiPlaceholders.length;
      searchBox.placeholder = aiPlaceholders[placeholderIndex];
    }
  }, 4000);
}

// ─── INITIALIZE ALL PREMIUM FEATURES ───
function initPremiumFeatures() {
  initCommandBar();
  initSignalsPanel();
  initExpertIntel();
  initSmartScreener();
  initProWatchlist();
  initNetworkStatusBar();
  initAISearch();

  console.log('🚀 Premium intelligence features initialized');
}
