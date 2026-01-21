# dot-claude-dev

Story-Driven Development workflow for Claude Code. A collection of skills, rules, and commands that enable TDD/PLAN-based development with automatic task classification.

## Overview

This repository provides a structured development workflow that:

1. **Converts user stories to tasks** with automatic TDD/PLAN classification
2. **Executes tasks** using the appropriate workflow (TDD for logic, PLAN for UI)
3. **Captures learnings** and proposes skill/rule improvements

## Installation

Copy the `.claude` directory to your project:

```bash
# Clone this repository
git clone https://github.com/ryryo/dot-claude-dev.git

# Copy .claude to your project
cp -r dot-claude-dev/.claude /path/to/your-project/

# Or symlink for automatic updates
ln -s /path/to/dot-claude-dev/.claude /path/to/your-project/.claude
```

## Usage

### 1. Start with a User Story

```bash
# In your project directory with Claude Code
/dev:story
```

Enter your user story when prompted. The skill will:
- Analyze the story
- Decompose it into tasks
- Classify each task as TDD or PLAN
- Generate `TODO.md` with labeled tasks

### 2. Execute Tasks

The `dev:developing` skill automatically selects the appropriate workflow:

**TDD Workflow** (for business logic, APIs, data processing):
```
RED → GREEN → REFACTOR → REVIEW → CHECK → COMMIT
```

**PLAN Workflow** (for UI/UX, visual elements):
```
IMPL → AUTO (agent-browser verification) → CHECK → COMMIT
```

### 3. Capture Feedback

```bash
/dev:feedback
```

After implementation, this skill:
- Updates `DESIGN.md` with learnings
- Detects recurring patterns
- Proposes skill/rule improvements

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Story-Driven Development                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. /dev:story                                              │
│     └── Story → TODO.md (with [TDD]/[PLAN] labels)         │
│                                                             │
│  2. dev:developing                                          │
│     ├── [TDD] RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT       │
│     └── [PLAN] IMPL→AUTO→CHECK→COMMIT                      │
│                                                             │
│  3. /dev:feedback                                           │
│     └── DESIGN.md update → Pattern detection → Improvement │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Structure

```
.claude/
├── skills/
│   ├── dev/
│   │   ├── story-to-tasks/   # Story → TODO.md conversion
│   │   ├── developing/       # Task execution (TDD/PLAN)
│   │   └── feedback/         # Learning capture
│   └── meta-skill-creator/   # Skill creation/improvement
├── rules/
│   ├── workflow/             # TDD/PLAN workflow rules
│   └── languages/            # Language-specific coding rules
└── commands/
    └── dev/                  # Shortcut commands
```

## Supported Languages

| Language | Coding | Testing | Design |
|----------|--------|---------|--------|
| TypeScript | ✅ | ✅ | - |
| React | ✅ | ✅ | ✅ |
| JavaScript | ✅ | ✅ | - |
| Python | ✅ | ✅ | - |
| PHP | ✅ | ✅ | - |
| HTML/CSS | ✅ | ✅ | ✅ |

## Key Concepts

### TDD Classification
Tasks are classified as TDD when:
- Input/output is clearly definable
- Can be verified with assertions
- Logic layer (validation, calculation, transformation)

### PLAN Classification
Tasks are classified as PLAN when:
- Visual confirmation is needed
- UX/UI judgment is involved
- Presentation layer (components, layouts, animations)

### DESIGN.md
A feature-specific specification document that accumulates:
- Implementation decisions
- Learnings from development
- Patterns discovered

## License

MIT
