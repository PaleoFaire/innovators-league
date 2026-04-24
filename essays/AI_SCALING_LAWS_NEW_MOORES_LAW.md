# AI Scaling Laws Are the New Moore's Law

_Draft essay · April 2026 · ~2,400 words · Substack-ready_

---

## The idea in one sentence

**Moore's Law wasn't a physics law. It was a social contract. And AI scaling laws are the same kind of contract, signed 55 years later, at ten times the speed.**

Both "laws" share the exact same DNA: an empirical regularity, discovered by looking at a chart, that hardened into an industrial religion. The religion made the curve real. Believers got rich. Skeptics got left behind. The curve holds because the capital keeps flowing, and the capital keeps flowing because the curve holds.

If you understand that loop, you understand the next decade of technology investing.

---

## What Moore's Law actually was

Gordon Moore wrote a short paper in 1965. He looked at four data points — four data points — and noticed that the number of transistors you could economically fit on a chip was doubling every year. He extrapolated the line and said: this is going to keep going.

It did.

For fifty years, the number of transistors on a chip doubled roughly every 18 to 24 months. A transistor in 1971 cost about $1. A transistor in 2021 cost about $0.000000001. That's a one-billion-fold collapse in unit cost. No other industrial product in human history has ever improved that much.

Here's the secret: **Moore's Law was not actually a law of physics**. There was no equation proving transistors had to shrink. There was just a chart, and a belief that the chart would continue.

What made the chart continue was coordination.

Once the entire semiconductor industry — Intel, TSMC, Samsung, Applied Materials, ASML, Synopsys — agreed that Moore's Law was real, every player in the supply chain planned their capex, their R&D, their hiring, their customer roadmaps around the expectation that the curve would hold. ASML spent $10 billion developing EUV lithography over 20 years because they were confident someone would need it. TSMC built a $40 billion fab in Arizona because they were confident customers would demand the transistors inside it. Customers booked the transistors because they were confident next-gen chips would ship on time.

The belief in the curve financed the infrastructure that kept the curve going. When one player tried to skip a generation, they fell behind. When one player tried to push ahead of the curve, they got stuck with capacity nobody was ready to buy. The whole industry moved in lockstep, because the penalty for not moving in lockstep was bankruptcy.

This is what I mean when I say it was a social contract. The chart was made real by the fact that fifty thousand engineers across thirty companies in six countries all woke up every morning and tried to hit the next node.

**Moore's Law was a coordinated hallucination that ended up being true.**

---

## The same pattern, 55 years later

In 2020, three OpenAI researchers — Jared Kaplan and colleagues — published a paper that did roughly what Moore's paper did in 1965. They plotted some data points. Specifically, they plotted the loss of language models against three variables: the number of parameters, the amount of training data, and the amount of compute used.

They found a clean line. The loss went down in a predictable way as any of the three inputs went up. The relationship held across five orders of magnitude of compute.

They called it a scaling law.

A few months later, DeepMind's Hoffmann et al. (the "Chinchilla" paper) tightened the relationship. A few months after that, OpenAI's GPT-4 confirmed the curve continued. Claude 3.5 continued it. Claude Opus 4 continued it. GPT-5 continued it. Reasoning models and inference-time compute added a second axis — the loss also went down predictably with "think time."

The same pattern Moore saw: an empirical line on a chart. No physical law says it has to continue. Nobody can prove it won't plateau next year.

But the industry is now acting as if it will.

---

## How you know a social contract is forming

You watch the capex.

Through 2019, the entire frontier-AI training run cost maybe $10 million. The famous DeepMind AlphaGo Zero run was around $35 million in hardware. The 2020 GPT-3 training run was about $5 million in compute.

Then, around 2022, something broke loose.

GPT-4 (2023): ~$100 million training run.
Gemini Ultra (2023): ~$200 million.
GPT-5 / frontier 2024: ~$500M-$1B per run.
The announced hyperscaler capex for frontier-AI infrastructure, 2026 alone: **$115 to $135 billion** at Meta. **$90 to $110 billion** at Microsoft. **$75 billion** at Google. OpenAI's Stargate partnership with SoftBank and Oracle: **$500 billion** committed through 2029. Saudi Arabia's HUMAIN: **$40 billion capitalized.** The United Arab Emirates' G42: multi-billion. AMD just signed a multi-year deal to ship OpenAI **six gigawatts** of Instinct GPUs — roughly the power draw of Ireland.

Those are not startup numbers. They are not even tech-industry numbers. Those are sovereign-wealth-fund numbers. **The global capital stack is now pricing in scaling laws as a 20-year curve, in exactly the way the global capital stack once priced in Moore's Law.**

And just like Moore's Law, the reason the curve will keep going is that too many players have now priced it in to let it not go.

---

## The analogy, made concrete

Here's what the old world looked like, and here's what the new world looks like:

| | Moore's Law era (1965–2015) | Scaling Laws era (2020–?) |
|---|---|---|
| **The line** | Transistors double every ~2 years | Loss falls predictably with compute × data × parameters |
| **Cycle time** | 18–24 months per generation | 6–12 months per frontier model |
| **First-stage enabler** | Silicon wafers | GPUs |
| **The monopoly** | Intel, then TSMC | Nvidia |
| **The oligopoly beneath it** | Applied Materials, ASML, KLA, Lam | Micron, SK Hynix, Samsung (HBM); TSMC (packaging) |
| **The bottleneck that moved** | Lithography → advanced packaging | FLOPs → bytes → power → optics |
| **Per-generation cost curve** | $1B → $10B fab | $100M → $100B training run |
| **The pick-and-shovel trade** | ASML ($340B market cap at peak) | NVIDIA ($3.5T+), Micron ($180B), Vertiv, Eaton, Broadcom |
| **Geopolitical stakes** | US vs Japan, then vs China on chips | US vs China on AI, plus sovereign AI funds |
| **The skeptical view** | "Moore's Law is hitting a wall" (repeated annually from 1995 to 2025) | "Scaling is plateauing" (repeated annually from 2023 onward) |
| **The economic prize** | Smartphone, internet, cloud, Google | Agents, copilots, physical robotics, drug discovery |

The parallels aren't loose — they're structural. Both curves power a **physical industrial buildout** that eats the entire global supply chain.

---

## The kitchen analogy (why the curve is now memory-constrained, not compute-constrained)

Think of an AI system as a kitchen.

The GPU is the chef. The chef is spectacularly fast. Over the last 20 years, the chef got **60,000 times faster.**

The memory is the pantry. The pantry has only gotten **100 times faster** over the same 20 years.

So today, the chef stands at the stove, ready to cook. She has a recipe the size of a phonebook — billions of parameters, hundreds of thousands of tokens of context, a running conversation she has to remember. She needs ingredients every second.

But the pantry is across the hall. Every time the chef needs salt, she has to walk across the hall and walk back. Most of the chef's time is spent walking, not cooking.

That's the memory wall.

High-Bandwidth Memory — HBM — is the solution: take the pantry, build it into a skyscraper, and stick it **three millimeters from the stove** with an ultra-wide walkway between them. Now the chef cooks continuously.

In your own notes, this is the "quiet kingmaker" of the AI boom. The numbers back it up: Micron's HBM revenue is projected to go from $0.6 billion in 2024, to $7.8 billion in 2025, to $13.7 billion in 2026, to $20.1 billion in 2027. HBM's share of Micron's DRAM revenue: 3% → 21% → 31% → 39%. Every HBM wafer is sold out through 2027. You cannot buy a spot in the queue.

This is exactly what happened with advanced lithography in the 2010s. When the curve got steep enough, the tools got constrained, and the tool makers became the kingmakers. ASML today is worth more than Intel. Micron in 2028 may be worth more than Nvidia's operating divisions.

---

## Why the buildout is bigger than Moore's ever was

Moore's Law spent a trillion dollars of global capex over its 50-year run. Scaling laws are about to spend a trillion dollars in the next three years alone.

Five reasons:

**1. The cycle is faster.** Nvidia launches a new flagship every 12 months now — Blackwell → Rubin → Rubin Ultra. TSMC launched a new node every 30 months at Moore's peak. Cycles that fast compound capex demands much more quickly.

**2. The capex concentrates in one buyer tier.** Moore's Law served tens of thousands of companies — every PC maker, every device brand. Scaling laws serve approximately ten buyers: Microsoft, Google, Meta, Amazon, Oracle, OpenAI, Anthropic, xAI, a few sovereign funds. When ten buyers place $100B orders each, the industry reshapes itself around them in ways it never had to for Intel's PC customers.

**3. The physical footprint extends further downstream.** A 5nm transistor fits on a wafer. A modern AI training cluster needs a **power substation, a gigawatt of generation capacity, a cooling loop that consumes swimming pools of water, a fiber network, a transformer supply chain, and a city's worth of land**. Your Capex notes are right that "AI has entered its electrons-and-exhaust phase." The IEA says global data-center electricity demand will more than double to 945 TWh by 2030, with the US accounting for half the growth.

This is why Constellation Energy, Vertiv, Eaton, Schneider, Quanta Services, Corning and Credo are suddenly behaving like semiconductor stocks.

**4. The capability payoff is immediate.** Moore's Law gave you 2× the transistors — you had to go design a product to use them. Scaling laws give you **a model that is demonstrably smarter, demonstrably more useful, and demonstrably more valuable within 60 days of the training run completing.** The payoff loop is so much tighter that the capital velocity is much higher.

**5. The geopolitical stakes are higher.** In 1990, being behind on Moore's Law meant your consumer electronics industry was less competitive. In 2026, being behind on scaling laws is framed as existential. That's why Saudi Arabia alone is spending $40B on HUMAIN. That's why France, Germany, the UK, Japan, India and UAE are all standing up "AI factory" programs. That's why the AMD-OpenAI 6-gigawatt deal was front-page news and the iPhone 17 wasn't.

---

## The best historical lesson Moore's Law teaches us

The single most important lesson from 50 years of Moore's Law:

**The industry consistently under-forecasted the curve.**

In 1995, experts said transistors couldn't shrink below 250nm because of optical diffraction limits. They did.
In 2005, experts said 45nm was the wall. It wasn't.
In 2015, experts said 7nm was physically impossible without a new paradigm. TSMC is shipping 2nm in 2026.

Every decade, the industry said the curve was about to bend. Every decade, it didn't. And every decade, the people who bet against the curve — who cut their capex, who downsized their fabs, who assumed demand would flatten — got destroyed by the ones who kept the faith.

**The same story is playing out in AI right now.** Every quarter, skeptics announce that scaling laws have hit a wall. Every quarter, the next flagship model comes out and the curve holds. OpenAI o3-reasoning beat every benchmark the skeptics pointed at. Claude Opus 4 held the loss curve. Gemini 3 kept it going.

Ilya Sutskever said recently that the pre-training scaling regime is slowing down — but that was a statement about *which axis* is scaling, not whether scaling has stopped. The compute going into inference-time reasoning is now growing faster than training compute did three years ago. A new axis opened up and everyone pivoted onto it. Same as when Moore's Law stopped being pure lithography and became advanced packaging + chiplets. The CURVE continued. The technology underneath shifted.

---

## Where this framing cracks (the honest corner)

To write this essay world-class, I have to say where the framing is weakest.

**Moore's Law had a deeper physical motivation than scaling laws do.** Silicon transistors shrink because smaller transistors actually work better — they switch faster, use less energy, fit in less space. Scaling laws have less-clear physical grounding. They may reflect the statistical structure of language and visual data, or they may be an artifact of current model architectures. We don't know yet. The line could break in a way Moore's never really did.

**The cost per unit improvement is rising, not falling.** Moore's Law got cheaper — transistors got more plentiful at lower unit price. Scaling laws get **more expensive** — each next-generation model costs roughly 10x the previous one. That's not sustainable forever unless either (a) algorithmic efficiency starts compounding on top of scaling, which it is starting to, or (b) the economic value scales even faster, which it might.

**The pool of buyers is narrower.** Moore's Law had a billion end customers. Scaling laws have ten. If two of those ten falter on capex — if OpenAI's economics crack, or if Meta pulls its guidance — the curve could bend abruptly. Moore's Law was never that fragile.

These are real cracks. But Moore's Law had its own cracks — the end of Dennard scaling in 2005, the frequency plateau, the leakage crisis. The industry found workarounds. AI will probably find workarounds too: better algorithms, better inference compute, sparse models, model distillation. The *curve* may continue even as the *technology underneath* mutates.

---

## The investment thesis in one breath

If you believe AI scaling laws are the new Moore's Law, the investment playbook writes itself. It's the same playbook that worked for 50 years of semiconductors:

1. **Own the monopoly at the top.** Moore's Law: Intel, then TSMC. Scaling laws: Nvidia. (Already priced in.)

2. **Own the oligopoly below it that everyone depends on.** Moore's Law: Applied Materials, ASML, KLA. Scaling laws: **Micron, SK Hynix, Samsung for HBM; TSMC for CoWoS packaging; Broadcom for networking silicon.**

3. **Own the picks-and-shovels for the new physical constraint.** In the 2000s, the constraint moved from compute to lithography — ASML won. In the 2020s, the constraint is moving from compute to memory-and-power — **Micron wins on the memory side; Vertiv, Eaton, Schneider, Quanta win on the power side; Corning, Credo, Lumentum, Coherent win on the optics side; Constellation wins on the generation side.** Every one of these is your database's own thesis. Every one of them is currently trading at a PE multiple that, if scaling laws hold, will look comical in five years.

4. **Don't own the prematurely-hyped adjacents.** Moore's Law made millionaires out of dot-com companies that had no moat and lost everything. Scaling laws will make the same mess out of "AI companies" that are just API wrappers with no infrastructure claim. **The infrastructure layer is where the compounding actually happens.**

5. **Don't get short the curve.** This is the hardest and most important rule. There will be weeks when the curve looks like it's bending. There will be papers from credible researchers saying scaling laws are over. **Every one of those calls has been wrong for five years running.** If you have to bet direction, bet that the curve continues, even if you're not sure of the exact mechanism that keeps it going.

---

## Bring it home

Moore's Law wasn't a physics law. It was a social contract that produced the largest industrial buildout in human history.

AI scaling laws are the same kind of contract — just signed at ten times the speed, with ten times the capex, and ten times the geopolitical stakes. The people who understood Moore's Law as a self-fulfilling prophecy made fortunes. The people who dismissed it as a lucky line on a chart missed every wealth event for fifty years.

The chart is here again. The religion is reforming. The sovereigns are signing up. The supply chains are reorienting.

The only real question is whether you're building a portfolio for a world where AI scaling laws continue, or one where they don't. If you're on the fence: look at who's spending the $500 billion. They've already voted.

The first AI wave was about buying GPUs. **The next wave is about feeding them, powering them, connecting them, and cooling them** — and owning the oligopolies that do it.

That's where the next trillion dollars of enterprise value gets printed.

The chart is real because everyone believes it is.

And everyone believes it is because the chart is real.

That's Moore's Law. That's scaling laws. That's the whole game.

---

_Built on the ROS Startup Database thesis material + Stephen McBride's April 2026 AI Capex working notes. Figures cross-checked against Meta FY26 capex guidance, AMD Q4 2025 earnings (the six-gigawatt OpenAI deal), IEA 2030 data-center demand projections, and Micron's December 2025 HBM supply commentary._
