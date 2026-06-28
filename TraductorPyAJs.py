import tkinter as tk
import re

def convertir_linea(linea):
    s = linea.strip()
    if not s:
        return ""

    # Comentarios
    if s.startswith("#"):
        return "//" + s[1:]

    # Reemplazos globales de palabras clave
    s = re.sub(r'\bTrue\b',  'true',  s)
    s = re.sub(r'\bFalse\b', 'false', s)
    s = re.sub(r'\bNone\b',  'null',  s)
    s = re.sub(r'\band\b',   '&&',    s)
    s = re.sub(r'\bor\b',    '||',    s)
    s = re.sub(r'\bnot\b',   '!',     s)

    # print a console.log
    s = re.sub(r'\bprint\s*\(', 'console.log(', s)

    # len(x) a x.length
    s = re.sub(r'\blen\s*\((\w+)\)', r'\1.length', s)

    # .append( a .push(
    s = s.replace('.append(', '.push(')

    # f-strings  f"hola {nombre}" a `hola ${nombre}`
    def fstring(m):
        contenido = m.group(1)
        contenido = re.sub(r'\{([^}]+)\}', r'${\1}', contenido)
        return f'`{contenido}`'
    s = re.sub(r'f"([^"]*)"', fstring, s)
    s = re.sub(r"f'([^']*)'", fstring, s)

    # elif condition: a } else if (condition) {
    m = re.match(r'^elif\s+(.+):$', s)
    if m:
        return f'}} else if ({m.group(1)}) {{'

    # else: a } else {
    if s == 'else:':
        return '} else {'

    # if condition: a if (condition) {
    m = re.match(r'^if\s+(.+):$', s)
    if m:
        return f'if ({m.group(1)}) {{'

    # while condition: a while (condition) {
    m = re.match(r'^while\s+(.+):$', s)
    if m:
        return f'while ({m.group(1)}) {{'

    # for i in range(n): a for (let i = 0; i < n; i++) {
    m = re.match(r'^for\s+(\w+)\s+in\s+range\((\w+)\):$', s)
    if m:
        v, n = m.group(1), m.group(2)
        return f'for (let {v} = 0; {v} < {n}; {v}++) {{'

    # for i in range(inicio, fin): a for (let i = inicio; i < fin; i++) {
    m = re.match(r'^for\s+(\w+)\s+in\s+range\((.+),\s*(.+)\):$', s)
    if m:
        v, ini, fin = m.group(1), m.group(2), m.group(3)
        return f'for (let {v} = {ini}; {v} < {fin}; {v}++) {{'

    # for item in lista: a for (let item of lista) {
    m = re.match(r'^for\s+(\w+)\s+in\s+(\w+):$', s)
    if m:
        v, lst = m.group(1), m.group(2)
        return f'for (let {v} of {lst}) {{'

    # def nombre(params): a function nombre(params) {
    m = re.match(r'^def\s+(\w+)\s*\((.*)\):$', s)
    if m:
        nombre, params = m.group(1), m.group(2)
        return f'function {nombre}({params}) {{'

    # class Nombre: a class Nombre {
    m = re.match(r'^class\s+(\w+)\s*:$', s)
    if m:
        return f'class {m.group(1)} {{'

    # return
    m = re.match(r'^return\s+(.+)$', s)
    if m:
        return f'return {m.group(1)};'
    if s == 'return':
        return 'return;'

    # x += n a x += n;
    m = re.match(r'^(\w+)\s*(\+=|-=|\*=|/=)\s*(.+)$', s)
    if m:
        return f'{m.group(1)} {m.group(2)} {m.group(3)};'

    # asignacion simple x = valor a let x = valor;
    m = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', s)
    if m:
        return f'let {m.group(1)} = {m.group(2)};'

    # cualquier otra cosa: agregar punto y coma si no lo tiene
    if not s.endswith(('{', '}', ';', '//')):
        s += ';'
    return s


def traducir(codigo_python):
    lineas     = codigo_python.split('\n')
    resultado  = []
    pila       = [0]         
    vars_decl  = set()       

    i = 0
    while i < len(lineas):
        linea = lineas[i]
        stripped = linea.strip()

        # linea vacia
        if not stripped:
            resultado.append('')
            i += 1
            continue

        # calcular indentacion actual
        indent_n = len(linea) - len(linea.lstrip())

        # cerrar bloques si la indentacion bajo
        es_elif_else = stripped.startswith('elif ') or stripped == 'else:'
        while len(pila) > 1 and indent_n < pila[-1]:
            pila.pop()
            if not es_elif_else:
                cierre_indent = '    ' * (len(pila) - 1)
                resultado.append(cierre_indent + '}')

        # calcular indent de salida
        nivel_salida = '    ' * (len(pila) - 1)

        # traducir la linea
        js = convertir_linea(linea)

        # si abre bloque, empujar nivel de indentacion del siguiente
        abre_bloque = stripped.endswith(':') and not stripped.startswith('#')
        if abre_bloque:
            # buscar la indentacion real del primer hijo
            sig_indent = indent_n + 4
            for j in range(i + 1, len(lineas)):
                if lineas[j].strip():
                    sig_indent = len(lineas[j]) - len(lineas[j].lstrip())
                    break
            pila.append(sig_indent)

        # manejar re-asignaciones para no repetir 'let'
        m = re.match(r'^let (\w+) =', js)
        if m:
            var = m.group(1)
            if var in vars_decl:
                js = js[4:]   # quitar 'let '
            else:
                vars_decl.add(var)

        resultado.append(nivel_salida + js)
        i += 1

    # cerrar bloques que quedaron abiertos
    while len(pila) > 1:
        pila.pop()
        cierre_indent = '    ' * (len(pila) - 1)
        resultado.append(cierre_indent + '}')

    return '\n'.join(resultado)



# INTERFAZ GRAFICA

NEGRO   = "#15171c"
PANEL   = "#1c1f26"
BORDE   = "#2a2e38"
TEXTO   = "#cfd3dc"
TENUE   = "#6b7280"
AZUL    = "#60a5fa"
AZUL_BG = "#0f1f2d"
AMBAR   = "#fbbf24"
AMBAR_BG= "#1f1600"
VERDE   = "#86efac"
BLANCO  = "#f4f4f5"
ROJO    = "#f87171"

ventana = tk.Tk()
ventana.title("Traductor Python -> JavaScript")
ventana.geometry("1200x750")
ventana.configure(bg=NEGRO)

sans   = ("Segoe UI", 10)
sans_b = ("Segoe UI", 10, "bold")
sans_t = ("Segoe UI", 14, "bold")
mono   = ("Consolas", 11)

# encabezado
header = tk.Frame(ventana, bg=NEGRO)
header.pack(fill="x", padx=24, pady=(16, 8))
tk.Label(header, text="Traductor Python",
         font=sans_t, bg=NEGRO, fg=BLANCO).pack(side="left")
tk.Label(header, text="→",
         font=("Segoe UI", 14), bg=NEGRO, fg=TENUE).pack(side="left", padx=8)
tk.Label(header, text="JavaScript",
         font=sans_t, bg=NEGRO, fg=AMBAR).pack(side="left")
tk.Label(header, text="UTESA  ·  INF-920-001  ·  Kelvin Lamar",
         font=sans, bg=NEGRO, fg=TENUE).pack(side="left", padx=20)

# dos columnas
cols = tk.Frame(ventana, bg=NEGRO)
cols.pack(fill="both", expand=True, padx=16, pady=(0, 4))

def panel_editor(parent, titulo, color, color_bg, lado, editable=True):
    f = tk.Frame(parent, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
    f.pack(side=lado, fill="both", expand=True, padx=6)
    cab = tk.Frame(f, bg=color_bg, height=38)
    cab.pack(fill="x"); cab.pack_propagate(False)
    tk.Label(cab, text=titulo, font=sans_b, bg=color_bg, fg=color,
             pady=8).pack(side="left", padx=14)
    txt = tk.Text(f, font=mono, bg=PANEL, fg=TEXTO, relief="flat",
                  padx=12, pady=10, wrap="none", bd=0,
                  insertbackground=color,
                  state="normal" if editable else "disabled")
    txt.pack(fill="both", expand=True, padx=2, pady=2)
    return txt

txt_py = panel_editor(cols, "Python  (entrada)", AZUL,  AZUL_BG,  "left",  True)
txt_js = panel_editor(cols, "JavaScript  (salida)", AMBAR, AMBAR_BG, "right", False)

# barra inferior
barra = tk.Frame(ventana, bg=PANEL, height=50,
                 highlightbackground=BORDE, highlightthickness=1)
barra.pack(fill="x", side="bottom"); barra.pack_propagate(False)

lbl = tk.Label(barra, text="  Escribe codigo Python y presiona Traducir",
               font=sans, bg=PANEL, fg=TENUE, anchor="w")
lbl.pack(side="left", fill="x", expand=True, padx=10)

def traducir_todo():
    codigo = txt_py.get("1.0", "end-1c")
    if not codigo.strip():
        return
    resultado = traducir(codigo)
    txt_js.config(state="normal")
    txt_js.delete("1.0", "end")
    txt_js.insert("end", resultado)
    txt_js.config(state="disabled")
    lineas_py = len([l for l in codigo.split('\n') if l.strip()])
    lineas_js = len([l for l in resultado.split('\n') if l.strip()])
    lbl.config(
        text=f"  Traduccion completada  —  {lineas_py} lineas Python  →  {lineas_js} lineas JavaScript",
        fg=VERDE
    )

tk.Button(barra, text="Traducir  →", command=traducir_todo,
          bg=AMBAR, fg="#15171c", font=sans_b,
          relief="flat", padx=20, pady=10,
          cursor="hand2", bd=0,
          activebackground="#f59e0b"
          ).pack(side="right", padx=12, pady=8)

# codigo de ejemplo
txt_py.insert("end", '''\
# Programa de ejemplo en Python
def saludar(nombre):
    mensaje = f"Hola, {nombre}!"
    print(mensaje)

def suma(a, b):
    return a + b

x = 10
y = 20
resultado = suma(x, y)

if resultado > 25:
    print("El resultado es mayor que 25")
elif resultado == 30:
    print("El resultado es exactamente 30")
else:
    print("El resultado es menor o igual a 25")

numeros = [1, 2, 3, 4, 5]
total = 0

for i in range(len(numeros)):
    total += numeros[i]

print(total)

contador = 0
while contador < 5:
    print(contador)
    contador += 1

saludar("Kelvin")
''')

ventana.mainloop()