import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
const venv = process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python";
const python = process.env.PYTHON || (existsSync(venv) ? venv : "python");
for (const args of [
  ["manage.py", "check", "--settings=config.settings.build"],
  ["manage.py", "makemigrations", "--check", "--dry-run", "--settings=config.settings.testing"],
  ["manage.py", "collectstatic", "--noinput", "--settings=config.settings.build"],
]) {
  const result = spawnSync(python, args, { stdio: "inherit", env: process.env });
  if (result.error) { console.error("Python could not start:", result.error.code); process.exit(1); }
  if (result.status !== 0) process.exit(result.status || 1);
}
console.log("TalentBridge Django build passed.");
