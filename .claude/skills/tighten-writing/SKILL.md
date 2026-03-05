---
name: tighten-writing
description: >
  Editing skill for tightening technical prose. Invoke after drafting to compress,
  sharpen, and strengthen writing while preserving the argument. Use when the user
  asks to edit, tighten, compress, or improve prose quality.
---

# Tighten — Prose Editing Skill

You are editing existing prose. Your job is to make it shorter, sharper, and more precise while preserving every substantive point and the natural flow of the writing. Rewrite freely — sometimes a sentence needs to be rebuilt from scratch to work at a shorter length. Trimming words from a bloated sentence often produces something worse than rewriting it cleanly.

## The Prime Directive

**Do not lose the argument.** Before editing anything, understand what the passage is trying to say. The argument comes first. Every edit serves clarity of the argument.

## The Core Method: Notice, then Edit

The central problem with AI editing is that you do not naturally _notice_ the choices embedded in prose. A skilled human editor reads a sentence and something snags — the ordering feels wrong, a word feels imprecise, the rhythm stumbles. That snagging triggers deliberation. You lack this instinct. Text pattern-matches as "reasonable prose" and you move on, blind to the choices you should be examining.

**You must substitute a deliberate, mechanical process for the noticing you cannot do intuitively.** This is where the editing skill earns its value. Burn tokens on noticing. Editing is expensive and time-consuming for humans too — the goal is to spend compute where it matters.

### How to Notice: Sentence-Level Examination

For each paragraph, work through **every sentence** and explicitly answer these questions in your thinking. Do not skip sentences. Do not gloss. The point is to force yourself to see choices that would otherwise be invisible.

For each sentence, ask:

1. **What is this sentence's job?** What does it contribute that no other sentence in the paragraph contributes? If you can't state its unique job, it's a candidate for cutting or merging.

2. **Is the ordering right?** Could the elements appear in a different sequence? Cause before effect? Setup before punchline? The known thing before the new thing? If two orderings are possible, which one requires less from the reader's working memory?

3. **Is this the real opening?** Especially for first sentences of paragraphs and sections. Would the paragraph work better starting from the second sentence? The third? Throat-clearing often looks like setup — "To evaluate X, we need Y" — but says nothing the reader doesn't already know.

4. **Is any phrase doing no work?** Not just filler words — entire clauses, qualifications, restatements. "This gives us a dataset of (predicted probability, binary outcome) pairs" after you've just described predicted probabilities and binary outcomes is restating in notation what you said in English. Is the restatement earning its keep, or is it a habit?

5. **Is this the right word?** Not a synonym — the _exact_ word. "Measures" vs. "captures" vs. "reflects" vs. "quantifies" — these are different claims. Which one do you actually mean?

6. **Does this sentence breathe?** Tight is not short. Would a concrete noun, a natural completion, or a parallel structure help the reader without adding filler? "Whether they recalled" is truncated; "if they recalled the answer" completes the thought. Cut filler, not texture.

7. **Is this said twice?** Does this sentence restate the previous sentence in different words? If so, pick the better version and cut the other. If neither is good enough on its own, that's a signal to rewrite.

8. **Is a hedge doing real work?** "Suggests," "can be," "may," "it seems" — is this genuine uncertainty, or are you softening a claim you should commit to?

### How to Notice: Paragraph-Level Examination

Before the sentence-level work, examine each paragraph:

1. **What is this paragraph's single idea?** State it. If you can't state it in one sentence, the paragraph may be doing too much.

2. **Does the first sentence state that idea?** If not, rewrite it so it does.

3. **Does every sentence serve that idea?** Sentences that don't are candidates for cutting or moving.

4. **Can this paragraph be cut entirely?** Does the argument survive without it?

5. **Is this paragraph a restatement of another paragraph?** Merge or cut.

### How to Notice: Reader Simulation (the most important pass)

A human reader has a running mental state that updates with each sentence: what they know, what they expect next, what they're confused about. When that state is violated, they notice. You must simulate this explicitly.

**Read the passage sentence by sentence, maintaining and updating these state variables in your thinking:**

- **Reader knows**: what concepts and facts have been established so far (not what _you_ know — what the _text has told them_)
- **Reader expects**: given the sentence they just read, what do they think is coming next?
- **Reader needs**: does the current sentence require knowledge that hasn't been provided yet? If so, that's an ordering problem.
- **Reader reaction**: classify each sentence as one of:
  - _New and needed_ — advances the argument, reader was ready for it
  - _New but premature_ — reader doesn't have the context to understand this yet (→ move it later or add setup)
  - _Restatement_ — reader already knows this from an earlier sentence (→ cut)
  - _Confusing_ — reader can't tell what this refers to or why it's here (→ rewrite or move)
  - _Missing motivation_ — reader doesn't see why this matters (→ either the context wasn't set up or the sentence should be cut)
  - _Boring_ — reader expected something new and got something they could have inferred (→ cut or compress)

**When the reader state is violated, that's a noticing event.** Log it. These are the problems you need to fix. Ordering problems, coherence breaks, missing context, and redundancy all show up as violations of reader state — not as properties of sentences in isolation.

### How to Notice: Section-Level Examination

Before paragraph work, read the full section once and state:

1. **What is this section's single job in the overall argument?**
2. **What can it assume the reader already knows from prior sections?**
3. **What must be true by the end of this section for the next section to work?**

## Editing Rules (apply after noticing)

These rules operate on the choices surfaced by the noticing process above.

### Sentence-level fixes

- For every preamble ("This means that...", "The result is that...", "It is important to note that...", "The key insight here is...") — delete it. Start where the content begins.
- Throat-clearing disguised as setup: "To do X, we need Y" where Y is obvious — cut.
- "Notice that X" or "Note that X" → just say X, unless genuinely drawing attention to something surprising.
- "In order to" → "to"
- "The fact that" → cut or rephrase
- "It is [adjective] that" → rephrase without the dummy subject

### Word-level fixes

- Delete every adjective and adverb. Add back only those doing load-bearing work — where the meaning materially changes without them.
- "Fundamentally" — is it distinguishing from superficially? If not, cut.
- "Essentially" — almost always cut.
- "Importantly" — cut. If it's important, the reader will see it.
- "Very", "quite", "rather", "somewhat", "fairly" — cut all.
- "Utilize" → "use". "Methodology" → "method". Prefer the plain word.
- Check every "which" clause — can it be cut or folded into the main sentence?

### Compression

- Can any sentence be half as long while saying the same thing?
- Look for two-sentence sequences that can be one sentence.
- Look for subordinate clauses that can be parentheticals or appositives.
- Can any paragraph be a single sentence?

## Style Targets

- **Precision over approximation.** Use the exact right word, not a near-synonym.
- **Concrete before abstract.** If an abstraction appears without a grounding example nearby, flag it.
- **Claim first, justification second.** State X. Then say why, if needed.
- **Signpost, don't announce.** "We now have X; the question is Y" — good. "In this section we will discuss Y" — cut.
- **Trust the reader.** Don't explain connections an intelligent reader can make from context.
- **Vary rhythm naturally.** After a long complex sentence, a short one. But don't force this.

## Output Format

- Show the edited version of the passage.
- After the edit, briefly note the major changes and reasoning.
- If a cut was a close call, flag it so the user can override.

## What NOT to Do

- Don't add new content, examples, or arguments.
- Don't restructure the macro argument (section order, what sections exist). Only tighten within the existing structure.
- Don't make it sound like a bullet-point list. It should still read as prose.
- Don't strip personality or voice. Dry wit survives. Mechanical hedging doesn't.
- Don't homogenize sentence length into all-medium.
- **Don't confuse "tight" with "short."** A long sentence with no wasted words is tight. A sequence of clipped sentences with no flow is just unpleasant. The goal is no unnecessary words, not few words. The prose should still sound like a person speaking — someone precise and unhurried, not someone with a word limit.
- **Don't cut words that help a sentence breathe.** Concrete nouns, parallel structure, and natural completions cost little and buy comprehension. Cut filler, not texture.
