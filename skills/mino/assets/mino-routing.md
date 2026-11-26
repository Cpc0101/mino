<!-- mino-routing:start -->
## Mino routing policy

This block is managed by the installed `mino` skill. Do not edit it by hand; re-run `scripts/install_routing_policy.py --apply` to refresh it.

The agent must classify the current user request by intent, not by product names or previous turns. Activate the Mino testing workflow only for an explicit QA/testing request: analyzing source cases, authoring or running test scripts, or inspecting/interacting with a target to establish a test assertion and evidence. Merely mentioning Mino, reading code, reviewing/fixing infrastructure, building/releasing/deploying software, domain/TLS operations, general product questions, and ordinary desktop work do not activate a testing workflow or require a test board. If intent is genuinely ambiguous, ask a short clarification instead of creating a workflow. Reclassify when the user changes tasks.

Mino/Nexus control-plane operations still use Mino MCP, and local Scout lifecycle/status uses mino-scout CLI, even outside testing; read-only diagnostics do not by themselves create a business test task. Ordinary repository edits, shell checks and deployment use their normal tools.

Within an explicitly classified Mino testing task:

- For Mino/Nexus control-plane operations, use the Mino MCP server only. Do not substitute a generic browser, database, shell, or another MCP server for equivalent Mino operations.
- When a Feishu document or spreadsheet contains the source cases, read it through Mino MCP `cli_query(plugin="feishu")`: use `wiki +node-get`, then `sheets +sheet-list`, then `sheets +cells-get`. Do not use Computer Use, browser screenshots, or copied visible fragments as a substitute for Feishu CLI content. If the CLI is unavailable or returns an incomplete range, report the concrete failure instead of guessing.
- For “write all cases”, “run all cases”, “continue testing”, or equivalent requests, first machine-read the original source and lock the complete case-ID list as `agent_workflow_init.expected_units`. Process it in batches from `coverage.next_units`; never infer the source total from current `tests/` files, `case_list`, or `case_run.script_targets[].case_ids=[]`. Only `coverage.all_implemented=true` proves all scripts are written, and only `coverage.all_verified=true` proves the whole set formally passed.
- For local Scout lifecycle, status, probe, and repository checks, use the `mino-scout` CLI. Do not infer local Scout state from another process or service.
- On the first Mino task in each new session, read the installed `mino` skill and run its read-only `scripts/check_updates.py` before substantive work. If a check is `unknown`, report it as unknown, not as up to date.
- Never install or update the Mino skill, Mino Scout, or this routing block without explicit user confirmation. Explain the impact first, then wait.
- When preflight returns `consent_required=true`, use each `consent_actions` item's `question` and `impact` to ask the user. After approval, execute the action yourself; never require the user to copy commands or edit `AGENTS.md` manually.
- If Scout is missing, ask before requesting an install token. After approval, follow the Mino MCP `scout_install_token` flow and execute the matching local install request; never expose the one-time token.
- If a Mino skill update is available, explain that a new session may be required and ask before updating. If a Scout update is available, use only the fixed `build_id` and `release_tag`, explain the service/interruption impact, and ask before updating.
- Verify the installed Mino routing block in this file. If it is missing or outdated, explain why persistent routing matters and ask before writing it.
- After the update and routing checks, call MCP `agent_guide` and follow the returned routing contract.
- For target Android, iOS, Web, browser, and desktop UI inspection or interaction, use Mino MCP `debug_case` / `debug_case_execute` for local authoring, and `case_run` for formal execution. Debugging binds the local authoring workspace without Git checkout and retains the device between fragments; remote Scout nodes are only for formal execution. Screenshots, hierarchy/control trees, locators, taps, typing, and UI evidence must come from the Scout execution for that task.
- Do not silently use platform Computer Use, Browser, Playwright, adb, Appium, WDA, pywinauto, or another desktop-automation tool for target UI work. A quick manual probe is also prohibited when it would bypass Scout evidence.
- Fall back to another tool only when the user explicitly requests that tool, or after checking Mino MCP/Scout and explaining a concrete unavailability to the user. If Mino is unavailable, use the `onboarding` skill to repair it instead of continuing the same test through another UI tool.
- A successful tool call, accepted task, or completed gesture is not a test pass. Report a pass only when the intended assertion and evidence exist.
<!-- mino-routing:end -->
