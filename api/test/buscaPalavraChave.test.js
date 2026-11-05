const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { normalizar, buscarPorPalavraChave } = require('../src/buscaPalavraChave');

const itens = [
  { id: 3, nome: 'Sopa de Legumes', descricao: 'Sopa leve com legumes frescos.' },
  { id: 1, nome: 'Salada Verde', descricao: 'Folhas verdes e legumes.' },
  { id: 2, nome: 'Bife', descricao: 'Carne grelhada.' },
];

test('normalizar remove acentos, pontuação e palavras ignoradas', () => {
  assert.deepStrictEqual(normalizar('Quero um Açaí, com Granola!'), ['acai', 'granola']);
});

test('a busca ignora itens com score 0', () => {
  const resultados = buscarPorPalavraChave(itens, 'carne', 10);
  assert.deepStrictEqual(resultados.map((r) => r.item.id), [2]);
});

test('a busca respeita k', () => {
  const resultados = buscarPorPalavraChave(itens, 'legumes', 1);
  assert.strictEqual(resultados.length, 1);
});

test('empate de score é resolvido por id crescente', () => {
  const resultados = buscarPorPalavraChave(itens, 'legumes', 10);
  assert.deepStrictEqual(resultados.map((r) => r.item.id), [1, 3]);
});

test('"açaí" retorna o id 24 em primeiro lugar no cardápio real', () => {
  const caminho = path.join(__dirname, '..', '..', 'dados', 'cardapio.json');
  const cardapio = JSON.parse(fs.readFileSync(caminho, 'utf-8'));
  const resultados = buscarPorPalavraChave(cardapio, 'açaí', 5);
  assert.strictEqual(resultados[0].item.id, 24);
});
