# Report

## Business use case

I chose a business writing workflow called summarizing data analysis findings into stakeholder updates. This is a realistic workflow because data analysts often need to translate raw metrics, trends, anomalies, and risks into short written updates for managers or other non-technical stakeholders. The user is a data analyst, the input is rough analysis notes, and the output is a polished business update or summary email written in clear, professional language. This task is valuable to automate or partially automate because it happens frequently, follows a repeatable pattern, and takes time that analysts could otherwise spend on higher-value analysis.

## Model choice

I used Groq with the model `llama-3.3-70b-versatile`. I chose it because I had working API access and it was easy to call from a simple Python script. For this assignment, that made it practical to build a reproducible command-line prototype that could generate stakeholder updates from the evaluation set. I did not run a full comparison across multiple models, so my conclusions are limited to this one model and prompt design.

## Baseline vs. final design

My baseline design used a very short prompt that simply asked for a stakeholder update from rough notes. That version was likely to be too vague because it did not explicitly require key metrics, risks, audience awareness, or limitations. In revision 1, I added instructions to include important metrics, trends, and risks, use non-technical language, avoid inventing facts, and include a recommendation when available. In revision 2, I made the system more controlled by requiring a subject line, focusing on anomalies and limitations, and explicitly telling the model not to exaggerate or make unsupported conclusions.

The final design is better aligned with the evaluation set because the evaluation cases include sparse inputs, data quality issues, and correlation-versus-causation risks. I ran the final prompt on one normal case and the output was strong in several ways: it included the main metrics, used a professional subject line, and ended with a clear recommendation. However, it also showed a real weakness by ending with `[Your Name]`, which is not appropriate for a final stakeholder message unless a human edits it first. The final prompt is therefore better than the baseline for structure and clarity, but it still produces draft-quality output rather than send-ready output.

## Where the prototype still fails or needs human review

This prototype still needs human review when the source notes are incomplete, when the data may be unreliable, or when the findings are correlational rather than causal. In those situations, an LLM may still produce writing that sounds confident even when the underlying evidence is weak. The evaluation set includes cases designed to catch exactly those risks, especially cases involving conflicting dashboards, tracking changes, and unsupported causal interpretations. Even with a stronger prompt, a human reviewer should still verify that the final message does not overstate what the analysis proves.

## Deployment recommendation

I would recommend this workflow only as a draft-generation tool, not as a fully autonomous system. It could be useful if a data analyst reviews the output before it is sent, especially for routine weekly or monthly updates with clear metrics. I would not recommend deploying it without review controls for higher-risk cases involving data quality issues, uncertain attribution, or strategic decisions. A responsible deployment would require a stable evaluation set, regular prompt testing, and human approval before stakeholder communication is sent.

## Honesty note

The repository includes a reusable evaluation set and three prompt versions, and I successfully ran the final prompt on at least one real case using the Groq API. I have not yet run a full side-by-side evaluation of every prompt version on every case, so the comparison in this report is partly based on the prompt design itself and partly based on the sample output I observed. I am keeping that limitation explicit rather than overstating the amount of evidence I collected.
