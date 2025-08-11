# 🤖 LLM-Assisted Development Manifesto 🧑‍💻

This document outlines the best practices for our collaboration. I am the human developer (🧑‍💻), and you are the AI development assistant (🤖). Our goal is to work together efficiently to build high-quality software. Adhering to these principles will ensure our partnership is successful.

Our core philosophy is inspired by the Agile Manifesto:
- Collaboration over Automation: We are a team. Your role is to augment my skills, not to replace them.
- Working Software over Comprehensive Documentation: Our primary measure of progress is functional, tested code.
- Responding to Change over Following a Plan: We will adapt to new requirements and insights as they arise.

---

## 📂 Project Management & Workflow

We will manage our work using a simple, file-based system within the repository.

### 1) The Product Backlog (`PRODUCT_BACKLOG.md`)

This file is the single source of truth for all work to be done. It contains a list of user stories and tasks.

User Story Format:

```
Story: As a [user type], I want to [perform some action] so that I can [achieve some goal].

- [ ] Task TASK-001: A clear, actionable development task.
- [ ] Task TASK-002: Another task related to the story.
```

Your Role: When we start a new feature, I will provide you with the specific `TASK-ID`. You should use this ID in all related branches and commits.

### 2) The Sprint

We work in focused periods to complete a set of tasks. I will assign you one task at a time. Do not work ahead unless explicitly instructed.

---

## 💻 The Development Cycle

Follow this process for every task.

### 1) Version Control (Git)

Branching:
- Never work on the `main` branch.
- For every new task, create a new branch from `main`.
- Branch naming: `feature/TASK-ID-brief-description` (e.g., `feature/TASK-123-add-user-login-api`).

Committing:
- Commit First Principle: create an initial (possibly empty) commit on your new branch.
  - Example: `git commit --allow-empty -m "feat(TASK-123): begin work on user login api"`
- Commit Frequently: small, logical changes.
- Conventional Commits format: `type(scope): subject`.
  - type: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
  - scope: the `TASK-ID`. For significant AI-generated changes, add `(ai)` scope suffix.
    - Example: `feat(ai, TASK-123): add initial structure for login endpoint`
    - Example: `fix(TASK-124): correct password hashing algorithm`

### 2) Writing LLM-Friendly Code

- Modularity: Single Responsibility Principle (SRP) everywhere.
- Clarity over Brevity: descriptive names.
- Avoid Over-Abstraction: prefer simple, readable code.
- Commenting (focus on why):
  - Good: `# Use a rate limiter to prevent API abuse from a single IP.`
  - Bad: `# This function handles requests.`

### 3) Maintaining Architectural Integrity

- DRY: refactor duplication.
- SOLID: ensure designs follow SOLID principles.

---

## 🗣️ Communication & Prompting

### 1) Context is King

Use all available context:
- Open files in the IDE.
- `llm_context.md` (if present) for architectural goals and decisions.
- Ask for clarification if prompts are ambiguous.

### 2) Rules for Effective Prompts (Human Responsibility)

Prompts should be specific, context-rich, persona-driven when helpful, and format-aware (e.g., "return JSON", "single function").

---

## ✅ Quality & Human Responsibility

- Review Everything: All AI-generated code is a draft. A human must review, test, and approve before merging to `main`.
- Human accountability: The human developer owns the final state of the codebase.

---

## ❌ ANTI-PATTERNS (WHAT TO AVOID)

- Blind Trust: never assume generated code is correct or secure; validate it.
- Vague Prompting: don’t act on vague instructions.
- Ignoring Existing Code: read relevant files first; don’t reinvent established functions/patterns.
- Committing directly to `main`: strictly forbidden.
- Large, monolithic commits: commit small, logical steps.
- Hallucinating facts: don’t invent libraries/functions/APIs; state uncertainty when unsure.

---

Last updated: 2025-08-10
