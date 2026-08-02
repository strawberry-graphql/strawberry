/**
 * @generated SignedSource<<44cbfbc8071461a05b7bb2c73aaa2898>>
 * @lightSyntaxTransform
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type relayTestsCountSubscription$variables = Record<PropertyKey, never>;
export type relayTestsCountSubscription$data = {
  readonly count: number;
};
export type relayTestsCountSubscription = {
  response: relayTestsCountSubscription$data;
  variables: relayTestsCountSubscription$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Literal",
        "name": "target",
        "value": 2
      }
    ],
    "kind": "ScalarField",
    "name": "count",
    "storageKey": "count(target:2)"
  }
];
return {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "relayTestsCountSubscription",
    "selections": (v0/*:: as any*/),
    "type": "Subscription",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "relayTestsCountSubscription",
    "selections": (v0/*:: as any*/)
  },
  "params": {
    "cacheID": "f6d57a746e9eeb4394af3e5c797ff558",
    "id": null,
    "metadata": {},
    "name": "relayTestsCountSubscription",
    "operationKind": "subscription",
    "text": "subscription relayTestsCountSubscription {\n  count(target: 2)\n}\n"
  }
};
})();

(node as any).hash = "f01dec6f416fe4c2433fb1cfdcdca30c";

export default node;
