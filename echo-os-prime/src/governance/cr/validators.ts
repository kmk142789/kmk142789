import fs from "fs";
import path from "path";
import YAML from "yaml";
import Ajv, { ValidateFunction } from "ajv";
import addFormats from "ajv-formats";
import { ChangeRequest } from "./types";

const schemaPath = path.resolve(__dirname, "../../../schemas/change-request.schema.yaml");
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

let cachedValidator: ValidateFunction<ChangeRequest> | undefined;

const loadSchema = () => {
  const raw = fs.readFileSync(schemaPath, "utf-8");
  return YAML.parse(raw);
};

export const getStructuralValidator = () => {
  if (!cachedValidator) {
    const schema = loadSchema();
    cachedValidator = ajv.compile<ChangeRequest>(schema);
  }
  return cachedValidator;
};

export const validateStructuralIntegrity = (
  cr: ChangeRequest
): { valid: boolean; errors?: string[] } => {
  const validate = getStructuralValidator();
  const valid = validate(cr) as boolean;

  if (!valid) {
    const errors = (validate.errors || []).map((err) =>
      `${err.instancePath || "root"} ${err.message}`.trim()
    );
    return { valid: false, errors };
  }

  return { valid: true };
};

export const validateUqlConsistency = (
  cr: ChangeRequest
): { valid: boolean; errors?: string[] } => {
  const normalized = cr.uql.statement.trim();
  const errors: string[] = [];

  if (normalized.length < 5) {
    errors.push("UQL statement is too short to be actionable");
  }

  if (normalized.includes(";")) {
    errors.push("UQL statement must not contain multi-statement separators");
  }

  if (!normalized.toLowerCase().includes(cr.uql.target.toLowerCase())) {
    errors.push("UQL target must be referenced within the statement");
  }

  return { valid: errors.length === 0, errors };
};

export const validateLedgerAttestation = (
  cr: ChangeRequest
): { valid: boolean; errors?: string[] } => {
  if (!cr.ledgerAttestation) return { valid: true };

  const errors: string[] = [];
  const { source, cursor, hash } = cr.ledgerAttestation;

  if (!source.trim()) errors.push("Ledger attestation source is required");
  if (cursor < 0) errors.push("Ledger cursor cannot be negative");
  if (!/^[a-fA-F0-9]{8,}$/.test(hash)) {
    errors.push("Ledger attestation hash must be hexadecimal");
  }

  return { valid: errors.length === 0, errors };
};
