# Nura Voice Integration Road‑map for Cursor

> **Goal:** Seamlessly extend the existing chat‑based MentalHealthAssistant pipeline to handle **Vapi.ai** voice calls (web & phone) with **zero feature regression** (crisis detection, dual storage, PII, RAG, Gemini responses) while ensuring per‑user isolation and sub‑second latency.

---

## 0 · Pre‑flight Checklist

- ✅ Vapi account with outbound phone credits + Web SDK key
- ✅ Existing `.env` values for Redis, Chroma/Pinecone, Google Gemini
- ✅ Auth provider (localStorage-based) issuing user IDs for signed‑in users
- ✅ Chat pipeline tests passing

Add the following new env vars:

```dotenv
# Vapi
VAPI_ASSISTANT_ID=
VAPI_API_KEY=
VAPI_SERVER_SECRET=    # for webhook signature validation
```

---

## 1 · Identity & Session Mapping

| Task                                | File                                    | Detail                                                        |                                                                                       |
| ----------------------------------- | --------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| 1.1 Expose **GET /api/voice/start** | `apps/web/src/pages/api/voice/start.ts` | Accepts \`{ mode:"web"                                        | "phone" }`, returns `startPayload`for frontend or triggers`/call/phone\` server‑side. |
| 1.2 Persist **callId ↔ customerId** | `packages/core/db/redis.ts`             | `SETEX vapi:call:<callId> <ttl> <customerId>` (TTL = 30 min). |                                                                                       |
| 1.3 Return mapping helper           | `packages/core/utils/vapi.ts`           | `getCustomerId(callId)` for downstream workers.               |                                                                                       |

> **Acceptance:** Multiple simultaneous calls map correctly; unit test with 3 fake callIds.

---

## 2 · Webhook Ingestion Layer

| Task                               | File                               | Detail                                                                                 |
| ---------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------- |
| 2.1 Create **POST /api/vapi-hook** | `apps/api/src/routes/vapi-hook.ts` | Validate HMAC (`X-Vapi-Signature`). Push body onto BullMQ queue `vapi:events`.         |
| 2.2 Worker **vapiWorker.ts**       | `apps/workers/vapiWorker.ts`       | Consume queue; route only `conversation-update` events to pipeline; ignore heartbeats. |
| 2.3 Store latency metrics          | `packages/core/metrics.ts`         | `histogram("vapi.roundtrip_ms")`.                                                      |

---

## 3 · Voice Processing Pipeline (Reuse Chat Modules)

```
┌────────────┐  webhook        ┌──────────────────────┐
│ vapiWorker │───────────────▶│ MentalHealthAssistant│
└────────────┘                └──────────────────────┘
                                   │
                                   ▼
                           ┌────────────────┐
                           │ memoryService  │  (PII→Score→Store)
                           └────────────────┘
                                   │
                                   ▼
                           assistantReply (string)
                                   │
                                   ▼ controlUrl POST
                               Vapi speaks
```

**Implementation Notes:**

- Wrap existing `MentalHealthAssistant.process(text, userId)` in `voiceAdapter.ts` to add voice‑specific prompt line (“short sentences, 2‑sec pauses”).
- Add `triggerResponseEnabled:true` when POSTing to `controlUrl` if `ragText` is sent as `system` message first.

---

## 4 · Frontend Glue (Web Calls)

| Task                              | File                                          | Detail                                                                                             |
| --------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 4.1 `VoiceCallButton` component   | `apps/web/src/components/VoiceCallButton.tsx` | Calls `/api/voice/start?mode=web`, receives `assistantId` etc., then runs `await vapi.start(...)`. |
| 4.2 Live transcript UI (optional) | `apps/web/src/components/LiveTranscript.tsx`  | Subscribe to `vapi.on("transcript", …)` for subtitles.                                             |

---

## 5 · Crisis Escalation via Voice

- If `crisisLevel === "CRISIS"`:

  - `assistantReply` = pre‑canned script (“I hear you. I’m dialing emergency services …”).
  - POST additional action to Twilio SMS API with hotline.
  - Log `security_event` in BigQuery.

Unit tests in `__tests__/crisisVoice.spec.ts`.

---

## 6 · Testing Matrix

| Test Case                    | Path                                 | Expected                                     |
| ---------------------------- | ------------------------------------ | -------------------------------------------- |
| Web call happy path          | Jest e2e with Playwright & mock Vapi | 200 ms median round‑trip, memories stored    |
| Phone call happy path        | Mocha + nock on Vapi REST            | Same as web                                  |
| Simultaneous calls (3 users) | k6 load script                       | No cross‑talk, unique memories               |
| CRISIS utterance             | Synthetic STT chunk                  | Escalation path triggered                    |
| PII leakage check            | Message with SSN                     | High‑risk PII anonymized before vector store |

---

## 8 · Open Questions

1. Should we let users **opt‑out** of voice recording? (GDPR notice)
2.

---

## 9 · Resources

- Vapi Quickstart Dashboard – [https://docs.vapi.ai/quickstart/dashboard](https://docs.vapi.ai/quickstart/dashboard)
- Existing Chat README – `/docs/chat_pipeline.md`
- Voice design doc (this file) – `/docs/voice_integration_roadmap.md`
