import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";

const CONTAINER = process.env.E2E_POSTGRES_CONTAINER ?? "gestorfrete-postgres-1";
const DB_USER = process.env.E2E_POSTGRES_USER ?? "gestorfrete";
const DB_NAME = process.env.E2E_POSTGRES_DB ?? "gestorfrete";

export default function globalTeardown(): void {
  const sqlPath = path.join(__dirname, "fixtures", "teardown.sql");
  const sql = fs.readFileSync(sqlPath, "utf-8");
  execFileSync("docker", ["exec", "-i", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"], {
    input: sql,
    stdio: ["pipe", "inherit", "inherit"],
  });
}
