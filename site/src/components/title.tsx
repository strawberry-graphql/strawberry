import styled from "styled-components";

const getFontSize = (props: any) => {
  if (props.as === "h2") {
    return "3rem";
  }

  return "4rem";
};

export const Title = styled.h1`
  font-family: "Titillium Web", sans-serif;
  margin: 0 0 0.5em;
  line-height: 1.2;
  font-size: ${getFontSize};
`;
