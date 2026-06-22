1. Before starting any task, read progress/01-architecture-state.md,
   progress/02-decisions-log.md, and progress/07-known-issues.md in full.
2. Never re-decide something already recorded in 02-decisions-log.md without
   flagging the conflict explicitly in your response — don't silently override it.
3. After finishing any task: update 01-architecture-state.md with what now exists,
   append new entries to 02-decisions-log.md for any non-trivial choice you made,
   append a run entry to 06-test-log.md for any test you ran, and add/update
   entries in 07-known-issues.md for anything you deferred or noticed but didn't fix.
4. Never delete history from these files — append, or mark old entries superseded.
5. Keep entries short and factual. This is a machine-readable project memory, not
   a narrative.

6. frontend prompts read/write the four new files above in addition to the original
   backend files; progress/03-api-contracts.md is the frontend's single source of truth
   for request/response shapes; any conflict between this prompt series and that file
   must be logged in 02-decisions-log.md before proceeding, with the file winning.
