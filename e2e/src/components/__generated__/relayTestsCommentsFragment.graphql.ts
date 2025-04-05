/**
 * @generated SignedSource<<8a2413eb8c2bdec10f525eccc282227e>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type relayTestsCommentsFragment$data = {
  readonly comments: ReadonlyArray<{
    readonly content: string;
    readonly id: string;
  }>;
  readonly " $fragmentType": "relayTestsCommentsFragment";
};
export type relayTestsCommentsFragment$key = {
  readonly " $data"?: relayTestsCommentsFragment$data;
  readonly " $fragmentSpreads": FragmentRefs<"relayTestsCommentsFragment">;
};

const node: ReaderFragment = {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "relayTestsCommentsFragment",
  "selections": [
    {
      "alias": null,
      "args": null,
      "concreteType": "Comment",
      "kind": "LinkedField",
      "name": "comments",
      "plural": true,
      "selections": [
        {
          "alias": null,
          "args": null,
          "kind": "ScalarField",
          "name": "id",
          "storageKey": null
        },
        {
          "alias": null,
          "args": null,
          "kind": "ScalarField",
          "name": "content",
          "storageKey": null
        }
      ],
      "storageKey": null
    }
  ],
  "type": "BlogPost",
  "abstractKey": null
};

(node as any).hash = "2bc5eb5c1b00234ad057cf1e9f9a06bc";

export default node;
