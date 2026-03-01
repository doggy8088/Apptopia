const fs = require("fs");
const path = require("path");
const assert = require("assert");

const root = path.resolve(__dirname, "..");

function read(file) {
  return fs.readFileSync(path.join(root, file), "utf8");
}

const indexHtml = read("index.html");
assert.ok(indexHtml.includes("id=\"roomCanvas\""), "index.html should include roomCanvas");
assert.ok(indexHtml.includes("id=\"editorModal\""), "index.html should include editor modal");
assert.ok(indexHtml.includes("manifest.webmanifest"), "index.html should link manifest");

const manifest = JSON.parse(read("manifest.webmanifest"));
assert.strictEqual(manifest.display, "standalone");
assert.ok(manifest.icons && manifest.icons.length > 0, "manifest should have icons");

const sw = read("sw.js");
assert.ok(sw.includes("pixelnest-v1"), "sw.js should define cache name");
assert.ok(sw.includes("vendor/jszip.min.js"), "sw.js should cache JSZip");

const appJs = read("src/app.js");
assert.ok(appJs.includes("autoSortInbox"), "app.js should include auto-sort logic");
assert.ok(appJs.includes("exportZip"), "app.js should include export logic");

console.log("All checks passed.");
