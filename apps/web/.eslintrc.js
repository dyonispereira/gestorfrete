/**
 * `require.resolve(...)` (not the bare specifier `"@gestorfrete/config/eslint-preset.js"`) because
 * ESLint's shareable-config naming convention mangles any scoped path with an extra path segment
 * (`@scope/pkg/file.js`) as if it were a package name to prefix with `eslint-config-`.
 */
module.exports = {
  extends: [require.resolve("@gestorfrete/config/eslint-preset.js"), "next/core-web-vitals"],
};
