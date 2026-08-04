import { readFile } from "node:fs/promises";

const load = async (name) => JSON.parse(await readFile(new URL(`../src/locales/${name}.json`, import.meta.url), "utf8"));
const flatten = (value, prefix = "", output = new Map()) => {
  for (const [key, child] of Object.entries(value)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof child === "string") output.set(path, child);
    else if (child && typeof child === "object" && !Array.isArray(child)) flatten(child, path, output);
    else throw new Error(`Invalid translation value at ${path}`);
  }
  return output;
};

const [en, ms] = await Promise.all([load("en"), load("ms")]);
const english = flatten(en);
const malay = flatten(ms);
const missing = [...english.keys()].filter((key) => !malay.has(key));
const extra = [...malay.keys()].filter((key) => !english.has(key));
const empty = [...malay.entries()].filter(([, value]) => !value.trim()).map(([key]) => key);
for (const required of ["common.language", "common.english", "common.malay"]) {
  if (!english.has(required) || !malay.has(required)) missing.push(required);
}
if (missing.length || extra.length || empty.length) {
  throw new Error(`Locale validation failed\nMissing: ${missing.join(", ") || "none"}\nExtra: ${extra.join(", ") || "none"}\nEmpty: ${empty.join(", ") || "none"}`);
}
console.log(`Locale dictionaries aligned: ${english.size} strings per language.`);
