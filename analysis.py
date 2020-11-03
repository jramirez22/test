from grammar.decafParser import decafParser
from grammar.decafVisitor import decafVisitor

import symtab

from error_handler import ErrorHandler

# LABELS
_int = "int"
_char = "char"
_boolean = "boolean"
_void = "void"
_error = "error"


class Analysis(decafVisitor):
    def __init__(self):
        self.count = 0
        self.currentScope = None
        self.isError = False
        self.scopes = dict()
        # Manage available data types
        self.T = symtab.Types()

    def createLocalScope(self, name):
        name = name + str(self.count)
        self.count += 1
        # Create and set as current scope
        localScope = symtab.Scope(name, self.currentScope)
        self.currentScope = localScope

    def exitScope(self):
        self.currentScope = self.currentScope.enclosingScope

    def createType(self, line, typeName):
        type = symtab.Type(typeName, self.T)
        if not type.isValid():
            ErrorHandler.nameError(line, typeName)
            self.error()

        return type

    def addStruct(self, line, typeName):
        if self.T.types.get(typeName) is not None:
            ErrorHandler.structError(line, typeName)
            self.error()

        self.T.types[typeName] = 0

    def defineSymbol(self, line, scope, symbol):
        if not scope.define(symbol):
            ErrorHandler.declError(line, scope)
            self.error()

    def mainCheker(self, line, scope):
        symbol = None
        isMain = False

        for symbolName in scope.symbols:
            if symbolName == "main":
                symbol = scope.symbols.get(symbolName)
                break

        if isinstance(symbol, symtab.MethodSymbol):
            isMain = True

        if not isMain:
            ErrorHandler.nameError(line, "main()")
            self.error()

    def intChecker(self, line, leftType, rightType, op):
        if leftType != _int or rightType != _int:
            ErrorHandler.typeError(line, op)
            self.error()
            return _error

        return _int

    def condChecker(self, line, stmt, expr):
        if expr != _boolean:
            ErrorHandler.typeError(line, stmt, 2)
            self.error()
            return _error

        return _boolean

    def error(self):
        self.isError = True

    def visitProgram(self, ctx: decafParser.ProgramContext):
        globalScope = symtab.Scope("globalScope", None)
        self.currentScope = globalScope
        # Visit declaration(s)
        self.visitChildren(ctx)
        # Save scope
        self.scopes[ctx] = self.currentScope
        # Check if there is a main method
        self.mainCheker(ctx.start.line, self.currentScope)

    def visitMethodCall(self, ctx: decafParser.MethodCallContext):
        name = ctx.ID().getText()

        methodSymbol = self.currentScope.resolve(name)

        # Check that the symbol is defined
        if not methodSymbol:
            ErrorHandler.nameError(ctx.start.line, name)
            self.error()

        # Check that the symbol is a method
        isMethod = isinstance(methodSymbol, symtab.MethodSymbol)
        if not isMethod:
            ErrorHandler.typeError(ctx.start.line, name, 3)
            self.error()

        # Check method signature
        signature = methodSymbol.args
        args = []

        for arg in ctx.arg():
            type = self.visit(arg)
            args.append(type)

        if not (signature == args):
            ErrorHandler.typeError(ctx.start.line, name, 4)
            self.error()

        # Return the type of the method
        # to be able to make methods calls from conditional statements
        return methodSymbol.type.name

    def visitMethodDecl(self, ctx: decafParser.MethodDeclContext):
        type = ctx.methodType().getText()
        name = ctx.ID().getText()

        type = self.createType(ctx.start.line, type)

        methodScope = symtab.MethodSymbol(name, type, self.currentScope)
        # Visit the parameters
        for param in ctx.parameter():
            symbol = self.visitParameter(param)
            # Create the signature
            methodScope.args.append(symbol.type.name)

            # Define the parameters in the scope of the method
            if not methodScope.define(symbol):
                ErrorHandler.paramError(ctx.start.line, symbol.name, name)
                self.error()

        # Define the method in the current scope
        self.defineSymbol(ctx.start.line, self.currentScope, methodScope)
        # Set method scope as current scope
        self.currentScope = methodScope
        # Visit block
        self.visit(ctx.bl)
        # Save scope
        self.scopes[ctx] = self.currentScope
        # Exit scope
        self.exitScope()

    def visitParameter(self, ctx: decafParser.ParameterContext):
        type = ctx.paramType.getText()
        name = ctx.ID().getText()
        # Create type for the parameter
        type = self.createType(ctx.start.line, type)

        return symtab.Symbol(name, type)

    def visitReturnStmt(self, ctx: decafParser.ReturnStmtContext):
        methodType = self.currentScope.type.name
        returnType = None

        if ctx.expression() is None:
            returnType = _void
        else:
            returnType = self.visit(ctx.expression())

        # Check that the return type is the same as the method type
        if returnType != methodType:
            ErrorHandler.returnError(ctx.start.line, methodType, returnType)
            self.error()

    def visitIfStmt(self, ctx: decafParser.IfStmtContext):
        stmt = "ifScope"
        expr = self.visit(ctx.expression())

        self.condChecker(ctx.start.line, stmt, expr)
        # Create scope and visit block
        self.createLocalScope(stmt)
        self.visit(ctx.bl)
        # Save and exit scope
        self.scopes[ctx] = self.currentScope
        self.exitScope()

    def visitWhileStmt(self, ctx: decafParser.WhileStmtContext):
        stmt = "whileScope"
        expr = self.visit(ctx.expression())

        self.condChecker(ctx.start.line, stmt, expr)
        # Create scope and visit block
        self.createLocalScope(stmt)
        self.visit(ctx.bl)
        # Save and exit scope
        self.scopes[ctx] = self.currentScope
        self.exitScope()

    def visitStructDecl(self, ctx: decafParser.StructDeclContext):
        name = ctx.ID().getText()
        # Add struct as new type
        self.addStruct(ctx, name)

        structSymbol = symtab.StructSymbol(name, None, self.currentScope)

        # Define the struct in the current scope
        self.defineSymbol(ctx.start.line, self.currentScope, structSymbol)
        # Set struct scope as current scope
        self.currentScope = structSymbol
        # Visit childs
        self.visit(ctx.bl)
        # Save scope
        self.scopes[ctx] = self.currentScope
        # Exit scope
        self.exitScope()

        # Returns the name to perform the following feature:
        # struct name {varDecl} var ;
        return name

    def visitVarDecl(self, ctx: decafParser.VarDeclContext):
        varType = self.visit(ctx.varType())
        name = ctx.ID().getText()

        type = self.createType(ctx.start.line, varType)
        symbol = symtab.VariableSymbol(name, type)

        self.defineSymbol(ctx.start.line, self.currentScope, symbol)

    def visitArrayDecl(self, ctx: decafParser.ArrayDeclContext):
        varType = ctx.varType().getText()
        name = ctx.ID().getText()

        num = ctx.NUM().getText()
        # <NUM> in the declaration of an array must be greater than 0.
        if int(num) <= 0:
            ErrorHandler.arrayError(ctx.start.line, name)
            self.error()

        type = self.createType(ctx.start.line, varType)
        symbol = symtab.ArraySymbol(name, type, num)

        self.defineSymbol(ctx.start.line, self.currentScope, symbol)

    def visitIntType(self, ctx: decafParser.IntTypeContext):
        return _int

    def visitCharType(self, ctx: decafParser.CharTypeContext):
        return _char

    def visitBoolType(self, ctx: decafParser.BoolTypeContext):
        return _boolean

    def visitStructType(self, ctx: decafParser.StructTypeContext):
        structName = ctx.ID().getText()
        return structName

    def visitAsignStmt(self, ctx: decafParser.AsignStmtContext):
        left = self.visit(ctx.location())
        right = self.visit(ctx.expression())

        if not left == right:
            ErrorHandler.typeError(ctx.start.line, "=")
            self.error()

    def visitLocation(self, ctx: decafParser.LocationContext):
        name = ctx.ID().getText()
        symbol = self.currentScope.resolve(name)

        if not symbol:
            ErrorHandler.nameError(ctx.start.line, name)
            self.error()

        expr = None
        loc = None

        if ctx.expr is not None:
            expr = self.visit(ctx.expr)

        if ctx.loc is not None:
            loc = self.visit(ctx.loc)

        # Declared as a variable
        if isinstance(symbol, symtab.VariableSymbol):
            pass

        # Declared as an arrangement
        elif isinstance(symbol, symtab.ArraySymbol):
            pass

        # Declared as an struct
        elif isinstance(symbol, symtab.StructSymbol):
            pass
        # if not symbol:
        #     ErrorHandler.nameError(ctx.start.line, name)
        #     self.error()

        # expr = ctx.expr

        # if expr is None:

        # loc = ctx.loc

        # return self.visitChildren(ctx)

    def visitMulExp(self, ctx: decafParser.MulExpContext):
        op = ctx.op.getText()

        leftType = self.visit(ctx.left)
        rightType = self.visit(ctx.right)

        return self.intChecker(ctx.start.line, leftType, rightType, op)

    def visitAddExp(self, ctx: decafParser.AddExpContext):
        op = ctx.op.getText()

        leftType = self.visit(ctx.left)
        rightType = self.visit(ctx.right)

        return self.intChecker(ctx.start.line, leftType, rightType, op)

    def visitRelExp(self, ctx: decafParser.RelExpContext):
        op = ctx.op.getText()

        leftType = self.visit(ctx.left)
        rightType = self.visit(ctx.right)

        return self.intChecker(ctx.start.line, leftType, rightType, op)

    def visitEqExp(self, ctx: decafParser.EqExpContext):
        op = ctx.op.getText()
        eq = [_int, _char, _boolean]

        leftType = self.visit(ctx.left)
        rightType = self.visit(ctx.right)

        if leftType != rightType:
            ErrorHandler.typeError(ctx.line.start, op)
            self.error()
            return _error

        if (leftType not in eq) or (rightType not in eq):
            ErrorHandler.typeError(ctx.line.start, op)
            self.error()
            return _error

        return leftType

    def visitCondExp(self, ctx: decafParser.CondExpContext):
        op = ctx.op.getText()

        leftType = self.visit(ctx.left)
        rightType = self.visit(ctx.right)

        if leftType != _boolean or rightType != _boolean:
            ErrorHandler.typeError(ctx.line.start, op)
            self.error()
            return _error

        return _boolean

    def visitMinExp(self, ctx: decafParser.MinExpContext):
        exprType = self.visit(ctx.expression())

        if exprType != _int:
            ErrorHandler.typeError(ctx.start.line, '-')
            self.error()
            return _error

        return _int

    def visitNegExp(self, ctx: decafParser.NegExpContext):
        exprType = self.visit(ctx.expression())

        if exprType != _boolean:
            ErrorHandler.typeError(ctx.start.line, '!')
            self.error()
            return _error

        return _boolean

    def visitIntLiteral(self, ctx: decafParser.IntLiteralContext):
        return _int

    def visitCharLiteral(self, ctx: decafParser.CharLiteralContext):
        return _char

    def visitBoolLiteral(self, ctx: decafParser.BoolLiteralContext):
        return _boolean
