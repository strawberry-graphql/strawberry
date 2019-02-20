import Highlight, { defaultProps } from "prism-react-renderer";
import * as React from "react";
import styled from "styled-components";

export const Wrapper = styled.code`
  pre {
    font-family: Consolas, Menlo, Monaco, source-code-pro, Courier New,
      monospace;
    font-size: 1.6rem;
    line-height: 1.5;
    padding: 1em;
    margin: 0 0 1em;
  }
`;

const theme /*: PrismTheme */ = {
  plain: {
    color: "#c7d0d9",
    backgroundColor: "#0b1015",
  },
  styles: [
    {
      types: ["keyword"],
      style: {
        color: "rgb(217, 101, 133)",
        fontStyle: "italic",
      },
    },
    {
      types: ["boolean"],
      style: {
        color: "rgb(90, 247, 142)",
      },
    },
    {
      types: ["builtin", "variable"],
      style: {
        color: "rgb(243, 249, 157)",
      },
    },
    {
      types: ["char", "constant"],
      style: {
        color: "rgb(255, 211, 217)",
      },
    },
    {
      types: ["attr-name"],
      style: {
        color: "rgb(154, 237, 254)",
      },
    },
    {
      types: ["tag", "punctuation"],
      style: {
        color: "rgb(255, 92, 87)",
      },
    },
    {
      types: ["operator"],
      style: {
        color: "rgb(132, 139, 178)",
      },
    },
    {
      types: ["string"],
      style: {
        color: "rgb(90, 193, 67)",
      },
    },
  ],
};

export const Code = ({ children, language }) => (
  <Wrapper>
    <Highlight
      {...defaultProps}
      theme={theme}
      code={children}
      language={language}
    >
      {({ className, style, tokens, getLineProps, getTokenProps }) => (
        <pre className={className} style={style}>
          {tokens.map((line, i) => (
            <div {...getLineProps({ line, key: i })}>
              {line.map((token, key) => (
                <span {...getTokenProps({ token, key })} />
              ))}
            </div>
          ))}
        </pre>
      )}
    </Highlight>
  </Wrapper>
);
