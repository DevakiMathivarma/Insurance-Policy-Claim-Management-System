# Mandatory Demo Flow 

This explains exactly what happens, step by step, when someone uses the app to
run a real insurance policy from purchase through to a settled claim —
including the background things (emails, live updates, generated documents)
that happen automatically without anyone clicking a separate button for them.

---

## 1. Register

Before anything else can happen, people need accounts. Here's how each type of
account actually gets created:

- The very first account, the **Super Admin**, is created automatically the
  moment the app starts — nobody has to sign it up.
- The Super Admin then creates an **Insurance Agent**, a **Claims Officer**,
  and a **Finance Officer** — all 3 report directly to the Super Admin, there's
  no extra layer of hierarchy.
- A **Customer** can either sign themselves up directly with no login needed
  at all, or an Insurance Agent can create the customer's account on their
  behalf — exactly like calling an insurance company and having someone set up
  your policy application for you over the phone.

**Background tasks involved here?** No, nothing happens automatically at
registration.

---

## 2. Login

Whoever's using the app logs in with their email and password.

**What actually happens:** the app hands back two things — a short-lived
"access token" (used for every single action afterward) and a longer-lived
"refresh token" (used only to get a fresh access token later, without having
to type the password again). The short token limits how much damage could
happen if it ever leaked, while the refresh token keeps the person logged in
smoothly.

---

## 3. Create Plan

The Super Admin builds an actual insurance product — "Comprehensive Health
Cover," with a coverage amount, a premium, an age range it's sold to, and how
many years it runs.

**What's checked automatically:** the coverage amount must genuinely be higher
than the premium — you can't create a plan promising to pay out less than what
someone pays in. The eligibility age range also has to make sense (a minimum
genuinely lower than the maximum).

---

## 4. Register Customer

A real person joins the system — either by signing up themselves, or an
Insurance Agent doing it on their behalf.

**What's checked automatically:** the customer must genuinely be an adult (18
or older) to hold their own account. Their email and their identification
number both have to be unique — the system won't let two different people
register with the same ID number.

---

## 5. Create Policy

An Insurance Agent sells a specific plan to a specific customer.

**What happens automatically, all at once:**
- The app checks the customer's actual age against this specific plan's
  allowed age range — someone too young or too old for a plan simply can't buy
  it
- It checks the plan itself is still active and available for sale
- It generates a real, unique policy number on its own (like "POL-2026-798073")
- It locks in the coverage amount and premium exactly as they stood on the
  plan at that moment — so if the plan's price changes later, this specific
  customer's agreed terms never silently shift

At this point, the policy exists but is only marked "Pending" — it isn't
genuinely active until the first premium payment actually comes in.

---

## 6. Add Beneficiary

The Agent (or the customer themselves) records who should receive the payout
if something happens — a spouse, children, other family members — each with
their own percentage share.

**What's checked automatically:** all the percentages added up across every
beneficiary on this one policy can never go over 100% — the moment an addition
would push the total past that limit, it's rejected immediately, with a clear
message showing exactly how much room is actually left. The system also won't
let the exact same person be listed twice on the same policy.

---

## 7. Pay Premium

This is the single biggest moment in the whole flow — the point where the
customer's payment actually gets recorded.

**A lot happens automatically, all at once:**
- The payment amount has to exactly match what this policy's premium actually
  is — no more, no less
- Each payment needs its own unique reference number — the system won't allow
  the exact same payment to accidentally be recorded twice
- If this is the very first payment on this policy, the policy's status
  automatically flips from "Pending" to "Active" right then and there
- A **PDF policy document** gets generated — a real file showing the
  policyholder's name, the plan, the coverage amount, and the dates — and it
  gets attached to an email
- **Two emails get queued to send** — one confirming the payment went
  through, and one confirming the policy activation (with that PDF attached).
  These don't send instantly from the same request — they get handed off to a
  background system (Celery) that sends them a moment later, so the person
  making the payment doesn't have to sit and wait for an email to finish
  sending
- The system also quietly records when the **next** premium payment will be
  due, so it can later send a reminder or flag it as overdue without anyone
  needing to track that by hand

---

## 8. Submit Claim

Once something actually happens — an accident, a hospital visit — the customer
reports it.

**What's checked automatically:** the policy this claim is filed against has
to genuinely be active right now — you can't file a claim on a policy that's
been cancelled or hasn't even started yet. The date the incident happened has
to fall inside the policy's own coverage period. The amount being claimed
can't be higher than what the policy actually covers. And the system won't let
the same incident be claimed twice.

A claim starts as a private "Draft" — the customer can still review and adjust
details before formally submitting it. Once they do submit it, an email goes
out confirming the claim is now genuinely in progress, and — for anyone
watching this claim live through a real-time connection (similar to how a live
sports score updates on its own without refreshing the page) — its status
change appears instantly.

---

## 9. Upload Documents

The customer attaches real supporting evidence — a medical report, a hospital
invoice, an ID proof, whatever's relevant to this specific claim.

**What's checked automatically:** only genuinely allowed file types (like PDFs
and photos) are accepted — anything else gets rejected outright, before it's
even saved. Each file also has a maximum size it can't exceed.

Once uploaded, each document sits waiting as "Pending" until a Claims Officer
actually reviews and verifies it.

---

## 10. Claim Assessment

A Claims Officer formally reviews everything — the claim itself, the
documents, the incident details — and decides how much of it should actually
be paid.

**What's checked automatically:** the amount the officer decides is eligible
can never be higher than the policy's real coverage ceiling — the system
enforces that hard limit regardless of what the officer types in. Also, a
claim can only ever be assessed once, not repeatedly.

---

## 11. Approval

Based on the assessment, the Claims Officer makes the final call — approve or
reject.

**What's checked automatically:** every single document attached to this
claim has to already be marked "Verified" before an approval is allowed to go
through — an unverified document blocks the whole claim from moving forward,
no exceptions.

The moment a decision is made, an email goes out to the customer either way,
and the same live, real-time update appears for anyone watching this claim.

---

## 12. Settlement

Once a claim is genuinely approved, the Finance Officer processes the actual
payout.

**What's checked automatically:**
- Only claims that are truly "Approved" can be settled at all
- The amount actually paid out can never be higher than what the Claims
  Officer's own assessment said was eligible
- The exact same claim can never be settled twice — the system physically
  won't allow it
- The moment settlement succeeds, the claim's own status automatically
  flips to "Settled"
- A **PDF settlement letter** gets generated, showing the approved amount and
  a payment reference, and gets attached to a final settlement email
- The same live, real-time update fires one last time for this claim

---

## 13. Policy Renewal

When a policy is nearing its end date, it can be renewed rather than left to
simply expire.

**What happens automatically:**
- The app checks the policy is genuinely eligible to renew (active or already
  expired, not cancelled)
- A brand-new policy gets created, picking up exactly where the old one's
  coverage period ends — same coverage amount, same premium, a fresh policy
  number
- The new policy keeps a permanent link back to the original one, so the
  full renewal history can always be traced
- The system also won't let the exact same policy be renewed a second time

---

## The Big Picture

```
Register (Admin → Agent/Claims Officer/Finance Officer → Customers)
   → Login (access + refresh tokens)
   → Create Plan (coverage must exceed premium)
   → Register Customer (age + uniqueness checked)
   → Create Policy (eligibility checked, coverage/premium locked in)
   → Add Beneficiary (percentages must total 100%)
   → Pay Premium (amount matched, policy activated, PDF + 2 emails)
   → Submit Claim (policy/date/amount validated, email sent, live update pushed)
   → Upload Documents (file type + size checked)
   → Claim Assessment (eligible amount capped at coverage)
   → Approval (all documents must be verified, email + live update)
   → Settlement (capped at eligible amount, PDF + email, live update)
   → Policy Renewal (eligibility checked, new period generated, duplicate blocked)
```

Every step that changes something important — a policy's status, a claim's
progress, a payout amount — happens automatically, as a direct result of the
action taken. Nobody has to do math by hand, remember to send a notification,
or manually check whether a document's been verified. The system keeps
everything accurate and connected on its own, from the very first registration
all the way through to a fully settled claim and a renewed policy.