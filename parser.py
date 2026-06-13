"""
Analizador Sintactico - Lamar
"""

import tkinter as tk
import subprocess
import sys

# ── Llamar al lexer.exe para obtener los tokens ───────────────────────────────
def tokenizar(codigo):
    ruta = r"lexer.exe"
    resultado = subprocess.run(
        [ruta],
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

# Parser con descenso recursivo 
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
            self.errores.append(f"Error: esperaba '{valor}', encontro '{tok[1]}'")
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
                    self.errores.append(f"Token inesperado: '{self.actual()[1]}'")
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
        elif tok[1] == "return":
            return self.sentencia_return()
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
        return ("DECLARACION", [("TIPO", tipo[1]), ("ID", nombre[1]), valor])

    def asignacion(self):
        nombre = self.consumir()
        self.consumir("=")
        valor  = self.expr()
        self.consumir(";")
        return ("ASIGNACION", [("ID", nombre[1]), valor])

    def sentencia_if(self):
        self.consumir("if")
        self.consumir("(")
        cond = self.expr()
        self.consumir(")")
        self.consumir("{")
        cuerpo = self.programa()
        self.consumir("}")
        nodo = ("SI", [("CONDICION", [cond]), ("CUERPO", cuerpo[1])])
        if self.actual()[1] == "else":
            self.consumir("else")
            self.consumir("{")
            sino = self.programa()
            self.consumir("}")
            nodo[1].append(("SINO", sino[1]))
        return nodo

    def sentencia_while(self):
        self.consumir("while")
        self.consumir("(")
        cond = self.expr()
        self.consumir(")")
        self.consumir("{")
        cuerpo = self.programa()
        self.consumir("}")
        return ("MIENTRAS", [("CONDICION", [cond]), ("CUERPO", cuerpo[1])])

    def sentencia_return(self):
        self.consumir("return")
        val = self.expr()
        self.consumir(";")
        return ("RETORNO", [val])

    def sentencia_print(self):
        self.consumir("print")
        self.consumir("(")
        val = self.expr()
        self.consumir(")")
        self.consumir(";")
        return ("IMPRIMIR", [val])

    def expr(self):
        izq = self.term()
        while self.actual()[1] in ("+", "-", "==", "!=", "<", ">", "<=", ">="):
            op  = self.consumir()
            der = self.term()
            izq = (f"EXPR {op[1]}", [izq, der])
        return izq

    def term(self):
        izq = self.factor()
        while self.actual()[1] in ("*", "/"):
            op  = self.consumir()
            der = self.factor()
            izq = (f"TERM {op[1]}", [izq, der])
        return izq

    def factor(self):
        tok = self.actual()
        if tok[1] == "(":
            self.consumir("(")
            e = self.expr()
            self.consumir(")")
            return e
        elif tok[0] in ("ENTERO", "FLOTANTE", "CADENA", "IDENTIFICADOR", "PALABRA CLAVE"):
            self.pos += 1
            return (tok[0], tok[1])
        else:
            self.pos += 1
            return ("?", tok[1])

# ── Interfaz ───────────────────────────────────────────────────────────────────
ventana = tk.Tk()
ventana.title("Analizador Sintactico — Lamar")
ventana.geometry("900x600")
ventana.configure(bg="#1e3a5f")

tk.Label(ventana,
         text="Analizador Sintactico — Lamar  ",
         font=("Segoe UI", 11, "bold"), bg="#1e3a5f", fg="white",
         pady=10).pack(fill="x")

panel = tk.Frame(ventana, bg="#1e3a5f")
panel.pack(fill="both", expand=True, padx=8, pady=(0, 8))

# Editor izquierda
izq = tk.Frame(panel, bg="#1e3a5f")
izq.pack(side="left", fill="both", expand=True, padx=(0, 4))
tk.Label(izq, text="Codigo fuente:", font=("Segoe UI", 9, "bold"),
         bg="#1e3a5f", fg="#94b4d4").pack(anchor="w")
editor = tk.Text(izq, font=("Consolas", 11), bg="white", fg="#111827",
                 relief="flat", padx=8, pady=6)
editor.pack(fill="both", expand=True)

# Arbol derecha
der = tk.Frame(panel, bg="#1e3a5f")
der.pack(side="right", fill="both", expand=True, padx=(4, 0))
tk.Label(der, text="Arbol sintactico:", font=("Segoe UI", 9, "bold"),
         bg="#1e3a5f", fg="#94b4d4").pack(anchor="w")
resultado = tk.Text(der, font=("Consolas", 10), bg="#0f172a", fg="#7dd3fc",
                    relief="flat", padx=8, pady=6, state="disabled")
resultado.pack(fill="both", expand=True)

# Barra inferior
barra = tk.Frame(ventana, bg="#0f172a")
barra.pack(fill="x")
lbl_estado = tk.Label(barra, text="  Listo.", font=("Segoe UI", 9),
                      bg="#0f172a", fg="#94b4d4", anchor="w")
lbl_estado.pack(side="left", fill="x", expand=True, padx=8, pady=6)

def mostrar_arbol(nodo, nivel=0):
    indent = "  " * nivel
    if isinstance(nodo, tuple):
        tipo   = nodo[0]
        hijos  = nodo[1] if len(nodo) > 1 else []
        if isinstance(hijos, list):
            resultado.insert("end", f"{indent}[{tipo}]\n")
            for h in hijos:
                mostrar_arbol(h, nivel + 1)
        else:
            resultado.insert("end", f"{indent}[{tipo}]  {hijos}\n")

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

    resultado.config(state="normal")
    resultado.delete("1.0", "end")
    mostrar_arbol(arbol)

    if parser.errores:
        resultado.insert("end", "\n--- ERRORES ---\n")
        for e in parser.errores:
            resultado.insert("end", e + "\n")
        lbl_estado.config(
            text=f"  {len(parser.errores)} error(es) encontrado(s)",
            fg="#f87171")
    else:
        resultado.insert("end", "\nSin errores.")
        lbl_estado.config(
            text=f"  Correcto. {len(tokens)} tokens.",
            fg="#86efac")

    resultado.config(state="disabled")

tk.Button(barra, text="Analizar", command=analizar,
          bg="#2563eb", fg="white", font=("Segoe UI", 10, "bold"),
          relief="flat", padx=16, pady=5, cursor="hand2"
          ).pack(side="right", padx=8, pady=5)

editor.insert("end", """int x = 10;
float nota = 95.5;

if (x > 5) {
    print("Aprobado");
} else {
    print("Reprobado");
}

while (x > 0) {
    x = x - 1;
}

return x;
""")

ventana.mainloop()