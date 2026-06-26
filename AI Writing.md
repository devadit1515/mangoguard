# AI Writing Patterns — The Complete Reference

> The definitive field guide to AI-generated prose: how to **detect** it, why models **produce** it, and how to **strip it out**.
> Three jobs in one document — spot AI writing, understand the machinery underneath it, and rewrite anything to read like a human wrote it.
>
> **Primary evidence base (verified against source papers):** Kobak et al. *Science Advances* 2025 (excess-vocabulary, >15M PubMed abstracts) · Liang et al. ICML 2024 (AI-modified peer reviews) · Juzek & Ward COLING 2025 (the "delve" word list + cause analysis) · Shaib et al. 2024 (syntactic templates) · Mitchell et al. ICML 2023 (DetectGPT) · Zhang et al. 2024 (RLHF format bias) · Kirk et al. & Padmakumar & He ICLR 2024 (RLHF homogenization) · Reuters Institute / Oxford · Wikipedia "Signs of AI Writing."
> **Humanization playbook synthesized from 7 open-source skills** (conorbronsdon, blader, jalaalrd, Aboudjem, adenaufal, gregorymm, matteoroversi — see §20).
> Compiled June 2026. Every load-bearing number is sourced; folklore is flagged as folklore.

> **How to read this.** Sections 1–9 are the **detection field guide** (what AI writing looks like). Sections 10–13 are the **forensics** (the statistical and mechanical reasons it looks that way). Sections 14–18 are the **humanization protocol** — the actual rewrite procedure, graded word tiers, scoring rubric, and self-tests. Sections 19–21 are the evidence base, the skill landscape, and a cut-out cheat sheet.
>
> **The one principle under all of it:** AI writes from the *top of the abstraction ladder* with *uniform rhythm*, a *neutral stance*, *windup openings*, and *reflexive hedging*. Every fix in this document inverts one of those — descend to the concrete, break the rhythm, take a side, start inside the action, and hedge only where the evidence is genuinely thin.

---

## Table of Contents

**Part I — Detection field guide**
1. [Common AI Words](#1-common-ai-words)
2. [AI Sentence Patterns](#2-ai-sentence-patterns)
3. [AI Email Habits](#3-ai-email-habits)
4. [AI YouTube Script Habits](#4-ai-youtube-script-habits)
5. [Weak Introductions](#5-weak-introductions)
6. [Weak Conclusions](#6-weak-conclusions)
7. [Human Alternatives](#7-human-alternatives)
8. [Natural Sentence Rhythm](#8-natural-sentence-rhythm)
9. [Conversational Examples](#9-conversational-examples)

**Part II — Forensics (why it reads like a machine)**
10. [Why AI Writes This Way — the RLHF Machinery](#10-why-ai-writes-this-way--the-rlhf-machinery)
11. [Statistical Fingerprints — Perplexity & Burstiness](#11-statistical-fingerprints--perplexity--burstiness)
12. [Punctuation & Formatting Forensics](#12-punctuation--formatting-forensics)
13. [Smoking-Gun Artifacts](#13-smoking-gun-artifacts)

**Part III — The humanization protocol (how to fix it)**
14. [The Graded Word Tiers — Replace, Don't Just Ban](#14-the-graded-word-tiers--replace-dont-just-ban)
15. [The Humanization Protocol — Multi-Pass Rewrite](#15-the-humanization-protocol--multi-pass-rewrite)
16. [The Cluster Rule & False Positives](#16-the-cluster-rule--false-positives)
17. [The 0–100 AI-Tell Score](#17-the-0100-ai-tell-score)
18. [Stylometric Self-Tests](#18-stylometric-self-tests)

**Part IV — Reference**
19. [The Verified Evidence Base](#19-the-verified-evidence-base)
20. [The Humanizer-Skill Landscape](#20-the-humanizer-skill-landscape)
21. [Quick Reference Card](#21-quick-reference-card)

---

## 1. Common AI Words

The core finding from peer-reviewed research (Kobak et al., *Science Advances* 2025; Liang et al., ICML 2024; Reuters Institute / Oxford):
AI defaults to a **semi-formal, corporate-academic register** — words that feel "professional"
but land as generic. These words appear at statistically elevated rates in AI-generated text.

> **The verified numbers (cite these, not the folklore).** In Kobak et al.'s study of **>15 million PubMed abstracts**, the word **"delves" appeared ≈25× more often** in 2024 than the pre-2023 trend predicted ("showcasing" ≈9.2×, "underscores" ≈9.1×); the authors estimate **≥13.5% of 2024 abstracts were LLM-processed**. In Liang et al.'s study of conference peer reviews, **"meticulous" appeared 34.7× more often, "intricate" 11.2×, "commendable" 9.8×** in AI-modified reviews — and **16.9% of EMNLP-2023 reviews** showed substantial AI modification. The popular "delve spiked 400%" claim is a garbled retelling; the real signal is a *frequency multiplier*, and it is far larger than 400%. **Caveat:** these are corpus-level proportions — a single "delve" never convicts a single document (see §16).

---

### GPT-4 Era Words (2023–mid 2024)

```
additionally      boasts            bolstered         crucial
delve / delves    emphasizing       enduring          garner
highlight         interplay         intricate         intricacies
key               landscape*        meticulous        meticulously
pivotal           robust            tapestry*         testament
underscore        valuable          vibrant           while**
```

`* used abstractly ("the political landscape," "a rich tapestry")`
`** used as a subordinating conjunction at the start of clauses`

---

### GPT-4o Era Words (mid 2024–2025)

```
align with        bolstered         crucial           emphasizing
enhance           enduring          fostering         highlighting
pivotal           showcasing        underscore        vibrant
```

---

### Corporate / Professional Register Words

```
transformative    innovative        cutting-edge      groundbreaking
revolutionize     leverage          synergy           seamlessly
scalable          comprehensive     streamline        empower
unlock            harness           elevate           game-changer
paradigm          ecosystem         navigate          resonate
commendable       comprehend        swift             forward-thinking
```

---

### Buzzword Filler Adjectives

```
amazing           remarkable        captivating       inspiring
profound          nuanced*          dynamic           impactful
thought-provoking multifaceted      holistic          integral
quintessential    cornerstone       landmark          paramount
```

`* "nuanced" used as a vague compliment rather than a specific description`

---

### Copula-Avoidance Verbs (replacing "is" / "has")

AI avoids repeating "is" by swapping it for these — they appear in clusters:

```
serves as         stands as         marks             represents
boasts            features          maintains         offers
refers to         highlights        underscores       reflects
```

---

### Present Participial Danglers (sentence-ending -ing phrases)

These appear at the end of sentences to add commentary without a new sentence:

```
...highlighting the importance of X.
...underscoring the need for Y.
...emphasizing the role of Z.
...reflecting broader trends in W.
...symbolizing the enduring legacy of...
...contributing to the ongoing debate.
...cultivating a culture of...
...fostering collaboration across...
...encompassing a wide range of...
```

---

### The "Significance Cluster" (Wikipedia editorial guide)

Phrases AI uses to signal importance — overused to the point of meaninglessness:

```
stands as / serves as         vital/significant/crucial/pivotal role
is a testament to             underscores the importance of
reflects broader trends       symbolizing enduring legacy
contributing to               setting the stage for
marks a key turning point     evolving landscape
indelible mark                deeply rooted
represents a shift            key moment in
```

---

### Promotional Language Cluster

```
boasts a           vibrant            rich               profound
enhancing          showcasing         exemplifies        commitment to
nestled            in the heart of    groundbreaking     renowned
featuring          diverse array      gateway to         seamlessly connecting
dependable         value-driven
```

---

## 2. AI Sentence Patterns

---

### Nominalization — Noun-Heavy Prose

**The single most reliable structural fingerprint.** (PNAS 2025 — HIGH confidence)
Instruction-tuned models use nominalizations at **1.5–2× human rates**.

| Human | AI |
|-------|----|
| "We studied how people learn" | "An investigation into the mechanisms of human learning acquisition" |
| "Companies are competing harder" | "The intensification of competitive dynamics across industries" |
| "He improved quickly" | "His improvement demonstrated significant acceleration" |
| "We decided to change it" | "A decision was made to implement modifications" |

---

### Negative Parallelism for Drama

Used across LinkedIn posts, marketing copy, YouTube scripts — wherever AI is prompted to "sound compelling."
(Washington Post 328,744-message dataset — MEDIUM confidence)

```
It's not just X. It's Y.
This isn't about A. It's about B.
Not just a tool. A transformation.
No shortcuts. No excuses. Just results.
Not only [X], but also [Y].
It's not X, it's Y — and that distinction matters.
X rather than Y.
```

---

### The Rule of Three (Mechanical Triplets)

AI defaults to grouping things in threes — three adjectives, three bullet points, three examples:

```
"This is innovative, scalable, and impactful."
"We need to educate, inspire, and transform."
"The solution is fast, reliable, and cost-effective."
"Communication, collaboration, and strategic thinking."
```

Real human writing uses two things, or four things, or one thing really well.

---

### Mechanical Transition Words

AI opens paragraphs and sentences with the same transitions in predictable rotation:

```
Moreover, ...
Furthermore, ...
Additionally, ...
In conclusion, ...
To summarize, ...
It is worth noting that ...
It is important to understand that ...
Ultimately, ...
At its core, ...
Notably, ...
Importantly, ...
In essence, ...
At the end of the day, ...
```

---

### Symmetric / Balanced Structures

- Every paragraph is the same length
- Pros and cons lists with exactly matching items on each side
- Bullet points that are all roughly the same word count
- Every section ends with a summary sentence

---

### Passive Voice Overuse

```
It is believed that...
The data was analyzed...
It has been found that...
Research has shown that...
It can be argued that...
It is widely accepted that...
It should be noted that...
```

---

### Vague Attribution (No Named Source)

```
Experts say...
Studies show...
Research suggests...
Observers have cited...
Critics argue...
Industry reports indicate...
Some have said...
Many believe...
It is generally understood that...
```

---

### Emphasis Through Restatement

AI restates the same idea with slightly different words instead of adding new information:

```
"This is crucial. In fact, it's one of the most important factors to consider.
The significance of this cannot be overstated."
```

Three sentences. One idea. No new information added.

---

### The "Despite" Pivot (Wikipedia editorial guide)

Nearly every AI article or section ends with this structure:

```
Despite [challenge], [subject] continues to [progress/thrive/evolve].
Despite its [limitations], the potential of X remains [clear/vast/promising].
Despite these obstacles, X faces an exciting future.
```

---

## 3. AI Email Habits

---

### Opening Lines — Dead Giveaways

```
I hope this message finds you well.
I hope this email finds you in good health and high spirits.
I hope you're doing well.
Dear Sir or Madam,
I wanted to reach out to...
I am writing to...
I trust this email finds you well.
I hope you had a great weekend.
```

**"Don't hesitate to reach out" appears 287% more often in AI-generated emails than human ones.**
(Digital Journal — ZeroBounce study)

---

### Body Transition Phrases

```
Moreover, ...
Furthermore, ...
Additionally, ...
It is worth noting that...
Please note that...
As mentioned previously, ...
In this regard, ...
With that in mind, ...
As per our discussion, ...
Following up on my previous email, ...
```

---

### Closing Lines — Formulaic Sign-Offs

```
Please don't hesitate to reach out.
Kindly let me know.
I look forward to hearing from you.
Thank you for your time and consideration.
Feel free to contact me if you have any questions.
I hope this helps!
I hope this provides some clarity.
Let me know if you need any modifications.
I remain at your disposal.
```

---

### Corporate Jargon Clusters in Emails

Words AI learned are "professional" from millions of corporate emails and LinkedIn posts:

```
leverage          bandwidth         circle back       touch base
reach out         synergize         align             action items
going forward     loop you in       move the needle   at this time
per my last email please find attached  as per our conversation
deep dive         take this offline  in terms of      going forward
```

---

### Structural Email Tells

- Perfectly structured paragraphs with no personal asides or humor
- Overly formal tone regardless of actual relationship
- No contractions ("do not" instead of "don't")
- No casual language or register shifts
- No specific references to prior conversation details
- Bullet points where a single sentence would be more natural
- Generic closings that fit any situation
- Vague, non-specific content despite smooth language

---

## 4. AI YouTube Script Habits

---

### Hook Patterns (Overused)

```
Have you ever wondered why...?
What if I told you that...?
In today's video, I'm going to show you exactly how to...
By the end of this video, you'll know exactly how to...
Most people don't know this, but...
Here's something that will completely change how you think about...
The #1 mistake people make when...
What separates the top 1% from everyone else is...
```

---

### Script Body Transitions

AI writes scripts for reading, not listening. It uses:

```
Now that we've covered X, let's move on to Y.
Let's start by talking about...
It's worth noting that...
It's important to understand that...
Furthermore, ...
As we've established, ...
With that said, let's dive into...
```

Nobody says "Furthermore" out loud in a YouTube video. These betray a script not rewritten for speech.

---

### Structural Pattern (Default AI Script Architecture)

```
1. Hook (question or bold claim)
2. "In today's video, I'm going to cover [X, Y, and Z]."
3. Point 1 → explanation → example
4. Point 2 → explanation → example
5. Point 3 → explanation → example
6. "So, as we've seen today, [recap of X, Y, and Z]."
7. "If you found this valuable, like and subscribe!"
```

Every section the same length. Every transition explicit. No tangents. No personality.

---

### Call-to-Action Patterns

```
Don't forget to like, comment, and subscribe!
Hit that subscribe button and ring the notification bell!
Drop a comment below and let me know what you think!
If you found this valuable, share it with someone who needs it!
Make sure to check out my other video on [topic]!
See you in the next one!
```

---

### What AI Scripts Miss

- Natural speaking rhythm (short bursts, restarts, emphasis words)
- Personal stories with specific, embarrassing, or vulnerable details
- Tangents that humanize the speaker
- Casual asides ("this is going to sound weird, but...")
- Actual opinions that could get pushback
- Humor that isn't formatted as a joke
- Silence cues or pacing notes

---

## 5. Weak Introductions

---

### The "World" Opener (Most Common AI Tell)

(Practitioner consensus — MEDIUM confidence; pre-dates LLMs but AI amplified it enormously)

```
In today's fast-paced world, ...
In a world where ...
In today's rapidly evolving landscape, ...
In an era characterized by ...
In the digital age, ...
As we navigate an increasingly complex world, ...
In today's competitive landscape, ...
As technology continues to advance, ...
In recent years, X has become increasingly crucial.
In the age of artificial intelligence, ...
```

---

### The Hollow Question Opener

```
Have you ever asked yourself...?
What does it really mean to...?
Why is it that so many people struggle with...?
What if there was a better way to...?
```

These ask questions no specific person has actually asked.

---

### The Significance Declaration

```
X has never been more important than it is today.
The importance of X cannot be overstated.
X is at the forefront of modern discourse.
X plays a vital role in today's world.
Now more than ever, X matters.
```

---

### The Definition Opener

```
According to Merriam-Webster, X is defined as "..."
X, by definition, refers to...
At its core, X is the process of...
Webster's dictionary defines X as...
```

---

### The Announcement Opener

```
In this article/guide/blog post, we will explore...
Today, we're going to dive deep into...
This comprehensive guide will cover everything you need to know about...
Welcome to our in-depth exploration of...
In this post, I'll walk you through...
```

---

## 6. Weak Conclusions

---

### The Summary Recap

```
In conclusion, we have explored...
To summarize the key points covered in this article...
As we've seen throughout this piece...
In summary, X is important because A, B, and C.
We hope this article has provided valuable insights into...
```

---

### The Bright Future Closer

```
The future of X looks bright.
X holds great promise for the future.
As we look to the future, it's clear that...
The possibilities are endless.
X is only going to grow in importance.
```

Section headers that signal this: "Challenges and Future Directions," "Future Outlook," "Future Prospects"

---

### The Call-to-Action Motivational Finish

```
Take the first step today!
Don't wait — the time to act is now.
Start your journey toward X today.
The journey of a thousand miles begins with a single step.
Remember, the only limit is yourself.
The world needs your unique perspective.
Together, we can make a difference.
Keep pushing forward.
```

---

### The Vague Encouragement Sign-Off

```
I hope this was helpful!
I hope this gives you some ideas.
I hope this provides clarity.
Let me know if you have any questions!
Feel free to reach out!
Thank you for reading!
```

---

### The "Despite" Conclusion

```
Despite the challenges, X continues to evolve.
Despite these limitations, the potential is clear.
Despite its obstacles, X represents a compelling vision.
While challenges remain, the future looks promising.
```

---

## 7. Human Alternatives

The goal is not to avoid these patterns mechanically — it's to replace **generic** with **specific**.
AI fails at specificity because it has no actual experience. You do.

---

### Replace "World" Openers → Specific Scene or Situation

| AI | Human |
|----|-------|
| "In today's fast-paced world, burnout is a serious issue." | "I missed my kid's school play because I was answering Slack messages. That was the moment I started paying attention to burnout." |
| "In today's competitive landscape, standing out matters." | "My last three cold emails got a 0% reply rate. Here's what I changed on email #4." |
| "In today's digital age, attention spans are shrinking." | "I read the same paragraph four times yesterday. My phone was face-down." |

---

### Replace Abstract Declarations → Concrete Detail

| AI | Human |
|----|-------|
| "AI is transforming healthcare in profound ways." | "A radiologist in Cleveland reduced false positives by 30% using an AI diagnostic tool." |
| "Remote work has changed everything." | "My team went from four people sharing an office to twelve people across eight time zones. The Tuesday standup is now three separate meetings." |

---

### Replace Transition Words → Cut or Restructure

| AI | Human |
|----|-------|
| "Furthermore, this approach saves time." | "This approach also saves time." (or start a new sentence) |
| "Moreover, the data supports this conclusion." | "The data backs this up." |
| "Additionally, we found that..." | "We also found that..." |
| "In conclusion, X matters." | Just say why it matters. No announcement. |

---

### Replace Passive Voice → Active and Specific

| AI | Human |
|----|-------|
| "It has been found that exercise improves mood." | "Exercise improves mood. The research on this is consistent." |
| "It is believed that..." | "I think..." / "Research from Stanford found that..." |
| "The data was analyzed to determine..." | "We looked at the data to figure out..." |

---

### Replace Vague Attribution → Named Source or Your Own View

| AI | Human |
|----|-------|
| "Experts say X is important." | "Dr. Andrew Huberman's research shows..." / "Every manager I've worked with says the same thing." |
| "Studies show that habits are hard to break." | "Wendy Wood's research at USC found that 43% of daily actions are habits, not decisions." |
| "Many believe this approach is effective." | "I've tried this twice. It worked once." |

---

### Replace Formulaic Closings → Natural Exit

| AI | Human |
|----|-------|
| "In conclusion, X is a vital component of modern life." | Leave the reader with one thing they can do before tomorrow. |
| "I hope this was helpful! Let me know if you have questions." | "The one thing I'd try first: [specific action]. Let me know if it works." |
| "The future looks bright for X." | "I don't know what's coming. But I know what I'm doing this month." |

---

### Replace -ing Dangler Endings → Complete Sentences

| AI | Human |
|----|-------|
| "The company pivoted, highlighting the growing importance of ESG." | "The company pivoted. ESG pressure was the reason." |
| "The policy changed, reflecting broader societal trends." | "The policy changed. Society changed first." |
| "He quit, underscoring the challenges of remote leadership." | "He quit. Managing people over video calls had worn him down." |

---

## 8. Natural Sentence Rhythm

---

### What AI Gets Wrong About Rhythm

AI produces:
- **Uniform sentence length** — every sentence is medium-length
- **No burstiness** — sentences are equally predictable throughout
- **Explicit transitions at every paragraph start** — no abrupt jumps
- **No fragments, no mid-paragraph questions, no one-word sentences**
- **Consistent register** — stays formal or stays casual, never shifts

Human writing has **burstiness** — it alternates between short punchy sentences and long winding explanatory ones, the way actual speech does.

---

### Patterns That Sound Human

**Short. Then long.**
A single punchy claim, followed by the explanation that earns it.

**Fragments for emphasis.**
Not always a full sentence. Intentional. Effective.

**Question mid-paragraph?**
Yes. Humans do this constantly. AI almost never does.

**Contractions.**
"Don't" not "do not." "It's" not "it is." "You'll" not "you will."
Contractions appear constantly in human informal writing and rarely in AI output.

**Abrupt paragraph endings.**
Human writers end sections bluntly and move on. AI adds a transitional summary sentence.

**Register shifts within a single piece.**
Human writers go from formal to casual to vulnerable within one article.
AI maintains a uniform register throughout.

**Personal interjections.**
"Honestly," / "Look," / "I'll be direct:" / "Here's the thing —"
AI rarely opens with these because they aren't "professional."

**Imperfect grammar used deliberately.**
Starting sentences with "And" or "But." Sentence fragments. Run-ons that work.

---

### The Burstiness Test

Real human text has high **burstiness** — some sentences are completely predictable from context;
others surprise you. AI text has low burstiness — each sentence is about as predictable as the last,
because the model always picks the most probable next token.

**Ask yourself:** Does this paragraph have any sentence that feels surprising? Any word choice that's weird?
Any structure that breaks the pattern? If every sentence feels inevitable — it's probably AI.

---

### Rhythm Comparison

**AI rhythm (flat):**
> "Effective communication is essential in any professional environment. It enables teams to collaborate more efficiently and ensures that everyone is aligned on goals and expectations. Moreover, strong communication skills can help prevent misunderstandings and build trust among team members."

**Human rhythm (varied):**
> "Bad communication doesn't announce itself. It shows up as a 47-reply email thread about a decision someone made in a five-minute hallway conversation — that nobody wrote down. Three departments working at cross-purposes. Not because people are bad at their jobs. Because nobody said the thing out loud."

---

## 9. Conversational Examples

Side-by-side comparisons across every major format.

---

### LinkedIn Post

**AI version:**
> I'm thrilled to share that I've just completed a transformative leadership program.
> The experience was truly profound, enhancing my skills in communication, collaboration,
> and strategic thinking. I'm grateful for the opportunity to grow alongside such incredible
> peers and mentors. What leadership lessons have resonated with you? 🚀

**Human version:**
> Six months ago my manager told me I was terrible at giving feedback.
> She was right.
> I just finished a leadership program specifically because of that conversation.
> I'm better at it now. Not great. Better.
> That's the update.

---

### Email Opening

**AI version:**
> I hope this message finds you well. I am writing to reach out regarding a potential
> collaboration that I believe could be mutually beneficial for both of our organizations.
> Please don't hesitate to reach out with any questions or concerns you may have.

**Human version:**
> Quick question — are you taking on new partnerships this quarter?
> I have a specific idea that might be worth 15 minutes.

---

### Blog Introduction

**AI version:**
> In today's fast-paced digital landscape, content creation has become more important than ever.
> As brands navigate an increasingly competitive environment, the ability to produce high-quality,
> engaging content is crucial to staying relevant and resonating with target audiences.

**Human version:**
> I wrote 47 blog posts last year. Three of them drove 90% of the traffic.
> Here's what those three had in common.

---

### YouTube Script Hook

**AI version:**
> Have you ever wondered why some people seem to achieve massive success while others
> struggle to make progress despite their best efforts? In today's video, we're going to
> explore the three key habits that separate high performers from the rest.

**Human version:**
> I tracked my time for 30 days. What I found was embarrassing. Let me show you.

---

### Blog Conclusion

**AI version:**
> In conclusion, building good habits is a multifaceted endeavor that requires consistency,
> patience, and self-awareness. By implementing these strategies, you can create lasting change
> and achieve your goals. The journey begins today — take the first step!

**Human version:**
> The single thing that changed my morning routine wasn't a system.
> It was telling my wife what I was trying to do.
> Accountability beat discipline every time.

---

### Cold Email (Sales)

**AI version:**
> I hope this message finds you well. I wanted to reach out to introduce our innovative
> solution that has been helping companies like yours streamline their workflows and
> leverage cutting-edge technology to drive transformative results. Would you be open
> to a brief call to explore how we could add value?

**Human version:**
> I looked at your LinkedIn — you're hiring three ops managers right now.
> We help ops teams stop using spreadsheets for scheduling.
> Worth a 20-minute call? I have Thursday at 2pm or Friday at 10am.

---

### Twitter / X Post

**AI version:**
> In today's rapidly evolving landscape, the ability to adapt is no longer optional —
> it's essential. Embrace change, invest in continuous learning, and position yourself
> for long-term success. The future belongs to those who prepare for it today. 💡

**Human version:**
> I got laid off in March.
> Found a better job in April.
> The month in between was the most I'd learned in years.
> Turns out having nothing to protect makes you move faster.

---

## 10. Why AI Writes This Way — the RLHF Machinery

Every tell in Part I has the same root cause, and it is not the pre-training data. It is **RLHF** (Reinforcement Learning from Human Feedback) — the preference-tuning step that turns a raw text predictor into a "helpful assistant." The base model writes far more like a human; the *aligned* model is what produces slop. Three measured effects explain almost everything above.

### 10.1 Format bias — the bold-bulleted "house style" is literally rewarded

Reward models (the scorers RLHF optimizes against) prefer formatted answers regardless of content quality. Zhang et al. (2024, arXiv:2409.11704) measured the win-rates a GPT-4 judge gives to formatting alone:

| Format feature | Win-rate the reward model gives it |
|---|---|
| **Bold text** | **89.5%** |
| Hyperlinks | 87.25% |
| Emojis | 86.75% |
| Exclamation marks | 80.5% |
| Bulleted lists | 75.75% |

And it is shockingly easy to install: **0.7% biased training data flips a model's preference** — lists from 51% → 77.5%, bold from 57.5% → 88%. *This is the direct mechanistic source* of the title-case bold mini-headers, the everything-in-bullets layout, and the emoji-in-headings habit. The model isn't organizing your ideas; it's chasing a reward signal that pays out for formatting.

### 10.2 Mode collapse — why every model sounds like the same model

- RLHF **"significantly reduces output diversity compared to supervised fine-tuning"** (Kirk et al., ICLR 2024, arXiv:2310.06452), measured across embedding-distance and entailment metrics.
- Co-writing with a preference-tuned model (**InstructGPT**) collapses lexical and content diversity; the **base GPT-3 does not** (Padmakumar & He, ICLR 2024, arXiv:2309.05196). That isolates *preference tuning*, not scale, as the homogenizer.
- Instruction tuning **sharpens the next-token distribution / lowers entropy** (arXiv:2501.14315). PPO's reverse-KL objective is mode-seeking — it chases the single highest-reward "voice" and abandons the long tail. The result is **low perplexity** (the model always reaches for the most probable word) and the eerie sense that all AI text was written by one slightly-corporate ghost.

### 10.3 Length bias & sycophancy — verbosity and people-pleasing as policy

- Reward models reward length: longer ≈ "more thorough" ≈ higher score, so models inflate (arXiv:2511.12573). This is the "treadmill effect" — paragraphs you can cut 40–60% with zero information loss (§18).
- RLHF induces **sycophancy** as a general behavior (Sharma et al., Anthropic, ICLR 2024, arXiv:2310.13548): "Great question!", "You're absolutely right!", reflexive agreement, the hedge-everything register. The assistant is optimized to be *liked*, and liked-ness correlates with deference and padding.

### 10.4 The lexical shift — measured *that*, unresolved *why*

The vocabulary spike (delve, underscore, intricate) is real and quantified (§1, §19). The *cause* is partly settled, partly not. RLHF narrowing vocabulary is **measured**; the specific "delve" origin is not. The widely-repeated theory that low-paid African-English RLHF annotators biased the reward toward "delve" is **empirically rejected** — Juzek & Ward (COLING 2025) tested it against the International Corpus of English and found *no* evidence the focal words are more common in any English variety. **Cite the dialect story as debunked; cite RLHF-in-general as the leading, still-open explanation.**

> **The practical upshot.** You cannot fix slop by swapping words alone, because the cause is structural — a reward model that pays for formatting, length, deference, and the single most-probable phrasing. That is exactly why the humanization protocol in Part III is a *process* (draft → cut → break symmetry → roughen → read aloud), not a find-and-replace.

---

## 11. Statistical Fingerprints — Perplexity & Burstiness

Detectors (GPTZero, DetectGPT, and the rest) mostly run on two numbers. Understanding them tells you *why* the rhythm advice in §8 actually works.

### 11.1 The two axes

- **Perplexity** = how *surprising* each word is given the ones before it, formally `exp(−(1/N) Σ log p(xᵢ | x_<ᵢ))`. AI picks high-probability tokens, so AI text is **low-perplexity** (predictable). Human word choice is lumpier and weirder → **high-perplexity**.
- **Burstiness** = how much that predictability (and sentence length) *varies* across the document. Humans write a 4-word sentence next to a 40-word one; AI clusters everything near the mean → **low burstiness**.

**Humans score high on both axes; AI scores low on both.** Almost every humanization move is, mechanically, a way to *raise perplexity* (pick the second or third word that comes to mind, not the first) or *raise burstiness* (vary sentence length and shape).

### 11.2 What the detector studies actually found

| Method | Finding | Source |
|---|---|---|
| **GPTZero** | Classifies on perplexity + burstiness. Failure mode: famously flagged the **US Constitution as AI** — regular, well-edited human text is *also* low-burstiness. | gptzero.me |
| **DetectGPT** (curvature) | Perturb the text and watch the log-prob: AI text sits in negative-curvature regions and drops; human text doesn't. **AUROC 0.95 vs 0.81** baseline (GPT-NeoX-20B). | Mitchell et al., ICML 2023, arXiv:2301.11305 |
| **Fast-DetectGPT** | Same idea, **~340× faster**, black-box ChatGPT/GPT-4 detection 0.93 AUROC. | Bao et al., ICLR 2024, arXiv:2310.05130 |
| **Sentence-length variance** | Human length distributions are "broader and flatter"; AI clusters near the mean. A classifier hit **93% on human texts vs 75% on AI** (AI is *harder* to catch — it hides in uniformity). | Rodrigues et al., *iScience* 2026 |

### 11.3 The numbers — trust the direction, not the decimals

Humanizer vendors quote **burstiness ≈ 0.6–0.85 for human** writing vs **≈ 0.18–0.40 for AI**, and note AI sentences cluster at **15–20 words**. These specific cutoffs come from tools with skin in the game — *treat them as indicative*. The peer-reviewed, durable claim is directional: **AI text has lower perplexity, lower burstiness, and lower sentence-length variance than human text.** Two consequences worth internalizing:

1. **Lexical word-lists decay; statistics don't.** Once "delve" and "intricate" were publicized, their frequency *dropped* while other markers rose (Geng & Trotta 2025). But perplexity/burstiness/curvature are properties of *how the model samples*, not of any word, so they degrade much more slowly.
2. **Low burstiness false-positives careful human writing.** Tight, edited, uniform prose (legal text, the US Constitution) reads as "AI" to these tools. This is why §16's cluster rule matters: never convict on a single axis.

---

## 12. Punctuation & Formatting Forensics

The single most consistent finding across all 7 humanizer skills (§20): punctuation and layout betray AI faster than vocabulary.

### 12.1 The em-dash — "the ChatGPT dash"

Every one of the 7 skills treats the em-dash (—) as the **#1 punctuation fingerprint**. GPT-4o uses it roughly **10× more than GPT-3.5** (Goedecke 2025), and OpenAI publicly acknowledged the problem — Sam Altman said (Nov 2025) that GPT-5.1 finally honors "no em-dashes" instructions.

- **Consensus limit:** target **zero**; hard maximum **one per 1,000 words** (conorbronsdon) or **one per 500 words** (jalaalrd).
- **Catch both forms:** the Unicode em-dash (—) *and* the double-hyphen (`--`). Also flag en-dashes (–) and curly/smart quotes (" " ' ') in plain-text contexts.
- **Replace in this order:** period → comma → colon → parentheses → restructure the sentence.

> **Honest caveat:** no matched-corpus study proves chatbots out-dash humans *in equivalent contexts* (a *Washington Post* point). The em-dash is a strong *prior*, not proof — which is, again, why §16 says cluster, don't convict.

### 12.2 The colon-vs-period tell (the sharpest single forensic)

A subtle, high-precision marker: **LLMs end bold list-labels with a period; humans use a colon.**

```
AI:    **Introductions.** Open on the specific claim.
Human: **Introductions:** open on the specific claim.
```

The fix is one character — change the period after a bold lead-in to a colon and lowercase what follows. It is one of the few tells that is nearly *unique* to machine output.

### 12.3 Formatting discipline

| AI tell | The fix |
|---|---|
| **Bold everywhere** (multiple bold phrases per paragraph) | Max **one** bold phrase per major section, or none. Reward-model habit (§10.1), not emphasis. |
| **Title Case Mini-Headers** | Use sentence case. Title Case On Every Heading is a machine signature. |
| `**Bold label:** explanation` bullet lists, 5+ in a row | Convert to prose. The tell is the *symmetry* — bare noun-phrases, each ≤6 words, no verb. |
| Emoji in headings / as bullets (🚀 ✅ 💡) | Delete. |
| `>3 headings in <300 words` / `>8 bullets in <200 words` | It's AI trying to *look* organized. Collapse into paragraphs. |
| Excess exclamation marks | Max one per ~1,000 words. |

---

## 13. Smoking-Gun Artifacts

Not stylistic tells — **forensic proof**. When these survive into published text, the content was pasted from a chatbot and never read:

```
citeturn0search0          ← ChatGPT web-search citation markup
oai_citation:…             ← OpenAI citation token
:contentReference[...]      ← leaked reference placeholder
utm_source=chatgpt.com      ← UTM parameter on a pasted link
【...】 / corrupted brackets  ← tool-call rendering artifacts
[Your Name] / [INSERT X]    ← unfilled template placeholders
"As an AI language model…"  ← the original confession
"As of my last update…"     ← knowledge-cutoff disclaimer
"I hope this helps! Let me   ← sycophancy residue left in a published doc
 know if you need anything"
```

Plus **fabricated-citation markers** — plausible-looking references with DOIs that don't resolve, page numbers that don't exist, or authors who never co-published. If a quote is too clean and the source can't be found, treat it as a hallucination until proven otherwise.

---

## 14. The Graded Word Tiers — Replace, Don't Just Ban

A flat blacklist is a blunt instrument — it false-positives real human writing (lawyers *do* say "robust," engineers *do* say "comprehensive"). The strongest skills (conorbronsdon/avoid-ai-writing) grade words by how damning they are. Use this three-tier system instead of a single list.

### Tier 1 — Always replace (near-zero legitimate use)

| AI word | Replace with |
|---|---|
| delve / delve into | explore, dig into, look at |
| tapestry (metaphor) | *(describe the actual complexity)* |
| landscape (metaphor) | field, space, area |
| realm | area, world |
| testament to | shows, proves |
| underscores | highlights, shows |
| showcasing | showing |
| leverage (verb) | use |
| utilize | use |
| robust | strong |
| comprehensive | thorough, full |
| meticulous | careful |
| seamless / seamlessly | smooth(ly) |
| cutting-edge | latest |
| pivotal | key, central |
| intricate | complex, detailed |
| boasts | has |
| nestled | sits, is |
| serves as | is |
| commence / embark | start |
| deep dive | examine |

### Tier 2 — Flag when 2+ appear in one paragraph (legitimate alone, AI in clusters)

`harness · navigate (figurative) · foster · elevate · unleash · streamline · empower · bolster · spearhead · resonate · revolutionize · facilitate · underpin · nuanced · crucial · multifaceted · ecosystem · myriad · plethora · encompass · catalyze · cultivate · illuminate · elucidate · cornerstone · paramount · poised · burgeoning · nascent · quintessential · overarching`

### Tier 3 — Flag only at high density (usually fine; suspicious in bulk)

`significant · innovative · effective · dynamic · scalable · compelling · unprecedented · exceptional · remarkable · sophisticated · instrumental · state-of-the-art · world-class · best-in-class`

### Filler swaps (cut wordcount 15–20%)

| AI | Human |
|---|---|
| In order to achieve this goal | To do this |
| Due to the fact that | Because |
| At this point in time | Now |
| has the ability to | can |
| It is important to note that | *(delete — just say it)* |
| A wide range of | many, *(or the actual number)* |
| In the realm of | in |

---

## 15. The Humanization Protocol — Multi-Pass Rewrite

The best skills don't find-and-replace; they run a **draft → revise loop**. This synthesizes matteoroversi/anti-ai-rhetoric (4-pass) and adenaufal/anti-slop-writing (post-gen checklist). Run it in order.

**Pass 0 — Draft.** Write freely, no rules. Rules during drafting produce stiff prose; fix it after.

**Pass 1 — Cut filler.** Remove every word that can go without changing the meaning. **Target a 15–20% word-count reduction.** Kill Tier-1 words (§14), hedges ("it's important to note"), and deletable transitions ("Furthermore," "Moreover").

**Pass 2 — Break symmetry.** Find every parallel scaffold — anaphora (repeated sentence openings), numbered lists doing a paragraph's job, within-sentence triplets (the rule of three), two-beat aphoristic closers — and **break at least one**. Use 2 items, or 4, where you had 3. Vary sentence length so no 3+ consecutive sentences match (§11). Vary sentence *openings* (§8).

**Pass 3 — Add a rough edge.** Insert at least one move that proves a human is thinking:
- a parenthetical that complicates the point (not just restates it),
- an example that doesn't perfectly fit — and you *say* it doesn't,
- a question you don't answer,
- a specific admission of uncertainty tied to a real limit,
- a self-interruption or a personal stake.

**Pass 4 — Read it aloud.** Six checks: (1) count repeated sentence openings; (2) find announced transitions ("Let's dive in") and delete them — *do* the thing, don't announce it; (3) count within-sentence triplets; (4) is the length distribution varied? (5) kill aphoristic closers ("X is the Y of Z"); (6) overall — does it sound like a person, or a press release? If you'd cringe saying it to a colleague over coffee, rewrite it.

> **The acceptance test (Aboudjem):** *"If the reader cannot picture a specific person behind it, it is not done."*

---

## 16. The Cluster Rule & False Positives

**The most important rule in this entire document — and the one that separates a useful audit from a witch-hunt:**

> **Flag clusters of tells, not isolated instances.** One em-dash, one "robust," one tricolon is *not* AI. A paragraph with an em-dash *and* a rule-of-three *and* uniform sentence length *and* a "delve" — that's AI.

A single marker has a high false-positive rate (recall §11.2: GPTZero flagged the US Constitution). Density is the signal. Both of the most sophisticated skills (blader/humanizer, conorbronsdon) ship an explicit **false-positives list** — do **not** flag these as AI:

- Perfect grammar and spelling (good human writers exist).
- Formal vocabulary *in formal contexts* (a legal brief saying "aforementioned").
- A single transition word, or one lone curly quote.
- Domain terms of art ("robust" in statistics, "comprehensive" in insurance).
- Em-dashes in the work of writers who always used them (they predate ChatGPT by centuries).

And a **signs-of-*human*-writing preserve list** — protect these, they're hard to fabricate:
- Concrete, checkable specifics (a name, a date, a real number, a brand).
- Unresolved tension or an argument that doesn't fully close.
- Era-bound slang, self-corrections, a genuine personal stake.
- An opinion that could actually get pushback.

---

## 17. The 0–100 AI-Tell Score

For auditing at scale (from Aboudjem/humanizer-skill). Score a passage on tell *density*:

| Score | Band | Meaning |
|---|---|---|
| **0–20** | Pristine | Reads fully human; ship it. |
| **21–40** | Mostly human | A stray tell or two; light edit. |
| **41–60** | Mixed | Real slop density; run the Part III protocol. |
| **61–80** | AI-leaning | Obvious machine voice; rewrite, don't patch. |
| **81–100** | Pure AI | Bulleted, bolded, em-dashed, hedged throughout. |

**Cheap scoring heuristic:** +8 per Tier-1 word, +5 per em-dash, +10 per "It's not X, it's Y", +6 per rule-of-three, +5 per "Furthermore/Moreover" opener, +10 per hedge cluster, +15 per smoking-gun artifact (§13), +8 if 3+ consecutive sentences are the same length. Sum, cap at 100. Anything over ~40 needs the protocol.

A complementary 7-category version (gregorymm/humanize-text) scores 1–10 on: AI vocabulary, content inflation, grammar patterns (copula avoidance), structural tells, punctuation, meta-content (disclaimers/sycophancy), and — for product copy — UX quality. Target **85%+ "human."**

---

## 18. Stylometric Self-Tests

Five fast tests that need no tools, drawn from the strongest skills. If a passage fails two or more, it's machine-written.

1. **The treadmill test.** Can you cut 40–60% of the passage and lose *no* information? AI pads; humans are denser. (Length bias, §10.3.)
2. **The paragraph-reshuffle test.** Swap two adjacent paragraphs. If the piece still "works," you wrote a *list*, not an *argument* — a hallmark of AI's additive, non-cumulative structure.
3. **The type-token ratio (TTR).** Unique words ÷ total words over a ~200-word window. **Human ≈ 0.50–0.65; AI often < 0.40** (it recycles its own vocabulary). Low TTR = repetitive = machine.
4. **The read-aloud test.** Out of breath = a sentence is too long. Droning monotone = sentences are too uniform (§8's Gary Provost problem). The ear catches low burstiness faster than the eye.
5. **The "picture the writer" test.** After reading, can you describe one specific human who wrote this — their stake, their opinion, their voice? If it could have been written by anyone about anything, it's AI.

---

## 19. The Verified Evidence Base

All sources, with the *corrected* attributions and numbers. Confidence: **[P]** peer-reviewed · **[S]** secondary/journalism · **[B]** practitioner. Tags: **[MEASURED]** quantified in a primary source · **[CONTESTED]** empirically disputed.

### 19.1 Lexical evidence (the word-frequency studies)

| Source | Conf. | Verified finding |
|---|---|---|
| [Kobak et al., *Science Advances* 2025 — arXiv:2406.07016](https://arxiv.org/abs/2406.07016) | [P] | **[MEASURED]** >15M PubMed abstracts. "delves" ≈**25.2×**, "showcasing" ≈9.2×, "underscores" ≈9.1× vs pre-2023 trend. **≥13.5% of 2024 abstracts LLM-processed.** *This is the real "delve" number — not "400%."* |
| [Liang et al., ICML 2024 — arXiv:2403.07183](https://arxiv.org/abs/2403.07183) | [P] | **[MEASURED]** AI-modified peer reviews: "meticulous" **34.7×**, "intricate" 11.2×, "commendable" 9.8×. **16.9% of EMNLP-2023 reviews** AI-modified (vs ~1.6% pre-ChatGPT). Nature journals: no significant rise. |
| [Juzek & Ward, COLING 2025 — arXiv:2412.11385](https://arxiv.org/abs/2412.11385) | [P] | **[MEASURED]** 21 focal words (delve, intricate, underscore, boasts, meticulous, realm…). **[CONTESTED]** Directly tested and **rejected** the "African-English RLHF annotator" origin theory — no dialect prevalence found. |
| [Reuters Institute / Oxford (Adami 2025)](https://reutersinstitute.politics.ox.ac.uk/news/how-ai-generated-prose-diverges-human-writing-and-why-it-matters) | [S] | Consumer-facing marker list: delve, resonate, navigate, commendable, comprehend, boast, swift, meticulous, nuanced. |
| [Geng & Trotta 2024/2025 — arXiv:2404.08627](https://arxiv.org/abs/2404.08627) | [P] | **[MEASURED]** ~35% of CS arXiv abstracts show LLM style. **Markers decay once publicized** — "delve" frequency *fell* after exposure while other tells rose. |

### 19.2 Structural & statistical evidence

| Source | Conf. | Verified finding |
|---|---|---|
| [Shaib et al. 2024 — arXiv:2407.00211](https://arxiv.org/abs/2407.00211) | [P] | **[MEASURED]** **~95% of AI summaries contain syntactic templates vs ~38% human**; 76% of those templates trace to pretraining. The hard number behind "rule of three." |
| [Mitchell et al., DetectGPT, ICML 2023 — arXiv:2301.11305](https://arxiv.org/abs/2301.11305) | [P] | **[MEASURED]** Curvature detection **AUROC 0.95 vs 0.81** baseline (GPT-NeoX-20B). |
| [Bao et al., Fast-DetectGPT, ICLR 2024 — arXiv:2310.05130](https://arxiv.org/abs/2310.05130) | [P] | **[MEASURED]** Black-box ChatGPT/GPT-4 detection 0.93 AUROC, **~340× faster**. |
| [Biber-style register analysis — arXiv:2410.16107](https://arxiv.org/abs/2410.16107) | [P] | **[MEASURED]** Instruction tuning → noun-heavy, informationally dense style; nominalization at **1.5–2× human rate**. |
| [Linguistic-characteristics survey — arXiv:2510.05136](https://arxiv.org/abs/2510.05136) | [P] | Five-dimension feature space: surface stats, lexical diversity, syntax, readability, discourse. |
| [GPTZero — perplexity & burstiness](https://gptzero.me/news/perplexity-and-burstiness-what-is-it/) | [S] | Detector mechanics; the canonical "flagged the US Constitution" false-positive. |

### 19.3 Mechanism evidence (why RLHF does it)

| Source | Conf. | Verified finding |
|---|---|---|
| [Zhang et al. 2024 — arXiv:2409.11704](https://arxiv.org/abs/2409.11704) | [P] | **[MEASURED]** Reward-model format win-rates: **bold 89.5%**, emoji 86.75%, lists 75.75%. **0.7% biased data flips bold 57.5%→88%.** |
| [Kirk et al., ICLR 2024 — arXiv:2310.06452](https://arxiv.org/abs/2310.06452) | [P] | **[MEASURED]** RLHF "significantly reduces output diversity vs SFT." |
| [Padmakumar & He, ICLR 2024 — arXiv:2309.05196](https://arxiv.org/abs/2309.05196) | [P] | **[MEASURED]** InstructGPT collapses co-writing diversity; base GPT-3 does not. Isolates preference-tuning as the homogenizer. |
| [Sharma et al. (Anthropic), ICLR 2024 — arXiv:2310.13548](https://arxiv.org/abs/2310.13548) | [P] | **[MEASURED]** RLHF induces sycophancy as a general behavior. |
| [Wikipedia — Signs of AI Writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | [B] | The most exhaustive community taxonomy; vocabulary, structure, formatting, markup artifacts. |

### 19.4 Load-bearing numbers — cite these exactly

| Claim | Number | Source |
|---|---|---|
| "delves" in abstracts | **25.2×** | Kobak, *Sci. Adv.* 2025 |
| "meticulous" in reviews | **34.7×** | Liang, ICML 2024 |
| LLM use, 2024 PubMed abstracts | **≥13.5%** | Kobak 2025 |
| AI-modified EMNLP-2023 reviews | **16.9%** | Liang 2024 |
| Syntactic templates, AI vs human | **95% vs 38%** | Shaib 2024 |
| DetectGPT vs baseline (GPT-NeoX) | **0.95 vs 0.81 AUROC** | Mitchell, ICML 2023 |
| Reward-model bold-format win-rate | **89.5%** | Zhang 2024 |
| Data needed to install bold bias | **0.7%** (57.5%→88%) | Zhang 2024 |

> **Two methodological caveats.** (1) Corpus-frequency methods (Kobak, Liang) estimate *population* proportions; they never accuse an individual document. (2) Lexical word-lists decay once publicized (Geng & Trotta); the durable signals are **statistical** (perplexity, burstiness, curvature) and **structural** (templates, formatting), not any single word.

---

## 20. The Humanizer-Skill Landscape

The Part III protocol is synthesized from 7 open-source "humanizer" skills (Claude Code / agent `SKILL.md` files and system prompts). What each contributes, and the techniques that appear across *multiple* tools (the consensus playbook).

| Skill | What it adds that others don't |
|---|---|
| [**conorbronsdon/avoid-ai-writing**](https://github.com/conorbronsdon/avoid-ai-writing) | The **graded 3-tier word table** (§14); per-context profiles (LinkedIn/blog/email) with a tolerance matrix; the colon-vs-period tell (§12.2); stylometric tests (TTR, reshuffle, treadmill). The most exhaustive. |
| [**blader/humanizer**](https://github.com/blader/humanizer) | **33 named patterns** + the **cluster rule and false-positives list** (§16); negative-parallelism and signposting bans; a "signs of *human* writing" preserve list. |
| [**jalaalrd/anti-ai-slop-writing**](https://github.com/jalaalrd/anti-ai-slop-writing) | The cleanest **hard blacklist**; quantified punctuation caps (1 em-dash / 500 words, 1 "!" / 1,000 words); banned sentence-openers and model-specific first words. |
| [**Aboudjem/humanizer-skill**](https://github.com/Aboudjem/humanizer-skill) | **43 patterns + the 0–100 AI-tell score** (§17); explicit burstiness/perplexity targets; forensic artifact list (§13). |
| [**adenaufal/anti-slop-writing**](https://github.com/adenaufal/anti-slop-writing) | Vocabulary grouped by *function* (significance puffers / analytical verbs / poetic nouns / promotional adjectives); bilingual (works on non-English slop); 10-item post-gen checklist. |
| [**gregorymm/humanize-text**](https://github.com/gregorymm/humanize-text) | **7-category 1–10 scoring**; the only one tuned for **UI/UX microcopy** (handles Figma/screenshots; user-centric reframing). |
| [**matteoroversi/anti-ai-rhetoric**](https://github.com/matteoroversi/anti-ai-rhetoric) | The **4-pass draft→revise process** (§15); "add a rough edge"; read-aloud six-check. Process over blacklist. |

**Consensus rules (appeared in 4+ of the 7 tools) — the de facto standard playbook:**

1. **Em-dash ban** (all 7) — the #1 fingerprint; target zero (§12.1).
2. **The core banned cluster** (all 7) — delve, tapestry, landscape, realm, pivotal, crucial, testament, vibrant, intricate, meticulous, seamless, robust, leverage, utilize, foster, bolster, underscore, showcase, harness, comprehensive, cutting-edge, groundbreaking, multifaceted, nuanced, paramount.
3. **Sentence-length variation / burstiness** (6/7) — mix 3–8-word and 20–40-word sentences; never 3+ similar in a row.
4. **Kill the rule of three** (6/7) — use 2, 4, or 5.
5. **Copula reversal** (5/7) — replace "serves as / boasts / represents" with "is / has."
6. **Negative-parallelism ban** (5/7) — kill "not only X but Y," "it's not just X, it's Y."
7. **No participial -ing tack-ons** (5/7) — kill ", highlighting the importance of…"
8. **Strip chatbot/sycophancy artifacts** (5/7) — "I hope this helps," "Great question!"
9. **Kill signposting** (5/7) — "Let's dive in," "Without further ado." Do it, don't announce it.
10. **Demand specifics over vague attribution** (5/7) — named source + real number, not "experts say."
11. **Formatting discipline** (4/7) — sentence-case headings, strip mechanical bold, colon-not-period after bold labels.

**Two meta-patterns in the best tools:** (a) flag *clusters*, not single words, with an explicit false-positives list; (b) wrap the blacklist in a *scored multi-pass process*, not a one-shot find-and-replace.

*(Secondary: [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) — terse rule list. Directories: [awesome-slop](https://github.com/hwajongpark/awesome-slop), [avoid-slop](https://github.com/shannhk/avoid-slop).)*

---

## 21. Quick Reference Card

Cut this out and keep it for editing.

### Red-flag words (Tier 1 — replace on sight)
`delve · tapestry · landscape · realm · testament · underscore · showcase · leverage · utilize · robust · comprehensive · meticulous · seamless · pivotal · intricate · boasts · nestled · commence · cutting-edge`

### Red-flag phrases
`"In today's fast-paced world" · "It's not just X, it's Y" · "Not only… but also" · "I hope this message finds you well" · "Don't hesitate to reach out" · "It's important to note that" · "Let's dive in" · "In conclusion" · "Furthermore / Moreover / Additionally" · "The importance of X cannot be overstated"`

### Red-flag punctuation & format
`— em-dash (target zero) · **bold everywhere** · Title Case Headings · **Bold label.** (period not colon) · 🚀 emoji bullets · rule-of-three triplets · uniform sentence length`

### Smoking guns (paste-evidence — see §13)
`citeturn0search0 · utm_source=chatgpt.com · [Your Name] · "As an AI language model" · "I hope this helps! Let me know…"`

### The 5-second core test
1. Is every sentence about the same length? → **AI**
2. Does any sentence surprise you? → if no, **AI**
3. Could this have been written about anyone, anywhere? → if yes, **AI**
4. Can you cut 40% with no information loss? → if yes, **AI** (treadmill)
5. Can you picture one specific person who wrote it? → if no, **AI**

### The fix, in one line
**Descend the abstraction ladder** (name the dog, pocket the coin) · **break the rhythm** (short then long) · **take a side** · **start inside the action** · **hedge only where the evidence is thin** · **flag clusters, never single words.**

---

*Compiled June 2026 · Detection field guide + RLHF mechanism + humanization protocol.*
*Every load-bearing number verified against its primary source (§19); folklore flagged as folklore.*
*Evidence tags: [P] peer-reviewed · [S] secondary · [B] practitioner · [MEASURED] quantified · [CONTESTED] disputed.*
*Humanization protocol synthesized from 7 open-source skills (§20). This is a craft reference, not an evasion manual — the load-bearing advice (specificity, stance, real detail, structural variety) simply makes writing better, which is why it also reads as human.*
