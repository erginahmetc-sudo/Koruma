import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Electron'da dosya file:// ile yükleneceği için göreli yollar şart.
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: { port: 5123, strictPort: true },
  build: { outDir: "dist", emptyOutDir: true },
});
