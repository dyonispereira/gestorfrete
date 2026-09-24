import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";

const CONTAINER = process.env.E2E_POSTGRES_CONTAINER ?? "gestorfrete-postgres-1";
const DB_USER = process.env.E2E_POSTGRES_USER ?? "gestorfrete";
const DB_NAME = process.env.E2E_POSTGRES_DB ?? "gestorfrete";

const FIXTURE_FILES = [
  "teardown.sql",
  "cadastros-teardown.sql",
  "frota-teardown.sql",
  "viagens-teardown.sql",
  "fiscal-teardown.sql",
  "checklist-teardown.sql",
  "work-orders-teardown.sql",
  "availability-teardown.sql",
  "financeiro-teardown.sql",
  "resultado-gerencial-teardown.sql",
  "dia-real-teardown.sql",
];

export default function globalTeardown(): void {
  for (const file of FIXTURE_FILES) {
    const sql = fs.readFileSync(path.join(__dirname, "fixtures", file), "utf-8");
    execFileSync("docker", ["exec", "-i", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"], {
      input: sql,
      stdio: ["pipe", "inherit", "inherit"],
    });
  }
}
