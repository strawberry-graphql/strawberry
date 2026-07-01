/**
 * @generated SignedSource<<1ae11baa131ab863ac725bd917a7de38>>
 * @lightSyntaxTransform
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type relayTestsBlogPostQuery$variables = {
  id: string;
  shouldDefer?: boolean | null | undefined;
};
export type relayTestsBlogPostQuery$data = {
  readonly blogPost: {
    readonly content: string;
    readonly title: string;
    readonly " $fragmentSpreads": FragmentRefs<"relayTestsCommentsFragment">;
  };
};
export type relayTestsBlogPostQuery = {
  response: relayTestsBlogPostQuery$data;
  variables: relayTestsBlogPostQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "id"
  },
  {
    "defaultValue": false,
    "kind": "LocalArgument",
    "name": "shouldDefer"
  }
],
v1 = [
  {
    "kind": "Variable",
    "name": "id",
    "variableName": "id"
  }
],
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "title",
  "storageKey": null
},
v3 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "content",
  "storageKey": null
},
v4 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": (v0/*:: as any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "relayTestsBlogPostQuery",
    "selections": [
      {
        "alias": null,
        "args": (v1/*:: as any*/),
        "concreteType": "BlogPost",
        "kind": "LinkedField",
        "name": "blogPost",
        "plural": false,
        "selections": [
          (v2/*:: as any*/),
          (v3/*:: as any*/),
          {
            "kind": "Defer",
            "selections": [
              {
                "args": null,
                "kind": "FragmentSpread",
                "name": "relayTestsCommentsFragment"
              }
            ]
          }
        ],
        "storageKey": null
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*:: as any*/),
    "kind": "Operation",
    "name": "relayTestsBlogPostQuery",
    "selections": [
      {
        "alias": null,
        "args": (v1/*:: as any*/),
        "concreteType": "BlogPost",
        "kind": "LinkedField",
        "name": "blogPost",
        "plural": false,
        "selections": [
          (v2/*:: as any*/),
          (v3/*:: as any*/),
          {
            "if": "shouldDefer",
            "kind": "Defer",
            "label": "relayTestsBlogPostQuery$defer$relayTestsCommentsFragment",
            "selections": [
              {
                "alias": null,
                "args": null,
                "concreteType": "Comment",
                "kind": "LinkedField",
                "name": "comments",
                "plural": true,
                "selections": [
                  (v4/*:: as any*/),
                  (v3/*:: as any*/)
                ],
                "storageKey": null
              }
            ]
          },
          (v4/*:: as any*/)
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "353f101f55e146c2c22598ddd0818c9e",
    "id": null,
    "metadata": {},
    "name": "relayTestsBlogPostQuery",
    "operationKind": "query",
    "text": "query relayTestsBlogPostQuery(\n  $id: ID!\n  $shouldDefer: Boolean = false\n) {\n  blogPost(id: $id) {\n    title\n    content\n    ...relayTestsCommentsFragment @defer(label: \"relayTestsBlogPostQuery$defer$relayTestsCommentsFragment\", if: $shouldDefer)\n    id\n  }\n}\n\nfragment relayTestsCommentsFragment on BlogPost {\n  comments {\n    id\n    content\n  }\n}\n"
  }
};
})();

(node as any).hash = "f04ba754cec2dd44c29bb48d17e151f4";

export default node;
