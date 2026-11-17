<!-- mino-routing:start -->
## Mino routing policy

This block is managed by the installed `mino` skill. Do not edit it by hand; re-run `scripts/install_routing_policy.py --apply` to refresh it.

Treat a request as a Mino task when it names Mino, Mino Scout, Mino Nexus, or Mino MCP, or when it asks to inspect, operate, screenshot, automate, debug, or verify an Android, iOS, Web, browser, or desktop target for testing/QA. This block does not change routing for ordinary desktop work unrelated to testing.

Within a Mino task:

- For Mino/Nexus control-plane operations, use the Mino MCP server only. Do not substitute a generic browser, database, shell, or another MCP server for equivalent Mino operations.
- For local Scout lifecycle, status, probe, and repository checks, use the `mino-scout` CLI. Do not infer local Scout state from another process or service.
- On the first Mino task in each new session, read the installed `mino` skill and run its read-only `scripts/check_updates.py` before substantive work. If a check is `unknown`, report it as unknown, not as up to date.
- If a Mino skill update is available, update it before continuing and tell the user whether a new session is required. If a Scout update is available, use only the fixed `build_id` and `release_tag`, explain the service/interruption impact, and obtain user confirmation before updating.
- Verify the installed Mino routing block in this file. If it is missing or outdated, explain why persistent routing matters and ask before writing it.
- After the update and routing checks, call MCP `agent_guide` and follow the returned routing contract.
- For target Android, iOS, Web, browser, and desktop UI inspection or interaction, write or use a Scout case script and submit it through Mino MCP `case_run`. Screenshots, hierarchy/control trees, locators, taps, typing, and UI evidence must come from the Scout execution for that task.
- Do not silently use platform Computer Use, Browser, Playwright, adb, Appium, WDA, pywinauto, or another desktop-automation tool for target UI work. A quick manual probe is also prohibited when it would bypass Scout evidence.
- Fall back to another tool only when the user explicitly requests that tool, or after checking Mino MCP/Scout and explaining a concrete unavailability to the user. If Mino is unavailable, use the `onboarding` skill to repair it instead of continuing the same test through another UI tool.
- A successful tool call, accepted task, or completed gesture is not a test pass. Report a pass only when the intended assertion and evidence exist.
<!-- mino-routing:end -->
