/**
 * @generated SignedSource<<deb0b42e44ffac99959a2112439be379>>
 * @lightSyntaxTransform
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type relayTestsHelloQuery$variables = {
  delay?: number | null | undefined;
};
export type relayTestsHelloQuery$data = {
  readonly hello: string;
};
export type relayTestsHelloQuery = {
  response: relayTestsHelloQuery$data;
  variables: relayTestsHelloQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": 0,
    "kind": "LocalArgument",
    "name": "delay"
  }
],
v1 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "delay",
        "variableName": "delay"
      }
    ],
    "kind": "ScalarField",
    "name": "hello",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*:: as any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "relayTestsHelloQuery",
    "selections": (v1/*:: as any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*:: as any*/),
    "kind": "Operation",
    "name": "relayTestsHelloQuery",
    "selections": (v1/*:: as any*/)
  },
  "params": {
    "cacheID": "32f886d6d7f0ca3b24c6b8c0897c33e5",
    "id": null,
    "metadata": {},
    "name": "relayTestsHelloQuery",
    "operationKind": "query",
    "text": "query relayTestsHelloQuery(\n  $delay: Float = 0\n) {\n  hello(delay: $delay)\n}\n"
  }
};
})();

(node as any).hash = "da986b16812095417497d884d89a6820";

export default node;
