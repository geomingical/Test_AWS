import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const FALLBACK_REPO_NAME = "Test_AWS";

export default defineConfig(({ command }) => {
  const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1] || FALLBACK_REPO_NAME;

  return {
    plugins: [react()],
    base: command === "serve" ? "/" : `/${repoName}/`,
  };
});
