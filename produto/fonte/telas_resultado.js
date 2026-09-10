/* ---------- tela de processamento ---------- */
const PASSOS = [
  "Agências selecionadas",
  "Restrições de agenda analisadas",
  "Alternativas de transporte comparadas",
  "Sequência de visitas montada",
];

function pintarProcessamento() {
  const p = estado.plano;
  const fase = estado.fase || 0;

  $("#conteudo").innerHTML = `
    <div class="processando">
      <h2>Analisando possibilidades de rota</h2>
      <p>${plural(p.selecionadas.size, "agência", "agências")} ·
         ${plural(capacidade(p).dias, "dia", "dias")} ·
         ${{ custo: "menor custo", tempo: "menor tempo", equilibrio: "equilíbrio entre custo e tempo" }[p.objetivo]}</p>
      <div class="passos">
        ${PASSOS.map((t, i) => `
          <div class="passo" data-fase="${i < fase ? "feito" : i === fase ? "atual" : "adiante"}">
            <span class="sinal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12l5 5L20 6"/></svg></span>
            ${t}
          </div>`).join("")}
      </div>
      <p class="medida">${
        fase >= PASSOS.length
          ? "Pronto."
          : `Comparando carro, ônibus e avião em ${plural(p.selecionadas.size + 1, "trecho", "trechos")}.`
      }</p>
    </div>`;
}

function processar() {
  estado.tela = "processando";
  estado.fase = 0;
  pintarMenu();
  $("#trilha").innerHTML = `${esc(estado.regional.nome)} <span style="color:var(--texto-tenue)">/</span> <b>Gerando planejamento</b>`;
  pintarProcessamento();

  const rapido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const passo = rapido ? 90 : 520;

  const avancar = () => {
    estado.fase++;
    if (estado.fase <= PASSOS.length) {
      pintarProcessamento();
      setTimeout(avancar, passo);
    } else {
      estado.roteiro = montarRoteiro(estado.plano);
      estado.expandido = null;
      irPara("resultado");
    }
  };
  setTimeout(avancar, passo);
}

/* ---------- tela de resultado ---------- */
function pintarResultado() {
  const p = estado.plano;
  const rt = estado.roteiro;
  const t = rt.totais;
  const ref = rt.referencia;

  const economia = ref.custo - t.custo;
  const tempoGanho = ref.minutos - t.minutos;
  const kmGanho = ref.km - t.km;

  const pct = (novo, velho) => (velho ? ((velho - novo) / velho) * 100 : 0);
  const sinal = (v, txt) => `<span class="delta ${v < 0 ? "pior" : ""}">${v >= 0 ? "−" : "+"}${txt}</span>`;

  $("#conteudo").innerHTML = `
    <div class="pagina">
      <div>
        <h1>Planejamento recomendado</h1>
        <p>${plural(t.visitas, "visita", "visitas")} em ${plural(t.dias, "dia", "dias")},
           saindo de ${esc(p.origem.municipio)}/${p.origem.uf} e retornando ao mesmo ponto.
           Otimizado por ${{ custo: "menor custo", tempo: "menor tempo",
             equilibrio: `equilíbrio ${Math.round(p.pesoCusto * 100)}% custo e ${Math.round((1 - p.pesoCusto) * 100)}% tempo` }[p.objetivo]}.</p>
      </div>
      <div class="pagina-acoes">
        <button class="btn" id="editar">Editar planejamento</button>
      </div>
    </div>

    <div class="resumo-topo">
      <div class="res">
        <div class="res-rot">Custo total</div>
        <div class="res-val">${dinheiro(t.custo)}</div>
        <div class="res-sub">${dinheiro(t.custoTrechos)} em trechos${
          t.noites ? ` + ${dinheiro(t.hospedagem)} em ${plural(t.noites, "diária", "diárias")}` : ""}</div>
      </div>
      <div class="res">
        <div class="res-rot">Tempo de deslocamento</div>
        <div class="res-val">${duracao(t.minutos)}</div>
        <div class="res-sub">fora ${duracao(t.visitas * p.duracaoVisita)} dentro das agências</div>
      </div>
      <div class="res">
        <div class="res-rot">Distância percorrida</div>
        <div class="res-val">${Math.round(t.km).toLocaleString("pt-BR")} km</div>
        <div class="res-sub">${plural(rt.trechos.length, "trecho", "trechos")}</div>
      </div>
      <div class="res ${economia > 0 ? "ganho" : ""}">
        <div class="res-rot">Economia estimada</div>
        <div class="res-val">${economia > 0 ? dinheiro(economia) : dinheiro(0)}</div>
        <div class="res-sub">${economia > 0 ? `${pct(t.custo, ref.custo).toFixed(1)}% ante o cenário de referência` : "sem ganho sobre a referência"}</div>
      </div>
    </div>

    <div class="resultado-colunas">
      <div class="mapa-caixa">
        <div id="mapa"></div>
        <div class="mapa-legenda">
          <span class="ch"><i style="background:#12263A"></i> Carro</span>
          <span class="ch"><i style="background:#0E7C66"></i> Ônibus</span>
          <span class="ch"><i style="background:#9A5B12"></i> Avião</span>
          <span class="ch"><i class="bola vazia"></i> ${
            agenciasDa(estado.regional.id).filter((a) => !p.selecionadas.has(a.id)).length
          } agências da regional fora desta viagem</span>
          <span class="ajuda">Arraste para mover, use a roda para aproximar, clique num trecho para o detalhe. O botão BR enquadra o país inteiro.</span>
        </div>
      </div>

      <div>
        <section class="painel" id="itinerario">
          <div class="painel-topo">
            <h2>Itinerário</h2>
            <span class="conta">${plural(rt.trechos.length, "trecho", "trechos")}</span>
          </div>
          <div id="itinerario-corpo">${montarItinerario(rt, p)}</div>
        </section>

        <section class="painel comparacao" style="margin-top:16px">
          <div class="painel-topo"><h2>Comparação de cenários</h2></div>
          <table>
            <thead>
              <tr><th>Indicador</th><th class="n">Referência</th><th class="n">Recomendada</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>Custo</td>
                <td class="n">${dinheiro(ref.custo)}</td>
                <td class="n"><span class="${t.custo <= ref.custo ? "melhor" : ""}">${dinheiro(t.custo)}</span><br>
                  ${sinal(economia, dinheiro(Math.abs(economia)))}</td>
              </tr>
              <tr>
                <td>Tempo de deslocamento</td>
                <td class="n">${duracao(ref.minutos)}</td>
                <td class="n"><span class="${t.minutos <= ref.minutos ? "melhor" : ""}">${duracao(t.minutos)}</span><br>
                  ${sinal(tempoGanho, duracao(Math.abs(tempoGanho)))}</td>
              </tr>
              <tr>
                <td>Distância</td>
                <td class="n">${Math.round(ref.km).toLocaleString("pt-BR")} km</td>
                <td class="n"><span class="${t.km <= ref.km ? "melhor" : ""}">${Math.round(t.km).toLocaleString("pt-BR")} km</span><br>
                  ${sinal(kmGanho, Math.round(Math.abs(kmGanho)).toLocaleString("pt-BR") + " km")}</td>
              </tr>
              <tr>
                <td>Dias de viagem</td>
                <td class="n">${ref.dias}</td>
                <td class="n"><span class="${t.dias <= ref.dias ? "melhor" : ""}">${t.dias}</span></td>
              </tr>
            </tbody>
          </table>
          <div class="leitura ${economia > 0 && tempoGanho > 0 ? "" : "neutra"}">
            ${leituraComparacao(economia, tempoGanho, kmGanho)}
          </div>
        </section>

        <div class="acoes-finais">
          <button class="btn" data-final="editar">Editar planejamento</button>
          <button class="btn" data-final="novo">Gerar novo cenário</button>
          <button class="btn" data-final="salvar">Salvar planejamento</button>
          <button class="btn btn-principal" data-final="exportar">Exportar relatório</button>
        </div>

        <p class="rodape-nota" style="margin-top:16px">
          <b>Como estes números são obtidos.</b> Custo, tempo e escolha de modal saem do modelo
          calibrado com ANP, ANTT e ANAC, aplicado às coordenadas reais das agências.
          A <b>sequência de visitas</b> ainda usa uma regra provisória de varredura geográfica:
          é o ponto onde entra o algoritmo de roteirização numa próxima fase.
          O cenário de referência assume a ordem de cadastro das agências, toda a viagem de carro.
        </p>
      </div>
    </div>`;

  pintarMapa(rt);
  ligarResultado();
}

/* Repinta apenas o itinerário, preservando o zoom do mapa. */
function atualizarItinerario(rt) {
  const corpo = $("#itinerario-corpo");
  if (!corpo) return;
  corpo.innerHTML = montarItinerario(rt, estado.plano);
  ligarTrechos(rt);
}

function leituraComparacao(economia, tempo, km) {
  if (economia > 0 && tempo > 0)
    return `Esta rota apresenta menor custo e menor tempo estimado que o cenário de referência,
            economizando ${dinheiro(economia)} e ${duracao(tempo)} de deslocamento.`;
  if (economia > 0)
    return `Esta rota custa ${dinheiro(economia)} a menos que a referência, com tempo de
            deslocamento equivalente.`;
  if (tempo > 0)
    return `Esta rota economiza ${duracao(tempo)} de deslocamento, com custo próximo ao da referência.`;
  return `Com esta seleção e estas restrições, a rota recomendada ficou equivalente ao cenário
          de referência. Poucas paradas ou distâncias curtas deixam pouca margem de otimização.`;
}

function montarItinerario(rt, p) {
  const nomesModal = { carro: "Carro", onibus: "Ônibus", aviao: "Avião" };
  let visita = 0;
  let html = "";

  rt.roteiro.forEach((dia) => {
    html += `
      <div class="dia-cab">
        <h3>Dia ${dia.numero}</h3>
        <span class="m">${plural(dia.visitas, "visita", "visitas")} · ${duracao(dia.minutos)} ocupadas</span>
      </div>`;

    dia.trechos.forEach((t) => {
      const e = t.escolha;
      const i = t.indice;
      const aberto = estado.expandido === i;

      html += `
        <div class="trecho" data-trecho="${i}" aria-expanded="${aberto}">
          <button class="trecho-topo">
            <span class="modal">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
                   stroke-linecap="round" stroke-linejoin="round"><path d="${ICONES[e ? e.modal : "carro"]}"/></svg>
            </span>
            <span class="via">
              <span class="p">${esc(t.de.nome || t.de.municipio)} &rarr; ${esc(t.para.nome || t.para.municipio)}</span>
              <span class="s">${nomesModal[e.modal]} · ${Math.round(e.distanciaKm)} km</span>
            </span>
            <span class="nums">
              <span class="c">${dinheiro(e.custo)}</span>
              <span class="t">${duracao(e.minutos)}</span>
            </span>
            <svg class="seta" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
          </button>
          <div class="detalhe">${detalheTrecho(t, p)}</div>
        </div>`;

      if (t.para.tipo !== "retorno") {
        visita++;
        const a = t.para;
        const d = dias(a.dataLimite);
        html += `
          <div class="parada">
            <span class="n">${visita}</span>
            <span>
              <span class="nome">${esc(a.nome)}</span>
              <span class="loc">${esc(a.municipio)}/${a.uf} · prioridade ${
                a.prioridade === "alta" ? "alta" : a.prioridade === "media" ? "média" : "baixa"}</span>
            </span>
            <span class="dir">visita de ${p.duracaoVisita} min<br>prazo ${dataBR(a.dataLimite)}${
              d < 0 ? " (vencido)" : ""}</span>
          </div>`;
      } else {
        html += `
          <div class="parada fim">
            <span class="n">&#8962;</span>
            <span>
              <span class="nome">Retorno a ${esc(t.para.municipio)}</span>
              <span class="loc">fim da viagem</span>
            </span>
          </div>`;
      }
    });
  });

  return html;
}

function detalheTrecho(t, p) {
  const nomesModal = { carro: "Carro", onibus: "Ônibus", aviao: "Avião" };
  const e = t.escolha;

  const alternativas = t.opcoes.map((o) => {
    const permitido = p.modais[o.modal];
    const eleito = o.modal === e.modal;
    return `
      <div class="alt ${eleito ? "eleito" : ""} ${!permitido || !o.disponivel ? "fora" : ""}">
        <span class="nm">${nomesModal[o.modal]}</span>
        ${o.disponivel
          ? `<span>${dinheiro(o.custo)}</span><span class="vs">${duracao(o.minutos)}</span>`
          : `<span class="vs">${!permitido ? "desativado nas restrições" : "indisponível neste trecho"}</span>`}
      </div>`;
  }).join("");

  const empate = t.margem !== null && t.margem < 0.03;
  const razao = e.modal === t.melhorCusto && e.modal === t.melhorTempo
    ? "É a opção mais barata e a mais rápida do trecho."
    : e.modal === t.melhorCusto
      ? "É a opção mais barata do trecho, dentro do peso escolhido para custo."
      : e.modal === t.melhorTempo
        ? "É a opção mais rápida do trecho, dentro do peso escolhido para tempo."
        : "Melhor combinação de custo e tempo segundo o peso escolhido.";

  return `
    <dl>
      <dt>Origem</dt><dd>${esc(t.de.nome || t.de.municipio)}${t.de.uf ? " — " + esc(t.de.municipio) + "/" + t.de.uf : ""}</dd>
      <dt>Destino</dt><dd>${esc(t.para.nome || t.para.municipio)}${t.para.uf ? " — " + esc(t.para.municipio) + "/" + t.para.uf : ""}</dd>
      <dt>Modal</dt><dd>${nomesModal[e.modal]}</dd>
      <dt>Distância</dt><dd>${Math.round(e.distanciaKm)} km${
        e.modal === "aviao" ? " em linha reta" : ` (linha reta × ${DADOS.parametros.fatorSinuosidade})`}</dd>
      <dt>Tempo</dt><dd>${duracao(e.minutos)}</dd>
      <dt>Custo</dt><dd>${dinheiro(e.custo)}</dd>
    </dl>
    <div class="alternativas">${alternativas}</div>
    <p class="nota-trecho ${empate ? "empate" : ""}">
      ${razao}
      ${empate ? ` O ${nomesModal[t.segundo]} ficou apenas ${(t.margem * 100).toFixed(1)}% atrás: é praticamente um empate técnico.` : ""}
      ${e.observacao ? " " + esc(e.observacao) : ""}
    </p>`;
}

function ligarTrechos(rt) {
  $("#conteudo").querySelectorAll(".trecho-topo").forEach((b) => {
    b.onclick = () => {
      const i = +b.closest(".trecho").dataset.trecho;
      estado.expandido = estado.expandido === i ? null : i;
      atualizarItinerario(rt);
      pintarMapa(rt);
    };
  });
}

function ligarResultado() {
  ligarTrechos(estado.roteiro);

  $("#editar").onclick = () => { estado.plano.etapa = 2; irPara("novo"); };

  $("#conteudo").querySelectorAll("[data-final]").forEach((b) => {
    b.onclick = () => {
      const q = b.dataset.final;
      if (q === "editar") { estado.plano.etapa = 2; return irPara("novo"); }
      if (q === "novo") { estado.plano.etapa = 4; return irPara("novo"); }
      if (q === "salvar") return salvarPlanejamento();
      if (q === "exportar") return aviso("Relatório exportado. (Demonstrativo: não há geração de arquivo neste protótipo.)");
    };
  });
}
