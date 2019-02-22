import styled from "styled-components";

export const ButtonLink = styled.a`
  color: ${props => props.theme.colors.background};
  background-color: black;
  padding: 1em;
  text-decoration: none;
  display: block;
  text-align: center;
  font-family: Archia;
  font-weight: bold;
  font-size: 1.6rem;
  margin: 2em 0;
  max-width: 450px;

  span {
    transition: 0.2s all ease-out;
    display: inline-block;
    transform: translate(1rem);
  }

  span:last-child {
    opacity: 0;
    position: relative;
    top: 0.2rem;
  }

  &:hover span {
    opacity: 1;
    transform: translate(0, 0);
  }
`;
