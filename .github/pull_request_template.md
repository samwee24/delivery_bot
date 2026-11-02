<!-- PR title = the squash commit: `type: YYYY-MM-DD what` (docs, ci, slam, tools, drivers, notes, fix) -->

## What changed

## How it was checked
<!-- Rule 6: every number travels with the command that produced it. Paste the Pi command and result, or say "docs only". -->

## Checklist
- [ ] `notes/notes.md` entry added at the top (append-only) if this was a lab run
- [ ] `docs/test_log.md` row added for any new measurement
- [ ] No `evidence/` file edited or deleted (new dated file instead)
- [ ] No `dry_run:=false`, GPIO write or `/cmd_vel` publisher added outside the motor node
