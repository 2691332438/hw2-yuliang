# Report

## Business use case

I chose a business writing workflow called summarizing data analysis findings into stakeholder updates. This is a realistic workflow because data analysts often need to translate raw metrics, trends, anomalies, and risks into short written updates for managers or other non-technical stakeholders. The user is a data analyst, the input is rough analysis notes, and the output is a polished business update or summary email written in clear, professional language. This task is valuable to automate or partially automate because it happens frequently, follows a repeatable pattern, and takes time that analysts could otherwise spend on higher-value analysis.

## Model choice

I chose `gemini-2.5-flash` because it is easy to access through Google AI Studio and fits the assignment's recommendation to use a simple, reproducible API workflow. It is also a practical model for a lightweight prototype because it is fast and designed for general text generation. I did not compare multiple live models in this environment because no API key was available during this setup session, so a fair cross-model comparison would need to be done later with the same evaluation set.

## Baseline vs. final design

My baseline design used a very short prompt that simply asked for a stakeholder update from rough notes. That version was likely to be too vague because it did not explicitly require key metrics, risks, audience awareness, or limitations. In revision 1, I added instructions to include important metrics, trends, and risks, use non-technical language, avoid inventing facts, and include a recommendation when available. In revision 2, I made the system more controlled by requiring a subject line, focusing on anomalies and limitations, and explicitly telling the model not to exaggerate or make unsupported conclusions.

The final design is better aligned with the evaluation set because the evaluation cases include sparse inputs, data quality issues, and correlation-versus-causation risks. The final prompt should perform better on those cases because it is much clearer about caution, limitations, and stakeholder-facing clarity. The main tradeoff is that the final output may be a little more formulaic than the baseline, but that is acceptable for this workflow.

## Where the prototype still fails or needs human review

This prototype still needs human review when the source notes are incomplete, when the data may be unreliable, or when the findings are correlational rather than causal. In those situations, an LLM may still produce writing that sounds confident even when the underlying evidence is weak. The evaluation set includes cases designed to catch exactly those risks, especially cases involving conflicting dashboards, tracking changes, and unsupported causal interpretations. Even with a stronger prompt, a human reviewer should still verify that the final message does not overstate what the analysis proves.

## Deployment recommendation

I would recommend this workflow only as a draft-generation tool, not as a fully autonomous system. It could be useful if a data analyst reviews the output before it is sent, especially for routine weekly or monthly updates with clear metrics. I would not recommend deploying it without review controls for higher-risk cases involving data quality issues, uncertain attribution, or strategic decisions. A responsible deployment would require a stable evaluation set, regular prompt testing, and human approval before stakeholder communication is sent.

## Honesty note

The repository includes a reusable evaluation set and three prompt versions, but live evidence from model outputs still needs to be collected with a real API key. That means this report reflects the intended comparison and evaluation design honestly, without inventing results that were not actually run in this environment.
