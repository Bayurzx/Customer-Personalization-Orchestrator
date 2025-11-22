---
name: "Update Roadmap After Task Completion"
description: "Automatically update the project roadmap when any task is marked complete"
trigger: "on_message_send"
enabled: true
---

# Roadmap Update Hook

## Trigger Condition
When a message contains task completion indicators:
- "Task X.Y: Complete" or "✅ Complete" 
- Checkbox changes from `[-]` to `[x]` in tasks.md
- "successfully completed" or "task finished"

## Action
Send this message to ensure roadmap update:

```
🔄 ROADMAP UPDATE REQUIRED

Task completion detected. Please update .kiro/steering/roadmap.md with:

1. **Task Status**: Mark as ✅ Complete with key achievement
2. **Lessons Learned**: Document any mistakes, solutions, or insights from this task
3. **Update Risks**: Adjust upcoming task risks based on new learnings  
4. **Validate Patterns**: Confirm or update success patterns
5. **Update Metrics**: Increment task completion count and update timeline

Use this template:

#### Task X.Y: [Task Name]
- **Status**: ✅ Complete
- **Key Achievement**: [Main accomplishment]
- **Lessons**:
  - [Key insight or mistake to avoid]
  - [Technical learning]
  - [Process improvement]

Then update:
- Task completion count in Project Health Metrics
- Last Updated date
- Current Status
- Next Update target

This is MANDATORY for project continuity.
```

## Validation
After update, verify:
- [ ] Task marked complete in roadmap
- [ ] Lessons documented
- [ ] Metrics updated
- [ ] Date updated