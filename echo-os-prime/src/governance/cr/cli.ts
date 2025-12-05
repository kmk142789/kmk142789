#!/usr/bin/env ts-node
import fs from "fs";
import path from "path";
import YAML from "yaml";
import { submitChangeRequest } from "./submit";
import { ChangeRequest } from "./types";

const [, , command, filePath] = process.argv;

if (!command || command === "--help" || command === "-h") {
  console.log("Usage: pnpm governance:cr submit <path/to/change-request.yaml>");
  process.exit(0);
}

if (command !== "submit") {
  console.error(`Unknown command: ${command}`);
  process.exit(1);
}

if (!filePath) {
  console.error("Please provide a path to the change request YAML file.");
  process.exit(1);
}

const absolutePath = path.resolve(process.cwd(), filePath);
if (!fs.existsSync(absolutePath)) {
  console.error(`Unable to find file at ${absolutePath}`);
  process.exit(1);
}

const raw = fs.readFileSync(absolutePath, "utf-8");
const data = YAML.parse(raw) as ChangeRequest;

const result = submitChangeRequest(data);

const heading = `Change Request ${data.id ?? "(unnamed)"}`;
console.log(heading);
console.log("=".repeat(heading.length));
console.log(`Decision: ${result.decision}`);

if (result.reasons.length > 0) {
  console.log("Reasons:");
  result.reasons.forEach((reason) => console.log(` - ${reason}`));
} else {
  console.log("Reasons: none (validated successfully)");
}
