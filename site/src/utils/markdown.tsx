import * as React from "react";

import marksy from "marksy";
import { Code } from "../components/code";
import { Codespan } from "../components/codespan";
import { Link } from "../components/link";
import { Title } from "../components/title";

export const compile = marksy({
  createElement: React.createElement,

  elements: {
    h1({ id, children }) {
      return <Title id={id}>{children}</Title>;
    },
    h2({ id, children }) {
      return (
        <Title as="h2" id={id}>
          {children}
        </Title>
      );
    },
    h3({ id, children }) {},
    h4({ id, children }) {},
    blockquote({ children }) {
      return children;
    },
    hr() {},
    ol({ children }) {},
    ul({ children }) {},
    p({ children }) {
      return <p>{children}</p>;
    },
    table({ children }) {},
    thead({ children }) {},
    tbody({ children }) {},
    tr({ children }) {},
    th({ children }) {},
    td({ children }) {},
    a({ href, title, target, children }) {
      return (
        <Link href={href} title={title} target={target}>
          {children}
        </Link>
      );
    },
    strong({ children }) {},
    em({ children }) {},
    br() {},
    del({ children }) {},
    img({ src, alt }) {
      return src;
    },
    code({ language, code }) {
      return <Code language={language}>{code}</Code>;
    },
    codespan({ children }) {
      return <Codespan>{children}</Codespan>;
    },
  },
});
