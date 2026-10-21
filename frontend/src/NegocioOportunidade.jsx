import { useCallback, useEffect, useMemo, useState } from "react";
import "./modulos-novos.css";

const API = "http://127.0.0.1:8000/api/negocio-oportunidade";
const VAZIO = {
  tipo: "profissional", nome: "", area: "", habilidades: "", experiencia: "",
  escolaridade: "", localizacao: "", telefone: "", descricao: "", disponibilidade: "",
};

async function respostaApi(res) {
  const texto = await res.text();
  let dados = {};
  try { dados = texto ? JSON.parse(texto) : {}; } catch { dados = { detail: texto }; }
  if (!res.ok) throw new Error(dados.detail || dados.mensagem || `Erro do servidor (${res.status}).`);
  return dados;
}

export default function NegocioOportunidade({ utilizador }) {
  const [aba, setAba] = useState("pesquisar");
  const [termo, setTermo] = useState("");
  const [termoPesquisa, setTermoPesquisa] = useState("");
  const [filtro, setFiltro] = useState("todos");
  const [form, setForm] = useState({ ...VAZIO, nome: utilizador?.nome_completo || "" });
  const [resultados, setResultados] = useState([]);
  const [meus, setMeus] = useState([]);
  const [aviso, setAviso] = useState("");
  const [erro, setErro] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const token = sessionStorage.getItem("smartbook-token");

  const chamar = useCallback(async (url, options = {}) => {
    const res = await fetch(url, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
    });
    return respostaApi(res);
  }, [token]);

  const carregarPesquisa = useCallback(async () => {
    setCarregando(true); setErro(false); setAviso("");
    try {
      const query = new URLSearchParams({ q: termoPesquisa.trim(), tipo: filtro, limite: "100" });
      const data = await chamar(`${API}/pesquisar?${query}`);
      setResultados(data.registos || []);
    } catch (e) { setErro(true); setAviso(e.message || "Não foi possível pesquisar oportunidades."); }
    finally { setCarregando(false); }
  }, [chamar, termoPesquisa, filtro]);

  const carregarMeus = useCallback(async () => {
    setCarregando(true); setErro(false); setAviso("");
    try { const data = await chamar(`${API}/meus`); setMeus(data.registos || []); }
    catch (e) { setErro(true); setAviso(e.message || "Não foi possível carregar os teus registos."); }
    finally { setCarregando(false); }
  }, [chamar]);

  useEffect(() => { if (aba === "pesquisar") carregarPesquisa(); }, [aba, carregarPesquisa]);
  useEffect(() => { if (aba === "meus") carregarMeus(); }, [aba, carregarMeus]);

  function mudar(campo, valor) { setForm(atual => ({ ...atual, [campo]: valor })); }

  async function guardar(evento) {
    evento.preventDefault(); setCarregando(true); setAviso(""); setErro(false);
    try {
      await chamar(`${API}/registos`, { method: "POST", body: JSON.stringify(form) });
      setForm({ ...VAZIO, nome: utilizador?.nome_completo || "" });
      setAviso("Publicado na base de dados. Os outros membros já podem encontrar este registo.");
      setAba("meus");
    } catch (e) { setErro(true); setAviso(e.message || "Não foi possível publicar o registo."); }
    finally { setCarregando(false); }
  }

  async function eliminar(id) {
    if (!window.confirm("Queres eliminar este registo? Esta ação não pode ser desfeita.")) return;
    setCarregando(true); setAviso(""); setErro(false);
    try { await chamar(`${API}/registos/${id}`, { method: "DELETE" }); await carregarMeus(); setAviso("Registo eliminado."); }
    catch (e) { setErro(true); setAviso(e.message || "Não foi possível eliminar o registo."); }
    finally { setCarregando(false); }
  }

  const totalVisivel = useMemo(() => resultados.length, [resultados]);

  return <div className="sb-modulo sb-negocio">
    <header className="sb-negocio-hero">
      <div className="sb-negocio-emblema">✦</div><span className="sb-eyebrow">SMART BOOK · IMPACTO SOCIAL</span>
      <h2>Negócio com Oportunidade</h2>
      <p>Talento existe em todo o lado. A oportunidade deve chegar a todos.</p>
      <div className="sb-negocio-stats"><div><strong>{totalVisivel}</strong><span>Resultados da pesquisa</span></div><div><strong>AO</strong><span>Oportunidades em Angola</span></div><div><strong>∞</strong><span>Competências e serviços</span></div></div>
    </header>
    {aviso && <div className="sb-alerta" role="status" style={erro ? { borderColor: "#d9534f" } : undefined}>{aviso}</div>}
    <nav className="sb-tabs sb-negocio-tabs">
      <button className={aba === "pesquisar" ? "ativo" : ""} onClick={() => setAba("pesquisar")}>⌕ Pesquisar talento</button>
      <button className={aba === "criar" ? "ativo" : ""} onClick={() => { setForm(f => ({ ...f, tipo: "profissional" })); setAba("criar"); }}>＋ Criar perfil profissional</button>
      <button className={aba === "empresa" ? "ativo" : ""} onClick={() => { setForm(f => ({ ...f, tipo: "empresa" })); setAba("empresa"); }}>▤ Criar empreendimento</button>
      <button className={aba === "meus" ? "ativo" : ""} onClick={() => setAba("meus")}>♙ Os meus registos</button>
    </nav>

    {aba === "pesquisar" && <>
      <section className="sb-card"><h3>De quem precisas?</h3><p>Pesquisa por profissão, serviço, competência, empresa ou localização.</p>
        <form className="sb-search" onSubmit={e => { e.preventDefault(); setTermoPesquisa(termo.trim()); }}>
          <input value={termo} onChange={e => setTermo(e.target.value)} placeholder="Ex.: eletricista, professor, informática..." />
          <select value={filtro} onChange={e => setFiltro(e.target.value)}><option value="todos">Todos os perfis</option><option value="profissional">Profissionais</option><option value="empresa">Empresas / empreendimentos</option></select>
          <button disabled={carregando}>{carregando ? "A pesquisar…" : "Pesquisar"}</button>
        </form>
      </section>
      <div className="sb-opportunity-grid">{resultados.map(r => <article className="sb-card sb-opportunity" key={r.id}>
        <div className="sb-opportunity-top"><span className="sb-opportunity-type">{r.tipo === "empresa" ? "EMPREENDIMENTO" : "PROFISSIONAL"}</span><span className="sb-location">⌖ {r.localizacao || "Localização não indicada"}</span></div>
        <h3>{r.nome}</h3><h4>{r.area}</h4><p>{r.descricao || "Sem descrição adicional."}</p>
        <div className="sb-chips">{(r.habilidades || "").split(",").filter(Boolean).map((h, i) => <span key={i}>{h.trim()}</span>)}</div>
        <dl><div><dt>Experiência</dt><dd>{r.experiencia || "Não indicada"}</dd></div><div><dt>Formação</dt><dd>{r.escolaridade || "Não indicada"}</dd></div><div><dt>Disponibilidade</dt><dd>{r.disponibilidade || "A combinar"}</dd></div><div><dt>Publicado por</dt><dd>@{r.username || "membro"}</dd></div></dl>
        <div className="sb-contact-actions">{r.telefone ? <a href={`tel:${r.telefone.replace(/[^+\d]/g, "")}`}>☎ Ligar</a> : <span className="sb-note">Sem telefone público</span>}<a href={`mailto:?subject=${encodeURIComponent("Contacto pelo SMART BOOK")}&body=${encodeURIComponent(`Olá ${r.nome}, encontrei o teu registo no SMART BOOK e gostaria de falar contigo sobre uma oportunidade.`)}`}>✉ Contactar</a></div>
      </article>)}{!carregando && !resultados.length && <div className="sb-empty sb-empty-wide">Não foram encontrados registos. Podes publicar um perfil profissional ou empreendimento.</div>}</div>
    </>}

    {(aba === "criar" || aba === "empresa") && <section className="sb-card">
      <h3>{aba === "empresa" ? "Registar empreendimento ou serviço" : "Criar o meu perfil profissional"}</h3>
      <p>{aba === "empresa" ? "Apresenta a tua empresa, negócio, oficina, loja ou serviço." : "Não precisas de ter um diploma para mostrar aquilo que sabes fazer."}</p>
      <form className="sb-business-form" onSubmit={guardar}>
        <label>Nome completo ou empreendimento<input value={form.nome} onChange={e => mudar("nome", e.target.value)} required maxLength={120} /></label>
        <label>Profissão, serviço ou área<input value={form.area} onChange={e => mudar("area", e.target.value)} required maxLength={120} placeholder="Ex.: eletricista, explicador, pastelaria" /></label>
        <label>Habilidades e competências<input value={form.habilidades} onChange={e => mudar("habilidades", e.target.value)} required maxLength={500} placeholder="Separa por vírgulas" /></label>
        <label>Experiência<textarea value={form.experiencia} onChange={e => mudar("experiencia", e.target.value)} maxLength={500} rows={2} /></label>
        <label>Escolaridade / formação<select value={form.escolaridade} onChange={e => mudar("escolaridade", e.target.value)}><option value="">Selecionar (opcional)</option><option>Sem escolaridade formal</option><option>Ensino primário</option><option>Ensino I ciclo</option><option>Ensino médio</option><option>Ensino técnico-profissional</option><option>Licenciatura</option><option>Pós-graduação / Mestrado / Doutoramento</option><option>Aprendizagem prática / autodidata</option><option>Formação profissional</option></select></label>
        <label>Localização<input value={form.localizacao} onChange={e => mudar("localizacao", e.target.value)} maxLength={120} placeholder="Município, província" /></label>
        <label>Telefone público (opcional)<input value={form.telefone} onChange={e => mudar("telefone", e.target.value)} maxLength={40} type="tel" /></label>
        <label>Disponibilidade<input value={form.disponibilidade} onChange={e => mudar("disponibilidade", e.target.value)} maxLength={120} placeholder="Imediata, fins de semana..." /></label>
        <label className="sb-full">Descrição / serviços<textarea value={form.descricao} onChange={e => mudar("descricao", e.target.value)} maxLength={1500} rows={4} /></label>
        <div className="sb-full sb-privacy-note">O telefone será público. Publica apenas um contacto que autorizas outras pessoas a utilizar.</div>
        <button className="sb-full" disabled={carregando}>{carregando ? "A guardar…" : `Publicar ${aba === "empresa" ? "empreendimento" : "perfil profissional"}`}</button>
      </form>
    </section>}

    {aba === "meus" && <section className="sb-card"><div className="sb-card-title"><h3>Os meus registos publicados</h3><button className="sb-secondary" onClick={carregarMeus} disabled={carregando}>Atualizar</button></div>
      {meus.map(r => <div className="sb-person" key={r.id}><div className="sb-avatar">{(r.nome || "U").slice(0, 1).toUpperCase()}</div><div className="sb-person-info"><strong>{r.nome}</strong><small>{r.area} · {r.tipo === "empresa" ? "Empreendimento" : "Profissional"}</small></div><button className="sb-secondary" onClick={() => eliminar(r.id)} disabled={carregando}>Eliminar</button></div>)}
      {!carregando && !meus.length && <div className="sb-empty">Ainda não publicaste nenhum registo nesta conta.</div>}
    </section>}
    <p className="sb-disclaimer">Os registos são guardados na base de dados do SMART BOOK e podem ser encontrados por outros membros autenticados. Partilha dados de contacto apenas com autorização.</p>
  </div>;
}
