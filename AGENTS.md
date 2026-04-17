## Core Rule: Package Manager

The agent must use **pnpm** for all JavaScript/Node workflows.

### Mandatory commands

- Install dependencies: `pnpm install`
- Start dev server: `pnpm dev`
- Build project: `pnpm build`
- Start production server: `pnpm start`
- Run scripts/tests/lint: `pnpm <script>`

### Prohibited commands

- Do **not** use `npm install`, `npm run ...`, or `yarn ...`
- Do **not** switch package managers mid-task

## Execution Principles

- Implement work in priority order from `plan.md`
- Keep changes minimal, focused, and reversible
- Preserve existing behavior unless task requires changes
- Add clear error handling for new APIs
- Keep frontend responsive and compatible with current styling system

## Safety Rules

- Do not run destructive git commands unless explicitly requested
- Do not delete unrelated files
- Do not commit secrets or environment credentials
- Respect existing project structure and naming conventions

## Reporting Format (after each milestone)

For each completed milestone, report:

1. Files changed
2. Endpoints/components added
3. Validation performed
4. Known issues or follow-ups
5. Next step
