const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const dist = path.join(root, "dist");

const entries = [
  "index.html",
  "manifest.webmanifest",
  "sw.js",
  "assets",
  "vendor",
  "src"
];

fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist, { recursive: true });

function copyRecursive(srcPath, destPath) {
  const stats = fs.statSync(srcPath);
  if (stats.isDirectory()) {
    fs.mkdirSync(destPath, { recursive: true });
    fs.readdirSync(srcPath).forEach((entry) => {
      copyRecursive(path.join(srcPath, entry), path.join(destPath, entry));
    });
    return;
  }
  fs.copyFileSync(srcPath, destPath);
}

entries.forEach((entry) => {
  const srcPath = path.join(root, entry);
  const destPath = path.join(dist, entry);
  copyRecursive(srcPath, destPath);
});

console.log("Build complete: dist/");
