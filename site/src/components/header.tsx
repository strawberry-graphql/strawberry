import { Link } from "gatsby";
import * as React from "react";

import styled from "styled-components";

interface HeaderProps {
  siteTitle?: string;
}

const Wrapper = styled.header`
  background: #040404;
  margin-bottom: "1.45rem";
  color: white;
  font-family: "Titillium Web", sans-serif;

  > div {
    margin: 0 auto;
    max-width: 80rem;

    display: flex;
  }

  h1 {
    font-size: 2.5rem;
    padding: 1rem;
  }

  nav {
    margin-left: auto;
  }

  nav a {
    display: flex;
    align-content: center;
    align-items: center;
    border-bottom: 2px solid red;
    height: 100%;
    font-size: 1.6rem;
    padding: 0 1em;
  }
`;

const Header: React.SFC<HeaderProps> = ({ siteTitle }) => (
  <Wrapper>
    <div>
      <h1>
        <Link
          to="/"
          style={{
            color: "white",
            textDecoration: "none",
          }}
        >
          {siteTitle}
        </Link>
      </h1>

      <nav>
        <a>Docs</a>
      </nav>
    </div>
  </Wrapper>
);

Header.defaultProps = {
  siteTitle: "",
};

export default Header;
