# hw2-yuliang

This repository contains my Homework 2 project for the business writing LLM assignment.

## Folder structure

- `README.md`
- `app.py`
- `prompts.md`
- `eval_set.json`
- `report.md`

## Project overview

This project focuses on an HR onboarding workflow. The system takes rough onboarding notes and turns them into a polished follow-up email for a new employee.

## Video Link

[Homework video](https://youtu.be/u4nWzEO6gqw)

## How to run

Set your API key:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

Preview the prompt:

```bash
python3 app.py --dry-run --case-id case_01 --prompt-version v3
```

Run the app:

```bash
python3 app.py --prompt-version v3
```
