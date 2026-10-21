import { useCallback, useEffect, useState } from "react";
import "./modulos-novos.css";

const API = "http://127.0.0.1:8000/api/casa-inteligente";
async function ler(res) {
  const txt = await res.text(); let data = {};
  try { data = txt ? JSON.parse(txt) : {}; } catch { data = { detail: txt }; }
  if (!res.ok) throw new Error(data.detail || `Erro do servidor (${res.status}).`);
  return data;
}

export default function CasaInteligente() {
  const token = sessionStorage.getItem("smartbook-token");
  const [casas, setCasas] = useState([]);
  const [casaId, setCasaId] = useState("");
  const [dispositivos, setDispositivos] = useState([]);
  const [nomeCasa, setNomeCasa] = useState("");
  const [descricaoCasa, setDescricaoCasa] = useState("");
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState("light");
  const [integracao, setIntegracao] = useState("manual");
  const [entidade, setEntidade] = useState("");
  const [marca, setMarca] = useState("");
  const [aviso, setAviso] = useState("");
  const [erro, setErro] = useState(false);
  const [carregando, setCarregando] = useState(false);

  const api = useCallback(async (url, options = {}) => {
    const res = await fetch(url, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
    });
    return ler(res);
  }, [token]);

  const carregarCasas = useCallback(async () => {
    setCarregando(true); setErro(false);
    try {
      const data = await api(`${API}/casas`);
      const lista = data.casas || [];
      setCasas(lista);
      setCasaId(atual => lista.some(c => String(c.id) === String(atual)) ? String(atual) : (lista[0] ? String(lista[0].id) : ""));
      setAviso("");
    } catch (e) { setErro(true); setAviso(e.message || "Não foi possível carregar as casas."); }
    finally { setCarregando(false); }
  }, [api]);

  const carregarDispositivos = useCallback(async (id) => {
    if (!id) { setDispositivos([]); return; }
    setCarregando(true); setErro(false);
    try {
      const data = await api(`${API}/casas/${id}/dispositivos`);
      setDispositivos(data.dispositivos || []); setAviso("");
    } catch (e) { setErro(true); setAviso(e.message || "Não foi possível carregar os dispositivos."); }
    finally { setCarregando(false); }
  }, [api]);

  useEffect(() => { carregarCasas(); }, [carregarCasas]);
  useEffect(() => { if (casaId) carregarDispositivos(casaId); else setDispositivos([]); }, [casaId, carregarDispositivos]);

  async function criarCasa(e) {
    e.preventDefault(); setCarregando(true); setErro(false); setAviso("");
    try {
      const data = await api(`${API}/casas`, { method: "POST", body: JSON.stringify({ nome: nomeCasa, descricao: descricaoCasa || null }) });
      setNomeCasa(""); setDescricaoCasa("");
      const criada = data.casa;
      const atual = await api(`${API}/casas`);
      setCasas(atual.casas || []); setCasaId(String(criada.id));
      setAviso("Casa criada e guardada na base de dados.");
    } catch (e2) { setErro(true); setAviso(e2.message || "Não foi possível criar a casa."); }
    finally { setCarregando(false); }
  }

  async function adicionarDispositivo(e) {
    e.preventDefault(); if (!casaId) { setErro(true); setAviso("Cria ou seleciona uma casa primeiro."); return; }
    setCarregando(true); setErro(false); setAviso("");
    try {
      await api(`${API}/casas/${casaId}/dispositivos`, { method: "POST", body: JSON.stringify({
        nome, tipo, marca: marca || null, integracao,
        entidade_externa: integracao === "home_assistant" ? (entidade || null) : null,
      }) });
      setNome(""); setMarca(""); setEntidade("");
      await carregarDispositivos(casaId); setAviso("Dispositivo registado no SMART BOOK.");
    } catch (e2) { setErro(true); setAviso(e2.message || "Não foi possível registar o dispositivo."); }
    finally { setCarregando(false); }
  }

  async function comandar(d) {
    if (!casaId) return;
    const ligado = Boolean(d.estado_conhecido?.ligado);
    setCarregando(true); setErro(false); setAviso("");
    try {
      const data = await api(`${API}/casas/${casaId}/dispositivos/${d.id}/comando`, {
        method: "POST", body: JSON.stringify({ comando: ligado ? "desligar" : "ligar", parametros: {} }),
      });
      await carregarDispositivos(casaId);
      setAviso(data.mensagem || "Comando processado.");
    } catch (e) { setErro(true); setAviso(e.message || "Não foi possível comandar o dispositivo."); }
    finally { setCarregando(false); }
  }

  return <div className="sb-modulo sb-casa">
    <header className="sb-negocio-hero"><div className="sb-negocio-emblema">⌂</div><span className="sb-eyebrow">SMART BOOK · AUTOMAÇÃO</span><h2>Casa Inteligente</h2><p>Regista as tuas casas, organiza dispositivos e liga equipamentos compatíveis.</p><div className="sb-negocio-stats"><div><strong>{casas.length}</strong><span>Casas</span></div><div><strong>{dispositivos.length}</strong><span>Dispositivos registados</span></div><div><strong>API</strong><span>Ligação ao backend</span></div></div></header>
    {aviso && <div className="sb-alerta" role="status" style={erro ? { borderColor: "#d9534f" } : undefined}>{aviso}</div>}
    <section className="sb-card"><div className="sb-card-title"><h3>As minhas casas</h3><button type="button" className="sb-secondary" onClick={carregarCasas} disabled={carregando}>Atualizar</button></div>
      {casas.length > 0 ? <label className="sb-house-select">Seleciona a casa<select value={casaId} onChange={e => setCasaId(e.target.value)}>{casas.map(c => <option value={c.id} key={c.id}>{c.nome}</option>)}</select></label> : <p>Ainda não tens uma casa registada. Cria uma abaixo.</p>}
      <form className="sb-business-form" onSubmit={criarCasa}><label>Nome da casa<input value={nomeCasa} onChange={e => setNomeCasa(e.target.value)} required maxLength={120} placeholder="Ex.: Minha casa" /></label><label>Descrição (opcional)<input value={descricaoCasa} onChange={e => setDescricaoCasa(e.target.value)} maxLength={2000} placeholder="Descrição da casa" /></label><button className="sb-full" disabled={carregando}>＋ Criar casa</button></form>
    </section>
    {casaId && <>
      <section className="sb-card"><div className="sb-card-title"><h3>Dispositivos</h3><span>{dispositivos.length} registado(s)</span></div>
        <div className="sb-device-grid">{dispositivos.map(d => { const ligado = Boolean(d.estado_conhecido?.ligado); return <article className={`sb-device ${ligado ? "ligado" : ""}`} key={d.id}>
          <div className="sb-device-icon">{({ light: "☼", switch: "◉", fan: "❄", climate: "❄", camera: "◉", media_player: "♫" })[d.tipo] || "⌘"}</div>
          <span className={ligado ? "sb-device-state on" : "sb-device-state"}>{ligado ? "Ligado" : "Desligado"}</span><h3>{d.nome}</h3><p>{d.tipo} · {d.integracao === "home_assistant" ? "Home Assistant" : "Estado interno"}</p>
          <button type="button" disabled={carregando || !d.ativo} onClick={() => comandar(d)}>{ligado ? "Desligar" : "Ligar"}</button>
          {d.integracao !== "home_assistant" && <small>Atualiza apenas o estado registado; não envia comando físico.</small>}
        </article>; })}{!dispositivos.length && <div className="sb-empty sb-empty-wide">Ainda não há dispositivos nesta casa.</div>}</div>
      </section>
      <section className="sb-card"><h3>Adicionar dispositivo</h3><form className="sb-business-form" onSubmit={adicionarDispositivo}>
        <label>Nome do dispositivo<input value={nome} onChange={e => setNome(e.target.value)} required maxLength={120} placeholder="Ex.: Luz da sala" /></label>
        <label>Tipo<select value={tipo} onChange={e => setTipo(e.target.value)}><option value="light">Luz</option><option value="switch">Interruptor</option><option value="fan">Ventoinha</option><option value="climate">Climatização</option><option value="camera">Câmara</option><option value="media_player">Multimédia</option><option value="other">Outro</option></select></label>
        <label>Marca / fabricante<input value={marca} onChange={e => setMarca(e.target.value)} maxLength={100} /></label>
        <label>Tipo de integração<select value={integracao} onChange={e => setIntegracao(e.target.value)}><option value="manual">Registo interno (sem controlo físico)</option><option value="home_assistant">Home Assistant (dispositivo real)</option></select></label>
        {integracao === "home_assistant" && <label className="sb-full">Entidade Home Assistant<input value={entidade} onChange={e => setEntidade(e.target.value)} required placeholder="Ex.: light.luz_sala" /><small>O servidor também precisa de HOME_ASSISTANT_URL e HOME_ASSISTANT_TOKEN no .env.</small></label>}
        <button className="sb-full" disabled={carregando}>Guardar dispositivo</button>
      </form></section>
    </>}
    <p className="sb-disclaimer">Os registos ficam na base de dados. O controlo físico só funciona quando o Home Assistant está configurado e a entidade corresponde a um dispositivo compatível. Os dispositivos com integração interna apenas guardam o estado lógico.</p>
  </div>;
}
