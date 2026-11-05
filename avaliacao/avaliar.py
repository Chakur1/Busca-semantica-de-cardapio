import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_CARDAPIO = RAIZ / "dados" / "cardapio.json"
CAMINHO_CONSULTAS = RAIZ / "dados" / "consultas_teste.json"
CAMINHO_RESULTADOS = Path(__file__).resolve().parent / "resultados.md"

NOME_DO_MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
PALAVRAS_IGNORADAS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e",
    "em", "no", "na", "nos", "nas", "com", "para", "pra", "por", "ao", "que",
    "quero", "algo",
}
TOPO = 10


def normalizar(texto):
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    palavras = re.sub(r"[^a-z0-9]", " ", sem_acento).split()
    return [p for p in palavras if p not in PALAVRAS_IGNORADAS]


def texto_do_item(item):
    return f"{item['nome']}. {item['descricao']}"


def busca_palavra_chave(itens, consulta, k=TOPO):
    palavras_da_consulta = set(normalizar(consulta))
    pontuados = []
    for item in itens:
        palavras_do_item = set(normalizar(f"{item['nome']} {item['descricao']}"))
        score = len(palavras_da_consulta & palavras_do_item)
        if score > 0:
            pontuados.append((item["id"], score))
    # Mesmo desempate da API: score decrescente e, depois, id crescente
    pontuados.sort(key=lambda par: (-par[1], par[0]))
    return [id_ for id_, _ in pontuados[:k]]


def busca_semantica(modelo, itens, vetores, consulta, k=TOPO):
    vetor_consulta = modelo.encode(consulta, normalize_embeddings=True)
    similaridades = vetores @ vetor_consulta
    return [itens[int(i)]["id"] for i in np.argsort(-similaridades)[:k]]


def recall_em_k(relevantes, recuperados, k=5):
    if not relevantes:
        return 0.0
    return len(set(relevantes) & set(recuperados[:k])) / len(relevantes)


def reciprocal_rank(relevantes, recuperados):
    for posicao, id_ in enumerate(recuperados, start=1):
        if id_ in relevantes:
            return 1 / posicao
    return 0.0


def gerar_markdown(media, linhas):
    texto = ["# Resultados da avaliação", "", "## Geral", ""]
    texto += ["| Busca | Recall@5 | MRR |", "|---|---|---|"]
    for nome, (recall, mrr) in media.items():
        texto.append(f"| {nome} | {recall:.2f} | {mrr:.2f} |")
    texto += ["", "## Por consulta", ""]
    texto += [
        "| Consulta | Recall@5 palavra-chave | Recall@5 semântica |",
        "|---|---|---|",
    ]
    for consulta, recall_pc, recall_sem in linhas:
        texto.append(f"| {consulta} | {recall_pc:.2f} | {recall_sem:.2f} |")
    return "\n".join(texto) + "\n"


def main():
    from sentence_transformers import SentenceTransformer

    itens = json.loads(CAMINHO_CARDAPIO.read_text(encoding="utf-8"))
    consultas = json.loads(CAMINHO_CONSULTAS.read_text(encoding="utf-8"))

    modelo = SentenceTransformer(NOME_DO_MODELO)
    vetores = modelo.encode(
        [texto_do_item(item) for item in itens], normalize_embeddings=True
    )

    recalls = {"palavra-chave": [], "semântica": []}
    rrs = {"palavra-chave": [], "semântica": []}
    linhas = []
    for pedido in consultas:
        relevantes = pedido["relevantes"]
        recuperados = {
            "palavra-chave": busca_palavra_chave(itens, pedido["consulta"]),
            "semântica": busca_semantica(modelo, itens, vetores, pedido["consulta"]),
        }
        for nome, ids in recuperados.items():
            recalls[nome].append(recall_em_k(relevantes, ids, 5))
            rrs[nome].append(reciprocal_rank(relevantes, ids))
        linhas.append(
            (pedido["consulta"], recalls["palavra-chave"][-1], recalls["semântica"][-1])
        )

    media = {
        nome: (float(np.mean(recalls[nome])), float(np.mean(rrs[nome])))
        for nome in recalls
    }
    markdown = gerar_markdown(media, linhas)
    CAMINHO_RESULTADOS.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
