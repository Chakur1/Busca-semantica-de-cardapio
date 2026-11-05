class CacheTTL {
  constructor(ttlEmMs) {
    this.ttlEmMs = ttlEmMs;
    this.entradas = new Map();
  }

  get(chave) {
    const entrada = this.entradas.get(chave);
    if (!entrada) return undefined;
    if (Date.now() > entrada.expiraEm) {
      // Remove na leitura para não acumular entradas vencidas
      this.entradas.delete(chave);
      return undefined;
    }
    return entrada.valor;
  }

  set(chave, valor) {
    this.entradas.set(chave, { valor, expiraEm: Date.now() + this.ttlEmMs });
  }
}

module.exports = { CacheTTL };
