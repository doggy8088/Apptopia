import { promises as fs } from "node:fs";
import path from "node:path";

const root = path.resolve(process.cwd());
const dist = path.join(root, "dist");

const entries = [
  "index.html",
  "manifest.webmanifest",
  "sw.js",
  "assets",
  "src"
];

async function run() {
  await fs.rm(dist, { recursive: true, force: true });
  await fs.mkdir(dist, { recursive: true });

  for (const entry of entries) {
    await fs.cp(path.join(root, entry), path.join(dist, entry), { recursive: true });
  }

  console.log(`Build complete: ${dist}`);
}

run().catch(error => {
  console.error(error);
  process.exit(1);
});
