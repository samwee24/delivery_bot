# 08 GitHub settings

What is configured on `samwee24/delivery_bot` outside the repo files, and the exact
commands that set it, so it can be rebuilt. The workflow it supports is in
`AGENTS.md` (Git workflow). Applied: see the dated rows at the bottom.

## Repo settings

Squash merge only, head branch deleted after merge:

```bash
gh repo edit samwee24/delivery_bot --enable-squash-merge --enable-merge-commit=false \
  --enable-rebase-merge=false --delete-branch-on-merge
```

## Ruleset `main`

Pull request required (0 approvals, since there is one author), `build-and-test` and
`repo-rules` must pass, no force-push, no deletion, **no bypass actors** (admins
included). Define it from `docs/system/08_github_ruleset.json`:

```bash
gh api -X POST repos/samwee24/delivery_bot/rulesets --input docs/system/08_github_ruleset.json
```

Emergency exit: Settings → Rules → `main` → set enforcement to *Disabled*, push, set it
back to *Active*. Record why in `notes/notes.md`.

The older branch protection on `main` (required check `build-and-test`, admins not
enforced) is left in place; the ruleset is the stricter of the two.

## Applied

| Date | What | Command |
| --- | --- | --- |
