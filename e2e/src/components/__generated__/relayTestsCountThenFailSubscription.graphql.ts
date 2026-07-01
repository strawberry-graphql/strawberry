/**
 * @generated SignedSource<<3fe35b075011888364af277aac224bb6>>
 * @lightSyntaxTransform
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type relayTestsCountThenFailSubscription$variables = Record<PropertyKey, never>;
export type relayTestsCountThenFailSubscription$data = {
  readonly countThenFail: number;
};
export type relayTestsCountThenFailSubscription = {
  response: relayTestsCountThenFailSubscription$data;
  variables: relayTestsCountThenFailSubscription$variables;
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
    "name": "countThenFail",
    "storageKey": "countThenFail(target:2)"
  }
];
return {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "relayTestsCountThenFailSubscription",
    "selections": (v0/*:: as any*/),
    "type": "Subscription",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "relayTestsCountThenFailSubscription",
    "selections": (v0/*:: as any*/)
  },
  "params": {
    "cacheID": "e068996c5dfa074c2edc7f37fca65067",
    "id": null,
    "metadata": {},
    "name": "relayTestsCountThenFailSubscription",
    "operationKind": "subscription",
    "text": "subscription relayTestsCountThenFailSubscription {\n  countThenFail(target: 2)\n}\n"
  }
};
})();

(node as any).hash = "c925dc6fbbb1d74ee83eb062b01b1354";

export default node;
