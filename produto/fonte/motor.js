/*
 * motor.js — porte de decisao_transporte.py para JavaScript.
 *
 * Mesmas formulas, mesmos parametros calibrados (ANP, ANTT, ANAC).
 * Os parametros nao ficam aqui: chegam do pacote de dados, para que
 * ajustar preco de combustivel seja mudar dado, nao mudar codigo.
 *
 * Diferenca de precisao em relacao ao Python: o Python arredonda tempo
 * para 1 casa decimal (0.1h = 6 min). Aqui o tempo fica em minutos
 * inteiros, porque a tela mostra "1h 25min" e nao "1,4h".
 */

const R_TERRA = 6371.0;

function distanciaKm(a, b) {
  const rad = (x) => (x * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLon = rad(b.lon - a.lon);
  const p1 = rad(a.lat);
  const p2 = rad(b.lat);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(p1) * Math.cos(p2) * Math.sin(dLon / 2) ** 2;
  return 2 * R_TERRA * Math.asin(Math.sqrt(h));
}

function estimarCarro(distReta, p) {
  const distRodo = distReta * p.fatorSinuosidade;
  const c = p.carro;
  return {
    modal: "carro",
    disponivel: true,
    distanciaKm: distRodo,
    custo: distRodo * (c.precoGasolinaLitro / c.consumoKmLitro + c.pedagioPorKm),
    minutos: (distRodo / c.velocidadeKmh) * 60,
    observacao:
      distRodo > c.maxKmDia
        ? "Acima do limite diário de condução segura: exige pernoite ou parada de descanso."
        : "",
  };
}

function estimarOnibus(distReta, p) {
  const distRodo = distReta * p.fatorSinuosidade;
  const o = p.onibus;
  let obs = "";
  if (distRodo > 3000) obs = "Linha direta pouco provável nessa distância.";
  else if (distRodo > 1200) obs = "Linha longa, pode exigir conexão.";
  return {
    modal: "onibus",
    disponivel: true,
    distanciaKm: distRodo,
    custo: o.a + o.b * Math.pow(distRodo, o.c),
    minutos: (distRodo / o.velocidadeKmh) * 60,
    observacao: obs,
  };
}

function estimarAviao(distReta, p) {
  const v = p.aviao;
  if (distReta < v.distanciaMinimaKm) {
    return {
      modal: "aviao",
      disponivel: false,
      distanciaKm: distReta,
      custo: 0,
      minutos: 0,
      observacao: "Distância curta demais para voo comercial.",
    };
  }
  const horasVoo = distReta / v.velocidadeKmh + v.taxiHoras;
  return {
    modal: "aviao",
    disponivel: true,
    distanciaKm: distReta,
    custo: v.a + v.b * Math.pow(distReta, v.c),
    minutos: (horasVoo + v.overheadAeroportoHoras) * 60,
    observacao:
      distReta > 2500
        ? "Pode exigir conexão."
        : `Inclui ${v.overheadAeroportoHoras}h de deslocamento até o aeroporto, check-in e desembarque.`,
  };
}

/*
 * pesoCusto entre 0 e 1. Em 1 decide so por custo, em 0 so por tempo.
 * Cada criterio e normalizado pelo maior valor entre os modais daquele
 * trecho, entao o score compara grandezas diferentes na mesma escala.
 *
 * permitidos limita quais modais entram na disputa (restricoes da etapa 3).
 * A normalizacao usa so os permitidos: desligar o aviao nao pode mudar a
 * escala de comparacao entre carro e onibus.
 */
function compararModais(origem, destino, parametros, pesoCusto = 0.5, permitidos = null) {
  const dist = distanciaKm(origem, destino);

  const opcoes = [
    estimarCarro(dist, parametros),
    estimarOnibus(dist, parametros),
    estimarAviao(dist, parametros),
  ];

  const liberado = (o) => !permitidos || permitidos[o.modal];
  const disponiveis = opcoes.filter((o) => o.disponivel && liberado(o));

  if (!disponiveis.length) {
    return { distanciaLinhaRetaKm: dist, opcoes, recomendado: null, trecho: null, pesoCusto };
  }

  const maxCusto = Math.max(...disponiveis.map((o) => o.custo));
  const maxTempo = Math.max(...disponiveis.map((o) => o.minutos));
  const pesoTempo = 1 - pesoCusto;

  const score = (o) =>
    pesoCusto * (maxCusto ? o.custo / maxCusto : 0) +
    pesoTempo * (maxTempo ? o.minutos / maxTempo : 0);

  const menorPor = (fn) =>
    disponiveis.reduce((a, b) => (fn(a) <= fn(b) ? a : b));

  const recomendado = menorPor(score);
  const ordenados = [...disponiveis].sort((a, b) => score(a) - score(b));

  /* Diferenca percentual para o segundo colocado. Serve para a tela dizer
     quando a escolha foi um empate tecnico em vez de fingir vencedor claro. */
  const margem =
    ordenados.length > 1 && score(ordenados[0]) > 0
      ? (score(ordenados[1]) - score(ordenados[0])) / score(ordenados[0])
      : null;

  return {
    distanciaLinhaRetaKm: dist,
    opcoes,
    disponiveis,
    melhorCusto: menorPor((o) => o.custo).modal,
    melhorTempo: menorPor((o) => o.minutos).modal,
    recomendado: recomendado.modal,
    trecho: recomendado,
    segundo: ordenados.length > 1 ? ordenados[1].modal : null,
    margem,
    pesoCusto,
  };
}

/* Aeroporto mais proximo, usado so para nomear o voo na tela. */
function aeroportoMaisProximo(ponto, aeroportos) {
  return aeroportos.reduce((a, b) =>
    distanciaKm(ponto, a) <= distanciaKm(ponto, b) ? a : b
  );
}

if (typeof module !== "undefined") {
  module.exports = { distanciaKm, compararModais, aeroportoMaisProximo };
}
