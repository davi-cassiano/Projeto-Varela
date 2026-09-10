/* =====================================================================
   MAPA DA ROTA

   Base cartográfica real: contorno dos 27 estados brasileiros, embutido
   no arquivo (nenhum tile, nenhuma requisição — funciona offline).

   Projeção equirretangular com correção de latitude no ponto central da
   rota. Em escala estadual a distorção é irrelevante, e o cálculo de
   distância nunca passa por aqui: quem calcula é o motor, por haversine.

   Interação: arrastar move, roda amplia, clicar num trecho ou numa
   parada abre o detalhe. O enquadramento vive em estado.mapa, para
   sobreviver às repinturas do itinerário.
   ===================================================================== */

const MAPA_L = 680, MAPA_A = 500, MAPA_M = 62;

const COR_MODAL = { carro: "#12263A", onibus: "#0E7C66", aviao: "#9A5B12" };

/* ---------- projeção ---------- */
function projetorMapa(pontos) {
  const lats = pontos.map((p) => p.lat), lons = pontos.map((p) => p.lon);
  const latMedia = lats.reduce((a, b) => a + b, 0) / lats.length;
  const cosLat = Math.cos((latMedia * Math.PI) / 180);

  const minX = Math.min(...lons) * cosLat, maxX = Math.max(...lons) * cosLat;
  const minY = -Math.max(...lats), maxY = -Math.min(...lats);
  const larg = Math.max(maxX - minX, 0.05), alt = Math.max(maxY - minY, 0.05);
  const escala = Math.min((MAPA_L - 2 * MAPA_M) / larg, (MAPA_A - 2 * MAPA_M) / alt);
  const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;

  const proj = (p) => ({
    x: MAPA_L / 2 + (p.lon * cosLat - cx) * escala,
    y: MAPA_A / 2 + (-p.lat - cy) * escala,
  });
  proj.kmPorUnidade = 111.32 / escala;
  return proj;
}

function vistaInicial() {
  return { x: 0, y: 0, w: MAPA_L, h: MAPA_A };
}

/* ---------- base cartográfica ---------- */
function desenharEstados(proj, ufsDaRota, v) {
  /* Visibilidade por interseção de retângulos. Testar vértice a vértice
     falha justamente no caso mais comum: um zoom dentro do estado, em
     que nenhum vértice da fronteira aparece na tela. */
  const k = v.w / MAPA_L;

  return DADOS.estados.map((e) => {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    const partes = e.aneis.map((anel) =>
      anel.map(([lon, lat], i) => {
        const q = proj({ lat, lon });
        if (q.x < x0) x0 = q.x;
        if (q.x > x1) x1 = q.x;
        if (q.y < y0) y0 = q.y;
        if (q.y > y1) y1 = q.y;
        return `${i ? "L" : "M"}${q.x.toFixed(1)} ${q.y.toFixed(1)}`;
      }).join("") + "Z"
    );

    const fora = x1 < v.x || x0 > v.x + v.w || y1 < v.y || y0 > v.y + v.h;
    if (fora) return "";

    const realce = ufsDaRota.has(e.uf);
    const d = partes.join("");

    const c = proj({ lat: e.centro[1], lon: e.centro[0] });
    const dentro =
      c.x > v.x + 16 && c.x < v.x + v.w - 16 && c.y > v.y + 16 && c.y < v.y + v.h - 16;

    const rotulo = dentro
      ? `<text x="${c.x.toFixed(1)}" y="${c.y.toFixed(1)}" text-anchor="middle"
           font-size="${(11 * k).toFixed(1)}" font-weight="600"
           fill="${realce ? "#5C8378" : "#9BABBB"}" pointer-events="none">${e.uf}</text>`
      : "";

    return `<path d="${d}" fill="${realce ? "#DEE9E5" : "#E7EDF3"}"
              stroke="${realce ? "#9FBDB4" : "#CBD6E1"}"
              stroke-width="${(0.9 * k).toFixed(2)}" pointer-events="none"/>${rotulo}`;
  }).join("");
}

/* ---------- camada de cidades ----------
   Contexto geográfico no zoom próximo, onde o contorno do estado sozinho
   não diz nada. Só entram cidades visíveis, e os rótulos passam por um
   controle de sobreposição para não virar borrão. */
function desenharCidades(proj, v, ocupados) {
  const k = v.w / MAPA_L;
  const kmPorPixel = proj.kmPorUnidade * k;

  /* Em vista nacional, só capitais. Aproximando, entram as demais. */
  const soCapitais = kmPorPixel > 1.2;
  if (kmPorPixel > 4) return "";

  const candidatos = [];
  for (const [nome, uf, lat, lon, capital] of DADOS.cidades) {
    if (soCapitais && !capital) continue;
    const q = proj({ lat, lon });
    if (q.x < v.x + 6 || q.x > v.x + v.w - 6 || q.y < v.y + 6 || q.y > v.y + v.h - 6) continue;
    candidatos.push({ nome, capital, x: q.x, y: q.y });
    if (candidatos.length > 700) break;
  }

  /* capitais primeiro, para vencerem a disputa por espaço */
  candidatos.sort((a, b) => b.capital - a.capital);

  const saida = [];
  let rotulados = 0;
  for (const c of candidatos) {
    const r = (c.capital ? 3.2 : 2.2) * k;
    saida.push(`<circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="${r.toFixed(1)}"
      fill="#8FA3B6" fill-opacity="${c.capital ? ".95" : ".7"}" pointer-events="none"/>`);

    if (rotulados >= 18) continue;
    const larg = c.nome.length * 5.2 * k, alt = 13 * k;
    const cx = c.x, cy = c.y + 11 * k;
    const bate = ocupados.some(
      (o) => Math.abs(o.x - cx) < (o.w + larg) / 2 && Math.abs(o.y - cy) < (o.h + alt) / 2
    );
    if (bate) continue;
    ocupados.push({ x: cx, y: cy, w: larg, h: alt });
    rotulados++;
    saida.push(`<text class="cidade-rot" x="${cx.toFixed(1)}" y="${cy.toFixed(1)}"
      text-anchor="middle" font-size="${((c.capital ? 9.5 : 8.5) * k).toFixed(1)}"
      font-weight="${c.capital ? 600 : 400}" stroke-width="${(3 * k).toFixed(1)}"
      pointer-events="none">${esc(c.nome)}</text>`);
  }
  return saida.join("");
}


/* ---------- navegação compartilhada ----------
   Zoom, arraste e enquadramento servem aos dois mapas: o da rota e o da
   aba de agências. Cada um passa a própria vista e a própria repintura. */
function ligarNavegacao({ area, svg, vista, aplicar, repintar, pontos }) {
  const limitar = () => {
    vista.w = Math.min(Math.max(vista.w, MAPA_L / 60), MAPA_L * 16);
    vista.h = vista.w * (MAPA_A / MAPA_L);
  };

  const zoom = (fator, cxRel = 0.5, cyRel = 0.5) => {
    const ax = vista.x + vista.w * cxRel, ay = vista.y + vista.h * cyRel;
    vista.w *= fator;
    limitar();
    vista.x = ax - vista.w * cxRel;
    vista.y = ay - vista.h * cyRel;
    repintar();
  };

  const verBrasil = () => {
    const proj = projetorMapa(pontos);
    const a = proj({ lat: 5.5, lon: -74.5 }), b = proj({ lat: -34.0, lon: -34.0 });
    vista.w = Math.abs(b.x - a.x) * 1.06;
    limitar();
    vista.x = (a.x + b.x) / 2 - vista.w / 2;
    vista.y = (a.y + b.y) / 2 - vista.h / 2;
    repintar();
  };

  area.querySelectorAll("[data-zoom]").forEach((b) => {
    b.onclick = (e) => {
      e.stopPropagation();
      const q = b.dataset.zoom;
      if (q === "reset") { aplicar(vistaInicial()); return repintar(); }
      if (q === "brasil") return verBrasil();
      zoom(q === "mais" ? 0.7 : 1 / 0.7);
    };
  });

  svg.addEventListener("wheel", (e) => {
    e.preventDefault();
    const r = svg.getBoundingClientRect();
    zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15,
         (e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height);
  }, { passive: false });

  let arrastando = null;
  svg.addEventListener("pointerdown", (e) => {
    arrastando = { x: e.clientX, y: e.clientY, vx: vista.x, vy: vista.y, moveu: false };
    svg.setPointerCapture(e.pointerId);
    svg.classList.add("arrastando");
  });
  svg.addEventListener("pointermove", (e) => {
    if (!arrastando) return;
    const r = svg.getBoundingClientRect();
    const dx = e.clientX - arrastando.x, dy = e.clientY - arrastando.y;
    if (Math.hypot(dx, dy) > 3) arrastando.moveu = true;
    vista.x = arrastando.vx - (dx * vista.w) / r.width;
    vista.y = arrastando.vy - (dy * vista.h) / r.height;
    svg.setAttribute("viewBox", `${vista.x} ${vista.y} ${vista.w} ${vista.h}`);
  });
  const soltar = () => {
    if (!arrastando) return;
    const moveu = arrastando.moveu;
    arrastando = null;
    svg.classList.remove("arrastando");
    if (moveu) repintar();
  };
  svg.addEventListener("pointerup", soltar);
  svg.addEventListener("pointercancel", soltar);
}

/* botões e escala, comuns aos dois mapas */
function controlesMapa() {
  return `
    <div class="mapa-controles">
      <button data-zoom="mais" aria-label="Aproximar">+</button>
      <button data-zoom="menos" aria-label="Afastar">&minus;</button>
      <button data-zoom="reset" aria-label="Enquadrar tudo" title="Enquadrar tudo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>
      </button>
      <button data-zoom="brasil" class="txt" aria-label="Ver o Brasil inteiro"
              title="Ver o Brasil inteiro">BR</button>
    </div>`;
}

function escalaMapa(proj, v) {
  const k = v.w / MAPA_L;
  const alvoPx = 110 * k;
  const passos = [1, 2, 5, 10, 25, 50, 100, 200, 400, 800, 1600, 3000];
  const alvo = passos.reduce((a, b) =>
    Math.abs(b / proj.kmPorUnidade - alvoPx) < Math.abs(a / proj.kmPorUnidade - alvoPx) ? b : a);
  return `
    <div class="mapa-escala">
      <div class="barra" style="width:${((alvo / proj.kmPorUnidade) / k).toFixed(1)}px"></div>
      <span>${alvo} km</span>
    </div>`;
}

/* agrupa pontos que dividem a mesma coordenada e abre o grupo em leque */
function espalhar(posicoes, k, raioBase = 13) {
  const grupos = [];
  posicoes.forEach((q, i) => {
    const g = grupos.find((x) => Math.hypot(x.x - q.x, x.y - q.y) < raioBase * k);
    if (g) g.itens.push(i);
    else grupos.push({ x: q.x, y: q.y, itens: [i] });
  });

  const ajuste = posicoes.map((q) => ({ ...q, ancora: null }));
  grupos.forEach((g) => {
    if (g.itens.length === 1) return;
    const raio = (raioBase + g.itens.length * 2.2) * k;
    g.itens.forEach((i, j) => {
      const ang = (2 * Math.PI * j) / g.itens.length - Math.PI / 2;
      ajuste[i] = {
        x: g.x + Math.cos(ang) * raio,
        y: g.y + Math.sin(ang) * raio,
        ancora: { x: g.x, y: g.y },
      };
    });
  });
  return { ajuste, grupos };
}

/* ---------- desenho ---------- */
function desenharMapa(rt) {
  const proj = projetorMapa(rt.pontos);
  if (!estado.mapa) estado.mapa = vistaInicial();
  const v = estado.mapa;
  const k = v.w / MAPA_L; /* mantém traços e textos com espessura constante na tela */

  const origem = rt.pontos[0];
  const o = proj(origem);
  const ufs = new Set(rt.ordem.map((a) => a.uf));

  /* Agências da regional que ficaram de fora da rota. Ficam visíveis de
     propósito: mostram o que o gerente deixou para um próximo ciclo. */
  const foraDaRota = agenciasDa(estado.regional.id)
    .filter((a) => !estado.plano.selecionadas.has(a.id));
  const posFora = espalhar(foraDaRota.map((a) => proj(a)), k, 9);
  const contexto = foraDaRota
    .map((a, i) => ({ a, q: posFora.ajuste[i] }))
    .filter(({ q }) => q.x > v.x - 20 && q.x < v.x + v.w + 20 &&
                       q.y > v.y - 20 && q.y < v.y + v.h + 20);

  /* barra de escala com valor redondo, recalculada a cada zoom */
  const alvoPx = 110 * k;
  const passos = [1, 2, 5, 10, 25, 50, 100, 200, 400, 800, 1600, 3000];
  const alvo = passos.reduce((a, b) =>
    Math.abs(b / proj.kmPorUnidade - alvoPx) < Math.abs(a / proj.kmPorUnidade - alvoPx) ? b : a);
  const larguraBarra = (alvo / proj.kmPorUnidade) / k;

  const caminho = (t) => {
    const a = proj(t.de), b = proj(t.para);
    if (t.escolha.modal !== "aviao") {
      return `M${a.x.toFixed(1)} ${a.y.toFixed(1)} L${b.x.toFixed(1)} ${b.y.toFixed(1)}`;
    }
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    const dx = b.x - a.x, dy = b.y - a.y;
    return `M${a.x.toFixed(1)} ${a.y.toFixed(1)} Q${(mx - dy * 0.18).toFixed(1)} ${(my + dx * 0.18).toFixed(1)} ${b.x.toFixed(1)} ${b.y.toFixed(1)}`;
  };

  const segmentos = rt.trechos.map((t) => {
    const d = caminho(t);
    const cor = COR_MODAL[t.escolha.modal];
    const ativo = estado.expandido === t.indice;
    const aereo = t.escolha.modal === "aviao";
    return `
      <g data-segmento="${t.indice}" style="cursor:pointer">
        <path d="${d}" fill="none" stroke="#FFFFFF" stroke-opacity=".8"
              stroke-width="${(5.6 * k).toFixed(2)}" stroke-linecap="round" pointer-events="none"/>
        <path d="${d}" fill="none" stroke="${cor}"
              stroke-width="${((ativo ? 3.8 : 2.2) * k).toFixed(2)}"
              stroke-linecap="round" stroke-linejoin="round"
              stroke-dasharray="${aereo ? `${(7 * k).toFixed(1)} ${(5 * k).toFixed(1)}` : "none"}"
              pointer-events="none"/>
        <path d="${d}" fill="none" stroke="#000" stroke-opacity="0"
              stroke-width="${(16 * k).toFixed(1)}"/>
      </g>`;
  }).join("");

  /* seta de sentido no meio do trecho: mais legível que ponta de flecha */
  const setas = rt.trechos.map((t) => {
    const a = proj(t.de), b = proj(t.para);
    if (Math.hypot(b.x - a.x, b.y - a.y) < 36 * k) return "";
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    const ang = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
    return `<path d="M-4 -3.4L4.6 0L-4 3.4Z" fill="${COR_MODAL[t.escolha.modal]}"
      transform="translate(${mx.toFixed(1)},${my.toFixed(1)}) rotate(${ang.toFixed(1)}) scale(${k.toFixed(2)})"
      pointer-events="none"/>`;
  }).join("");

  /* ---- pinos coincidentes ----
     Agências da mesma cidade dividem a coordenada, então os pinos se
     empilhariam e só o último apareceria. Nesse caso o grupo é aberto em
     leque em torno do ponto real, com um fio ligando à posição verdadeira. */
  const { ajuste, grupos } = espalhar(rt.ordem.map((a) => proj(a)), k);

  /* Espaços já ocupados por rótulos da rota: as cidades cedem lugar. */
  const ocupados = [];
  const rotulaCidade = new Set(grupos.map((g) => g.itens[0]));
  rt.ordem.forEach((a, i) => {
    if (!rotulaCidade.has(i)) return;
    const g = grupos.find((x) => x.itens.includes(i));
    ocupados.push({
      x: g.x, y: g.y + 26 * k,
      w: a.municipio.length * 6 * k, h: 15 * k,
    });
  });
  ocupados.push({ x: o.x, y: o.y - 15 * k, w: origem.municipio.length * 6.5 * k, h: 15 * k });

  const paradas = rt.ordem.map((a, i) => {
    const q = ajuste[i];
    const g = grupos.find((x) => x.itens.includes(i));
    const t = rt.trechos.find((x) => x.para === a);
    const ativo = t && estado.expandido === t.indice;
    const r = (ativo ? 12.5 : 10.5) * k;

    const fio = q.ancora
      ? `<line x1="${q.ancora.x.toFixed(1)}" y1="${q.ancora.y.toFixed(1)}"
           x2="${q.x.toFixed(1)}" y2="${q.y.toFixed(1)}" stroke="#12263A" stroke-opacity=".45"
           stroke-width="${(1.1 * k).toFixed(2)}" pointer-events="none"/>`
      : "";

    const etiqueta = rotulaCidade.has(i)
      ? `<text class="etiqueta" x="${g.x.toFixed(1)}" y="${(g.y + (g.itens.length > 1 ? 30 : 22) * k).toFixed(1)}"
           text-anchor="middle" font-size="${(10.5 * k).toFixed(1)}"
           stroke-width="${(3.2 * k).toFixed(1)}" pointer-events="none">${esc(a.municipio)}</text>`
      : "";

    return `
      ${fio}
      <g data-segmento="${t ? t.indice : ""}" tabindex="0" role="button" style="cursor:pointer"
         aria-label="Parada ${i + 1}, ${esc(a.nome)}, ${esc(a.municipio)}">
        <circle cx="${q.x.toFixed(1)}" cy="${q.y.toFixed(1)}" r="${(r + 5 * k).toFixed(1)}"
                fill="#12263A" fill-opacity="${ativo ? ".16" : "0"}"/>
        <circle cx="${q.x.toFixed(1)}" cy="${q.y.toFixed(1)}" r="${r.toFixed(1)}"
                fill="${ativo ? "#0E7C66" : "#12263A"}" stroke="#FFFFFF"
                stroke-width="${(2 * k).toFixed(2)}"/>
        <text x="${q.x.toFixed(1)}" y="${(q.y + 3.8 * k).toFixed(1)}" text-anchor="middle"
              font-size="${(11 * k).toFixed(1)}" font-weight="600" fill="#FFFFFF"
              pointer-events="none">${i + 1}</text>
      </g>
      ${etiqueta}`;
  }).join("");

  return `
    <div class="mapa" id="mapa-area">
      <svg id="mapa-svg" viewBox="${v.x} ${v.y} ${v.w} ${v.h}"
           role="img" aria-label="Mapa da rota planejada sobre o território brasileiro">
        <rect x="${v.x}" y="${v.y}" width="${v.w}" height="${v.h}" fill="#DCE6EE"/>
        <g>${desenharEstados(proj, ufs, v)}</g>
        <g>${desenharCidades(proj, v, ocupados)}</g>
        <g class="fora-rota">${contexto.map(({ a, q }) => `
          ${q.ancora ? `<line x1="${q.ancora.x.toFixed(1)}" y1="${q.ancora.y.toFixed(1)}"
              x2="${q.x.toFixed(1)}" y2="${q.y.toFixed(1)}" stroke="#7E93A8" stroke-opacity=".6"
              stroke-width="${(0.9 * k).toFixed(2)}" pointer-events="none"/>` : ""}
          <circle class="fora" data-agencia="${a.id}" cx="${q.x.toFixed(1)}" cy="${q.y.toFixed(1)}"
              r="${(6 * k).toFixed(1)}" fill="#FFFFFF" stroke="#5A7185"
              stroke-width="${(1.8 * k).toFixed(2)}" style="cursor:help"/>`).join("")}</g>
        ${segmentos}
        ${setas}
        <g aria-label="Ponto de partida">
          <circle cx="${o.x.toFixed(1)}" cy="${o.y.toFixed(1)}" r="${(10.5 * k).toFixed(1)}"
                  fill="#FFFFFF" stroke="#12263A" stroke-width="${(2.6 * k).toFixed(2)}"/>
          <path d="M-4.4 1L0 -3.3L4.4 1M-2.9 0.4V4.4h5.8V0.4" fill="none" stroke="#12263A"
                stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                transform="translate(${o.x.toFixed(1)},${o.y.toFixed(1)}) scale(${k.toFixed(2)})"
                pointer-events="none"/>
          <text class="etiqueta" x="${o.x.toFixed(1)}" y="${(o.y - 15 * k).toFixed(1)}"
                text-anchor="middle" font-size="${(11 * k).toFixed(1)}" font-weight="600"
                stroke-width="${(3.4 * k).toFixed(1)}" pointer-events="none">${esc(origem.municipio)}</text>
        </g>
        ${paradas}
      </svg>

      <div class="mapa-controles">
        <button data-zoom="mais" aria-label="Aproximar">+</button>
        <button data-zoom="menos" aria-label="Afastar">&minus;</button>
        <button data-zoom="reset" aria-label="Enquadrar a rota" title="Enquadrar a rota">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
               stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>
        </button>
        <button data-zoom="brasil" class="txt" aria-label="Ver o Brasil inteiro"
                title="Ver o Brasil inteiro">BR</button>
      </div>

      <div class="mapa-escala">
        <div class="barra" style="width:${larguraBarra.toFixed(1)}px"></div>
        <span>${alvo} km</span>
      </div>

      <div class="mapa-dica" id="mapa-dica" hidden></div>
    </div>`;
}

/* ---------- interação do mapa da rota ---------- */
function ligarMapa(rt) {
  const area = $("#mapa-area");
  const svg = $("#mapa-svg");
  if (!svg) return;

  ligarNavegacao({
    area, svg,
    vista: estado.mapa,
    aplicar: (v) => { estado.mapa = v; },
    repintar: () => pintarMapa(rt),
    pontos: rt.pontos,
  });

  const abrir = (i) => {
    if (i === "" || i === undefined) return;
    estado.expandido = estado.expandido === +i ? null : +i;
    atualizarItinerario(rt);
    pintarMapa(rt);
    const alvo = $("#conteudo").querySelector(`.trecho[data-trecho="${i}"]`);
    if (alvo && estado.expandido !== null) alvo.scrollIntoView({ block: "center", behavior: "smooth" });
  };

  area.querySelectorAll("[data-agencia]").forEach((c) => {
    const a = DADOS.agencias.find((x) => x.id === c.dataset.agencia);
    if (!a) return;
    c.onmouseenter = () => dicaAgencia(a, "não incluída nesta viagem");
    c.onmouseleave = esconderDica;
  });

  area.querySelectorAll("[data-segmento]").forEach((g) => {
    g.onclick = () => abrir(g.dataset.segmento);
    g.onmouseenter = () => mostrarDica(rt, +g.dataset.segmento);
    g.onmouseleave = esconderDica;
    g.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrir(g.dataset.segmento); }
    };
  });
}

function mostrarDica(rt, i) {
  const t = rt.trechos[i];
  const d = $("#mapa-dica");
  if (!t || !d) return;
  const nomes = { carro: "Carro", onibus: "Ônibus", aviao: "Avião" };
  d.innerHTML = `
    <b>${esc(t.de.nome || t.de.municipio)} &rarr; ${esc(t.para.nome || t.para.municipio)}</b>
    <span>${nomes[t.escolha.modal]} · ${Math.round(t.escolha.distanciaKm)} km ·
      ${duracao(t.escolha.minutos)} · ${dinheiro(t.escolha.custo)}</span>`;
  d.hidden = false;
}

function dicaAgencia(a, complemento) {
  const d = $("#mapa-dica");
  if (!d) return;
  const p = { alta: "prioridade alta", media: "prioridade média", baixa: "prioridade baixa" }[a.prioridade];
  const dd = dias(a.dataLimite);
  d.innerHTML = `
    <b>${esc(a.nome)}</b>
    <span>${esc(a.municipio)}/${a.uf} · ${p}</span>
    <span>prazo ${dataBR(a.dataLimite)}${dd < 0 ? " (vencido)" : ""}${
      complemento ? " · " + complemento : ""}</span>`;
  d.hidden = false;
}

function esconderDica() {
  const d = $("#mapa-dica");
  if (d) d.hidden = true;
}

function pintarMapa(rt) {
  const caixa = $("#mapa");
  if (!caixa) return;
  caixa.innerHTML = desenharMapa(rt);
  ligarMapa(rt);
}

/* =====================================================================
   MAPA DA ABA DE AGÊNCIAS

   Mostra a regional inteira. As agências que passam pelos filtros ativos
   aparecem cheias e coloridas por prioridade; as demais ficam apagadas,
   para que o efeito do filtro seja visível no mapa e não só na lista.
   ===================================================================== */

const COR_PRIORIDADE = { alta: "#9A5B12", media: "#12263A", baixa: "#7E93A8" };

function desenharMapaAgencias(todas, visiveis) {
  const proj = projetorMapa(todas);
  if (!estado.mapaAg) estado.mapaAg = vistaInicial();
  const v = estado.mapaAg;
  const k = v.w / MAPA_L;

  const ufs = new Set(todas.map((a) => a.uf));
  const dentroDoFiltro = new Set(visiveis.map((a) => a.id));

  const { ajuste, grupos } = espalhar(todas.map((a) => proj(a)), k, 11);

  /* rótulo de cidade uma vez por grupo, e só se houver espaço */
  const ocupados = [];
  const rotula = new Map();
  grupos.forEach((g) => {
    const a = todas[g.itens[0]];
    const larg = a.municipio.length * 5.6 * k, alt = 14 * k;
    const cx = g.x, cy = g.y + (g.itens.length > 1 ? 30 : 20) * k;
    const bate = ocupados.some(
      (o) => Math.abs(o.x - cx) < (o.w + larg) / 2 && Math.abs(o.y - cy) < (o.h + alt) / 2
    );
    if (bate) return;
    ocupados.push({ x: cx, y: cy, w: larg, h: alt });
    rotula.set(g.itens[0], { x: cx, y: cy, nome: a.municipio });
  });

  const pontos = todas.map((a, i) => {
    const q = ajuste[i];
    const ativa = dentroDoFiltro.has(a.id);
    const foco = estado.agenciaFoco === a.id;
    const r = (foco ? 9 : ativa ? 7 : 5) * k;
    const cor = ativa ? COR_PRIORIDADE[a.prioridade] : "#FFFFFF";
    const rot = rotula.get(i);

    const fio = q.ancora
      ? `<line x1="${q.ancora.x.toFixed(1)}" y1="${q.ancora.y.toFixed(1)}"
           x2="${q.x.toFixed(1)}" y2="${q.y.toFixed(1)}" stroke="#8A9DB0"
           stroke-opacity=".55" stroke-width="${(0.9 * k).toFixed(2)}" pointer-events="none"/>`
      : "";

    const etiqueta = rot
      ? `<text class="etiqueta" x="${rot.x.toFixed(1)}" y="${rot.y.toFixed(1)}"
           text-anchor="middle" font-size="${(10 * k).toFixed(1)}"
           stroke-width="${(3.2 * k).toFixed(1)}" pointer-events="none">${esc(rot.nome)}</text>`
      : "";

    return `
      ${fio}
      <g data-agencia="${a.id}" tabindex="0" role="button" style="cursor:pointer"
         aria-label="${esc(a.nome)}, ${esc(a.municipio)}">
        ${foco ? `<circle cx="${q.x.toFixed(1)}" cy="${q.y.toFixed(1)}"
            r="${(r + 6 * k).toFixed(1)}" fill="#0E7C66" fill-opacity=".18"/>` : ""}
        <circle cx="${q.x.toFixed(1)}" cy="${q.y.toFixed(1)}" r="${r.toFixed(1)}"
                fill="${foco ? "#0E7C66" : cor}"
                stroke="${ativa || foco ? "#FFFFFF" : "#8A9DB0"}"
                stroke-width="${((ativa || foco ? 1.8 : 1.3) * k).toFixed(2)}"
                fill-opacity="${ativa || foco ? 1 : 0.9}"/>
      </g>
      ${etiqueta}`;
  }).join("");

  return `
    <div class="mapa" id="mapa-ag-area">
      <svg id="mapa-ag-svg" viewBox="${v.x} ${v.y} ${v.w} ${v.h}"
           role="img" aria-label="Mapa das agências da regional">
        <rect x="${v.x}" y="${v.y}" width="${v.w}" height="${v.h}" fill="#DCE6EE"/>
        <g>${desenharEstados(proj, ufs, v)}</g>
        <g>${desenharCidades(proj, v, ocupados)}</g>
        ${pontos}
      </svg>
      ${controlesMapa()}
      ${escalaMapa(proj, v)}
      <div class="mapa-dica" id="mapa-dica" hidden></div>
    </div>`;
}

function ligarMapaAgencias(todas, visiveis) {
  const area = $("#mapa-ag-area");
  const svg = $("#mapa-ag-svg");
  if (!svg) return;

  ligarNavegacao({
    area, svg,
    vista: estado.mapaAg,
    aplicar: (v) => { estado.mapaAg = v; },
    repintar: () => pintarMapaAgencias(todas, visiveis),
    pontos: todas,
  });

  area.querySelectorAll("[data-agencia]").forEach((g) => {
    const a = todas.find((x) => x.id === g.dataset.agencia);
    if (!a) return;
    const foraDoFiltro = !visiveis.some((x) => x.id === a.id);
    g.onmouseenter = () => dicaAgencia(a, foraDoFiltro ? "fora dos filtros atuais" : "");
    g.onmouseleave = esconderDica;
    g.onclick = () => focarAgencia(a);
    g.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); focarAgencia(a); }
    };
  });
}

/* Clicar no mapa destaca a agência e leva até ela na lista. */
function focarAgencia(a) {
  estado.agenciaFoco = estado.agenciaFoco === a.id ? null : a.id;
  pintarAgencias();
  if (estado.agenciaFoco) {
    const linha = $("#conteudo").querySelector(`[data-linha-ag="${a.id}"]`);
    if (linha) linha.scrollIntoView({ block: "center", behavior: "smooth" });
  }
}

function pintarMapaAgencias(todas, visiveis) {
  const caixa = $("#mapa-agencias");
  if (!caixa) return;
  caixa.innerHTML = desenharMapaAgencias(todas, visiveis);
  ligarMapaAgencias(todas, visiveis);
}
