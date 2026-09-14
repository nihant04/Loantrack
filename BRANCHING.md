# Git Branching Strategy

LoanTrack uses a protected-style Git workflow with `main` as the stable, deployable branch and `develop` as the integration branch.

## Branches

- `main` - production/stable branch. It contains only working, reviewed changes.
- `develop` - integration branch for completed feature work.
- `feature/*` - short-lived development branches created from `develop` for each assignment part.

The project uses separate feature branches for the major assignment parts:

- `feature/application`
- `feature/database`
- `feature/docker`
- `feature/kubernetes`

## Pull Request Workflow

Development work is completed on a `feature/*` branch and submitted through a Pull Request targeting `develop`. Each Pull Request contains a meaningful description of the implemented change and includes a review comment on the author's own diff to document verification.

After the feature is reviewed and verified, the Pull Request is merged into `develop`. Feature branches are retained because the assignment requires the complete branch history to remain available.

`develop` is periodically merged into `main` only when the complete project is in a working, deployable state. Direct development commits to `main` and `develop` are avoided.

## Commit and Release Strategy

Commits describe actual project changes rather than artificial history. The repository retains the complete commit and merge history without squashing or rewriting it.

Annotated release tags are used for assignment milestones:

- `v1.0.0` - Docker/Compose implementation working.
- `v1.1.0` - Kubernetes implementation working.

This workflow keeps the stable branch deployable while allowing individual assignment components to be developed and integrated independently.
