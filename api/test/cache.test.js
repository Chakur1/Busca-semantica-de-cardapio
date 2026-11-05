const test = require('node:test');
const assert = require('node:assert');
const { CacheTTL } = require('../src/cache');

const esperar = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

test('devolve o valor dentro do prazo', () => {
  const cache = new CacheTTL(1000);
  cache.set('a', 42);
  assert.strictEqual(cache.get('a'), 42);
});

test('devolve undefined depois que o prazo vence', async () => {
  const cache = new CacheTTL(20);
  cache.set('a', 42);
  await esperar(50);
  assert.strictEqual(cache.get('a'), undefined);
});

test('devolve undefined para chave inexistente', () => {
  const cache = new CacheTTL(1000);
  assert.strictEqual(cache.get('nada'), undefined);
});
