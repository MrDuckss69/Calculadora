from flask import Flask, request, jsonify, render_template
import re
import ply.lex as lex

app = Flask(__name__)

# Definir los tokens para el análisis léxico con ply
tokens = (
    'NUMBER',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
)

# Reglas de expresión regular para los tokens
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_ignore = ' \t'

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value)
    return t

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Construir el analizador léxico con ply
lexer = lex.lex()

# Función para realizar el análisis léxico usando expresiones regulares
def analisis_lexico_para_tabla(expression):
    tokens_expr = [
        (r'\d+', 'Número'),      # Detecta la parte numérica entera
        (r'\.', 'Punto Decimal'),# Detecta el punto decimal
        (r'\+', 'Suma'),         # Detecta el operador suma
        (r'-', 'Resta'),         # Detecta el operador resta
        (r'\*', 'Multiplicación'),# Detecta el operador multiplicación
        (r'/', 'División'),      # Detecta el operador división
        (r'\(', 'Paréntesis Izquierdo'),# Detecta paréntesis izquierdo
        (r'\)', 'Paréntesis Derecho')   # Detecta paréntesis derecho
    ]
    
    tokens = []
    pos = 0
    while pos < len(expression):
        match = None
        for token_expr in tokens_expr:
            pattern, token_type = token_expr
            regex = re.compile(pattern)
            match = regex.match(expression, pos)
            if match:
                token_value = match.group(0)
                tokens.append({"token": token_value, "type": token_type})
                pos = match.end(0)
                break
        if not match:
            pos += 1  # Ignorar caracteres no válidos

    return tokens

def analisis_lexico_para_arbol(expression):
    tokens_expr = [
        (r'\d+(\.\d+)?', 'NUMBER'),  # Detecta el número completo, incluidos decimales
        (r'[+\-*/]', 'OPERATOR'),
        (r'[()]', 'PARENTHESIS')
    ]
    
    tokens = []
    pos = 0
    while pos < len(expression):
        match = None
        for token_expr in tokens_expr:
            pattern, token_type = token_expr
            regex = re.compile(pattern)
            match = regex.match(expression, pos)
            if match:
                token_value = match.group(0)
                tokens.append({"token": token_value, "type": token_type})
                pos = match.end(0)
                break
        if not match:
            pos += 1  # Ignorar caracteres no válidos

    return tokens


# Función para evaluar la expresión (con manejo de errores)
def evaluar_expresion(expression):
    try:
        resultado = eval(expression)
        return {"status": "success", "resultado": resultado}
    except ZeroDivisionError:
        return {"status": "error", "message": "Error: División entre 0 no permitida"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Estructura de árbol de nodos
class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

# Función para construir el árbol de operaciones
def construir_arbol(tokens):
    def parse_expression(index):
        node_stack = []
        op_stack = []

        while index < len(tokens):
            token = tokens[index]['token']
            tipo = tokens[index]['type']

            if tipo == 'NUMBER':
                node_stack.append(Node(token))

            elif token == '(':
                subtree, index = parse_expression(index + 1)
                node_stack.append(subtree)

            elif token == ')':
                break

            elif tipo == 'OPERATOR':
                while op_stack and op_stack[-1] in ['*', '/']:
                    operator = op_stack.pop()
                    right = node_stack.pop()
                    left = node_stack.pop()
                    node_stack.append(Node(operator, left, right))
                op_stack.append(token)

            index += 1

        while op_stack:
            operator = op_stack.pop()
            right = node_stack.pop()
            left = node_stack.pop()
            node_stack.append(Node(operator, left, right))

        return node_stack[0], index

    tree, _ = parse_expression(0)
    return tree

# Función para recorrer el árbol de forma recursiva
def recorrer_arbol(node):
    if node is None:
        return None

    return {
        'value': str(node.value),
        'left': recorrer_arbol(node.left),
        'right': recorrer_arbol(node.right)
    }

# Función para describir los tokens usando ply
def describir_token(tok):
    if tok.type == 'NUMBER':
        if '.' in str(tok.value):
            return 'Decimal'
        else:
            return 'Entero'
    elif tok.type == 'PLUS':
        return 'Suma'
    elif tok.type == 'MINUS':
        return 'Resta'
    elif tok.type == 'TIMES':
        return 'Multiplicación'
    elif tok.type == 'DIVIDE':
        return 'División'
    elif tok.type == 'LPAREN':
        return 'Paréntesis Izquierdo'
    elif tok.type == 'RPAREN':
        return 'Paréntesis Derecho'
    else:
        return 'Desconocido'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    data = request.get_json()
    expression = data['expression']

    # Evaluar la expresión aritmética
    resultado = evaluar_expresion(expression)

    # Análisis léxico para mostrar en la tabla
    tokens_regex = analisis_lexico_para_tabla(expression)

    return jsonify({
        'resultado': resultado.get('resultado', None),
        'status': resultado.get('status'),
        'message': resultado.get('message', ''),
        'tokens_regex': tokens_regex
    })

@app.route('/tree', methods=['POST'])
def generar_arbol():
    data = request.get_json()
    expression = data.get('expression', '')

    # Análisis léxico para construir el árbol
    tokens = analisis_lexico_para_arbol(expression)
    tree = construir_arbol(tokens)

    arbol_representation = recorrer_arbol(tree)
    
    return jsonify({
        "arbol": arbol_representation
    })

if __name__ == '__main__':
    app.run(debug=True)