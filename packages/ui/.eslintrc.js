/**
 * `require.resolve(...)` (not the bare specifier `"@gestorfrete/config/eslint-preset.js"`) — mesmo
 * motivo do `apps/web/.eslintrc.js`: ESLint mangla qualquer path escopado com segmento extra
 * (`@scope/pkg/file.js`) como se fosse um nome de pacote a prefixar com `eslint-config-`.
 */
module.exports = {
  extends: [require.resolve("@gestorfrete/config/eslint-preset.js")],
};
