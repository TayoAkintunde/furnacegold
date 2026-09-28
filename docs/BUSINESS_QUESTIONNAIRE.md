# Business profile questionnaire

Your answers become `config/business_profile.yaml`, which configures the agents and the knowledge base. **Nothing is filled in until you answer.** A question you skip stays UNKNOWN, and agents treat it as unknown rather than guessing.

**How to answer.** Choose whichever is easier:
- **Reply in chat** with the question numbers (e.g. `Q3.1: …`). Your answers are transcribed exactly into the profile, and you confirm them before they are applied.
- **Edit `config/business_profile.yaml` directly**, then run `python -m aibos profile` to check it.

Short answers are fine, and so are "don't know", "skip" and "not yet". Please leave out personal data such as client names, emails or phone numbers.

---

## Q0. The business
- **Q0.1** What is the business or brand called? Answer "none yet" if it has no name.
- **Q0.2** In one sentence, what do you do and for whom?
- **Q0.3** What stage are you at? *idea / side project / early (less than a year of revenue) / established / other*

## Q1. Expertise
- **Q1.1** List your areas of expertise. For each, give:
  - your level: *beginner / intermediate / advanced / expert*
  - roughly how many years
- **Q1.2** For each area, what evidence could you show someone? For example: projects shipped, roles held, certifications, published work.

*This configures:* which research agents are prioritised, and what you can credibly teach and sell.

## Q2. Interests
- **Q2.1** Which topics do you enjoy following, even where you aren't (yet) an expert?

*This configures:* the research watch-list. These topics are kept separate from expertise, so content never claims authority you haven't stated.

## Q3. Target audience
List up to three segments, most important first. For each:
- **Q3.1** Who are they? Give roles or job titles and the type of organisation.
- **Q3.2** How technical are they? *beginner / intermediate / advanced / mixed*
- **Q3.3** Which problems do they have that you can help with? Use their words if you know them.
- **Q3.4** What outcomes do they want?
- **Q3.5** Where do they spend time online or in person?
- **Q3.6** Who pays? *individuals / small businesses / mid-market / enterprise / mixed*
- **Q3.7** How do you know this? *data (analytics, sales) / conversations / assumption*

*This configures:* audience context for content, education and product agents. Answers marked "assumption" are treated as hypotheses to test, never as facts.

## Q4. Geographic market
- **Q4.1** Which countries or regions do you mainly serve? Any secondary ones?
- **Q4.2** What language(s) should content be written in?
- **Q4.3** What is your time zone?
- **Q4.4** Which currency do you price in?
- **Q4.5** Are there regulations you must follow? For example, data protection, advertising or financial-promotion rules in your market.

*This configures:* language, spelling, dates and currency in drafts; your scheduling time zone; and compliance notes for agents.

## Q5. Content platforms
- **Q5.1** Which platforms do you want to publish on? Rank them 1 (most important) to 5. The system supports:
  - X posts and X threads
  - LinkedIn posts and LinkedIn carousels
  - Instagram posts and Instagram carousels
  - TikTok and YouTube Shorts
  - Facebook, Reddit, and communities (Discord, Slack or forums)
  - Newsletter, blog, SEO articles, and podcast
- **Q5.2** For each platform, do you already have an account? If you know it from the platform's analytics, how large is the audience?
- **Q5.3** How often do you realistically want to post on each?
- **Q5.4** Are there platforms you want to avoid?

*This configures:* the default platforms and the cadence for the content calendar.

## Q6. Content style
- **Q6.1** Pick three to five words for your tone. For example: *calm, direct, technical, warm, playful, contrarian, practical.*
- **Q6.2** How formal should it be? *casual / conversational / professional / academic*
- **Q6.3** Should it be written as "I", "we", or the brand name?
- **Q6.4** How much humour? *none / light / frequent.* How many emoji? *none / sparing / frequent.*
- **Q6.5** Do you prefer short, medium or long content, or does it depend on the platform?
- **Q6.6** Which words or phrases should never appear? Which phrases do you naturally use?
- **Q6.7** Are there creators whose style you admire? (Optional.)
- **Q6.8** How do you disclose sponsorships and affiliate links?

*This configures:* the brand-voice rules that every draft is checked against automatically.

## Q7. Business goals
- **Q7.1** What should be true in 90 days?
- **Q7.2** In 12 months?
- **Q7.3** In three years? (Optional.)
- **Q7.4** How will you judge progress? For example: subscribers, qualified leads, clients, launches, revenue.

*This configures:* how opportunities are ranked, and the goals section of the weekly report.

## Q8. Revenue goals
These are targets. The system never promises or forecasts them.
- **Q8.1** What is your current monthly revenue? Optional; only share it if you want to.
- **Q8.2** What is your target monthly revenue in 12 months?
- **Q8.3** What is the minimum monthly revenue that would make this worthwhile?
- **Q8.4** Which currency?

*This configures:* the progress-toward-target line in weekly reports, calculated only from revenue data you supply.

## Q9. Current products
For each product that is live now:
- **Q9.1** Name and type (for example: ebook, template, course, SaaS, membership).
- **Q9.2** Price and currency.
- **Q9.3** Who it is for.
- **Q9.4** Status: *live / paused / retired.*
- **Q9.5** Results so far, only if you know them. Otherwise "unknown".

*This configures:* business memory, so opportunity agents don't propose products you already sell and can suggest links between them.

## Q10. Planned products
For each planned product:
- **Q10.1** Name or working title, and type.
- **Q10.2** Stage: *idea / validating / building / ready.*
- **Q10.3** Target date, if you have one.
- **Q10.4** Who it is for.

*This configures:* the product and experiment pipeline. Planned products get validation experiments before anything is built.

## Q11. Services
For each service you offer, or want to offer:
- **Q11.1** Name and what is delivered.
- **Q11.2** Pricing model (*fixed / hourly / retainer / value-based*) and price.
- **Q11.3** How many clients or projects you can take per month.
- **Q11.4** Delivery: *remote / in person / both.*

*This configures:* the service and sales agents, which also respect your capacity limit.

## Q12. Technology preferences
- **Q12.1** Which tools do you use today? For example: CMS, email platform, CRM, analytics, automation, code hosting.
- **Q12.2** Which technologies do you prefer to build with? Is your approach *no-code / low-code / code / mixed*?
- **Q12.3** Which AI providers or models do you prefer, and which do you want to avoid?
- **Q12.4** Are there tools you refuse to use?

*This configures:* the software and automation agents, and which integrations to build first.

## Q13. Strengths
- **Q13.1** What do you do better than most people in your field?
- **Q13.2** What do people come to you for?

## Q14. Weaknesses
- **Q14.1** What do you struggle with or avoid? For example: selling, consistency, video, design, finance.
- **Q14.2** Which of those would you like the system, or other people, to take over?

*Q13 and Q14 configure:* which opportunities are ranked as feasible for you, and where the system prepares more of the work.

## Q15. Available time
- **Q15.1** How many hours per week can you realistically give this?
- **Q15.2** If you know it, roughly how does that split between content, client work, product building, and learning/research?
- **Q15.3** Which days are you available? Are there constraints, such as a day job, a non-compete, or family commitments?

*This configures:* limits on cadence and experiment scope. No plan will need more hours than you've stated.

## Q16. Budget
- **Q16.1** What is your monthly budget in total?
- **Q16.2** How is it split between tools, paid advertising (0 means none), and contractors?
- **Q16.3** What is the most you'd spend on a single experiment?

*This configures:* budget caps. Any spend still needs your approval every time.

## Q17. Preferred business models
- **Q17.1** Rank the models you want to pursue:
  - consulting
  - AI automation services
  - digital products, templates, and prompt/workflow products
  - courses and workshops
  - memberships, subscriptions and SaaS
  - affiliate, sponsorship and licensing
- **Q17.2** Which do you want to exclude entirely?

*This configures:* which revenue streams the revenue agents consider.

## Q18. Topics to become known for
- **Q18.1** List three to seven topics you want to be known for, most important first.

*This configures:* research priorities, content pillars, the taxonomy, and the topics for the daily run.

## Q19. Topics to avoid
- **Q19.1** Which topics must never be covered, and why?
- **Q19.2** Which sensitive categories should be avoided? For example: medical, legal or personal-financial advice; politics; specific competitors.

*This configures:* a content check that blocks drafts touching these topics, and a research filter.

## Q20. Anything else
- **Q20.1** Is there anything else the system should know? For example: legal constraints, brand history, or things that have already failed for you.
