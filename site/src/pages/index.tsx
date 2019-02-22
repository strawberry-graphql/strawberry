import * as React from "react";
import styled from "styled-components";

import MediaQuery from "react-responsive";
import { ButtonLink } from "../components/landing/button-link";
import { Footer } from "../components/landing/footer";
import { Layout } from "../components/landing/layout";
import { LogoDesktop, LogoMobile } from "../components/landing/logo";
import { Paragraph } from "../components/landing/paragraph";
import { Logo } from "../components/logo";
import SEO from "../components/seo";
import { Wrapper } from "../components/wrapper";

const Main = styled.main`
  width: 90%;
  max-width: 87.3rem;
  margin: 0 auto;
`;

export default () => (
  <>
    <Wrapper>
      <SEO
        title="Strawberry GraphQL"
        keywords={["python", "graphql", "strawberry", "api"]}
      />

      <Layout>
        <MediaQuery query="(min-width: 600px)">
          {matches => !matches && <LogoMobile />}
        </MediaQuery>

        <Main>
          <MediaQuery query="(min-width: 600px)">
            {matches => matches && <LogoDesktop />}
          </MediaQuery>

          <Paragraph>
            <strong>Strawberry</strong> is a new GraphQL library for Python 3,
            inspired by dataclasses.
          </Paragraph>
          <Paragraph>
            Strawberry is currently being developed, register to the newsletter
            to be the first to know when it will be released.
          </Paragraph>

          <ButtonLink href="http://eepurl.com/gc9mZ1" target="_blank">
            <span>Subscribe for updates</span> <span>💌</span>
          </ButtonLink>
        </Main>
        <Footer>
          <Logo />
          <p>
            Follow me on{" "}
            <a href="https://twitter.com/patrick91" target="_blank">
              Twitter.
            </a>
          </p>
        </Footer>
      </Layout>
    </Wrapper>
  </>
);
