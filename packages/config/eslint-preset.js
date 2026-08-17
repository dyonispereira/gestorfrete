/** Base ESLint config shared by every app/package of the monorepo. */
module.exports = {
  root: true,
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint"],
  env: {
    es2022: true,
    node: true,
  },
  ignorePatterns: ["dist/", ".next/", "node_modules/"],
};
