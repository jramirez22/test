from antlr4.error.ErrorListener import ErrorListener


class ErrorHandler(ErrorListener):
    def __init__(self):
        super().__init__()

    def syntaxError(recognizer, offendingSymbol, line, column, msg, e):
        template = "SyntaxError: line: {}:{}. {}"
        errorMsg = "{}: {}".format(offendingSymbol, msg)

        print(template.format(line, column, errorMsg))

    def arrayError(line, name):
        template = "ArrayError: line:{}. {}"
        errorMsg = "Size of array '{}' is negative or 0".format(name)

        print(template.format(line, errorMsg))

    def declError(line, value):
        template = "DeclError: line:{}. {}"
        errorMsg = "Redeclaration of ‘{}’".format(value)

        print(template.format(line, errorMsg))

    def nameError(line, name):
        template = "NameError: line:{}. {}"
        errorMsg = "Name '{}' is not defined".format(name)

        print(template.format(line, errorMsg))

    def paramError(line, param, methodName):
        template = "ParamError: line:{}. {}"
        errorMsg = "Duplicate argument '{}' in '{}()'".format(param, methodName)

        print(template.format(line, errorMsg))

    def structError(line, name):
        template = "StructError: line:{}. {}"

        errorMsg = "Struct '{}' cannot have the same name as a built-in type"
        errorMsg = errorMsg.format(name)

        print(template.format(line, errorMsg))

    def returnError(line, returnType, methodType):
        template = "returnError: line:{}. {}"

        errorMsg = "The return type '{}' must be the same as the method '{}'"
        errorMsg = errorMsg.format(returnType, methodType)

        print(template.format(line, errorMsg))

    def typeError(line, value, errorCode=1):
        template = "TypeError: line:{}. {}"
        errorMsg = ""

        if errorCode == 1:
            errorMsg = "Unsupported operand type(s) for '{}'"
            errorMsg = errorMsg.format(value)

        elif errorCode == 2:
            errorMsg = "Conditional '{}' evaluates <expr> of type 'boolean'"
            errorMsg = errorMsg.format(value)

        elif errorCode == 3:
            errorMsg = "'{}' object is not callable"
            errorMsg = errorMsg.format(value)

        elif errorCode == 4:
            errorMsg = "'{}()' does not have the correct arguments"
            errorMsg = errorMsg.format(value)

        print(template.format(line, errorMsg))
