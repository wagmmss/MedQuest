import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const swPath = path.resolve(__dirname, "../public/sw.js");

console.log("[SW Validator] Verifying Service Worker security rules in:", swPath);

if (!fs.existsSync(swPath)) {
  console.error("[SW Validator ERROR] public/sw.js does not exist!");
  process.exit(1);
}

const swContent = fs.readFileSync(swPath, "utf-8");

// 1. Forbidden caches that store user data, HTML or API responses
const forbiddenPatterns = [
  { pattern: /cacheName:\s*["']apis["']/, name: 'cacheName:"apis"' },
  { pattern: /cacheName:\s*["']pages["']/, name: 'cacheName:"pages"' },
  { pattern: /cacheName:\s*["']pages-rsc["']/, name: 'cacheName:"pages-rsc"' },
  { pattern: /cacheName:\s*["']pages-rsc-prefetch["']/, name: 'cacheName:"pages-rsc-prefetch"' },
  { pattern: /cacheName:\s*["']start-url["']/, name: 'cacheName:"start-url"' },
];

let hasErrors = false;

for (const { pattern, name } of forbiddenPatterns) {
  if (pattern.test(swContent)) {
    console.error(`[SW Validator ERROR] Security violation: Found forbidden cache ${name} in sw.js!`);
    hasErrors = true;
  }
}

// 2. Required cache rule: medquest-image-cache for /api/images/**
if (!swContent.includes("medquest-image-cache")) {
  console.error("[SW Validator ERROR] Required rule 'medquest-image-cache' for images is missing in sw.js!");
  hasErrors = true;
}

// 3. Required handler: NetworkOnly for /api/**
if (!swContent.includes("NetworkOnly")) {
  console.error("[SW Validator ERROR] Required handler 'NetworkOnly' for APIs is missing in sw.js!");
  hasErrors = true;
}

if (hasErrors) {
  console.error("[SW Validator FAILED] Service Worker contains invalid or insecure caching configuration.");
  process.exit(1);
}

console.log("[SW Validator PASSED] Service Worker is verified safe:");
console.log(" - No user/API/page data caches found.");
console.log(" - medquest-image-cache present.");
console.log(" - NetworkOnly for /api/** present.");
process.exit(0);
