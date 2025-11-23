
from bs4 import BeautifulSoup
import re
import sys
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Set, FrozenSet as FS, Deque, Any
from types import UnionType
import pickle
import markdown
def to_html(code: str) -> str:
    """Convierte el código .iml procesado en un HTML completo y bien formado."""
    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {extra_head}
</head>
<body>
{body}
</body>
</html>
"""

    # --- Extraer título y contenido adicional para el <head> ---
    title_match = re.search(r"--title\s+(.+)", code)
    title = title_match.group(1).strip() if title_match else "Documento IML"

    extra_head = "\n".join(
        head.strip() for head in re.findall(r"--head\s+(.+)", code)
    )

    # Limpiar las directivas del código antes del body
    code = re.sub(r"--title\s+.+\n?", "", code)
    code = re.sub(r"--head\s+.+\n?", "", code)

    # --- Transformar bloques Mermaid ---
    if "```mermaid" in code:
        code = re.sub(
            r"```mermaid\s*\n(.*?)\n```",
            r'<div class="mermaid">\1</div>',
            code,
            flags=re.DOTALL
        )
        mermaid_script = '    <script src="https://unpkg.com/mermaid@10/dist/mermaid.min.js"></script>'
    else:
        mermaid_script = "    "

    # --- Reemplazar cuadros ---
    code = code.replace("<cuadro>", "<div>").replace("</cuadro>", "</div>")

    # --- Alinear indentación simple ---
    code = "\n".join(line.strip() for line in code.splitlines())

    # --- Ensamblar HTML ---
    # --- Convertir el resto de Markdown a HTML ---
    code = markdown.markdown(
       code,
        extensions=["fenced_code", "tables", "sane_lists"]
    )

    html_final = HTML_TEMPLATE.format(
        title=title,
        extra_head= extra_head + "\n\t" + mermaid_script,
        body=code.strip()
    )
    soup = BeautifulSoup(html_final, "html.parser")
    html_final = soup.prettify()
    html_final = re.sub(r"\s*<p>\n\s*--meta.*\n\s*</p>", "", html_final, flags=re.DOTALL)
    return html_final


class collection(ABC):
    @abstractmethod
    def __getitem__(cls, ctype) -> UnionType:
        raise NotImplementedError("abstract class not have implemented errors")
    
class mutcoll(collection):
    @classmethod
    def __getitem__(cls, ctype=Any) -> UnionType:
        return List[ctype] | Dict[ctype, ctype] | Set[ctype] | Deque[ctype]

class notmutcoll(collection):
    @classmethod
    def __getitem__(cls, ctype=Any) -> UnionType:
        return Tuple[ctype] | FS[Set[ctype] | ctype]
    
def compile_file(argv: mutcoll[Any] | notmutcoll[Any]) -> None:
    with open(argv[1], encoding="utf-8") as f:
            c = f.read()
    with open(argv[2], "wb") as f:
        pickle.dump(c, f)
    return None
def load_file(path) -> str:
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except:
        return "file not found"
def main(argv: mutcoll[Any] | notmutcoll[Any]):
    html_yes =  False
    if argv[1] == "--init":
        if argv[2] == "-yes":
            with open("intro.imlf", "wb") as f:
                pickle.dump("", f)
            with open("outro.imlf", "wb") as f:
                pickle.dump("", f)
            with open("body.imlf", "wb") as f:
                pickle.dump("", f)
            with open("main.iml", "w") as f:
                f.write("""
--const -name your name
--const -surname your surname
--const -autor -name -surname

--use intro.imlf

--use body.imlf

--use outro.iml
""")
        else:
            with open("main.iml", "w") as f:
                f.write("")
    elif len(argv) == 4 and argv[3] == "-c":
        compile_file(argv)
        return None
    elif len(argv) == 4 and argv[3] == "-h":
        html_yes =  True
    elif len(argv) == 3: 
        None
    else:
        sys.exit("arguments error")
        
    with open(argv[1], encoding="utf-8") as f:
        code = f.read()
    # --- Reemplazar --use <file> por contenido del archivo primero ---
    use_pattern = r"--use\s+(.+)"
    for match in re.findall(use_pattern, code):
        file_name = match
        file_path = os.path.join(os.path.dirname(argv[1]), file_name)
        if os.path.isfile(file_path):
            content = load_file(file_path)
            code = code.replace(f"--use {file_name}", content)
        else:
            print(f"Advertencia: archivo {file_name} no encontrado")
    # Borrar líneas --use que no fueron reemplazadas
    code = re.sub(use_pattern + r"\n?", "", code)
    # Sustituciones para encabezados con @
    for n in range(6, 0, -1):
        pattern = r"^@{%d}\s*(.+)$" % n
        repl = lambda m: f'<h{n} id="{m.group(1)}" style="text-align: center;">{m.group(1)}</h{n}>'
        code = re.sub(pattern, repl, code, flags=re.MULTILINE)

    # Sustitución para video estilo Markdown (!![attrs](src))
    code = re.sub(
        r"!!\[(.*?)\]\((.*?)\)",
        r'<video \1 src="\2"></video>',
        code
    )

    # Buscar todas las constantes
    constants = dict(re.findall(r"--const\s+-([\w]+)\s+(.+)", code))
    
    # Borrar las líneas de definición
    code = re.sub(r"--const\s+-[\w]+\s+.+\n?", "", code)
    
    # Reemplazar las referencias
    for name, value in constants.items():
        code= code.replace(f"-{name}", value)

    code = re.sub(r"--end -code (.*)", "<!-- \1 -->", code, flags=re.DOTALL)
    code = re.sub(r"(.*)--end -init", "<!-- \1 -->", code, flags=re.DOTALL)
    code = re.sub(r"--start -([a-zA-Z]+) (.*)--end -\1", "<!-- \2 -->", code, flags=re.DOTALL)
    code = re.sub(r"--end -([a-zA-Z]+) (.*) --start -\1", "<!-- \2 -->", code, flags=re.DOTALL)
    if html_yes:
        code = to_html(code)
    with open(argv[2], "w", encoding="utf-8") as f:
        f.write(code)

if __name__ == "__main__":
    main(sys.argv)

    