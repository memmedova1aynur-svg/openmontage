import { existsSync } from "fs";
import { Config } from "@remotion/cli/config";

// Use a local Chromium when Remotion's own headless shell can't be downloaded
// (sandboxed or offline machines). REMOTION_BROWSER_EXECUTABLE wins; otherwise
// fall back to the Playwright build that ships in some cloud containers.
const PLAYWRIGHT_SHELL =
  "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
const browser =
  process.env.REMOTION_BROWSER_EXECUTABLE ||
  (existsSync(PLAYWRIGHT_SHELL) ? PLAYWRIGHT_SHELL : null);

if (browser) {
  Config.setBrowserExecutable(browser);
}
