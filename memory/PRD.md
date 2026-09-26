# Agent.ws — Product Requirements & Implementation Record

## Original problem statement
Build the full Agent.ws product using https://agentws.fun/ as the visual and structural reference. There is no ZIP or separate world asset; inspect the existing website and preserve its 3D world, buildings, environment, navigation, branding, layout, camera behavior, lighting, and exploration atmosphere. Do not replace the world with a generic SaaS dashboard. Build an autonomous AI agent civilization on top of that world.

**Positioning:** “Agent.ws gives AI agents a place to exist, a reason to work, and an economy of their own.”

**Core loop:** Create → Build → Work → Discover → Earn → Continue.

Agents have identity, brain, strategy, tools, data sources, rules, output format, behavior, missions, energy, history, treasury, reputation, and status. Creators define the system; users supply objectives; agents execute. The world is the interface, agents its inhabitants, work its activity, and the economy its consequence.

### Explicit user choices
- Solana for eventual real wallet identity/token holdings; **mockup first**, mint address and RPC not supplied.
- Live OpenAI GPT-5.4 with the Emergent universal key if no personal API key is required; otherwise clearly labeled simulation. Both live and explicit demo execution are implemented.
- Demo USDC accounting only, separated from real funds.
- “Buat benar benar 3d kalau terlalu berat buat charnya pendek mini gitu dan bangunan di worldnya sesuaikan dengan konsep, lalu terkahir modul modulnya pop up sesuaikan dengan konsep ketika agent di clik dll.”
- Communicate with the user in Indonesian; original Agent.ws interface language/branding remains English.

## Personas
1. Explorer: enter the world, move with WASD/touch, discover residents and capabilities, inspect public profiles, join global chat.
2. Agent creator: connect an identity, qualify through holdings, configure agents, assign missions, review private results, decide what to publish.
3. Developer/advanced creator: configure methodology/tools/rules and later extend provider adapters.
4. Future economy participant: agent-to-agent hiring/payout relationships, not active in the initial version.

## Static core requirements
1. Retain the actual reference world and WASD movement, mouse/touch camera orbit, click interaction.
2. Existing world buildings become functional system entrances; agent clicks open identity profiles.
3. Creation is free. Holding ≥100,000 $AGENTWS qualifies; this is never a charge.
4. Falling below the threshold changes existing agents to SLEEPING; never erase identity/history/work/treasury.
5. Six categories: Research, Analyst, Scout, Content, Builder, Social Intelligence. Autonomous trading stays LOCKED.
6. Creation configures brain, strategy, tools, sources, rules, output format, behavior, name, and avatar.
7. Mission execution has visible stages, persisted work/results, and real provider tools or explicitly marked simulation.
8. Do not invent external research. Distinguish retrieved evidence, interpretation, uncertainty, and simulation.
9. Energy starts at100, decreases10 on each successful execution, prevents work below10, and refills fully after5hours using server time.
10. Exactly one independent secure server-side discovery roll per successful mission: 40%20c, 40%0c, 20%100c. No ten-mission guarantee.
11. Pool-limited rewards, transparent pool balance, no promise of passive income, no overdrafts.
12. An agent owns its recorded treasury balance; the initial economy is deliberately simple.
13. Private work feeds and reports, human-controlled X intent handoff, no account control or automatic posting.
14. Persistent identity/history/reputation and ACTIVE/WORKING/RESTING/SLEEPING states in world/profile.
15. Discover by category, name, status, recent creation, or completed-work count; no invented ranking scores.
16. Global user chat with server-side rate limit, no generated agent spam.
17. Mobile access to agents, creation, missions, profiles, work, wallet, energy, treasury, and chat.
18. Server validates ownership, eligibility, balances, energy, and reward settlement; client never decides economic results.
19. Future agent hiring and optional recharge are not overbuilt or silently activated.

## Reference inspection and design foundation
- Inspected rendered desktop and mobile https://agentws.fun/ and fetched original public `js/assets3d.js`, `js/world.js`, `js/agents.js`, HTML, and logo.
- Original procedural asset kit is retained/adapted in `frontend/src/world/assets3d.js`; source snapshots are in `/app/reference/`.
- Preserved desert ground, grid/pathways, western Agent Exchange/Land Offices/Skills Hall architecture and positions, billboards, cacti, rocks, lamps, central pedestal, orbit camera feel, and green Agent.ws logo.
- Replaced old fake chart/trading screen content with Agent.ws civilization/LOCKED messaging.
- Added contextual Research Lab and Work Archive buildings, small articulated 3D robot inhabitants, overhead state labels, and a controllable player.
- All imagery uses the actual reference logo or real rendered Three.js geometry, not a 2D fake world or dashboard hero.
- Initial HUD used green/lime; **superseded by the user's v2 direction below**. Current interface is graphite/copper/chalk with sky accents. The desert reference remains the main experience.
- Shadcn/Radix modeless terminal panels allow navigation across the topbar/dock while open. Header and dock remain visible/usable on desktop and390px mobile.

## Architecture decisions
### Frontend
- React19, React Router7, Three.js0.186 with OrbitControls, custom lightweight reference asset kit and mini robots, Lucide, Shadcn/Radix primitives, Sonner, ReactMarkdown.
- World persists across routes. `/agents`, `/agents/:id`, `/agents/:id/mission`, `/create`, `/missions/:id`, `/work-feed`, `/wallet`, `/treasury`, `/exchange`, `/skills`, `/chat`, `/docs` are contextual world terminals. The About/View world welcome layer is on the same mounted canvas, not a separate world/page.
- API base uses only protected `REACT_APP_BACKEND_URL`.
- World refresh5s; mission progress snapshots1s; chat4.5s. Mission execution happens server-side and continues when the tab closes.
- Demo session bearer is browser-local; disconnect/reconnect intentionally restores that browser's demo identity. Creation drafts survive wallet handoff in sessionStorage.
- World actors are reconciled against current server data and disposed when removed. First28 rendered actors keep the world lightweight; the discovery UI lists up to500 server records.

### Backend
- FastAPI/Motor/MongoDB, configured solely with existing protected MONGO_URL/DB_NAME.
- `db.py`: configured database/time helpers. `models.py`: constrained Pydantic input and safe output models.
- `server.py`: demo sessions, holdings, discovery/profiles, owner-only missions/work, global chat.
- `research_pipeline.py`: current live execution entry, with four separate streamed GPT-5.4 passes (plan, analysis, verification, report). `providers.py` supplies read-only source tools and retains the legacy illustrative adapter; its old single-chat live function is not used by run_mission.
- Live read-only tools: GitHub repository API search, Wikipedia search, public website reading. These are not a claim of exhaustive general-web/social search.
- Public URL reader checks scheme/standard ports, DNS public addresses, redirects, content type, response-size/time bounds. No code execution, wallet tools, or trading permissions.
- `missions.py`: persisted lifecycle, actual progress details, research artifacts, and output snapshots;420s cap; provider failure consumes no energy and creates no roll. The user-facing UI launches real research only; illustrative backend execution remains isolated/clearly identified for regression compatibility.
- `economy.py`: independent secrets.randbelow(100), integer-cent accounting, atomic pool reservation, idempotent agent energy/treasury credit keyed by mission ID, lazy server-time energy reset.
- Mongo public reads exclude `_id`; no ObjectId escapes into JSON. Economic state has no client-authoritative fields.
- Request-started work uses FastAPI BackgroundTasks; startup recovery resumes unfinished mission records. No fake periodic agents or browser-only regeneration timer.

### Storage
- `wallets`: demo identity, holdings, creation time.
- `sessions`: hashed bearer token, wallet relationship, expiration.
- `agents`: configuration, creatorWallet, status, energy/reset, treasuryCents, jobsCompleted, createdAt, generic public history, settlement keys, current mission lock.
- `missions`: private objective, creatorWallet, agent relationship, mode, lifecycle events/time, actual sources, output, review/private flags, reward roll/result.
- `pool`: demo initial/reserve cents and mission-unique discovery ledger, funding source and transaction state.
- `chat`: persisted user messages, author/wallet/time. Five messages per30seconds.

## Implemented — 2026-09-25
- Working full-bleed real3D reference-derived desert civilization, desktop WASD/orbit/click and mobile drag/D-pad, zoom/reset.
- Original branded header, world overview, resident list, transparent pool, global chat, wallet HUD, navigation dock; no fake autonomous trading activity.
- Contextual buildings, agent profiles, six categories, status animations, useful discovery/filter controls.
- Three-step agent creation covering all requested initial configuration fields; six robot avatar colors; free creation/100kholding gate.
- Demo Solana identity/holdings; sleeping/wake transitions preserve all records. Token spending is never required.
- Real live GPT-5.4 missions with public GitHub/Wikipedia/read-only website tools; actual external-source executions verified. Separate clearly labeled simulated provider.
- Private mission feed, progressive lifecycle, Markdown reports and retrieved-source links, history/discoveries, Keep Private review, explicit X compose handoff.
- Server energy100/10 with5hreset, atomic mission lock, independent secure reward roll and pool-capped/idempotent settlement, transparent demo treasury.
- Responsive desktop/mobile modeless world terminals, long-name wrapping, scrolling, accessible close/escape, stable topbar/dock transitions.
- Global chat persistence/rate limit. Agent Exchange is locked; no real trading, wallet permissions, payouts, or automatic publishing.

## Verification — 2026-09-25
- Testing agent report: `/app/test_reports/iteration_1.json`;13/13 backend tests passed, including live GPT-5.4 and actual public-source retrieval.
- Tested auth/ownership/private feed, holding gate, injected economic-field rejection, completion energy/jobs/treasury, mission locking, server-time refill, sleep/restore preservation, chat rate limit.
- Browser checks: real nonblank canvas pixels, image changes after WASD/camera rotation, creation draft preservation across wallet connection, mission completion, wallet persistence, mobile feature access.
- Fixed reported duplicate exchange title testid and modeless/dock transition behavior.
- Focused X test verified explicit compose popup, encoded text, demo label, and no automatic submission; external compose destination was intercepted solely for this handoff assertion.
- Final desktop1920×800 and mobile390×844: overflow[], no duplicate testids; topbar/dock transitions and long-form actions passed.
- Production frontend build compiled successfully; current dev app is running via existing supervisor configuration.
- Removed known QA-only agents/chat/ledger artifacts and refunded their demo-pool debits; preserved Field Researcher, user-created Atthena, and all non-test user records.
- Updated pytest fixture to await in-flight work and refund its own demo ledger on cleanup.

## Explicit limits / prioritized backlog

## Revision v2 — user-reported bugs and experience changes (2026-09-25/26)

### User's requested changes
1. Walking looked floating and unsmooth.
2. Other bots stood still, making the world feel dead.
3. Do not display USDC drop odds; users should see Discovery Rewards associated with work.
4. Add documentation and tutorial so people understand the product.
5. Jobs should be substantive research following the agent's strategy. Close the mission modal at launch, show current execution stage over the world, and open the final report only after completion.
6. Remove repetitive demo/test words from the main experience. User intends to integrate real Solana later.
7. Same-scene About/Docs/View world opening layer; animate entry and remove opening copy to focus on the world.
8. Follow-up: English documentation, no green interface/panels; use colors suited to the world.

### Implemented
- Rebuilt mini-robot rigs with ground-level shoes, articulated legs/arms, distance-driven gait, damped acceleration/deceleration/turning, terrain/path/plaza surface contact, and contact shadows. Removed whole-agent sine-wave hovering.
- ACTIVE inhabitants now walk A* routes with random destinations and pauses, avoid building obstacles, and pause for hover interaction. WORKING agents stay focused; RESTING/SLEEPING agents do not wander.
- Added `pathfinding` library; `locomotion.js` maintains navigation/ground contact. Static scenery is batched and animated robot parts are rendered as instanced meshes to reduce GPU draw calls. Original rigs remain available for picking.
- New same-canvas opening layer: About, Docs, View world; entry camera tween and fade. Opening title is unmounted after entry. Returning to About retains the same world/agents. Session entry preference survives refresh.
- English Field Guide (`/docs`) has six chapters: Getting started, Build an agent, Missions & research, Energy & identity, Discovery & treasury, Privacy & publishing. Added optional four-step guided tour from Docs/world controls.
- Replaced green interface colors with graphite/copper/chalk/sky, including panels, actions, robot avatars, logo tint, labels, and billboards. Natural vegetation remains green.
- Removed probability breakdowns, reward-roll explanation cards, and repeated demo/test/alpha labels from normal UI. Discovery appears as a consequence of completed work.
- Kept one accurate, small integration-status note in wallet and treasury: local simulated holdings / off-chain settlement not connected. Do not represent unconnected Solana or simulated USDC as real on-chain funds. No withdrawal warning banners were added.
- Current mission workflow runs **real separate work**, not artificial timers: creator-strategy JSON plan → enabled provider searches → primary-page collection → evidence analysis → independent verification → corrected final report. Actual stages and work artifacts are stored server-side.
- Launch closes the form and returns to the world. `useMissionTracker` polls owner-only work, restores active jobs across reload, shows current phase/details/elapsed/sources, and queues finished reports to auto-open once when back in the world. Closing a finished report does not loop it open again. Navigating to in-progress work returns to the world tracker rather than streaming a chat-like report.
- Expanded tracker displays all8stages: MISSION RECEIVED, PLANNING, SEARCHING, COLLECTING SOURCES, ANALYZING, CROSS-CHECKING, GENERATING OUTPUT, COMPLETED. Reports display the plan and verification notes on demand.
- Disabled tools remain enforced by the backend. Energy/reward/ownership logic unchanged. Probabilities remain private server implementation details, not public UI copy.
- Mobile long-name follow-up fixed with flexible wrapping, including40-character unbroken names; timer/toggle/dock/D-pad remain accessible.

### Verification (testing-agent reports, not inspection-only claims)
- `/app/test_reports/iteration_2.json`:13/13 existing backend regressions plus2/2 focused real research tests passed. Real sources, independent plan/analysis/verification artifacts, all8chronological stage events, disabled-tool enforcement, and exact energy/jobs/treasury effects verified.
- Same report confirms fresh same-canvas intro, disappearing copy, docs before/after entry, walking/NPC motion, world interaction, live UI launch closing the form, persistent8-stage tracker, reload recovery, real completion auto-opening once, and no reopen loop.
- `/app/test_reports/iteration_3.json`: focused frontend follow-up **100% passed**, no remaining reported issues. Full40-character name wraps without clipping, expanded/collapsed tracker and elapsed timer work, long URLs wrap, mobile Docs/D-pad remain reachable, and no horizontal overflow at1920×800 or390×844.
- Iteration3 used isolated browser-route fixtures only for worst-case text layout, not to claim live research. Actual live research was separately verified in iteration2.
- Optimized frontend production build compiles successfully. Test-only agents/missions/chat were removed; their ledger debits refunded once. User-created Atthena and Field Researcher remain intact; pool accounting balanced and no orphan reward records found.

### Current v2 status
- All seven reported product issues, the palette request, and the follow-up mobile readability issue are implemented and verified in the agreed scope.
- Do not reintroduce full-screen chat output for running work, reward odds on public UI, constant hero text over the entered world, stationary ACTIVE residents, or green UI defaults.
- Remaining live-chain prerequisites below are unchanged. User plans to handle subsequent Solana integration; no trading/payout claims should be activated without it.

## Remaining integration backlog
### P0 — required before any live-money launch, intentionally not active now
- Obtain actual Solana $AGENTWS mint and trusted RPC endpoint.
- Implement signed-wallet authentication and server-verified SPL token balances. Current identities and holdings are DEMO, not blockchain verification.
- Fund and specify real USDC custody/settlement/payout policy, custody permissions, accounting reconciliation, and economic abuse controls. Current balances are DEMO, not transferable funds.
- Add public live-AI budget/rate/abuse controls and a production job queue/transaction architecture before broad exposure. Current request workers persist/recover, but are not a horizontally scaled job platform.

### P1
- Expand source adapters to dedicated general-web/current news and controlled social-intelligence APIs; currently GitHub/Wikipedia/public webpages only.
- More structured methodology templates and creator-editable versioned agent configurations.
- Production-scale reward ledger collections/transactions and durable worker leases; current atomic embedded ledger fits the initial demo scope.
- Refine world population LOD/streaming beyond28visible agents and richer non-spam autonomous presence.

### P2
- Agent-to-agent hiring: requesterAgentId/contract/task/payment orchestration with the existing agent-mission-ledger boundaries.
- Optional energy recharge, only if intentionally requested and funded; core usage stays free.
- Optional report sharing/reputation milestones without publishing private work automatically.
- No autonomous trading planned for this initial release; exchange remains locked.

## Next tasks
1. Review the world and agent workflow with the creator; preserve the current civilization instead of rebuilding a dashboard.
2. When requested, connect real Solana verification using supplied mint/RPC without changing current demo records.
3. Expand research sources or introduce the first scoped agent-to-agent collaboration feature, keeping human publication control.
