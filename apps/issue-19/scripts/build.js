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

async function copyRecursive(source, target) {
  const stat = await fs.stat(source);
  if (stat.isDirectory()) {
    await fs.mkdir(target, { recursive: true });
    const items = await fs.readdir(source);
    for (const item of items) {
      await copyRecursive(path.join(source, item), path.join(target, item));
    }
    return;
  }
  await fs.copyFile(source, target);
}

async function run() {
  await fs.rm(dist, { recursive: true, force: true });
  await fs.mkdir(dist, { recursive: true });

  for (const entry of entries) {
    await copyRecursive(path.join(root, entry), path.join(dist, entry));
  }

  console.log(`Build complete: ${dist}`);
}

run().catch(error => {
  console.error(error);
  process.exit(1);
});
