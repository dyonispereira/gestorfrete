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
const FIXTURE_FILES = ["seed.sql", "cadastros-seed.sql", "frota-seed.sql", "viagens-seed.sql", "fiscal-seed.sql"];

export default function globalSetup(): void {
  for (const file of FIXTURE_FILES) {
    const sql = fs.readFileSync(path.join(__dirname, "fixtures", file), "utf-8");
    execFileSync("docker", ["exec", "-i", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"], {
      input: sql,
      stdio: ["pipe", "inherit", "inherit"],
    });
  }
}
