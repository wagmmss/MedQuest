import { readdir, stat } from "node:fs/promises";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname.replace(/^\/(.:)/, "$1");
const chunksDir = join(root, ".next", "static", "chunks");
const budgets = {
  totalJavaScript: 2_300_000,
  largestChunk: 450_000,
  serviceWorker: 250_000,
};


async function filesUnder(directory) {
  const output = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) output.push(...await filesUnder(path));
    else output.push(path);
  }
  return output;
}

const chunks = (await filesUnder(chunksDir)).filter(file => file.endsWith(".js"));
const sizes = await Promise.all(chunks.map(async file => ({ file, size: (await stat(file)).size })));
const totalJavaScript = sizes.reduce((sum, item) => sum + item.size, 0);
const largest = sizes.sort((a, b) => b.size - a.size)[0];
const serviceWorkerPath = join(root, "public", "sw.js");
let serviceWorker = null;
try {
  serviceWorker = (await stat(serviceWorkerPath)).size;
} catch (error) {
  // O next-pwa gera este arquivo durante `next build`. No pre-push rápido ele
  // pode ainda não existir, pois não é mais um artefato versionado.
  if (error?.code !== "ENOENT") throw error;
}
const failures = [];
if (totalJavaScript > budgets.totalJavaScript) failures.push(`JS total ${totalJavaScript} > ${budgets.totalJavaScript}`);
if (largest.size > budgets.largestChunk) failures.push(`largest chunk ${largest.size} > ${budgets.largestChunk}`);
if (serviceWorker !== null && serviceWorker > budgets.serviceWorker) failures.push(`service worker ${serviceWorker} > ${budgets.serviceWorker}`);

console.log(JSON.stringify({
  totalJavaScript,
  largestChunk: { name: largest.file.replace(root, ""), bytes: largest.size },
  serviceWorker,
  serviceWorkerStatus: serviceWorker === null ? "not-generated" : "measured",
  budgets,
}, null, 2));
if (failures.length) throw new Error(`Performance budget exceeded: ${failures.join("; ")}`);
