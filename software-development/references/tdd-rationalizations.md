# TDD Rationalizations Reference

> Shared across: `test-driven-development`, `systematic-debugging`, `code-review`

## Common Rationalizations Table

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is technical debt. |
| "Keep as reference, write tests first" | You'll adapt it. That's testing after. Delete means delete. |
| "Need to explore first" | Fine. Throw away exploration, start with TDD. |
| "Test hard = design unclear" | Listen to the test. Hard to test = hard to use. |
| "TDD will slow me down" | TDD faster than debugging. Pragmatic = test-first. |
| "Manual test faster" | Manual doesn't prove edge cases. You'll re-test every change. |
| "Existing code has no tests" | You're improving it. Add tests for the code you touch. |

## Debugging Rationalizations (Additional)

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Code Review Rationalizations (Additional)

| Excuse | Reality |
|--------|---------|
| "Quick fix for now, investigate later" | Never happens. Technical debt accumulates. |
| "Just try changing X and see if it works" | Guessing without loop is the failure mode. |
| "Add multiple changes, run tests" | Can't isolate what fixed it. |
| "Skip the test, I'll manually verify" | Manual doesn't re-run. Regressions slip. |
| "It's probably X, let me fix that" | Probability ≠ evidence. |
| "I don't fully understand but this might work" | Hope is not a strategy. |
| "Pattern says X but I'll adapt it differently" | Partial understanding = bugs. |
| "Here are the main problems: [lists fixes]" | Solutions before investigation = symptom fixing. |