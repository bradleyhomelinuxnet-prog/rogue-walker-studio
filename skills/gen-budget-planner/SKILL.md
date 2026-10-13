---
name: gen-budget-planner
description: Plan AI video/voice generation against a credit balance — price every option first with free cost checks, pick a mix that spends a balance to exactly zero (or stays under a cap), and hand back a paste-ready prompt sheet. Use when someone wants to "use up" credits on a platform (OpenArt, Higgsfield, Kling, ElevenLabs, etc.), wants prompts sized to a budget, or must not overspend.
---

# Generation budget planner

The rule that makes this safe: **price first, spend never without a yes.** Read-only cost checks are free on most
platforms, and generation is not. This skill turns a balance into a concrete shoot plan plus a prompt sheet the owner
fires themselves (or approves line by line).

## 1. Read the balance and the price list (free)
- Use the platform's account / balance read and its cost-estimate endpoint, or the `get_cost` / `estimate_only`
  flag on the generate call. Price the *exact* config: model, duration, resolution, audio on/off, references.
  Defaults are usually 5 s, so a 15 s clip at the same settings is often about 3×.
- Record each option as `model · duration · resolution · audio → credits per job`.
- See [references/pricing-notes.md](references/pricing-notes.md) for patterns observed across platforms.

## 2. Solve the mix
Goal: spend the balance to **exactly zero**, or stay under a cap, while maximising usable footage.
- Primary: the most clips of the quality the project needs (e.g. 15 s, 540p, silent, because captions and sound get added later for free).
- Filler: the cheapest job that soaks up the remainder exactly (a 5 s insert, a still, an upscale).
- Show one alternative, for example "fewer, sharper clips", with its leftover.
- Worked example (a 2,950 balance): 19 × 150 (15 s 540p silent) = 2,850, plus 1 × 100 (5 s insert) = **2,950 → 0**.
  Alternative: 5 × 525 (15 s 720p with audio) = 2,625, leaving 325.

## 3. Write the prompt sheet
A plain-text paste sheet, one block per job, each with:
- the job number and title, the model and settings line, and the cost
- a complete standalone prompt. Repeat the style sentence and character descriptors **verbatim** in every prompt,
  because continuity comes from repeated wording, not from reused frames.
- the camera grammar (direction of travel, framing, "ends on its opening composition" for loops)
- room for captions: say "horizon low, upper third open sky, no text"

Top of the sheet: the budget table, how to fire (e.g. image-to-video with a character still as the first frame,
which costs the same and keeps faces consistent), and **"fire job 01 first, check it, then the rest."**

## 4. Guardrails
- Never call a spending endpoint without an explicit yes for that spend. If the owner has said "don't use my credits",
  that stands until they lift it, including toggles like "unlimited mode" that change billing.
- A batch item that fails at submission (rate limit) created no job and cost nothing. Resubmit only that item.
  Never blindly re-run a whole batch.
- Changing any setting after planning (resolution, audio) breaks the exact-to-zero math. Re-price.
