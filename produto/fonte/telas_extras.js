/* ---------- planejamentos salvos ----------
   Guardados no navegador. Só o plano é gravado; o roteiro é recalculado
   na leitura, o que mantém o registro pequeno e garante que uma mudança
   nos parâmetros do modelo se reflita nos planejamentos antigos.

   Se o armazenamento não estiver disponível (janela restrita, modo
   privado), tudo continua funcionando apenas na memória da sessão. */

const CHAVE_ARMAZEM = "roteirizacao.planejamentos.v1";

function armazemDisponivel() {
  try {
    const t = "__teste__";
    window.localStorage.setItem(t, "1");
    window.localStorage.removeItem(t);
    return true;
  } catch (e) {
    return false;
  }
}

function serializar(s) {
  const p = s.plano;
  return {
    id: s.id,
    regional: s.regional,
    regionalNome: s.regionalNome,
    criadoEm: s.criadoEm.toISOString(),
    plano: { ...p, selecionadas: [...p.selecionadas] },
  };
}

function gravar() {
  if (!estado.temArmazem) return;
  try {
    window.localStorage.setItem(
      CHAVE_ARMAZEM,
      JSON.stringify(estado.salvos.map(serializar))
    );
  } catch (e) {
    estado.temArmazem = false;
  }
}

function carregarSalvos() {
  estado.temArmazem = armazemDisponivel();
  if (!estado.temArmazem) return [];
  try {
    const bruto = window.localStorage.getItem(CHAVE_ARMAZEM);
    if (!bruto) return [];
    return JSON.parse(bruto).map((s) => {
      const plano = { ...s.plano, selecionadas: new Set(s.plano.selecionadas) };
      return {
        ...s,
        criadoEm: new Date(s.criadoEm),
        plano,
        roteiro: montarRoteiro(plano), // recalculado, não gravado
      };
    }).filter((s) => s.plano.selecionadas.size >= 2);
  } catch (e) {
    return [];
  }
}

function salvarPlanejamento() {
  const p = estado.plano;
  const clone = { ...p, selecionadas: new Set(p.selecionadas), modais: { ...p.modais } };

  estado.salvos.unshift({
    id: "p" + Date.now().toString(36),
    regional: estado.regional.id,
    regionalNome: estado.regional.nome,
    criadoEm: new Date(),
    plano: clone,
    roteiro: estado.roteiro,
  });
  gravar();
  aviso(
    estado.temArmazem
      ? `Planejamento salvo. Já aparece em Planejamentos (${estado.salvos.length}).`
      : "Salvo apenas nesta sessão: este navegador não permitiu gravação local."
  );
}

function excluirSalvo(id) {
  estado.salvos = estado.salvos.filter((s) => s.id !== id);
  gravar();
  pintarPlanejamentos();
  aviso("Planejamento excluído.");
}

function abrirSalvo(id) {
  const s = estado.salvos.find((x) => x.id === id);
  if (!s) return;
  estado.regional = DADOS.regionais.find((r) => r.id === s.regional);
  estado.plano = { ...s.plano, selecionadas: new Set(s.plano.selecionadas), modais: { ...s.plano.modais } };
  estado.roteiro = s.roteiro;
  estado.expandido = null;
  pintarRegional();
  irPara("resultado");
}

const horaBR = (d) =>
  `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")} às ` +
  `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;

function pintarPlanejamentos() {
  const meus = estado.salvos;
  const exemplos = planejamentosDe(estado.regional);

  $("#conteudo").innerHTML = `
    <div class="pagina">
      <div>
        <h1>Planejamentos</h1>
        <p>Viagens montadas nesta sessão e exemplos históricos da regional
           ${esc(estado.regional.nome)}.</p>
      </div>
      <div class="pagina-acoes">
        <button class="btn btn-principal" id="criar">Novo planejamento</button>
      </div>
    </div>

    <section class="painel">
      <div class="painel-topo">
        <h2>Salvos nesta sessão</h2>
        <span class="conta">${meus.length ? plural(meus.length, "planejamento", "planejamentos") : ""}</span>
      </div>
      ${meus.length ? meus.map((s) => {
        const t = s.roteiro.totais;
        const eco = s.roteiro.referencia.custo - t.custo;
        return `
        <div class="linha-salvo">
          <button class="item-ag" data-abrir="${s.id}" style="cursor:pointer;border:0">
            <span class="corpo">
              <span class="n">${esc(s.regionalNome)} · ${plural(t.visitas, "visita", "visitas")}</span>
              <span class="l">${plural(t.dias, "dia", "dias")} · ${Math.round(t.km).toLocaleString("pt-BR")} km ·
                salvo ${horaBR(s.criadoEm)}</span>
            </span>
            <span class="dir">
              <span class="d">${dinheiro(t.custo)}</span>
              <span class="r">${eco > 0 ? "economia de " + dinheiro(eco) : "sem ganho"}</span>
            </span>
          </button>
          <button class="excluir" data-excluir="${s.id}" title="Excluir planejamento" aria-label="Excluir planejamento">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round"><path d="M5 7h14M10 7V5h4v2M6 7l1 12h10l1-12M10 11v5M14 11v5"/></svg>
          </button>
        </div>`;
      }).join("") : `
        <div class="vazio" style="padding:30px">
          Nenhum planejamento salvo ainda.<br>
          Monte uma viagem e use "Salvar planejamento" na tela de resultado.
        </div>`}
      ${estado.temArmazem
        ? `<div class="leitura neutra">Os planejamentos ficam gravados neste navegador e
             continuam disponíveis ao reabrir o arquivo.</div>`
        : `<div class="leitura neutra">Este navegador não permitiu gravação local, então os
             planejamentos existem só enquanto a página estiver aberta.</div>`}
    </section>

    <section class="painel" style="margin-top:16px">
      <div class="painel-topo"><h2>Exemplos da regional</h2></div>
      ${exemplos.map((e) => `
        <div class="plan">
          <div class="plan-topo">
            <span class="plan-nome">${e.nome}</span>
            <span class="plan-estado e-${e.estado}">${e.rotulo}</span>
          </div>
          <div class="plan-meta">
            ${plural(e.agencias, "agência", "agências")} · ${plural(e.dias, "dia", "dias")} ·
            início ${dataBR(e.inicio)} · R$ ${e.custo.toLocaleString("pt-BR")}
          </div>
        </div>`).join("")}
      <div class="leitura neutra">
        Estes quatro exemplos são simulados, para demonstrar o histórico que o sistema
        acumularia com o uso.
      </div>
    </section>`;

  $("#criar").onclick = () => { estado.plano = novoPlano(); irPara("novo"); };
  $("#conteudo").querySelectorAll("[data-abrir]").forEach((b) => {
    b.onclick = () => abrirSalvo(b.dataset.abrir);
  });
  $("#conteudo").querySelectorAll("[data-excluir]").forEach((b) => {
    b.onclick = () => excluirSalvo(b.dataset.excluir);
  });
}

/* ---------- tela de agências ---------- */
function pintarAgencias() {
  const r = estado.regional;
  const todas = agenciasDa(r.id);
  const f = estado.filtroAgencias;

  const ufs = [...new Set(todas.map((a) => a.uf))].sort();
  const muns = [...new Set(todas.map((a) => a.municipio))].sort((a, b) => a.localeCompare(b, "pt-BR"));

  const texto = f.texto.trim().toLowerCase();
  const lista = todas.filter((a) =>
    (!texto || a.nome.toLowerCase().includes(texto) || a.municipio.toLowerCase().includes(texto) ||
      String(a.codigo).includes(texto) || a.bairro.toLowerCase().includes(texto)) &&
    (!f.uf || a.uf === f.uf) &&
    (!f.municipio || a.municipio === f.municipio) &&
    (!f.prioridade || a.prioridade === f.prioridade)
  ).sort((a, b) => dias(a.dataLimite) - dias(b.dataLimite));

  const porPrecisao = todas.reduce((c, a) => ((c[a.precisao] = (c[a.precisao] || 0) + 1), c), {});
  const exatas = (porPrecisao.bairro || 0) + (porPrecisao.bairro_aprox || 0);

  const prazoClasse = (d) => (d < 0 ? "urgente" : d <= 30 ? "proximo" : "");
  const prazoTexto = (d) => (d < 0 ? `${Math.abs(d)} d em atraso` : d === 0 ? "vence hoje" : `em ${d} d`);

  $("#conteudo").innerHTML = `
    <div class="pagina">
      <div>
        <h1>Agências da regional</h1>
        <p>${plural(r.agencias, "agência", "agências")} em ${plural(r.municipios, "município", "municípios")}
           (${r.ufs.join(", ")}). Cadastro do Banco Central; prioridade e prazo são dados de planejamento.</p>
      </div>
      <div class="pagina-acoes">
        <button class="btn btn-principal" id="planejar">Planejar visitas</button>
      </div>
    </div>

    <div class="forma">
      <div class="forma-corpo">
        <div class="filtros">
          <input type="text" class="entrada busca" id="a-texto" placeholder="Buscar por agência, bairro, cidade ou código" value="${esc(f.texto)}">
          <select id="a-uf"><option value="">Todos os estados</option>
            ${ufs.map((u) => `<option ${f.uf === u ? "selected" : ""}>${u}</option>`).join("")}</select>
          <select id="a-mun"><option value="">Todas as cidades</option>
            ${muns.map((m) => `<option ${f.municipio === m ? "selected" : ""}>${esc(m)}</option>`).join("")}</select>
          <select id="a-pri"><option value="">Todas as prioridades</option>
            <option value="alta" ${f.prioridade === "alta" ? "selected" : ""}>Prioridade alta</option>
            <option value="media" ${f.prioridade === "media" ? "selected" : ""}>Prioridade média</option>
            <option value="baixa" ${f.prioridade === "baixa" ? "selected" : ""}>Prioridade baixa</option></select>
        </div>

        <div class="ag-colunas">
        <div class="mapa-caixa" style="position:sticky;top:80px">
          <div id="mapa-agencias"></div>
          <div class="mapa-legenda">
            <span class="ch"><i class="bola" style="background:#9A5B12"></i> Prioridade alta</span>
            <span class="ch"><i class="bola" style="background:#12263A"></i> Média</span>
            <span class="ch"><i class="bola" style="background:#7E93A8"></i> Baixa</span>
            <span class="ch"><i class="bola vazia"></i> Fora dos filtros</span>
            <span class="ajuda">Clique num ponto para localizar a agência na lista.
              Agências da mesma cidade abrem em leque.</span>
          </div>
        </div>

        <div class="tabela">
          <div class="tabela-topo">
            <span>${lista.length === todas.length
              ? plural(todas.length, "agência", "agências")
              : `${lista.length} de ${todas.length} agências`}</span>
            <span style="margin-left:auto">ordenadas por prazo</span>
          </div>
          <div class="tabela-corpo">
            ${lista.length ? lista.map((a) => {
              const d = dias(a.dataLimite);
              return `
              <div class="item-ag ${estado.agenciaFoco === a.id ? "focada" : ""}"
                   data-linha-ag="${a.id}" style="cursor:default">
                <span class="marca-pri pri-${a.prioridade}">${
                  a.prioridade === "alta" ? "Alta" : a.prioridade === "media" ? "Média" : "Baixa"}</span>
                <span class="corpo">
                  <span class="n">${esc(a.nome)}</span>
                  <span class="l">${esc(a.endereco)} · ${esc(a.bairro)} · ${esc(a.municipio)}/${a.uf}
                    · agência ${a.codigo}${a.precisao === "municipio" ? " · localização aproximada" : ""}</span>
                </span>
                <span class="dir ${prazoClasse(d)}">
                  <span class="d">${dataBR(a.dataLimite)}</span>
                  <span class="r">${prazoTexto(d)}</span>
                </span>
              </div>`;
            }).join("") : `<div class="vazio">Nenhuma agência corresponde aos filtros.</div>`}
          </div>
        </div>
        </div>

        <p class="rodape-nota" style="margin-top:16px">
          <b>Precisão da localização.</b> ${exatas} de ${todas.length} agências desta regional têm
          coordenada de bairro; as demais usam o centro do município e aparecem marcadas como
          localização aproximada. Isso não afeta o cálculo de rotas entre cidades, mas explica
          por que agências vizinhas podem dividir o mesmo ponto no mapa.
        </p>
      </div>
    </div>`;

  pintarMapaAgencias(todas, lista);

  const repintar = () => pintarAgencias();
  $("#a-texto").oninput = (e) => {
    f.texto = e.target.value;
    const pos = e.target.selectionStart;
    pintarAgencias();
    const campo = $("#a-texto");
    campo.focus();
    campo.setSelectionRange(pos, pos);
  };
  $("#a-uf").onchange = (e) => { f.uf = e.target.value; f.municipio = ""; repintar(); };
  $("#a-mun").onchange = (e) => { f.municipio = e.target.value; repintar(); };
  $("#a-pri").onchange = (e) => { f.prioridade = e.target.value; repintar(); };
  $("#planejar").onclick = () => { estado.plano = novoPlano(); irPara("novo"); };
}
