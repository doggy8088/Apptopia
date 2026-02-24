import { rm, mkdir, readdir, copyFile, stat } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(process.cwd());
const srcDir = path.join(root, 'src');
const distDir = path.join(root, 'dist');

async function copyDir(from, to) {
  await mkdir(to, { recursive: true });
  const entries = await readdir(from, { withFileTypes: true });
  for (const entry of entries) {
    const fromPath = path.join(from, entry.name);
    const toPath = path.join(to, entry.name);
    if (entry.isDirectory()) {
      await copyDir(fromPath, toPath);
    } else if (entry.isFile()) {
      await copyFile(fromPath, toPath);
    } else if ((await stat(fromPath)).isFile()) {
      await copyFile(fromPath, toPath);
    }
  }
}

async function build() {
  await rm(distDir, { recursive: true, force: true });
  await copyDir(srcDir, distDir);
  console.log('Build complete:', distDir);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
