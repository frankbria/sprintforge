import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";
import { createRequire } from "node:module";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

// eslint-config-next sets `settings.react.version = "detect"`, and detection is
// the only path that calls `context.getFilename()`, which ESLint 10 removed.
// Pinning the installed version (read, never hard-coded) skips detection.
const reactVersion = createRequire(import.meta.url)("react/package.json").version;

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  { settings: { react: { version: reactVersion } } },
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "out/**",
      "build/**",
      "next-env.d.ts",
    ],
  },
];

export default eslintConfig;
