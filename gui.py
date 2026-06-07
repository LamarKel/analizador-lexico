import tkinter as tk
import subprocess

def analizar():
    codigo = entrada.get("1.0", "end-1c")
    resultado = subprocess.run(
        [r"D:\Documentos\COMPILADORE\AnalizadorLexico\lexer.exe"],
        input=codigo, capture_output=True, text=True
    )
    salida.config(state="normal")
    salida.delete("1.0", "end")
    salida.insert("end", resultado.stdout)
    salida.config(state="disabled")

ventana = tk.Tk()
ventana.title("Analizador Lexico")
ventana.geometry("600x500")

tk.Label(ventana, text="Escribe tu codigo:").pack(pady=5)
entrada = tk.Text(ventana, height=10)
entrada.pack(padx=10, fill="x")

tk.Button(ventana, text="Analizar", command=analizar).pack(pady=10)

tk.Label(ventana, text="Tokens encontrados:").pack()
salida = tk.Text(ventana, height=15, state="disabled")
salida.pack(padx=10, fill="x")

ventana.mainloop()