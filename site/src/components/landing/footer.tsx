import styled from "styled-components";

export const Footer = styled.footer`
  text-align: center;
  font-family: Archia;
  font-size: 1.4rem;
  margin-top: auto;

  a {
    color: inherit;
  }

  svg {
    margin-bottom: 2rem;
    width: 10rem;
    height: auto;
  }

  @media (min-width: 600px) {
    display: flex;
    align-items: center;

    width: 90%;
    max-width: 87.3rem;
    margin: auto auto 0;

    svg {
      margin-right: 2rem;
    }
  }
`;
