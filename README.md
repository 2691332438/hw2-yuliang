# hw2-yuliang

This repository contains my Homework 2 project for the business writing LLM assignment.

## Folder structure

- `README.md`
- `app.py`
- `prompts.md`
- `eval_set.json`
- `report.md`
- `outputs/`

## Project overview

This project focuses on a business writing workflow: summarizing data analysis findings into stakeholder updates. The system takes rough analysis notes, key metrics, trends, and business observations and turns them into a polished written update for managers or other non-technical stakeholders.

## Video Link

https://youtu.be/rGnVj-JH1Xs

## How to run

Set your API key:

```bash
export GROQ_API_KEY="your_api_key_here"
```

Preview the prompt:

```bash
python3 app.py --provider groq --dry-run --case-id case_01_normal_weekly_sales --prompt-version v3
```

Run the app:

```bash
python3 app.py --provider groq --prompt-version v3
```

Sample generated outputs are saved in `outputs/`.
