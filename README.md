# Busca Semântica de Cardápio

Uma busca de pratos que entende a intenção da consulta: "fritura" encontra coxinha, kibe frito e batata frita, mesmo sem essa palavra em nenhuma descrição. O projeto compara essa busca semântica, feita com embeddings, com uma busca tradicional por palavra-chave, e usa a segunda como plano B quando a primeira está fora do ar.

## Resultado

Avaliação com 25 consultas de teste sobre 60 pratos (top 10 de cada busca):

| Busca | Recall@5 | MRR |
|---|---|---|
| palavra-chave | 0.28 | 0.47 |
| semântica | 0.39 | 0.57 |

A semântica ganha nas consultas por conceito ("comida japonesa", "churrasco", "fritura"), mas está longe de ser perfeita. O detalhe por consulta está em [avaliacao/resultados.md](avaliacao/resultados.md).

## Como funciona

- **servico-ml** (Python + FastAPI, porta 8000): gera os embeddings dos pratos e responde buscas por similaridade de cosseno.
- **api** (Node.js + Express, porta 3000): porta de entrada, com cache TTL, tempo limite para o serviço de ML e fallback para busca por palavra-chave.
- **avaliacao** (Python): compara as duas buscas com Recall@5 e MRR.

## Decisões técnicas

- **Modelo multilíngue em CPU**: `paraphrase-multilingual-MiniLM-L12-v2` entende português, é pequeno e roda sem GPU, o que basta para 60 pratos.
- **Embeddings calculados na inicialização**: o cardápio é pequeno e fixo, então os vetores são gerados uma vez e cada busca só embeda a consulta.
- **Cache TTL de 60 s**: consultas repetidas não passam pelo modelo; o prazo curto evita servir resultado velho por muito tempo.
- **Tempo limite de 2 s para o ML**: se o serviço travar ou cair, o usuário recebe a busca por palavra-chave em vez de um erro.
- **Só resultados semânticos entram no cache**: se o fallback fosse cacheado, a resposta degradada ficaria presa por até 60 s depois que o ML voltasse.

## Limitações encontradas

Olhando a tabela por consulta:

- **"sopa quentinha para dia frio"** (palavra-chave 1.00, semântica 0.00): a palavra "sopa" resolve sozinha na busca lexical. O modelo deu peso a "quentinha" e "frio" e trouxe lasanha, hot roll e burrito. A Sopa de Legumes não tem nenhuma dessas ideias na descrição ("caldo caseiro com batata, cenoura...").
- **"prato sem carne"** (0.00 nas duas): o modelo não trata a negação; as primeiras respostas foram Pastel de Carne e Feijoada, porque "carne" pesa mais que "sem".
- **"algo leve pra jantar"** (0.00 nas duas): "leve" é subjetivo e as descrições não dizem se o prato é leve. O topo foi Nhoque e Lasanha.
- **"comida chinesa"** e **"comida mexicana"** (0.00 nas duas): a semântica trouxe sushi para "chinesa" (hipótese: associa a culinária oriental em geral; o único relevante é um yakisoba) e, para "mexicana", pratos sem relação, mesmo havendo tacos, burrito e nachos. Possível causa: o modelo é pequeno e as descrições mal citam a origem do prato.
- **"lanche rápido e barato"** e **"petisco para dividir com os amigos"** (0.00 nas duas): dependem de preço e de contexto de consumo, que o texto do prato não carrega.
- Com 25 consultas, a diferença entre as buscas é indicativa e não estatisticamente sólida.

## Como rodar no Windows (PowerShell)

Requisitos: Python 3.12 e Node.js LTS.

Serviço de ML (primeiro terminal; o modelo é baixado na primeira execução):

```powershell
cd servico-ml
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --port 8000
```

API (segundo terminal):

```powershell
cd api
npm install
npm start
```

Exemplo de busca (terceiro terminal):

```powershell
Invoke-RestMethod "http://localhost:3000/buscar?q=fritura&k=3"
```

Testes:

```powershell
cd api
npm test

cd ..\servico-ml
.\.venv\Scripts\Activate.ps1
cd ..
pytest avaliacao
```

Avaliação (da raiz do projeto, com o .venv do servico-ml ativo):

```powershell
python avaliacao/avaliar.py
```

## Próximos passos

- Entendimento da consulta: transformar termos como "barato" em filtro de preço e tratar negações como "sem carne".
- Testar outros modelos de embedding, inclusive maiores, e comparar com a mesma avaliação.
- Usar um índice vetorial (FAISS, pgvector) se o catálogo crescer; para 60 pratos, o produto de matrizes em memória é suficiente.
