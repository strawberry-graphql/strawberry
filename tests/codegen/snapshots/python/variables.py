from typing import List, NewType, Optional

class OperationNameResult:
    with_inputs: bool

class OperationNameVariables:
    id: Optional[ID]
    input: ExampleInput
    ids: List[ID]
    ids2: Optional[List[Optional[ID]]]
    ids3: Optional[List[Optional[List[Optional[ID]]]]]
