import json
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

NOME_DO_MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CAMINHO_CARDAPIO = Path(__file__).resolve().parent.parent / "dados" / "cardapio.json"

estado = {}


def texto_do_item(item):
    return f"{item['nome']}. {item['descricao']}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    modelo = SentenceTransformer(NOME_DO_MODELO)
    itens = json.loads(CAMINHO_CARDAPIO.read_text(encoding="utf-8"))
    vetores = modelo.encode(
        [texto_do_item(item) for item in itens], normalize_embeddings=True
    )
    estado["modelo"] = modelo
    estado["itens"] = itens
    estado["vetores"] = np.asarray(vetores)
    yield
    estado.clear()


app = FastAPI(lifespan=lifespan)


class PedidoDeBusca(BaseModel):
    consulta: str = Field(min_length=1, max_length=200)
    k: int = Field(default=5, ge=1, le=20)


@app.get("/saude")
def saude():
    return {"status": "ok", "itens": len(estado["itens"])}


@app.post("/buscar")
def buscar(pedido: PedidoDeBusca):
    vetor_consulta = estado["modelo"].encode(
        pedido.consulta, normalize_embeddings=True
    )
    
    similaridades = estado["vetores"] @ vetor_consulta
    melhores = np.argsort(-similaridades)[: pedido.k]
    return {
        "consulta": pedido.consulta,
        "resultados": [
            {
                "id": estado["itens"][int(i)]["id"],
                "score": round(float(similaridades[i]), 4),
            }
            for i in melhores
        ],
    }
