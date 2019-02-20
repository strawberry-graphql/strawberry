import * as React from "react";
import { createGlobalStyle, ThemeProvider } from "styled-components";

import { fonts } from "../assets/fonts";

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  html {
    font-size: 62.5%;
    box-sizing: border-box;
  }

  *, *:before, *:after {
    box-sizing: inherit;
  }

  ::selection {
    background: black;
    color: white;
  }
  ::-moz-selection {
    background: black;
    color: white;
  }

  @font-face {
    font-family: 'Archia';
    src: url('${fonts.archia.regular.woff2}') format('woff2'),
        url('${fonts.archia.regular.woff}') format('woff');
    font-weight: normal;
    font-style: normal;
  }

  @font-face {
    font-family: 'Archia';
    src: url('${fonts.archia.thin.woff2}') format('woff2'),
        url('${fonts.archia.thin.woff}') format('woff');
    font-weight: 100;
    font-style: normal;
  }

  @font-face {
    font-family: 'Archia';
    src: url('${fonts.archia.bold.woff2}') format('woff2'),
        url('${fonts.archia.bold.woff}') format('woff');
    font-weight: bold;
    font-style: normal;
  }

  @font-face {
    font-family: 'Archia';
    src: url('${fonts.archia.light.woff2}') format('woff2'),
        url('${fonts.archia.light.woff}') format('woff');
    font-weight: 300;
    font-style: normal;
  }
`;

export const Wrapper: React.SFC = ({ children }) => (
  <ThemeProvider
    theme={{
      colors: {
        background: "#FFE600",
      },
    }}
  >
    <>
      <GlobalStyle />
      {children}
    </>
  </ThemeProvider>
);
