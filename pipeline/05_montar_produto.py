"""
05_montar_produto.py

Injeta o pacote de dados e os módulos JavaScript no template e grava o
arquivo HTML final, autocontido. É a última etapa do pipeline.

Uso:
    python pipeline/05_montar_produto.py

Entrada:  dados/dados_prototipo.json e produto/fonte/*
Saída:    produto/roteirizacao-visitas.html
"""

import os

FONTE = "produto/fonte"


def ler(nome):
    with open(os.path.join(FONTE, nome), encoding="utf-8") as f:
        return f.read()


def main():
    template = ler("app.template.html")
    with open("dados/dados_prototipo.json", encoding="utf-8") as f:
        dados = f.read()

    # o export para Node não faz sentido no navegador
    motor = ler("motor.js").split('if (typeof module !== "undefined")')[0].rstrip()

    html = (template
            .replace("__DADOS__", dados)
            .replace("__MOTOR__", motor)
            .replace("__CSS_RESULTADO__", ler("resultado.css"))
            .replace("__ROTEIRO__", ler("roteiro.js"))
            .replace("__MAPA__", ler("mapa.js"))
            .replace("__TELAS__", ler("telas_resultado.js"))
            .replace("__EXTRAS__", ler("telas_extras.js")))

    saida = "produto/roteirizacao-visitas.html"
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"{saida}: {os.path.getsize(saida) / 1024:.0f} KB")
    print("Abra o arquivo no navegador. Não requer servidor nem internet.")


if __name__ == "__main__":
    main()
