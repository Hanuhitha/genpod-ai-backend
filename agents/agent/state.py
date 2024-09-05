from typing import Any, Dict, Generic, List, TypeVar

GenericAgentState = TypeVar('GenericAgentState', bound=Any)

class State(Generic[GenericAgentState]):
    """
    Base class to handle field classifications and provide utility methods.
    
    Field classifications:
    - @in: Indicates that the field is used for information only and no modifications are made to it.
    - @out: Indicates that the field is used to store results and is updated during processing.
    - @inout: Indicates that the field is used both as @in (for input information) and @out (for storing results).
    """
    
    _in_: str = "@in"
    _out_: str = "@out"
    _inout_: str ="@inout"

    # Class variables to store field names classified by type
    _in_fields: List[str]
    _out_fields: List[str]
    _inout_fields: List[str]
    _fields: List[str]

    def __init__(self, cls: GenericAgentState):
        """
        Initialize with a TypedDict class to classify fields.

        :param cls: The TypedDict class whose fields need to be classified.
        """
        self.cls = cls
        self.class_name = cls.__name__
        self.annotations = self._extract_annotations()
        self._fields = []
        self._in_fields = []
        self._out_fields = []
        self._inout_fields = []

        self._classify_fields()

    def _extract_annotations(self) -> Dict[str, str]:
        """
        Extract annotations from the TypedDict class.
        
        :return: A dictionary of field names and their annotations.
        """
        annotations = {}
        type_hints = getattr(self.cls, '__annotations__', {})
        for field_name, field_type in type_hints.items():
            if hasattr(field_type, '__metadata__'):
                metadata = field_type.__metadata__
                if metadata and isinstance(metadata[0], str):
                    annotations[field_name] = metadata[0]
        return annotations
    
    def _classify_fields(self):
        """
        Classify fields based on their annotations.
        """
        self._in_fields = []
        self._out_fields = []
        self._inout_fields = []

        for field_name, annotation in self.annotations.items():
            self._fields.append(field_name)
            if annotation.startswith(self._inout_):
                self._in_fields.append(field_name)
                self._out_fields.append(field_name)
                self._inout_fields.append(field_name)
            elif annotation.startswith(self._in_):
                self._in_fields.append(field_name)
            elif annotation.startswith(self._out_):
                self._out_fields.append(field_name)

    @classmethod
    def in_field(cls, description: str="") -> str:
        """
        Returns the classification string for input fields with a description.
        
        @in fields are used only for providing information, with no modifications made to them.
        """
        return f"{cls._in_} {description}"

    @classmethod
    def out_field(cls, description: str="") -> str:
        """
        Returns the classification string for output fields with a description.
        
        @out fields are used to store results and are updated as processing progresses.
        """
        return f"{cls._out_} {description}"
    
    @classmethod
    def inout_field(cls, description: str="") -> str:
        """
        Returns the classification string for input-output fields with a description.
        
        @inout fields are used both for providing input information and storing results.
        """
        return f"{cls._inout_} {description}"

    def get_fields(self) -> List[str]:
        """
        Get all field names classified by their annotations.

        :return: List of all field names.
        """
        return self._fields
    
    def get_in_fields(self) -> List[str]:
        """
        Get a list of field names classified as @in or @inout.

        @in fields are used for input purposes only, while @inout fields are used for both input and output.

        :return: List of field names classified as @in.
        """
        return self._in_fields

    def get_out_fields(self) -> List[str]:
        """
        Get a list of field names classified as @out or @inout.

        @out fields are used for output purposes only, while @inout fields are used for both input and output.

        :return: List of field names classified as @out.
        """
        return self._out_fields

    def get_inout_fields(self) -> List[str]:
        """
        Get a list of field names classified as @inout.

        @inout fields are used for both input and output purposes.

        :return: List of field names classified as @inout.
        """
        return self._inout_fields
    
    def print_field_classifications(self):
        """
        Class method to print field classifications.
        """
        print(f"Field Classifications for {self.class_name}:")
        print(f"All the fields of {self.class_name}: {', '.join(self.get_fields())}")
        print(f"@in fields: {', '.join(self.get_in_fields())}")
        print(f"@out fields: {', '.join(self.get_out_fields())}")
        print(f"@inout fields: {', '.join(self.get_inout_fields())}")
