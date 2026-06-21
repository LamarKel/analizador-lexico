import tkinter as tk
import subprocess

# Llamar al lexer.exe 
def tokenizar(codigo):
    resultado = subprocess.run(
        ["lexer.exe"],
        input=codigo,
        capture_output=True,
        text=True
    )
    tokens = []
    for linea in resultado.stdout.strip().split("\n"):
        if "|" in linea:
            partes = linea.split("|")
            tipo  = partes[0].strip()
            valor = partes[1].strip()
            tokens.append((tipo, valor))
    return tokens

#  Parser con descenso recursivo 
class Parser:
    def __init__(self, tokens):
        self.tokens  = tokens
        self.pos     = 0
        self.errores = []

    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", "$")

    def consumir(self, valor=None):
        tok = self.actual()
        if valor and tok[1] != valor:
            self.errores.append(f"Error sintactico: esperaba '{valor}', encontro '{tok[1]}'")
        self.pos += 1
        return tok

    def programa(self):
        nodo = ("PROGRAMA", [])
        while self.actual()[0] != "EOF" and self.actual()[1] != "}":
            inst = self.instruccion()
            if inst:
                nodo[1].append(inst)
            else:
                if self.actual()[0] != "EOF":
                    self.pos += 1
        return nodo

    def instruccion(self):
        tok = self.actual()
        if tok[1] in ("int", "float", "string", "bool"):
            return self.declaracion()
        elif tok[1] == "if":
            return self.sentencia_if()
        elif tok[1] == "while":
            return self.sentencia_while()
        elif tok[1] == "print":
            return self.sentencia_print()
        elif tok[0] == "IDENTIFICADOR":
            return self.asignacion()
        return None

    def declaracion(self):
        tipo   = self.consumir()
        nombre = self.consumir()
        self.consumir("=")
        valor  = self.expr()
        self.consumir(";")
        return ("DECLARACION", tipo[1], nombre[1], valor)

    def asignacion(self):
        nombre = self.consumir()
        self.consumir("=")
        valor  = self.expr()
        self.consumir(";")
        return ("ASIGNACION", nombre[1], valor)

    def sentencia_if(self):
        self.consumir("if")
        self.consumir("(")
        cond = self.expr()
        self.consumir(")")
        self.consumir("{")
        cuerpo = self.programa()
        self.consumir("}")
        sino = []
        if self.actual()[1] == "else":
            self.consumir("else")
            self.consumir("{")
            sino = self.programa()[1]
            self.consumir("}")
        return ("SI", cond, cuerpo[1], sino)

    def sentencia_while(self):
        self.consumir("while")
        self.consumir("(")
        cond = self.expr()
        self.consumir(")")
        self.consumir("{")
        cuerpo = self.programa()
        self.consumir("}")
        return ("MIENTRAS", cond, cuerpo[1])

    def sentencia_print(self):
        self.consumir("print")
        self.consumir("(")
        val = self.expr()
        self.consumir(")")
        self.consumir(";")
        return ("IMPRIMIR", val)

    def expr(self):
        izq = self.term()
        while self.actual()[1] in ("+", "-", "==", "!=", "<", ">", "<=", ">="):
            op  = self.consumir()
            der = self.term()
            izq = ("OP", op[1], izq, der)
        return izq

    def term(self):
        izq = self.factor()
        while self.actual()[1] in ("*", "/"):
            op  = self.consumir()
            der = self.factor()
            izq = ("OP", op[1], izq, der)
        return izq

    def factor(self):
        tok = self.actual()
        if tok[1] == "(":
            self.consumir("(")
            e = self.expr()
            self.consumir(")")
            return e
        elif tok[0] == "ENTERO":
            self.pos += 1
            return ("ENTERO", tok[1])
        elif tok[0] == "FLOTANTE":
            self.pos += 1
            return ("FLOTANTE", tok[1])
        elif tok[0] == "CADENA":
            self.pos += 1
            return ("CADENA", tok[1])
        elif tok[1] in ("true", "false"):
            self.pos += 1
            return ("BOOL", tok[1])
        elif tok[0] == "IDENTIFICADOR":
            self.pos += 1
            return ("ID", tok[1])
        else:
            self.pos += 1
            return ("ERROR", tok[1])

# Analizador Semantico
class AnalizadorSemantico:
    def __init__(self):
        self.tabla    = {}   
        self.errores  = []
        self.registro = []    

    def tipo_de(self, nodo):
        # devuelve el tipo de una expresion ya evaluada
        if nodo[0] == "ENTERO":   return "int"
        if nodo[0] == "FLOTANTE": return "float"
        if nodo[0] == "CADENA":   return "string"
        if nodo[0] == "BOOL":     return "bool"
        if nodo[0] == "ID":
            nombre = nodo[1]
            if nombre not in self.tabla:
                self.errores.append(f"Variable '{nombre}' no declarada")
                return "error"
            return self.tabla[nombre]
        if nodo[0] == "OP":
            op = nodo[1]
            t1 = self.tipo_de(nodo[2])
            t2 = self.tipo_de(nodo[3])
            if t1 == "error" or t2 == "error":
                return "error"
            if op in ("==","!=","<",">","<=",">="):
                if t1 != t2:
                    self.errores.append(
                        f"No se puede comparar '{t1}' con '{t2}' usando '{op}'")
                    return "error"
                return "bool"
            # operadores aritmeticos
            if t1 == "string" or t2 == "string":
                self.errores.append(
                    f"No se puede usar el operador '{op}' con tipo string")
                return "error"
            if t1 == t2:
                return t1
            if {t1,t2} == {"int","float"}:
                self.registro.append(
                    f"Conversion automatica de int a float en operacion '{op}'")
                return "float"
            self.errores.append(
                f"Tipos incompatibles: '{t1}' {op} '{t2}'")
            return "error"
        return "error"

    def visitar(self, nodo):
        tipo = nodo[0]

        if tipo == "PROGRAMA":
            for inst in nodo[1]:
                self.visitar(inst)

        elif tipo == "DECLARACION":
            _, tipo_decl, nombre, expr = nodo
            if nombre in self.tabla:
                self.errores.append(f"Variable '{nombre}' ya fue declarada antes")
            else:
                self.tabla[nombre] = tipo_decl
                self.registro.append(f"Se declara '{nombre}' como tipo {tipo_decl}")
            t_expr = self.tipo_de(expr)
            if t_expr != "error" and t_expr != tipo_decl:
                if {t_expr, tipo_decl} == {"int","float"}:
                    self.registro.append(
                        f"Conversion automatica al asignar a '{nombre}' (de {t_expr} a {tipo_decl})")
                else:
                    self.errores.append(
                        f"No se puede asignar tipo '{t_expr}' a la variable '{nombre}' de tipo '{tipo_decl}'")

        elif tipo == "ASIGNACION":
            _, nombre, expr = nodo
            if nombre not in self.tabla:
                self.errores.append(f"Variable '{nombre}' no declarada")
            else:
                t_var  = self.tabla[nombre]
                t_expr = self.tipo_de(expr)
                if t_expr != "error" and t_expr != t_var:
                    if {t_expr, t_var} == {"int","float"}:
                        self.registro.append(
                            f"Conversion automatica al asignar a '{nombre}'")
                    else:
                        self.errores.append(
                            f"No se puede asignar tipo '{t_expr}' a la variable '{nombre}' de tipo '{t_var}'")

        elif tipo == "SI":
            _, cond, cuerpo, sino = nodo
            t_cond = self.tipo_de(cond)
            if t_cond != "bool" and t_cond != "error":
                self.errores.append(
                    f"La condicion del if debe ser bool, se encontro '{t_cond}'")
            for inst in cuerpo:
                self.visitar(inst)
            for inst in sino:
                self.visitar(inst)

        elif tipo == "MIENTRAS":
            _, cond, cuerpo = nodo
            t_cond = self.tipo_de(cond)
            if t_cond != "bool" and t_cond != "error":
                self.errores.append(
                    f"La condicion del while debe ser bool, se encontro '{t_cond}'")
            for inst in cuerpo:
                self.visitar(inst)

        elif tipo == "IMPRIMIR":
            _, expr = nodo
            self.tipo_de(expr)

    def analizar(self, arbol):
        self.visitar(arbol)
        return self.errores, self.tabla, self.registro

# Interfaz
ventana = tk.Tk()
ventana.title("Analizador Semantico")
ventana.geometry("1000x650")
ventana.configure(bg="#1e5f4f")

tk.Label(ventana,
         font=("Segoe UI", 11, "bold"), bg="#1e5f4f", fg="white",
         pady=10).pack(fill="x")

panel = tk.Frame(ventana, bg="#1e5f4f")
panel.pack(fill="both", expand=True, padx=8, pady=(0, 8))

# Editor izquierda
izq = tk.Frame(panel, bg="#1e5f4f")
izq.pack(side="left", fill="both", expand=True, padx=(0, 4))
tk.Label(izq, text="Codigo fuente:", font=("Segoe UI", 9, "bold"),
         bg="#1e5f4f", fg="#94b4d4").pack(anchor="w")
editor = tk.Text(izq, font=("Consolas", 11), bg="white", fg="#111827",
                 relief="flat", padx=8, pady=6)
editor.pack(fill="both", expand=True)

# Resultado derecha
der = tk.Frame(panel, bg="#1e5f4f")
der.pack(side="right", fill="both", expand=True, padx=(4, 0))
tk.Label(der, text="Analisis semantico:", font=("Segoe UI", 9, "bold"),
         bg="#1e5f4f", fg="#94b4d4").pack(anchor="w")
resultado = tk.Text(der, font=("Consolas", 10), bg="#122a0f", fg="#7dd3fc",
                    relief="flat", padx=8, pady=6, state="disabled")
resultado.pack(fill="both", expand=True)
resultado.tag_config("ok",  foreground="#86efac")
resultado.tag_config("err", foreground="#f87171")
resultado.tag_config("tit", foreground="#fbbf24")
resultado.tag_config("nor", foreground="#7dd3fc")

# Barra inferior
barra = tk.Frame(ventana, bg="#122a0f")
barra.pack(fill="x")
lbl_estado = tk.Label(barra, text="  Listo.", font=("Segoe UI", 9),
                      bg="#122a0f", fg="#94b4d4", anchor="w")
lbl_estado.pack(side="left", fill="x", expand=True, padx=8, pady=6)

def analizar():
    codigo = editor.get("1.0", "end-1c")
    if not codigo.strip():
        return

    tokens = tokenizar(codigo)
    if not tokens:
        lbl_estado.config(text="  No se pudo conectar con lexer.exe", fg="#f87171")
        return

    parser = Parser(tokens)
    arbol  = parser.programa()

    semantico = AnalizadorSemantico()
    errores, tabla, registro = semantico.analizar(arbol)

    resultado.config(state="normal")
    resultado.delete("1.0", "end")

    resultado.insert("end", "TABLA DE SIMBOLOS\n", "tit")
    if tabla:
        for nombre, tipo in tabla.items():
            resultado.insert("end", f"  {nombre} : {tipo}\n", "nor")
    else:
        resultado.insert("end", "  (vacia)\n", "nor")

    resultado.insert("end", "\nREGISTRO DE ANALISIS\n", "tit")
    if registro:
        for r in registro:
            resultado.insert("end", f"  {r}\n", "nor")
    else:
        resultado.insert("end", "  Sin conversiones ni eventos especiales\n", "nor")

    resultado.insert("end", "\nERRORES SEMANTICOS\n", "tit")
    if parser.errores:
        for e in parser.errores:
            resultado.insert("end", f"  {e}\n", "err")
    if errores:
        for e in errores:
            resultado.insert("end", f"  {e}\n", "err")
    if not parser.errores and not errores:
        resultado.insert("end", "  Sin errores. El programa es semanticamente correcto.\n", "ok")

    resultado.config(state="disabled")

    total_err = len(parser.errores) + len(errores)
    if total_err == 0:
        lbl_estado.config(text=f"  Correcto. {len(tabla)} variables, 0 errores.", fg="#86efac")
    else:
        lbl_estado.config(text=f"  {total_err} error(es) encontrado(s).", fg="#f87171")

tk.Button(barra, text="Analizar", command=analizar,
          bg="#2563eb", fg="white", font=("Segoe UI", 10, "bold"),
          relief="flat", padx=16, pady=5, cursor="hand2"
          ).pack(side="right", padx=8, pady=5)

editor.insert("end", """int x = 10;
float promedio = 95.5;
string nombre = "Kelvin";

promedio = x;

if (x > 5) {
    print("Mayor que 5");
} else {
    print("Menor o igual");
}

while (x > 0) {
    x = x - 1;
}

y = 20;
""")

ventana.mainloop()
