import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import assert from "node:assert/strict";
import { Files } from "files-sdk";
import { neon } from "files-sdk/neon";

const envFile = existsSync(".env") ? ".env" : ".env.local";
if (existsSync(envFile)) process.loadEnvFile(envFile);

async function main() {
  for (const key of ["AWS_ENDPOINT_URL_S3", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]) {
    assert(process.env[key], `Missing ${key}; run neon deploy first.`);
  }
  const bucket = process.env.NEON_STORAGE_BUCKET || "uploads";
  const files = new Files({ adapter: neon({ bucket }), timeout: 30000, retries: 2 });
  const prefix = `verification/${randomUUID()}/`;
  const key = prefix + "hello.txt";
  const content = await readFile(new URL("../fixtures/neon-upload-verification.txt", import.meta.url));
  await files.upload(key, content, { contentType: "text/plain", cacheControl: "private, no-store" });
  console.log(`PASS: uploaded ${content.byteLength} bytes to private bucket ${bucket}`);
  const listing = await files.list({ prefix });
  assert(listing.items.some((file) => file.key === key), "Uploaded file is missing from the listing.");
  console.log("Bucket listing:");
  for (const file of listing.items) console.log(`  ${file.key} (${file.size} bytes)`);
  const downloaded = await files.download(key);
  const text = await downloaded.text();
  assert.equal(text, content.toString("utf8"), "Downloaded content differs from the local file.");
  console.log("PASS: downloaded content matches the local text file.");
  console.log("File contents:\n" + text);
}
main().catch((error) => {
  console.error(`Storage verification failed: ${error.name}${error.code ? ` (${error.code})` : ""}`);
  process.exitCode = 1;
});
