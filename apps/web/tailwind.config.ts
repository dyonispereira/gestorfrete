import type { Config } from "tailwindcss";
import sharedPreset from "@gestorfrete/config/tailwind.preset";

const config: Config = {
  presets: [sharedPreset as Config],
  content: [
    "./src/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
  ],
};

export default config;
