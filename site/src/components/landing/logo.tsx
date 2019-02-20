import * as React from "react";
import styled from "styled-components";
import { LogoExpanded } from "../logo-expanded";

const LogoPiece = styled(LogoExpanded)`
  width: 200%;
  height: auto;

  margin-top: ${props => (props.alternate ? "-1.5rem" : 0)};
  margin-left: ${props => (props.alternate ? "-105%" : 0)};
`;

const LogoMobileWrapper = styled.div`
  width: 100%;
  overflow: hidden;
  margin-bottom: 5rem;
`;

export const LogoMobile = () => (
  <LogoMobileWrapper>
    <LogoPiece />
    <LogoPiece alternate={true} />
  </LogoMobileWrapper>
);

export const LogoDesktop = styled(LogoExpanded)`
  width: 100%;
  height: auto;

  margin-bottom: 10rem;
`;
