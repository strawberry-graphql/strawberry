import {
	buildSchema,
	experimentalExecuteIncrementally,
	GraphQLObjectType,
	GraphQLString,
	GraphQLID,
	GraphQLNonNull,
	GraphQLList,
	GraphQLFloat,
	GraphQLSchema,
	GraphQLDirective,
	GraphQLBoolean,
	GraphQLInt,
	DirectiveLocation,
} from "graphql";
import { createHandler } from "graphql-http/lib/use/express";
import express from "express";
import cors from "cors";

// Simulate async delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Define directives
const DeferDirective = new GraphQLDirective({
	name: "defer",
	locations: [
		DirectiveLocation.FRAGMENT_SPREAD,
		DirectiveLocation.INLINE_FRAGMENT,
	],
	args: {
		if: { type: GraphQLBoolean },
		label: { type: GraphQLString },
	},
});

const StreamDirective = new GraphQLDirective({
	name: "stream",
	locations: [DirectiveLocation.FIELD],
	args: {
		if: { type: GraphQLBoolean },
		label: { type: GraphQLString },
		initialCount: { type: GraphQLInt, defaultValue: 0 },
	},
});

// Define types using GraphQLObjectType
const CommentType = new GraphQLObjectType({
	name: "Comment",
	fields: {
		id: { type: new GraphQLNonNull(GraphQLID) },
		content: { type: new GraphQLNonNull(GraphQLString) },
	},
});

const BlogPostType = new GraphQLObjectType({
	name: "BlogPost",
	fields: {
		id: { type: new GraphQLNonNull(GraphQLID) },
		title: { type: new GraphQLNonNull(GraphQLString) },
		content: { type: new GraphQLNonNull(GraphQLString) },
		comments: {
			type: new GraphQLNonNull(
				new GraphQLList(new GraphQLNonNull(CommentType)),
			),
			resolve: async () => {
				await delay(4000);
				return [
					{ id: "1", content: "Great post!" },
					{ id: "2", content: "Thanks for sharing!" },
				];
			},
		},
	},
});

const QueryType = new GraphQLObjectType({
	name: "Query",
	fields: {
		hello: {
			type: new GraphQLNonNull(GraphQLString),
			args: {
				delay: { type: GraphQLFloat, defaultValue: 0 },
			},
			resolve: async (_: unknown, { delay: delayMs }: { delay: number }) => {
				await delay(delayMs * 1000);
				return "Hello, world!";
			},
		},
		blogPost: {
			type: new GraphQLNonNull(BlogPostType),
			args: {
				id: { type: GraphQLID },
			},
			resolve: (_: unknown, { id }: { id: string }) => {
				return {
					id,
					title: "My Blog Post",
					content: "This is my blog post.",
				};
			},
		},
	},
});

// Create the schema
const schema = new GraphQLSchema({
	query: QueryType,
	directives: [DeferDirective, StreamDirective],
});

const app = express();

// Enable CORS for all routes
app.use(
	cors({
		origin: "http://localhost:5173", // Allow requests from your frontend
		methods: ["GET", "POST", "OPTIONS"], // Allow these HTTP methods
		allowedHeaders: ["Content-Type", "Authorization"], // Allow these headers
		credentials: true, // Allow credentials (cookies, authorization headers, etc.)
	}),
);

// Create and use the GraphQL handler.
app.all(
	"/graphql",
	createHandler({
		schema,
		execute: experimentalExecuteIncrementally,
	}),
);

app.listen(4000, () => {
	console.log("Server is running on port 4000");
});
