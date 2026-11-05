const PALAVRAS_IGNORADAS = new Set([
  'a', 'o', 'as', 'os', 'um', 'uma', 'de', 'da', 'do', 'das', 'dos', 'e',
  'em', 'no', 'na', 'nos', 'nas', 'com', 'para', 'pra', 'por', 'ao', 'que',
  'quero', 'algo',
]);

function normalizar(texto) {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]/g, ' ')
    .split(' ')
    .filter((palavra) => palavra && !PALAVRAS_IGNORADAS.has(palavra));
}

function buscarPorPalavraChave(itens, consulta, k) {
  const palavrasDaConsulta = new Set(normalizar(consulta));

  return itens
    .map((item) => {
      const palavrasDoItem = new Set(normalizar(`${item.nome} ${item.descricao}`));
      let score = 0;
      for (const palavra of palavrasDaConsulta) {
        if (palavrasDoItem.has(palavra)) score += 1;
      }
      return { item, score };
    })
    .filter((resultado) => resultado.score > 0)
    // Desempate por id mantém a ordem estável e reproduzível
    .sort((a, b) => b.score - a.score || a.item.id - b.item.id)
    .slice(0, k);
}

module.exports = { normalizar, buscarPorPalavraChave };
