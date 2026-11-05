const express = require('express');
const fs = require('node:fs');
const path = require('node:path');
const { CacheTTL } = require('./cache');
const { buscarPorPalavraChave } = require('./buscaPalavraChave');

const PORTA = 3000;
const URL_SERVICO_ML = 'http://localhost:8000';
const TEMPO_LIMITE_ML_MS = 2000;
const cache = new CacheTTL(60_000);

const caminhoCardapio = path.join(__dirname, '..', '..', 'dados', 'cardapio.json');
const itens = JSON.parse(fs.readFileSync(caminhoCardapio, 'utf-8'));
const itensPorId = new Map(itens.map((item) => [item.id, item]));

function formatarItem(item, score) {
  const { id, nome, descricao, categoria, preco } = item;
  return { id, nome, descricao, categoria, preco, score };
}

async function buscarNoServicoML(consulta, k) {
  const resposta = await fetch(`${URL_SERVICO_ML}/buscar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ consulta, k }),
    signal: AbortSignal.timeout(TEMPO_LIMITE_ML_MS),
  });
  if (!resposta.ok) {
    throw new Error(`serviço de ML respondeu ${resposta.status}`);
  }
  const dados = await resposta.json();
  return dados.resultados.map(({ id, score }) => formatarItem(itensPorId.get(id), score));
}

const app = express();

app.get('/buscar', async (req, res) => {
  const consulta = String(req.query.q ?? '').trim();
  if (!consulta) {
    return res.status(400).json({ erro: 'Informe a busca no parâmetro q. Ex.: /buscar?q=pizza' });
  }
  const kInformado = parseInt(req.query.k, 10);
  const k = Number.isNaN(kInformado) ? 5 : Math.min(20, Math.max(1, kInformado));

  const chave = `${consulta.toLowerCase()}|${k}`;
  const emCache = cache.get(chave);
  if (emCache) {
    return res.json({ consulta, fonte: 'cache', resultados: emCache });
  }

  try {
    const resultados = await buscarNoServicoML(consulta, k);
    // Só o resultado semântico é cacheado, para o fallback não ficar preso após o ML voltar
    cache.set(chave, resultados);
    return res.json({ consulta, fonte: 'semantica', resultados });
  } catch (erro) {
    console.warn(`Busca semântica indisponível, usando palavra-chave: ${erro.message}`);
    const resultados = buscarPorPalavraChave(itens, consulta, k).map(({ item, score }) =>
      formatarItem(item, score)
    );
    return res.json({ consulta, fonte: 'palavra-chave', resultados });
  }
});

app.listen(PORTA, () => {
  console.log(`API no ar em http://localhost:${PORTA}`);
  console.log(`Exemplo: http://localhost:${PORTA}/buscar?q=fritura`);
});
