import { promises as fs } from "node:fs";
import path from "node:path";

const root = path.resolve(process.cwd());
const dist = path.join(root, "dist");

const entries = ["index.html", "manifest.webmanifest", "sw.js", "assets", "src"];

async function collectFiles(dir, baseDir) {
  const items = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory()) {
      files.push(...(await collectFiles(fullPath, baseDir)));
    } else if (item.isFile()) {
      const relativePath = path.relative(baseDir, fullPath).split(path.sep).join("/");
      files.push(`./${relativePath}`);
    }
  }
  return files;
}

async function updateServiceWorkerAssets() {
  const swPath = path.join(dist, "sw.js");
  const assets = ["./", ...(await collectFiles(dist, dist)).sort()];
  const swSource = await fs.readFile(swPath, "utf8");
  const assetsLiteral = `const ASSETS = ${JSON.stringify(assets, null, 2)};`;
  const swUpdated = swSource.replace(/const ASSETS = \\[[\\s\\S]*?\\];/, assetsLiteral);
  await fs.writeFile(swPath, swUpdated);
}

async function run() {
  await fs.rm(dist, { recursive: true, force: true });
  await fs.mkdir(dist, { recursive: true });

  for (const entry of entries) {
    await fs.cp(path.join(root, entry), path.join(dist, entry), { recursive: true });
  }

  await updateServiceWorkerAssets();

  console.log(`Build complete: ${dist}`);
}

run().catch(error => {
  console.error(error);
  process.exit(1);
});
