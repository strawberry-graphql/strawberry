import styled from "styled-components";

export const Layout = styled.div`
  background: ${props => props.theme.colors.background};
  width: 100vw;
  min-height: 100vh;
  padding: 5rem 0;
  display: flex;
  flex-direction: column;
`;
