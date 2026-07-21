import relay from "vite-plugin-relay";
import path from "path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const graphqlUrl = new URL(
	process.env.E2E_GRAPHQL_URL ?? "http://localhost:8000/graphql",
);
const graphqlPath = graphqlUrl.pathname.replace(/\/$/, "") || "/";

function rewriteGraphqlPath(pathname: string) {
	const suffix = pathname.slice("/graphql".length);

	if (graphqlPath === "/") {
		return suffix.startsWith("?") ? `/${suffix}` : suffix || "/";
	}

	return `${graphqlPath}${suffix}`;
}

// https://vite.dev/config/
export default defineConfig({
	plugins: [relay, react(), tailwindcss()],
	server: {
		proxy: {
			"/graphql": {
				target: graphqlUrl.origin,
				changeOrigin: true,
				rewrite: rewriteGraphqlPath,
				ws: true,
			},
		},
	},
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
		},
	},
});
