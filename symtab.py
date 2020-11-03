class Types():
    def __init__(self):
        self.types = {
            "int": 4,
            "char": 1,
            "boolean": 1,
            "void": 0,
            }


class Type():
    def __init__(self, name, T):
        self.name = name
        self.size = T.types.get(name)

    def isValid(self):
        if self.size is None:
            return False
        return True


class Symbol():
    def __init__(self, name, type):
        self.name = name
        self.type = type


class VariableSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)


class ArraySymbol(Symbol):
    def __init__(self, name, type, num):
        super().__init__(name, type)
        self.num = num


class Scope():
    def __init__(self, name, enclosingScope):
        self.name = name
        self.enclosingScope = enclosingScope
        self.symbols = dict()

    def define(self, symbol):
        if symbol.name not in self.symbols:
            self.symbols[symbol.name] = symbol
            return True
        return False

    def resolve(self, name):
        symbol = self.symbols.get(name)
        if symbol is not None:
            return Symbol

        elif self.enclosingScope is not None:
            return self.enclosingScope.resolve(name)

        else:
            return False


class MethodSymbol(Symbol, Scope):
    def __init__(self, name, type, enclosingScope):
        super().__init__(name, type)
        self.args = list()
        self.enclosingScope = enclosingScope
        self.symbols = dict()


class StructSymbol(Symbol, Scope):
    def __init__(self, name, type, enclosingScope):
        super().__init__(name, type)
        self.enclosingScope = enclosingScope
        self.symbols = dict()

    def resolve(self, name):
        symbol = self.symbols.get(name)
        if symbol is not None:
            return Symbol

        else:
            return False


if __name__ == "__main__":
    pass
