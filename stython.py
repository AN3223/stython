from queue import LifoQueue
import queue
from inspect import signature as sig
from tatsu import compile
from tatsu.ast import AST
from fpbox import head, tail, last, reverse, map
from string import digits
from copy import deepcopy


class Stython(Exception):
    pass


queue.Empty = Stython("Stack is empty")


class Stack(LifoQueue):
    def push(self, x):
        self.put(x)

    def pop(self):
        return self.get_nowait()


class String:
    @staticmethod
    def from_ast(x: AST) -> str:
        return list(x.values())[0][1:-1]

    @staticmethod
    def to_ast(x: str) -> AST:
        return AST(String='"{}"'.format(x))

    @staticmethod
    def is_string(x: AST) -> bool:
        if not isinstance(x, AST):
            return False
        return 'String' in x.keys()


class Func:
    @staticmethod
    def is_fn(x: AST) -> bool:
        if not isinstance(x, AST):
            return False
        return 'Func' in x.keys()


class List:
    @staticmethod
    def is_list(x: AST) -> bool:
        if not isinstance(x, AST):
            return False
        return 'List' in x.keys()

    @staticmethod
    def as_str(x: AST) -> str:
        return x['List']


class Combinator:
    def __init__(self, f):
        self.f = f

    @staticmethod
    def run(xs, stack):
        run(xs, stack)

    @staticmethod
    def slice(xs):
        return xs[1:-1]

    @staticmethod
    def foresee(xs):
        return peekstack(run(xs[1:-1]))


GRAMMAR = compile(r'''
    @@grammar::Stython

    start = statement | expr;
    statement = (def) [&(';')];
    expr = {type}+;
    type = listeral | integer | string | func | bool;
    listeral = List:/\[.+?\]/;
    def = Func+:/\w[a-zA-Z\d]*/ "=" Func+:{expr}+;
    bool = 'True' | 'False';
    func = /\w[a-zA-Z\d]*/ | /[+\/*\-=!><%]*/;
    string = String:/".+?"/;
    integer = /\d+/;
''')

CORE_FUNCS = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '/': lambda x, y: x / y,
    '*': lambda x, y: x * y,
    '%': lambda x, y: x % y,
    '==': lambda x, y: x == y,
    '!=': lambda x, y: x != y,
    '>=': lambda x, y: x >= y,
    '<=': lambda x, y: x <= y,
    '>': lambda x, y: x > y,
    '<': lambda x, y: x < y,
    'pop': lambda x: None,
    'swap': lambda x, y: (y, x),
    'dup': lambda x: (x, x),
    'over': lambda x, y: (x, y, x),
    'rot': lambda x, y, z: (y, z, x),
    'i': Combinator(lambda xs, stack: Combinator.run(Combinator.slice(xs), stack)),
    'map': Combinator(lambda xs, f, stack:
                      tuple(
                          [Combinator.run(f'{x} {Combinator.slice(f)}', stack) for x in Combinator.foresee(xs)]
                      )
                      )  # TODO: Figure out why this isn't pure
}


def compute(tokens: list, stack=Stack(), scope={}):
    for xs in tokens:
        if Func.is_fn(xs):
            func = xs['Func']
            scope[func[0]] = func[1][0]
        else:  # Expressions fall in here
            for x in xs:  # Breaking down the expression
                if not isinstance(x, AST):
                    if x in CORE_FUNCS.keys():  # Runs core functions
                        x = pyfunc(CORE_FUNCS[x], stack)
                    elif x in scope.keys():  # Runs user-defined functions
                        compute([scope[x]], stack=stack)
                        x = None

                if read(x) is not None:  # Pushes expressions
                    if isinstance(x, tuple):  # Tuples make multiple pushes
                        for y in x:
                            if y is not None:
                                stack.push(read(y))
                    else:
                        stack.push(read(x))
    return stack


def read(xs):
    if isinstance(xs, str):
        if xs == 'True':
            return True
        elif xs == 'False':
            return False
        num = False
        for x in xs:
            if x in digits:
                num = True
            else:
                num = False
                break
        if num:
            return int(xs)
    elif String.is_string(xs):
        return String.from_ast(xs)
    elif List.is_list(xs):
        return List.as_str(xs)
    else:
        return xs


def pyfunc(f, stack: Stack):
    if isinstance(f, Combinator):
        xs = reverse([stack.pop() for _ in range(params(f.f) - 1)])
        xs.append(stack)
        result = f.f(*xs)
    else:
        xs = reverse([stack.pop() for _ in range(params(f))])
        result = f(*xs)
    if isinstance(result, str):
        result = String.to_ast(result)
    return result


def params(f) -> int:
    return len(sig(f).parameters)


def ast(xs: str) -> list:
    for x in xs.splitlines():
        yield GRAMMAR.parse(x)


def run(xs: str, stack=Stack()) -> Stack:
    # print(list(ast(xs)))  # DEBUG
    return compute(list(ast(xs)), stack=stack)


def dumpstack(stack: Stack) -> list:
    xs = []
    while not stack.empty():
        xs.append(stack.get())
    return xs


def peekstack(stack: Stack) -> list:
    new_stack = reverse(dumpstack(stack))
    for x in new_stack:
        stack.put(x)
    return new_stack


def interactive():
    stack = Stack()
    while True:
        try:
            ui = input('stython> ')
            current = peekstack(run(ui, stack=stack))
            if current:
                print(current)
        except Exception as e:
            print('Error: {} "{}"'.format(type(e).__name__, e))


def interactive_debug():
    stack = Stack()
    while True:
        ui = input('stython> ')
        current = peekstack(run(ui, stack=stack))
        if current:
            print(current)


if __name__ == '__main__':
    interactive()
