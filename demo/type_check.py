class Type:
    def __eq__(self, other):
        return isinstance(other, type(self))

class IntType(Type):
    def __str__(self):
        return "int"

class StringType(Type):
    def __str__(self):
        return "string"

class RecordType(Type):
    def __init__(self, fields):
        # fields is a dict mapping field names to their types
        self.fields = fields
        
    def __eq__(self, other):
        if not isinstance(other, RecordType):
            return False
        return self.fields == other.fields
    
    def __str__(self):
        return f"record {{{', '.join(f'{name}: {typ}' for name, typ in self.fields.items())}}}"

class ArrayType(Type):
    def __init__(self, element_type):
        self.element_type = element_type
        
    def __eq__(self, other):
        if not isinstance(other, ArrayType):
            return False
        return self.element_type == other.element_type
    
    def __str__(self):
        return f"array of {self.element_type}"

class NamedType(Type):
    def __init__(self, name, actual_type=None):
        self.name = name
        self.actual_type = actual_type
        
    def __eq__(self, other):
        if isinstance(other, NamedType):
            return self.name == other.name
        if self.actual_type:
            return self.actual_type == other
        return False
    
    def __str__(self):
        return self.name

class NilType(Type):
    def __eq__(self, other):
        return isinstance(other, NilType) or isinstance(other, RecordType)
    
    def __str__(self):
        return "nil"

class BoolType(Type):
    def __str__(self):
        return "bool"

class TypeChecker:
    def __init__(self):
        self.env = {}  # Environment for variables
        self.type_env = {
            "int": IntType(),
            "string": StringType(),
            "nil": NilType(),
            "bool": BoolType()
        }  # Environment for type definitions
        self.indent = 0
        
    def log(self, msg):
        print("  " * self.indent + msg)
        
    def check(self, ast):
        self.log("Starting type checking...")
        return self.check_expr(ast)
    
    def check_expr(self, expr):
        self.indent += 1
        result = None
        
        self.log(f"Checking expression: {type(expr).__name__}")
        
        if isinstance(expr, IntLiteral):
            self.log(f"Found integer literal: {expr.value}")
            result = IntType()
        
        elif isinstance(expr, StringLiteral):
            self.log(f"Found string literal: {expr.value}")
            result = StringType()
            
        elif isinstance(expr, NilLiteral):
            self.log("Found nil literal")
            result = NilType()
        
        elif isinstance(expr, VarExpr):
            self.log(f"Checking variable: {expr.name}")
            if expr.name not in self.env:
                raise TypeError(f"Undefined variable: {expr.name}")
            result = self.env[expr.name]
            self.log(f"Variable {expr.name} has type: {result}")
        
        elif isinstance(expr, BinOpExpr):
            self.log(f"Checking binary operation: {expr.op}")
            left_type = self.check_expr(expr.left)
            right_type = self.check_expr(expr.right)
            self.log(f"Left operand type: {left_type}")
            self.log(f"Right operand type: {right_type}")
            
            # Arithmetic operations
            if expr.op in ['+', '-', '*', '/']:
                if isinstance(left_type, IntType) and isinstance(right_type, IntType):
                    result = IntType()
                    self.log(f"Arithmetic operation returns: {result}")
                else:
                    raise TypeError(f"Type error: {expr.op} requires integer operands")
            
            # String concatenation
            elif expr.op == '+' and isinstance(left_type, StringType) and isinstance(right_type, StringType):
                result = StringType()
                self.log("String concatenation returns: string")
            
            # Comparison operations
            elif expr.op in ['=', '<>', '<', '>', '<=', '>=']:
                if type(left_type) == type(right_type) or \
                   (isinstance(left_type, RecordType) and isinstance(right_type, NilType)) or \
                   (isinstance(left_type, NilType) and isinstance(right_type, RecordType)):
                    result = BoolType()
                    self.log("Comparison operation returns: bool")
                else:
                    raise TypeError(f"Type error: {expr.op} requires operands of the same type")
            
            else:
                raise TypeError(f"Unsupported operator: {expr.op}")
        
        elif isinstance(expr, IfExpr):
            cond_type = self.check_expr(expr.condition)
            if not isinstance(cond_type, BoolType):
                raise TypeError("Condition in if-expression must be boolean")
            
            then_type = self.check_expr(expr.then_expr)
            if expr.else_expr:
                else_type = self.check_expr(expr.else_expr)
                if then_type != else_type:
                    raise TypeError("Types of then and else branches must match")
                result = then_type
            else:
                # If no else branch, then the if-expression must be in a void context
                result = None
        
        elif isinstance(expr, ArrayExpr):
            self.log(f"Checking array expression of type: {expr.type_name}")
            # Check if the type exists
            if expr.type_name not in self.type_env:
                raise TypeError(f"Undefined type: {expr.type_name}")
            
            array_type = self.type_env[expr.type_name]
            if not isinstance(array_type, ArrayType):
                raise TypeError(f"{expr.type_name} is not an array type")
            
            # Check size expression
            self.log("Checking array size expression")
            size_type = self.check_expr(expr.size)
            if not isinstance(size_type, IntType):
                raise TypeError("Array size must be an integer")
            
            # Check init expression
            self.log("Checking array init expression")
            init_type = self.check_expr(expr.init)
            if init_type != array_type.element_type:
                raise TypeError(f"Array initialization type mismatch: expected {array_type.element_type}, got {init_type}")
            
            result = array_type
            self.log(f"Array expression type: {result}")
        
        elif isinstance(expr, RecordExpr):
            # Check if the type exists
            if expr.type_name not in self.type_env:
                raise TypeError(f"Undefined type: {expr.type_name}")
            
            record_type = self.type_env[expr.type_name]
            if not isinstance(record_type, RecordType):
                raise TypeError(f"{expr.type_name} is not a record type")
            
            # Check that all required fields are present
            field_names = {field.name for field in expr.fields}
            required_fields = set(record_type.fields.keys())
            
            if field_names != required_fields:
                missing = required_fields - field_names
                extra = field_names - required_fields
                error_msg = ""
                if missing:
                    error_msg += f"Missing fields: {', '.join(missing)}. "
                if extra:
                    error_msg += f"Extra fields: {', '.join(extra)}."
                raise TypeError(error_msg)
            
            # Check field types
            for field in expr.fields:
                field_type = self.check_expr(field.expr)
                expected_type = record_type.fields[field.name]
                if field_type != expected_type and not (isinstance(field_type, NilType) and isinstance(expected_type, RecordType)):
                    raise TypeError(f"Field {field.name} type mismatch: expected {expected_type}, got {field_type}")
            
            result = record_type
        
        elif isinstance(expr, SubscriptExpr):
            self.log("Checking array subscript")
            array_type = self.check_expr(expr.array)
            self.log(f"Array variable type: {array_type}")
            
            if not isinstance(array_type, ArrayType):
                raise TypeError(f"Cannot subscript non-array type: {array_type}")
                
            index_type = self.check_expr(expr.index)
            self.log(f"Index expression type: {index_type}")
            
            if not isinstance(index_type, IntType):
                raise TypeError(f"Array index must be an integer, got: {index_type}")
                
            result = array_type.element_type
            self.log(f"Subscript expression type: {result}")
        
        elif isinstance(expr, FieldExpr):
            record_type = self.check_expr(expr.record)
            
            # Check that it's a record
            if not isinstance(record_type, RecordType):
                raise TypeError(f"Cannot access field of non-record type: {record_type}")
                
            # Check that the field exists
            if expr.field_name not in record_type.fields:
                raise TypeError(f"Field {expr.field_name} not found in record type {record_type}")
                
            # Return the field type
            result = record_type.fields[expr.field_name]
        
        elif isinstance(expr, AssignExpr):
            self.log("Checking assignment expression")
            if not self.is_lvalue(expr.var):
                raise TypeError(f"Cannot assign to non-lvalue")
                
            var_type = self.check_expr(expr.var)
            self.log(f"Left side type: {var_type}")
            
            expr_type = self.check_expr(expr.expr)
            self.log(f"Right side type: {expr_type}")
            
            if var_type != expr_type and not (isinstance(expr_type, NilType) and isinstance(var_type, RecordType)):
                raise TypeError(f"Type mismatch in assignment: expected {var_type}, got {expr_type}")
                
            self.log("Assignment type checks successfully")
            result = None
        
        elif isinstance(expr, WhileExpr):
            # Check the condition
            cond_type = self.check_expr(expr.condition)
            if not isinstance(cond_type, BoolType):
                raise TypeError(f"While condition must be boolean, got: {cond_type}")
                
            # Check the body
            self.check_expr(expr.body)
            
            # While has no value in Tiger
            result = None
        
        elif isinstance(expr, ForExpr):
            # Check the range expressions
            from_type = self.check_expr(expr.from_expr)
            to_type = self.check_expr(expr.to_expr)
            
            if not isinstance(from_type, IntType) or not isinstance(to_type, IntType):
                raise TypeError(f"For loop range must be integers")
                
            # Add the loop variable to the environment
            old_type = self.env.get(expr.var_name)
            self.env[expr.var_name] = IntType()
            
            # Check the body
            self.check_expr(expr.body)
            
            # Restore the environment
            if old_type:
                self.env[expr.var_name] = old_type
            else:
                del self.env[expr.var_name]
                
            # For has no value in Tiger
            result = None
        
        elif isinstance(expr, LetExpr):
            self.log("Checking let expression")
            # Save the old environment
            old_env = self.env.copy()
            old_type_env = self.type_env.copy()
            
            self.log("Processing declarations...")
            # Process declarations
            for decl in expr.decls:
                self.check_decl(decl)
                
            self.log("Checking let body...")
            # Check the body
            result = self.check_expr(expr.body)
            self.log(f"Let body type: {result}")
            
            # Restore the environment
            self.env = old_env
            self.type_env = old_type_env
            self.log("Restored previous environment")
        
        elif isinstance(expr, SeqExpr):
            self.log("Checking sequence expression")
            # Check each expression in sequence
            result = None
            for e in expr.exprs:
                result = self.check_expr(e)
                self.log(f"Sequence expression result type: {result}")
        
        self.indent -= 1
        return result
    
    def is_lvalue(self, expr):
        return isinstance(expr, VarExpr) or \
               isinstance(expr, SubscriptExpr) or \
               isinstance(expr, FieldExpr)
               
    def check_decl(self, decl):
        self.indent += 1
        self.log(f"Checking declaration: {type(decl).__name__}")
        
        if isinstance(decl, TypeDecl):
            if isinstance(decl, ArrayTypeDecl):
                self.log(f"Processing array type declaration: {decl.name}")
                element_type = self.resolve_type(decl.element_type)
                self.type_env[decl.name] = ArrayType(element_type)
                self.log(f"Added array type {decl.name} with element type {element_type}")
                
        elif isinstance(decl, VarDecl):
            self.log(f"Processing variable declaration: {decl.name}")
            if decl.type_name:
                if decl.type_name not in self.type_env:
                    raise TypeError(f"Undefined type: {decl.type_name}")
                var_type = self.type_env[decl.type_name]
                self.log(f"Explicit type: {var_type}")
                
                if decl.init:
                    init_type = self.check_expr(decl.init)
                    self.log(f"Initialization expression type: {init_type}")
                    if init_type != var_type and not (isinstance(init_type, NilType) and isinstance(var_type, RecordType)):
                        raise TypeError(f"Variable initialization type mismatch: expected {var_type}, got {init_type}")
            else:
                if not decl.init:
                    raise TypeError("Cannot infer type without initialization")
                var_type = self.check_expr(decl.init)
                self.log(f"Inferred type: {var_type}")
            
            self.env[decl.name] = var_type
            self.log(f"Added variable {decl.name} with type {var_type}")
            
        elif isinstance(decl, FunctionDecl):
            # Check parameter types
            param_types = []
            for param in decl.params:
                if param.type_name not in self.type_env:
                    raise TypeError(f"Undefined parameter type: {param.type_name}")
                param_types.append((param.name, self.type_env[param.type_name]))
            
            # Check return type if specified
            return_type = None
            if decl.return_type:
                if decl.return_type not in self.type_env:
                    raise TypeError(f"Undefined return type: {decl.return_type}")
                return_type = self.type_env[decl.return_type]
            
            # Save old environment and add parameters
            old_env = self.env.copy()
            for name, typ in param_types:
                self.env[name] = typ
            
            # Check function body
            body_type = self.check_expr(decl.body)
            
            # Check return type compatibility
            if return_type and body_type != return_type:
                raise TypeError(f"Function return type mismatch: expected {return_type}, got {body_type}")
            
            # Restore environment
            self.env = old_env
        
        self.indent -= 1
    
    def resolve_type(self, type_name):
        if type_name in self.type_env:
            typ = self.type_env[type_name]
            # If it's a named type, resolve to the actual type
            if isinstance(typ, NamedType) and typ.actual_type:
                return typ.actual_type
            return typ
        else:
            raise TypeError(f"Undefined type: {type_name}")


########
# Example Tiger AST nodes for demonstration
class IntLiteral:
    def __init__(self, value):
        self.value = value

class StringLiteral:
    def __init__(self, value):
        self.value = value

class NilLiteral:
    pass

class VarExpr:
    def __init__(self, name):
        self.name = name

class BinOpExpr:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class IfExpr:
    def __init__(self, condition, then_expr, else_expr=None):
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr

class ArrayExpr:
    def __init__(self, type_name, size, init):
        self.type_name = type_name
        self.size = size
        self.init = init

class SubscriptExpr:
    def __init__(self, array, index):
        self.array = array
        self.index = index

class FieldExpr:
    def __init__(self, record, field_name):
        self.record = record
        self.field_name = field_name

class RecordExpr:
    def __init__(self, type_name, fields):
        self.type_name = type_name
        self.fields = fields

class Field:
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class AssignExpr:
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

class WhileExpr:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ForExpr:
    def __init__(self, var_name, from_expr, to_expr, body):
        self.var_name = var_name
        self.from_expr = from_expr
        self.to_expr = to_expr
        self.body = body

class LetExpr:
    def __init__(self, decls, body):
        self.decls = decls
        self.body = body

class SeqExpr:
    def __init__(self, exprs):
        self.exprs = exprs

class VarDecl:
    def __init__(self, name, type_name=None, init=None):
        self.name = name
        self.type_name = type_name
        self.init = init

class TypeDecl:
    pass

class TypeAlias(TypeDecl):
    def __init__(self, name, type_name):
        self.name = name
        self.type = type_name

class RecordTypeDecl(TypeDecl):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

class RecordField:
    def __init__(self, name, type_name):
        self.name = name
        self.type = type_name

class ArrayTypeDecl(TypeDecl):
    def __init__(self, name, element_type):
        self.name = name
        self.element_type = element_type

class FunctionDecl:
    def __init__(self, name, params, return_type, body):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body

class Parameter:
    def __init__(self, name, type_name):
        self.name = name
        self.type_name = type_name

# Example Tiger program represented as an AST:
# let
#   type tigerArray = array of int
#   var a := tigerArray[10] of 0
# in
#   a[5] := 100;
#   a[5] + 20
# end

tiger_program = LetExpr(
    decls=[
        ArrayTypeDecl("tigerArray", "int"),
        VarDecl("a", init=ArrayExpr("tigerArray", IntLiteral(10), IntLiteral(0)))
    ],
    body=SeqExpr([
        AssignExpr(
            SubscriptExpr(VarExpr("a"), IntLiteral(5)),
            IntLiteral(100)
        ),
        BinOpExpr(
            SubscriptExpr(VarExpr("a"), IntLiteral(5)),
            "+",
            IntLiteral(20)
        )
    ])
)

# Type check the Tiger program
#checker = TypeChecker()
#result_type = checker.check(tiger_program)
#print(f"\nFinal program result type: {result_type}")  # Should print "int"

# Simpler example:
# let 
#   var x := 5 + 3 
# in 
#   x * 2 
# end

simple_program = LetExpr(
    decls=[
        VarDecl("x", init=BinOpExpr(
            IntLiteral(5),
            "+",
            IntLiteral(3)
        ))
    ],
    body=BinOpExpr(
        VarExpr("x"),
        "*",
        IntLiteral(2)
    )
)

print("\n=== Running simple example ===")
checker = TypeChecker()
simple_result = checker.check(simple_program)
print(f"\nFinal program result type: {simple_result}")  # Should print "int"