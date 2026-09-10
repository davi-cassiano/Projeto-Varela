/* =====================================================================
   MONTAGEM DO ROTEIRO

   ATENÇÃO AO ESCOPO: aqui NÃO há algoritmo de roteirização. A sequência
   de visitas vem de uma regra provisória (varredura angular em torno da
   origem, com prazos vencidos puxados para a frente). É o ponto exato
   onde o otimizador (TSP/VRP) entra numa próxima fase — trocar a função
   sequenciar() é suficiente, o resto da tela não muda.

   O que É calculado de verdade: custo, tempo, distância e escolha de
   modal por trecho, pelo modelo calibrado em decisao_transporte.py.
   ===================================================================== */

/* Varredura angular: ordena os pontos pelo ângulo em torno da origem,
   o que produz um circuito sem cruzamentos grosseiros no mapa. */
function sequenciar(origem, agencias, priorizarAtrasadas) {
  const angulo = (a) =>
    Math.atan2(a.lat - origem.lat, (a.lon - origem.lon) * Math.cos((origem.lat * Math.PI) / 180));

  const varrer = (lista) => [...lista].sort((a, b) => angulo(a) - angulo(b));

  if (!priorizarAtrasadas) return varrer(agencias);

  const atrasadas = agencias.filter((a) => dias(a.dataLimite) < 0);
  const demais = agencias.filter((a) => dias(a.dataLimite) >= 0);
  return [...varrer(atrasadas), ...varrer(demais)];
}

const CUSTO_DIARIA = 168.0; /* hospedagem + refeições por pernoite (estimativa) */
const RAIO_CASA_KM = 80.0;  /* abaixo disso o gerente dorme em casa, sem diária */

/* Um dia só gera diária se terminar longe da origem. Sem isso, uma
   viagem inteira dentro da mesma cidade cobraria hotel sem sentido. */
function contarPernoites(roteiro, origem) {
  let noites = 0;
  for (let i = 0; i < roteiro.length - 1; i++) {
    const ultimo = roteiro[i].trechos[roteiro[i].trechos.length - 1];
    if (ultimo && distanciaKm(origem, ultimo.para) > RAIO_CASA_KM) noites++;
  }
  return noites;
}

function minutosDoHorario(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}

/* Distribui os trechos em dias, respeitando o teto de visitas e a janela
   de horário. Usada nos dois cenários, para a comparação ser justa. */
function distribuirDias(trechos, p) {
  const janela = minutosDoHorario(p.horaFim) - minutosDoHorario(p.horaInicio);
  const roteiro = [];
  let dia = { numero: 1, trechos: [], visitas: 0, minutos: 0 };

  trechos.forEach((t) => {
    const ehVisita = t.para.tipo !== "retorno";
    const custoTempo = t.escolha ? t.escolha.minutos + (ehVisita ? p.duracaoVisita : 0) : 0;

    const estouraTeto = ehVisita && dia.visitas >= p.visitasDia;
    const estouraJanela = dia.minutos + custoTempo > janela && dia.trechos.length > 0;

    if ((estouraTeto || estouraJanela) && p.aceitaPernoite) {
      roteiro.push(dia);
      dia = { numero: dia.numero + 1, trechos: [], visitas: 0, minutos: 0 };
    }

    dia.trechos.push(t);
    dia.minutos += custoTempo;
    if (ehVisita) dia.visitas++;
  });

  roteiro.push(dia);
  return roteiro;
}

function montarRoteiro(p) {
  const selecionadas = DADOS.agencias.filter((a) => p.selecionadas.has(a.id));
  const ordem = sequenciar(p.origem, selecionadas, p.priorizarAtrasadas);
  const peso = pesoAtual(p);

  const origem = { ...p.origem, nome: p.origem.municipio, tipo: "origem" };
  const pontos = [origem, ...ordem, { ...origem, tipo: "retorno" }];

  /* ---- trechos ---- */
  const trechos = [];
  for (let i = 0; i < pontos.length - 1; i++) {
    const de = pontos[i];
    const para = pontos[i + 1];
    const r = compararModais(de, para, DADOS.parametros, peso, p.modais);
    trechos.push({ de, para, indice: i, ...r, escolha: r.trecho });
  }

  const roteiro = distribuirDias(trechos, p);

  /* ---- totais ---- */
  const custoTrechos = trechos.reduce((s, t) => s + (t.escolha ? t.escolha.custo : 0), 0);
  const minutos = trechos.reduce((s, t) => s + (t.escolha ? t.escolha.minutos : 0), 0);
  const km = trechos.reduce((s, t) => s + (t.escolha ? t.escolha.distanciaKm : 0), 0);
  const noites = p.aceitaPernoite ? contarPernoites(roteiro, origem) : 0;
  const hospedagem = noites * CUSTO_DIARIA;

  /* ---- cenário de referência ----
     O que o gerente faria sem o sistema: visitar na ordem do cadastro,
     tudo de carro, sem comparar modal. É o comparativo honesto, porque
     usa exatamente as mesmas agências e o mesmo modelo de custo. */
  const ordemCadastro = [...selecionadas].sort((a, b) => a.codigo - b.codigo);
  const pontosRef = [origem, ...ordemCadastro, { ...origem, tipo: "retorno" }];
  const trechosRef = [];
  for (let i = 0; i < pontosRef.length - 1; i++) {
    const r = compararModais(pontosRef[i], pontosRef[i + 1], DADOS.parametros, peso, { carro: true });
    trechosRef.push({ de: pontosRef[i], para: pontosRef[i + 1], indice: i, ...r, escolha: r.trecho });
  }

  const roteiroRef = distribuirDias(trechosRef, p);
  const custoRef = trechosRef.reduce((s, t) => s + t.escolha.custo, 0);
  const minutosRef = trechosRef.reduce((s, t) => s + t.escolha.minutos, 0);
  const kmRef = trechosRef.reduce((s, t) => s + t.escolha.distanciaKm, 0);
  const noitesRef = p.aceitaPernoite ? contarPernoites(roteiroRef, origem) : 0;

  return {
    pontos, trechos, roteiro, ordem,
    totais: {
      custoTrechos, hospedagem, noites,
      custo: custoTrechos + hospedagem,
      minutos, km, dias: roteiro.length,
      visitas: ordem.length,
    },
    referencia: {
      custo: custoRef + noitesRef * CUSTO_DIARIA,
      minutos: minutosRef,
      km: kmRef,
      dias: roteiroRef.length,
      noites: noitesRef,
    },
  };
}
