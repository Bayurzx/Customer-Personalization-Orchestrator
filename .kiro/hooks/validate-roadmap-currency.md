---
name: "Validate Roadmap Currency"
description: "Check if roadmap is up-to-date before starting new tasks"
trigger: "on_session_start"
enabled: true
---

# Roadmap Currency Validation

## Purpose
Ensure the roadmap is current before beginning any new work.

## Validation Checks
Before starting any new task, verify:

1. **Last Updated Date**: Should be within 24 hours of current date
2. **Task Count Accuracy**: Completed tasks in roadmap match tasks.md
3. **Current Status**: Reflects actual project state

## Action on Validation Failure
If roadmap is outdated, send this message:

```
⚠️ ROADMAP OUT OF DATE

The project roadmap (.kiro/steering/roadmap.md) appears outdated:
- Last updated: [date from file]
- Current date: [today]
- Gap: [X] days

Please update the roadmap before proceeding with new tasks to ensure:
- Previous lessons are applied
- Success patterns are followed  
- Known risks are mitigated
- Project metrics are accurate

This prevents repeating mistakes and maintains project quality.
```

## Success Message
If roadmap is current:
```
✅ Roadmap is current - proceeding with established lessons and patterns.
```