import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";

const CONTAINER = process.env.E2E_POSTGRES_CONTAINER ?? "gestorfrete-postgres-1";
const DB_USER = process.env.E2E_POSTGRES_USER ?? "gestorfrete";
const DB_NAME = process.env.E2E_POSTGRES_DB ?? "gestorfrete";

/**
 * There is no self-service tenant/onboarding endpoint yet (`modules/onboarding` is empty) — the
 * fixtures a fresh tenant + its first Users/Papéis need can only be seeded directly against
 * Postgres, via the same `docker exec ... psql` mechanism validated by hand earlier this session.
 */
export default function globalSetup(): void {
  const sqlPath = path.join(__dirname, "fixtures", "seed.sql");
  const sql = fs.readFileSync(sqlPath, "utf-8");
  execFileSync("docker", ["exec", "-i", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"], {
    input: sql,
    stdio: ["pipe", "inherit", "inherit"],
  });
}
