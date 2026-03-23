# Ollama Benchmark Report

- Generated: 2026-03-22T23:56:01
- Models: qwen3:8b, qwen3.5:latest, qwen3:14b, phi4-mini-reasoning:latest, gemma3:12b
- Repeat per question: 1
- num_ctx: 4096
- num_predict: 512
- temperature: 0.2

## Model Speed Summary

| Model | Runs | Avg wall time (s) | Median wall time (s) | Avg tokens/s |
|---|---:|---:|---:|---:|
| qwen3:8b | 6 | 7.19 | 5.10 | 37.62 |
| qwen3:14b | 6 | 8.21 | 8.52 | 21.57 |
| gemma3:12b | 6 | 12.10 | 11.38 | 24.44 |
| phi4-mini-reasoning:latest | 6 | 12.85 | 12.94 | 57.07 |
| qwen3.5:latest | 6 | 15.11 | 15.33 | 22.76 |

## kedah-investor-summary

- Topic: kedah-investment
- Source note: `showcase_kedah_best_qa.txt`
- Prompt: Using only the context, write a short investor-facing summary of Kedah's approved investment story. Mention the overall scale, the strongest industries, and what foreign investor interest suggests.

### qwen3:14b

- Wall time: 10.66 s
- Total duration: 10.66 s
- Load duration: 3.18 s
- Prompt tokens: 464
- Output tokens: 92
- Output speed: 21.30 tok/s

```text
Kedah has attracted a total approved investment of approximately RM62.6 billion, showcasing strong investor confidence in the region. The strongest industries are manufacturing, plastic products, electrical and electronics, transport equipment, and services. Foreign investment is notably led by the USA, Japan, and China, indicating significant international interest in Kedah's economic opportunities. This diverse and substantial investment highlights Kedah as an attractive destination for both local and global investors.
```
### qwen3.5:latest

- Wall time: 10.84 s
- Total duration: 10.83 s
- Load duration: 4.43 s
- Prompt tokens: 465
- Output tokens: 101
- Output speed: 23.01 tok/s

```text
Kedah has attracted a massive total approved investment of over RM 62.5 billion, signaling strong confidence in the state's economic potential. The investment is heavily concentrated in manufacturing, which leads the sector, followed closely by plastic products and electrical & electronics. This heavy focus on industrial production suggests a robust supply chain ecosystem. Furthermore, foreign investors from top economies like the USA, Japan, and China have committed significant capital, indicating that Kedah is a globally recognized hub for international business and manufacturing.
```
### gemma3:12b

- Wall time: 14.28 s
- Total duration: 14.28 s
- Load duration: 5.03 s
- Prompt tokens: 451
- Output tokens: 136
- Output speed: 23.99 tok/s

```text
Here's an investor-facing summary of Kedah's approved investment story, based solely on the provided information:

Kedah presents a significant investment opportunity, with a total of over RM 62.6 billion in approved investments. Manufacturing is the leading sector, attracting over RM 4 billion, followed by plastic products, electrical & electronics, transport equipment, and services. Investment interest is broad, with substantial commitments from the USA, Japan, China, Germany, and Singapore, suggesting confidence in Kedah’s potential.

**Note:** The context does not provide yearly investment totals, so it's impossible to determine which year saw the highest investment activity.
```
### phi4-mini-reasoning:latest

- Wall time: 14.44 s
- Total duration: 14.42 s
- Load duration: 3.14 s
- Prompt tokens: 362
- Output tokens: 512
- Output speed: 56.73 tok/s

```text
<think>
Okay, let's tackle this problem step by step. The user wants an investor-facing summary based on the provided data about Kedah's approved investment. First, I need to extract the key points from the context without adding any external information.

Starting with the overall scale: the total approved investment is RM 62,599,928,663.3959. That's a huge number, so mentioning it in terms of billions would make sense for clarity. Maybe convert it to approximately RM 62.6 billion to simplify.

Next, the top 5 industries by approved investment. The sectors listed are Manufacturing (RM 4,065,041,041.63), Plastic Products (RM 2,562,888,007.09), Electrical & Electronics (RM 725,028,545.14), Transport Equipment (RM 604,691,083.88), and Services (RM 299,393,519.82). The strongest industry is clearly Manufacturing, followed by Plastic Products. Then the next two are Electrical/Electronics and Transport Equipment. It's important to note these numbers in descending order.

Foreign investment comes from top countries: USA, Japan, China, Germany, Singapore with respective amounts over 9 trillion, 7.3 trillion, etc. So highlighting that foreign investors, especially from these major economies, have significant interest. The USA is the biggest contributor, followed by Japan and China. This suggests confidence in Kedah's market potential.

Distinct sectors present include services, unknown (since the original list mentions "unknown" as one of the distinct sectors), and manufacturing. Wait, the user listed "services, unknown, manufacturing" under distinct sectors. But looking back at the top industries, Manufacturing is first. Maybe there's a typo or mislabeling here. The third industry in the top 5 is Electrical & Electronics, which might fall under 'unknown' if that's not specified? Or perhaps the distinct sectors are broader categories. Hmm. Need to clarify: the problem states "distinct sectors present: services, unknown, manufacturing." So maybe there are three main sectors: Services (which includes the Services industry), Manufacturing, and another sector labeled as 'unknown'. But that seems odd. Alternatively, maybe the list of top industries is under broader distinct sectors. Wait, perhaps the distinct sectors are more general categories, like Manufacturing, Plastic Products (which could be part of Manufacturing?), Electrical & Electronics (maybe part of a tech category?), Transport Equipment (another sub-industry), Services. The mention of "unknown" as a
```
### qwen3:8b

- Wall time: 18.28 s
- Total duration: 18.27 s
- Load duration: 5.72 s
- Prompt tokens: 464
- Output tokens: 110
- Output speed: 36.47 tok/s

```text
Kedah has attracted significant approved investment, totaling RM62.6 billion. The strongest industries in terms of investment are manufacturing, plastic products, electrical & electronics, transport equipment, and services. Manufacturing leads with over RM4 billion in approved investment, followed by plastic products and electrical & electronics. Foreign investor interest is primarily from the USA, Japan, and China, indicating strong confidence in Kedah's potential for growth and business opportunities. However, the context does not provide enough yearly data to determine which year had the highest approved investment.
```

## kedah-priority-sectors

- Topic: kedah-investment
- Source note: `showcase_kedah_best_qa.txt`
- Prompt: From the context, recommend the top 3 sectors to highlight in a Kedah investment pitch. Give one sentence of justification for each.

### qwen3:8b

- Wall time: 5.74 s
- Total duration: 5.74 s
- Load duration: 2.15 s
- Prompt tokens: 456
- Output tokens: 82
- Output speed: 37.80 tok/s

```text
1. **Manufacturing** – It is the largest sector by approved investment, showing strong industrial interest in Kedah.  
2. **Plastic Products** – This sector has the second-highest investment, indicating a significant focus on this key industry.  
3. **Electrical & Electronics** – This sector shows substantial investment, highlighting Kedah's appeal for high-tech and advanced manufacturing.
```
### qwen3:14b

- Wall time: 8.87 s
- Total duration: 8.87 s
- Load duration: 2.97 s
- Prompt tokens: 456
- Output tokens: 71
- Output speed: 21.71 tok/s

```text
1. Manufacturing - It has the highest approved investment among all sectors, showing strong interest and potential for growth.  
2. Plastic Products - This sector comes second in approved investment, indicating significant economic contribution and opportunity.  
3. Services - Although it has the lowest investment compared to manufacturing and plastic products, it still contributes to employment and economic diversity.
```
### phi4-mini-reasoning:latest

- Wall time: 13.76 s
- Total duration: 13.73 s
- Load duration: 0.11 s
- Prompt tokens: 354
- Output tokens: 512
- Output speed: 56.38 tok/s

```text
<think>
Okay, let's tackle this problem step by step. The user wants the top 3 sectors to highlight in a Kedah investment pitch based on the provided data. First, I need to analyze the given information carefully.

Looking at the Top 5 industries by approved investment: Manufacturing is first with over 4 billion RM, followed by Plastic Products, Electrical & Electronics, Transport Equipment, and Services. The distinct sectors mentioned are services, unknown (maybe a placeholder for other sectors not listed?), and manufacturing. 

The total employment across all investments is 268,621 jobs, which might indicate the scale of the workforce, but the question focuses on sector performance rather than job numbers unless specified. However, highlighting high-employment sectors could also be persuasive.

Countries by foreign investment aren't directly related to sectors, so maybe that's a distraction here. The limitation mentioned doesn't affect this since we're not asked about years or countries.

So, Manufacturing is clearly top with nearly 4 billion. Next is Plastic Products at over 2.5 billion. Electrical & Electronics is third with around 725 million. Then Services next with about 299 million. But wait, the distinct sectors are services, unknown, and manufacturing. So even though Plastic Products is second in industry rank, it's not listed as a distinct sector. The problem states "distinct sectors present: services, unknown, manufacturing." Hmm, that's confusing. Maybe 'unknown' is a category for other sectors not specified? Or perhaps there's a mistake here.

Wait, the user might have meant that the known distinct sectors are three: services, another (maybe like IT or something else?), and manufacturing. But according diversification, Plastic Products isn't listed as one of them. So maybe the Top 5 industries include sectors beyond those three mentioned as distinct? That could be a problem because if only three sectors are considered distinct but there are five top industries, perhaps some overlap.

Alternatively, maybe "distinct sectors present" refers to unique sector categories in the data, which might not align with the industry rankings. For example, services is one of them, manufacturing another, and then there's an 'unknown' category that aggregates other sectors like Plastic Products or Electrical & Electronics. But that's speculative. The context says "distinct sectors present: services, unknown, manufacturing." So perhaps there are three distinct sector categories, where 'unknown' covers the remaining two top industries (Plastic, Transport Equipment, etc.). That seems odd but possible.

If that's the case, then the Top 3 would be Manufacturing (1st), Services (3rd
```
### gemma3:12b

- Wall time: 15.18 s
- Total duration: 15.17 s
- Load duration: 5.22 s
- Prompt tokens: 441
- Output tokens: 147
- Output speed: 23.86 tok/s

```text
Here are the top 3 sectors to highlight, based on the provided Kedah investment showcase data:

1. **Manufacturing:** With RM 4,065,271,041.63 in approved investment, it represents the largest sector and demonstrates Kedah's strength in production.
2. **Plastic Products:** Attracting RM 2,562,888,007.09 in investment, this sector shows significant investor interest and potential for growth.
3. **Electrical & Electronics:** The RM 725,028,545.14 in approved investment indicates a valuable and growing technology-driven industry in Kedah.
```
### qwen3.5:latest

- Wall time: 18.49 s
- Total duration: 18.48 s
- Load duration: 5.27 s
- Prompt tokens: 457
- Output tokens: 188
- Output speed: 22.38 tok/s

```text
Based on the provided context, here are the top 3 sectors to highlight in a Kedah investment pitch, along with justifications:

1.  **Manufacturing**: This is the strongest sector to feature because it accounts for the largest portion of approved investments at over RM 4 billion, demonstrating significant industrial scale.
2.  **Plastic Products**: This is the second-best choice as it represents the next highest investment category with over RM 2.5 billion, indicating a robust and specialized manufacturing base.
3.  **Electrical & Electronics**: This sector should be highlighted as the third option because it shows strong diversification with over RM 725 million in approved investments, appealing to high-tech investors.

*Note: The "Services" sector is excluded from the top three because its investment amount (approx. RM 300 million) is significantly lower than the top three manufacturing categories listed.*
```

## kedah-data-limitation

- Topic: kedah-investment
- Source note: `showcase_kedah_best_qa.txt`
- Prompt: A client asks which year had the highest total approved investment RM. Answer safely using only the context and explain the data limitation.

### qwen3:8b

- Wall time: 4.96 s
- Total duration: 4.96 s
- Load duration: 2.00 s
- Prompt tokens: 453
- Output tokens: 58
- Output speed: 37.93 tok/s

```text
The context does not provide enough information to determine which year had the highest total approved investment RM. The available data includes the total approved investment amount but does not break it down by year. Therefore, it is not possible to identify the year with the highest investment based on the given information.
```
### qwen3:14b

- Wall time: 8.17 s
- Total duration: 8.12 s
- Load duration: 3.37 s
- Prompt tokens: 453
- Output tokens: 39
- Output speed: 21.53 tok/s

```text
The context provided does not include yearly totals for approved investments, so it is not possible to determine which year had the highest total approved investment RM. This is a limitation of the available data.
```
### gemma3:12b

- Wall time: 9.76 s
- Total duration: 9.76 s
- Load duration: 5.18 s
- Prompt tokens: 439
- Output tokens: 39
- Output speed: 24.83 tok/s

```text
The available information doesn't state which year had the highest total approved investment. The data only provides a total approved investment amount for the entire period covered by the showcase, not yearly breakdowns.
```
### phi4-mini-reasoning:latest

- Wall time: 10.97 s
- Total duration: 10.97 s
- Load duration: 0.11 s
- Prompt tokens: 352
- Output tokens: 412
- Output speed: 57.40 tok/s

```text
<think>
Okay, let's tackle this question. The user wants to know which year had the highest total approved investment RM based on the provided context. Let me start by reviewing all the given information carefully.

First, the total approved investment is a big number: RM 62,599,928,663.3959. But that's probably the cumulative figure over several years since it's much larger than individual industry investments listed under "Top 5 industries." Each of those top industries has specific amounts attached, but they are likely parts of the total rather than yearly figures.

The context mentions that there are employment numbers (268,621) and foreign investment by country, but neither of these directly addresses years. The key point raised as a limitation is that the available summary doesn't include enough yearly totals to identify the year with the highest approved investment. 

So, even though we have total investments broken down by industry and countries, there's no data provided on annual figures. Without knowing how these totals are distributed across different years (like 2020, 2021, etc.), it's impossible to determine which specific year had the most investment. The limitation explicitly states that the summary lacks sufficient yearly breakdowns. Therefore, based on the given information, we can't answer the client's question because the necessary data (yearly totals) isn't available here. We have to stick strictly to what's provided; inventing dates or making assumptions isn't allowed. So the safe conclusion is to point out the absence of yearly data as the limitation.
</think>

The context does not provide sufficient information to determine which year had the highest total approved investment RM. While the total cumulative investment (RM 62,599,928,663.3959) and breakdowns by industry/country are included, **yearly totals are explicitly stated as insufficient** in the data limitation. Without knowing how these figures are distributed across individual years, it is impossible to identify the peak year. 

**Data Limitation:** The summary lacks yearly investment totals, making it unsafe to conclude which year had the highest investment.
```
### qwen3.5:latest

- Wall time: 14.16 s
- Total duration: 14.00 s
- Load duration: 5.16 s
- Prompt tokens: 455
- Output tokens: 69
- Output speed: 22.86 tok/s

```text
Based on the provided context, it is not possible to determine which year had the highest total approved investment.

The available data lists the total approved investment amount and breaks it down by industry and country, but it does not include yearly totals or a timeline. Without specific investment figures for individual years, the highest-performing year cannot be identified.
```

## airport-runway-incident

- Topic: airport-operations
- Source note: `production_multitenant_customer_service_platform_blueprint.md`
- Prompt: An aircraft incident happens on the runway. Draft the safest short answer an internal airport assistant should give, based only on the context.

### qwen3:8b

- Wall time: 4.29 s
- Total duration: 4.29 s
- Load duration: 1.93 s
- Prompt tokens: 268
- Output tokens: 55
- Output speed: 38.02 tok/s

```text
Based on the airport operations blueprint, in the event of an aircraft incident on the runway, notify the Airport Fire & Rescue Service immediately and initiate the incident reporting Form IR-02. Please verify with the duty supervisor if the incident involves fuel leakage or other hazardous conditions.
```
### qwen3:14b

- Wall time: 6.20 s
- Total duration: 6.20 s
- Load duration: 3.11 s
- Prompt tokens: 268
- Output tokens: 31
- Output speed: 21.97 tok/s

```text
Based on the context provided, the information is insufficient to draft a specific response. Please consult the Emergency Response Manual and relevant incident reporting procedures for guidance.
```
### gemma3:12b

- Wall time: 10.63 s
- Total duration: 10.62 s
- Load duration: 4.30 s
- Prompt tokens: 264
- Output tokens: 71
- Output speed: 24.71 tok/s

```text
Based on Emergency Response Manual v3.2, Section 4.1, notify Airport Fire & Rescue Service immediately and initiate incident reporting Form IR-02. Please verify with duty supervisor.

**Escalation Note:** The context does not specify the severity of the incident, so further assessment is needed to determine if additional procedures are required.
```
### phi4-mini-reasoning:latest

- Wall time: 12.80 s
- Total duration: 12.75 s
- Load duration: 0.12 s
- Prompt tokens: 248
- Output tokens: 493
- Output speed: 57.02 tok/s

```text
<think>
Okay, let's see. The user wants a safe, concise answer for an aircraft incident on the runway, following the project's grounding rules. Let me break this down.

First, the context mentions high-risk domains like safety incidents should prefer approved documents, show citations, avoid speculation, and add escalation notes if confidence is low. The example given cites Emergency Response Manual v3.2 and asks to verify with a duty supervisor.

So, in this scenario, an aircraft incident on the runway is definitely a high-risk situation. The assistant must prioritize approved sources. Since it's a runway incident, maybe there's an SOP or emergency manual specific to runway incidents. But without knowing the exact document, the answer should reference whatever the approved protocol is. 

The safest approach would be to cite the relevant procedure, provide clear actions, and escalate if necessary. Avoid any speculative language. For example, if there's a Runway Incursion Response Policy, the assistant should point to that, outline steps like securing the area, notifying authorities, etc., and add an escalation note if they're unsure about something. 

But wait, the user says "based only on the context." The provided context doesn't mention specific documents beyond general ones like Emergency Response Manual. So maybe the answer has to refer to a generic approved document, state the action citing it, avoid speculation, and include escalation. Let's structure it similarly to the example but tailored to a runway incident. 

Possible steps: alert emergency services (fire, rescue), secure the runway, notify air traffic control, etc. But without specific documents, use "Emergency Response Manual" as the source. Also, add an escalation note because this is a high-risk scenario and the assistant might not be fully certain about all details. So the answer should cite the manual, outline actions, and say to escalate if needed.
</think>

Based on the Emergency Response Protocol v5.1 (ERPM) for runway incidents, **immediately activate Runway Incident Procedure IR-09A**:  
1. Secure the incident area and prevent further aircraft movement.  
2. Notify Airport Fire & Rescue Services and emergency medical teams (if required).  
3. Coordinate with Air Traffic Control to clear safe flight paths.  
4. *Escalation note: Verify actions with Duty Supervisor ATC001 before executing fuel-related procedures.*  

**Action prioritized by grounding rules:** Use approved SOP, cite ERPM, avoid speculation, and escalate uncertainty.
```
### qwen3.5:latest

- Wall time: 15.45 s
- Total duration: 15.44 s
- Load duration: 4.94 s
- Prompt tokens: 272
- Output tokens: 101
- Output speed: 22.88 tok/s

```text
Based on the provided context, the safest short answer an internal airport assistant should give is:

"Based on Emergency Response Manual v3.2, Section 4.1, notify Airport Fire & Rescue Service immediately and initiate incident reporting Form IR-02. Please verify with duty supervisor if the incident involves fuel leakage."

*(Note: This answer is derived directly from the example approved answer provided in the context, as the specific details of the runway incident are not defined in the text.)*
```

## airport-ai-guardrails

- Topic: airport-operations
- Source note: `production_multitenant_customer_service_platform_blueprint.md`
- Prompt: Summarize the response rules the assistant should follow for airport emergency or safety questions. Keep it brief and practical.

### qwen3:8b

- Wall time: 4.62 s
- Total duration: 4.61 s
- Load duration: 1.99 s
- Prompt tokens: 265
- Output tokens: 65
- Output speed: 37.83 tok/s

```text
For airport emergency or safety questions, the assistant should:  
- Use approved documents and cite them with version numbers.  
- Avoid speculation; if unsure, add an escalation note.  
- Follow the priority order: FAQs > SOPs > data > model reasoning.  
- Provide clear, concise, and actionable guidance.
```
### qwen3:14b

- Wall time: 5.97 s
- Total duration: 5.96 s
- Load duration: 3.02 s
- Prompt tokens: 265
- Output tokens: 29
- Output speed: 22.34 tok/s

```text
Use approved documents and cite them with version and section. Avoid guesses. Escalate if unsure. Keep answers clear and to the point.
```
### gemma3:12b

- Wall time: 11.81 s
- Total duration: 11.81 s
- Load duration: 4.91 s
- Prompt tokens: 260
- Output tokens: 102
- Output speed: 24.71 tok/s

```text
For airport emergency or safety questions, here's what I'll do:

1. **Use official documents first:** I'll prioritize answers from approved documents.
2. **Cite my sources:** I'll tell you where the information came from (document name and section).
3. **Stick to the facts:** I won't guess or speculate.
4. **Escalate when unsure:** If I'm not confident in the answer, I'll let you know.
```
### phi4-mini-reasoning:latest

- Wall time: 13.09 s
- Total duration: 13.08 s
- Load duration: 0.10 s
- Prompt tokens: 245
- Output tokens: 512
- Output speed: 57.76 tok/s

```text
<think>

Okay, let's see. The user wants a summary of the response rules for airport emergency or safety questions based on the provided context. Let me start by breaking down the key points from the grounding rules.

First, the high-risk domains mentioned include things like safety, compliance, HR, legal, and emergencies. For these, the guidelines are pretty strict. The priority is to prefer approved documents over other answers. So whenever someone asks a question in these areas, the assistant should reference specific approved sources first.

The example given uses an Emergency Response Manual version 3.2, cites Section 4.1, and advises immediate action while suggesting verification with a duty supervisor if there's uncertainty, especially regarding fuel leakage. That escalation note is important because it shows low confidence and directs the user to someone more knowledgeable.

Then there's the grounding order priority: 1. Curated FAQ or approved answers take top precedence. If those aren't available, then approved SOPs/policy chunks come next. If neither is sufficient, structured data results might be used. Only if all that isn't enough should general model reasoning kick in, but that's a last resort.

So putting this together for emergency/safety questions: The assistant must always start with the most reliable source—approved documents like manuals or policies. They need to cite exactly what they're referencing, show the version (if applicable), and avoid any speculative answers unless they're sure. If there's doubt, they have to escalate the issue to a responsible party.

Also, if approved sources don't cover the query, the next steps in the grounding order apply. But since the user asked specifically about emergency or safety questions, which are high-risk, those fall under the first set of rules. The key points are citing approved documents, avoiding speculation, and escalating when confidence is low.

Wait, but does the example mention checking with a duty supervisor? That's part of the escalation process. So in responses, if the answer isn't clear from the document, adding an escalation note is necessary. That means directing the user to contact someone else for confirmation or further action.

So summarizing all that into response rules: For airport emergency/safety questions, always reference and cite approved documents (like manuals or SOPs), include version numbers when relevant, avoid giving speculative answers unless absolutely certain, and if there's uncertainty or low confidence, prompt escalation to the appropriate authority. Follow the priority order of FAQs/SOPs first, then structured data, and only use general reasoning as a last resort.

I need to make sure I didn't miss anything. The user's question is
```
### qwen3.5:latest

- Wall time: 16.52 s
- Total duration: 16.51 s
- Load duration: 5.11 s
- Prompt tokens: 269
- Output tokens: 121
- Output speed: 22.78 tok/s

```text
For airport emergency or safety questions, the assistant must:
1. **Prioritize approved sources**: Use curated FAQs, approved SOPs, or policies first. Only use general reasoning if no approved source exists.
2. **Cite precisely**: Always include the specific document name and version number.
3. **Avoid speculation**: Do not guess or invent facts; state clearly if information is unknown.
4. **Escalate when unsure**: Add an escalation note if confidence in the answer is low.
5. **Stay grounded**: Base every answer strictly on the provided blueprint rules.
```

## airport-form-and-escalation

- Topic: airport-operations
- Source note: `production_multitenant_customer_service_platform_blueprint.md`
- Prompt: What form should be initiated for an apron or runway incident, and who should be notified first? Answer carefully and include an escalation caveat if needed.

### qwen3:8b

- Wall time: 5.24 s
- Total duration: 5.24 s
- Load duration: 2.05 s
- Prompt tokens: 272
- Output tokens: 85
- Output speed: 37.67 tok/s

```text
Based on the provided context, the specific form and notification procedure for an apron or runway incident are not explicitly detailed. To provide an accurate answer, please refer to the approved documents such as the Emergency Response Manual or relevant SOPs, and ensure you include the citation and document version. 

Escalation caveat: If the exact procedure is not found in approved sources, consult the duty supervisor or incident command for guidance.
```
### qwen3:14b

- Wall time: 9.41 s
- Total duration: 9.40 s
- Load duration: 3.39 s
- Prompt tokens: 272
- Output tokens: 88
- Output speed: 20.60 tok/s

```text
Based on the Emergency Response Manual v3.2, Section 4.1, for an apron or runway incident, you should initiate incident reporting Form IR-02. Notify the Airport Fire & Rescue Service immediately. Please verify with the duty supervisor if the incident involves fuel leakage or other high-risk conditions. 

Escalation note: If the incident involves unknown or complex risks, consult the safety management system for further guidance.
```
### gemma3:12b

- Wall time: 10.95 s
- Total duration: 10.94 s
- Load duration: 5.35 s
- Prompt tokens: 267
- Output tokens: 80
- Output speed: 24.51 tok/s

```text
Based on Emergency Response Manual v3.2, Section 4.1, initiate incident reporting Form IR-02 and notify Airport Fire & Rescue Service immediately. Please verify with duty supervisor if the incident involves fuel leakage.

**Escalation Note:** The provided context only covers general incident reporting. Specific apron or runway incident procedures might be detailed in other documents not included in this excerpt.
```
### phi4-mini-reasoning:latest

- Wall time: 12.06 s
- Total duration: 12.05 s
- Load duration: 0.12 s
- Prompt tokens: 252
- Output tokens: 457
- Output speed: 57.14 tok/s

```text
<think>
Okay, let's tackle this question. The user is asking about initiating a form and notifying someone for an apron or runway incident based on grounding rules from an airport operations blueprint.

First, I need to recall the provided examples and guidelines. The key points are that in high-risk domains like incidents, you should prefer approved documents, show citations, avoid speculation, and add escalation notes if confidence is low.

The example answer mentioned initiating "incident reporting Form IR-02" and notifying the Airport Fire & Rescue Service. Also, they mention verifying with a duty supervisor if there's fuel leakage.

So, the question is specifically about an apron or runway incident. Apron incidents usually involve areas near gates or passenger bridges, while runway incidents might relate to aircraft operations on the runways. Both are high-risk, so grounding rules apply here.

Looking at the priority-based order: curated FAQ/approved answers come first. If there's an approved SOP or policy chunk related to incidents, that should be used. The example cites Emergency Response Manual v3.2, Section 4.1. So, perhaps the form and notification are guided by such a manual.

The answer needs to initiate the correct form (IR-02) and notify the right person (Airport Fire & Rescue). Also, include an escalation caveat if confidence is low. Since the user is asking carefully, maybe they want to ensure that if there's uncertainty, especially regarding fuel leakage which would escalate, the responder adds a note to verify with the duty supervisor.

Putting it all together: The answer should state initiating Form IR-02 and notifying Airport Fire & Rescue. If the incident involves fuel leakage, confirm with the duty supervisor first. So the escalation caveat is adding that verification step.
</think>

The correct procedure for an apron or runway incident is to initiate **incident reporting Form IR-02** and notify the **Airport Fire & Rescue Service** immediately. If there is any uncertainty—particularly if fuel leakage is involved—a confirmation with the *duty supervisor* must be added (**escalation caveat**). 

**Answer:**  
Initiate Incident Reporting (IR-02) form. Notify Airport Fire & Rescue Service first. If fuel leakage is suspected, verify with the duty supervisor prior to further action.
```
### qwen3.5:latest

- Wall time: 15.21 s
- Total duration: 15.20 s
- Load duration: 5.02 s
- Prompt tokens: 276
- Output tokens: 88
- Output speed: 22.63 tok/s

```text
The provided context does not contain specific information regarding which form to initiate or who to notify first for an apron or runway incident.

According to the grounding rules, when the available context is insufficient to answer a question about high-risk domains like airport incidents, I must state that the information is unknown rather than inventing facts. Therefore, based strictly on the provided text, I cannot determine the specific form number or the primary notification contact.
```
