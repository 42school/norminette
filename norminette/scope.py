class Scope:
    """
    Main scope class
    Contain various scope informations updated as the norminette runs through the file
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.name = type(self).__name__
        self.lvl = (parent.lvl + 1) if parent is not None else 0
        self.indent = (parent.indent + 1) if parent is not None else 0
        self.lines = 0
        self.instructions = 0
        # ########################################################## #
        self.vdeclarations_allowed = False
        self.vars = 0
        self.vars_name = []
        self.vars_alignment = 0
        self.func_alignment = 0
        # ########################################################## #
        self.fdeclarations_allowed = False  # False everywhere but GlobalScope
        self.multiline = False
        self.header_protection = -1
        self.tmp_scope = None
        self.include_allowed = False

    def inner(self, sub):
        return sub(self)

    def outer(self):
        """
        Return outer scope (None if called on GlobalScope)
        Adds the line of current scope to parent scope
        to calculate function length or control structure length
        """
        if self.parent is not None:
            self.parent.lines += self.lines
        # print (f"{self.name} -> {self.parent.name}")
        return self.parent

    def __eq__(self, value) -> bool:
        if isinstance(value, str):
            return self.name == value
        if isinstance(value, type) and issubclass(value, Scope):
            return self.name == value.__name__
        if hasattr(value, "name"):
            return self.name == value.name
        return super().__eq__(value)

    def __ne__(self, value) -> bool:
        return not (self == value)

    def get_outer(self):
        """
        Allows to peek to the parent scope without adding lines to
        the parent scope
        """
        return self.parent


class GlobalScope(Scope):
    """
    GlobalScope contains every other scope
    Has no parent scope (returns None)
    """

    def __init__(self):
        super().__init__()
        self.fdeclarations_allowed = True
        self.fnames = []
        self.functions = 0
        self.func_alignment = 0
        self.include_allowed = True


class Function(Scope):
    """
    Function definition scope, anything between the opening/closing braces of
    a function
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.fname_pos = 0
        self.vdeclarations_allowed = None
        self.args = []


class ControlStructure(Scope):
    """
    Control structures scopes (if/else, while, for, do-while, ...), don't
    necessarily have opening/closing braces. If they don't, they can contain
    only one instruction, if that instruction creates a new sub scope, it can
    contain as many instruction as that scope can "hold"
    """

    def __init__(self, parent, multiline=False):
        super().__init__(parent)
        self.multiline = multiline
        self.keyword = None


class UserDefinedType(Scope):
    """
    User defined type scope (struct, union, enum), only variables declarations
    are allowed within this scope
    """

    def __init__(self, parent, typedef=False):
        super().__init__(parent)
        self.typedef = typedef


class UserDefinedEnum(Scope):
    """
    User defined type scope (struct, union, enum), only variables declarations
    are allowed within this scope
    """

    def __init__(self, parent, typedef=False):
        super().__init__(parent)
        self.typedef = typedef


class VariableAssignation(Scope):
    """
    This isn't an 'actual' C scope, but it'll help us parse multiple
    assignations (int foo[4] = {0, 0, 0, 0};) easier.
    - Unused
    """

    pass
