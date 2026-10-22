import { useCallback, useEffect, useMemo, useState } from "react";
import "./modulos-novos.css";

const API = import.meta.env.VITE_API_URL || (
  import.meta.env.DEV
    ? "http://127.0.0.1:8000"
    : window.location.origin
);
const TITULOS = {
  amigos: ["Os teus amigos", "Encontra pessoas e gere as tuas amizades."],
  pedidos: ["Pedidos de amizade", "Aceita, recusa e acompanha pedidos reais."],
  videos: ["Vídeos", "Publica vídeos para a comunidade SMART BOOK."],
  mensagens: ["Mensagens", "Conversa com os teus amigos."],
  notificacoes: ["Notificações", "Acompanha as novidades da tua conta."],
};

function tokenAtual() { return sessionStorage.getItem("smartbook-token") || ""; }
async function api(path, options = {}) {
  const token = tokenAtual();
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  const response = await fetch(`${API}${path}`, { ...options, headers });
  let data = {};
  const raw = await response.text();
  try { data = raw ? JSON.parse(raw) : {}; } catch { data = { detail: raw || "Resposta inválida do servidor." }; }
  if (!response.ok) {
    if (response.status === 401) throw new Error("A sessão expirou. Sai da conta e inicia sessão novamente.");
    throw new Error(data.detail || data.mensagem || `Erro ${response.status} ao comunicar com o servidor.`);
  }
  return data;
}
function dataCurta(value) {
  if (!value) return "";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleString("pt-AO", { dateStyle: "short", timeStyle: "short" });
}
function Pessoa({ pessoa, children }) {
  const nome = pessoa?.nome_completo || pessoa?.username || "Utilizador";
  return <div className="sb-person"><div className="sb-avatar">{nome.slice(0, 1).toUpperCase()}</div><div className="sb-person-info"><strong>{nome}</strong><small>@{pessoa?.username || "utilizador"}</small></div>{children}</div>;
}

export default function ModulosSociais({ pagina, utilizador }) {
  const [termo, setTermo] = useState("");
  const [estado, setEstado] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [resultados, setResultados] = useState([]);
  const [amigos, setAmigos] = useState([]);
  const [recebidos, setRecebidos] = useState([]);
  const [enviados, setEnviados] = useState([]);
  const [abaPedidos, setAbaPedidos] = useState("recebidos");
  const [videos, setVideos] = useState([]);
  const [ficheiroVideo, setFicheiroVideo] = useState(null);
  const [videoTitulo, setVideoTitulo] = useState("");
  const [videoDescricao, setVideoDescricao] = useState("");
  const [conversas, setConversas] = useState([]);
  const [destinatarioId, setDestinatarioId] = useState("");
  const [mensagens, setMensagens] = useState([]);
  const [textoMensagem, setTextoMensagem] = useState("");
  const [notificacoes, setNotificacoes] = useState([]);
  const [naoLidas, setNaoLidas] = useState(0);

  const titulo = TITULOS[pagina] || ["SMART BOOK", ""];
  const amigosPorId = useMemo(() => new Map(amigos.map(a => [String(a.id), a])), [amigos]);
  const selecionado = amigosPorId.get(String(destinatarioId)) || conversas.find(c => String(c.utilizador?.id) === String(destinatarioId))?.utilizador;

  const executar = useCallback(async (acao) => {
    setCarregando(true); setErro("");
    try { await acao(); }
    catch (e) { setErro(e.message || "Não foi possível concluir a operação."); }
    finally { setCarregando(false); }
  }, []);

  const carregarAmigos = useCallback(() => executar(async () => {
    const d = await api("/api/amizades"); setAmigos(d.amigos || []);
  }), [executar]);
  const carregarPedidos = useCallback(() => executar(async () => {
    const [r, e] = await Promise.all([api("/api/amizades/pedidos/recebidos"), api("/api/amizades/pedidos/enviados")]);
    setRecebidos(r.pedidos || []); setEnviados(e.pedidos || []);
  }), [executar]);
  const carregarConversas = useCallback(() => executar(async () => {
    const d = await api("/api/mensagens"); setConversas(d.conversas || []);
    if (!destinatarioId && d.conversas?.length) setDestinatarioId(String(d.conversas[0].utilizador.id));
  }), [destinatarioId, executar]);
  const carregarVideos = useCallback(() => executar(async () => {
    const d = await api("/api/videos"); setVideos(d.videos || []);
  }), [executar]);
  const carregarNotificacoes = useCallback(() => executar(async () => {
    const d = await api("/api/notificacoes"); setNotificacoes(d.notificacoes || []); setNaoLidas(d.nao_lidas || 0);
  }), [executar]);

  useEffect(() => {
    setEstado(""); setErro("");
    if (!tokenAtual()) { setErro("Inicia sessão para utilizar esta área."); return; }
    if (pagina === "amigos") carregarAmigos();
    if (pagina === "pedidos") carregarPedidos();
    if (pagina === "mensagens") { carregarAmigos(); carregarConversas(); }
    if (pagina === "videos") carregarVideos();
    if (pagina === "notificacoes") carregarNotificacoes();
  }, [pagina, carregarAmigos, carregarPedidos, carregarConversas, carregarVideos, carregarNotificacoes]);

  useEffect(() => {
    if (pagina !== "mensagens" || !destinatarioId) { setMensagens([]); return; }
    let cancelado = false;
    api(`/api/mensagens/${encodeURIComponent(destinatarioId)}`).then(d => { if (!cancelado) setMensagens(d.mensagens || []); }).catch(e => { if (!cancelado) setErro(e.message); });
    return () => { cancelado = true; };
  }, [pagina, destinatarioId]);

  async function pesquisarPessoas(e) {
    e?.preventDefault();
    await executar(async () => {
      const d = await api(`/api/amizades/utilizadores?busca=${encodeURIComponent(termo.trim())}`);
      setResultados(d.utilizadores || []);
      if (!(d.utilizadores || []).length) setEstado("Não foram encontrados utilizadores.");
    });
  }
  async function enviarPedido(pessoa) {
    await executar(async () => {
      const d = await api(`/api/amizades/pedidos/${pessoa.id}`, { method: "POST" });
      setEstado(d.mensagem || "Pedido de amizade enviado.");
      setResultados(lista => lista.map(p => p.id === pessoa.id ? { ...p, estado_amizade: "pedido_enviado" } : p));
    });
  }
  async function responderPedido(pedido, decisao) {
    await executar(async () => {
      const d = await api(`/api/amizades/pedidos/${pedido.id}`, { method: "PATCH", body: JSON.stringify({ estado: decisao }) });
      setEstado(d.mensagem || "Pedido atualizado.");
      await Promise.all([carregarPedidos(), decisao === "aceite" ? carregarAmigos() : Promise.resolve()]);
    });
  }
  async function publicarVideo(e) {
    e.preventDefault();
    if (!ficheiroVideo) { setErro("Escolhe um ficheiro de vídeo."); return; }
    await executar(async () => {
      const form = new FormData(); form.append("titulo", videoTitulo.trim()); form.append("descricao", videoDescricao.trim()); form.append("ficheiro", ficheiroVideo);
      const d = await api("/api/videos", { method: "POST", body: form });
      setEstado(d.mensagem || "Vídeo publicado."); setVideoTitulo(""); setVideoDescricao(""); setFicheiroVideo(null);
      const input = document.getElementById("sb-video-file"); if (input) input.value = "";
      await carregarVideos();
    });
  }
  async function enviarMensagem(e) {
    e.preventDefault();
    if (!destinatarioId) { setErro("Escolhe um amigo para iniciar a conversa."); return; }
    await executar(async () => {
      const d = await api(`/api/mensagens/${encodeURIComponent(destinatarioId)}`, { method: "POST", body: JSON.stringify({ conteudo: textoMensagem.trim() }) });
      setTextoMensagem(""); setEstado(d.mensagem || "Mensagem enviada.");
      const hist = await api(`/api/mensagens/${encodeURIComponent(destinatarioId)}`); setMensagens(hist.mensagens || []);
      const conv = await api("/api/mensagens"); setConversas(conv.conversas || []);
    });
  }
  async function marcarNotificacao(n) {
    if (n.lida) return;
    await executar(async () => { await api(`/api/notificacoes/${n.id}/ler`, { method: "PATCH" }); setNotificacoes(lista => lista.map(x => x.id === n.id ? { ...x, lida: true } : x)); setNaoLidas(v => Math.max(0, v - 1)); });
  }
  async function marcarTodas() {
    await executar(async () => { await api("/api/notificacoes/ler-todas", { method: "PATCH" }); setNotificacoes(lista => lista.map(n => ({ ...n, lida: true }))); setNaoLidas(0); setEstado("Todas as notificações foram marcadas como lidas."); });
  }
  async function apagarVideo(video) {
    if (!window.confirm(`Apagar o vídeo “${video.titulo}”?`)) return;
    await executar(async () => { await api(`/api/videos/${video.id}`, { method: "DELETE" }); setVideos(lista => lista.filter(v => v.id !== video.id)); setEstado("Vídeo apagado."); });
  }

  const urlVideo = (url) => url?.startsWith("http") ? url : `${API}${url || ""}`;
  return <div className="sb-modulo">
    <header className="sb-modulo-hero"><div className="sb-modulo-icon">{({ amigos:"♧", pedidos:"↔", videos:"▷", mensagens:"✉", notificacoes:"♧" })[pagina] || "◆"}</div><div><span className="sb-eyebrow">SMART BOOK · COMUNIDADE</span><h2>{titulo[0]}</h2><p>{titulo[1]}</p></div></header>
    {erro && <div className="sb-alerta" role="alert">{erro}</div>}{estado && <div className="sb-alerta" role="status">{estado}</div>}
    {pagina === "amigos" && <>
      <section className="sb-card"><h3>Encontrar pessoas</h3><form className="sb-search" onSubmit={pesquisarPessoas}><input value={termo} onChange={e=>setTermo(e.target.value)} placeholder="Nome ou nome de utilizador"/><button disabled={carregando}>{carregando ? "A pesquisar…" : "Pesquisar"}</button></form></section>
      <section className="sb-card"><div className="sb-card-title"><h3>Os teus amigos ({amigos.length})</h3><button className="sb-secondary" onClick={carregarAmigos} disabled={carregando}>Atualizar</button></div>{amigos.map(p=><Pessoa key={p.id} pessoa={p}><span className="sb-status">Amigo</span></Pessoa>)}{!amigos.length && <div className="sb-empty">Ainda não tens amigos. Pesquisa utilizadores acima.</div>}</section>
      {resultados.length > 0 && <section className="sb-card"><h3>Resultados da pesquisa</h3>{resultados.map(p=><Pessoa key={p.id} pessoa={p}>{p.estado_amizade === "amigos" ? <span className="sb-status">Já são amigos</span> : p.estado_amizade === "pedido_enviado" ? <span className="sb-status">Pedido enviado</span> : p.estado_amizade === "pedido_recebido" ? <button onClick={()=>setEstado("Abre Pedidos de amizade para responder ao pedido recebido.")}>Pedido recebido</button> : <button onClick={()=>enviarPedido(p)} disabled={carregando}>Adicionar amigo</button>}</Pessoa>)}</section>}
    </>}
    {pagina === "pedidos" && <><div className="sb-tabs"><button className={abaPedidos === "recebidos" ? "ativo" : ""} onClick={()=>setAbaPedidos("recebidos")}>Recebidos ({recebidos.length})</button><button className={abaPedidos === "enviados" ? "ativo" : ""} onClick={()=>setAbaPedidos("enviados")}>Enviados ({enviados.length})</button></div><section className="sb-card"><div className="sb-card-title"><h3>{abaPedidos === "recebidos" ? "Pedidos recebidos" : "Pedidos enviados"}</h3><button className="sb-secondary" onClick={carregarPedidos}>Atualizar</button></div>{(abaPedidos === "recebidos" ? recebidos : enviados).map(p=>{const pessoa = abaPedidos === "recebidos" ? p.remetente : p.destinatario; return <Pessoa key={p.id} pessoa={pessoa}>{abaPedidos === "recebidos" ? <><button onClick={()=>responderPedido(p,"aceite")} disabled={carregando}>Aceitar</button><button className="sb-secondary" onClick={()=>responderPedido(p,"recusado")} disabled={carregando}>Recusar</button></> : <span className="sb-status">Pendente</span>}</Pessoa>;})}{!(abaPedidos === "recebidos" ? recebidos : enviados).length && <div className="sb-empty">Não existem pedidos {abaPedidos}.</div>}</section></>}
    {pagina === "videos" && <><section className="sb-card"><h3>Publicar vídeo</h3><form className="sb-stack" onSubmit={publicarVideo}><label>Título<input value={videoTitulo} onChange={e=>setVideoTitulo(e.target.value)} required maxLength={200} placeholder="Título do vídeo"/></label><label>Descrição<textarea value={videoDescricao} onChange={e=>setVideoDescricao(e.target.value)} maxLength={5000} rows={3} placeholder="Descrição (opcional)"/></label><label>Ficheiro de vídeo (MP4, WebM, MOV ou MKV; máximo 100 MB)<input id="sb-video-file" type="file" accept="video/mp4,video/webm,video/quicktime,video/x-matroska,.mp4,.webm,.mov,.mkv" onChange={e=>setFicheiroVideo(e.target.files?.[0] || null)} required/></label><button disabled={carregando}>{carregando ? "A publicar…" : "Publicar vídeo"}</button></form></section><section className="sb-video-grid">{videos.map(v=><article className="sb-card sb-video" key={v.id}><video controls preload="metadata" src={urlVideo(v.url_video)} style={{width:"100%",borderRadius:12,maxHeight:420}}/><h3>{v.titulo}</h3>{v.descricao && <p>{v.descricao}</p>}<p>Publicado por {v.autor?.nome_completo || v.autor?.username || "Utilizador"} · {dataCurta(v.data_criacao)}</p>{v.pode_apagar && <button className="sb-secondary" onClick={()=>apagarVideo(v)} disabled={carregando}>Apagar vídeo</button>}</article>)}{!videos.length && <div className="sb-empty">Ainda não há vídeos publicados.</div>}</section><button className="sb-secondary" onClick={carregarVideos} disabled={carregando}>Atualizar vídeos</button></>}
    {pagina === "mensagens" && <><section className="sb-card"><div className="sb-card-title"><h3>Conversas</h3><button className="sb-secondary" onClick={()=>{carregarAmigos();carregarConversas();}} disabled={carregando}>Atualizar</button></div><label>Escolher amigo<select value={destinatarioId} onChange={e=>setDestinatarioId(e.target.value)}><option value="">Seleciona um amigo</option>{amigos.map(a=><option key={a.id} value={a.id}>{a.nome_completo} (@{a.username})</option>)}{conversas.filter(c=>!amigosPorId.has(String(c.utilizador?.id))).map(c=><option key={c.utilizador.id} value={c.utilizador.id}>{c.utilizador.nome_completo} (@{c.utilizador.username})</option>)}</select></label>{conversas.length > 0 && <div className="sb-conversation-list">{conversas.map(c=><button className="sb-secondary" key={c.utilizador.id} onClick={()=>setDestinatarioId(String(c.utilizador.id))}>{c.utilizador.nome_completo} · {c.ultima_mensagem?.conteudo || "Conversa"}{c.mensagens_nao_lidas ? ` (${c.mensagens_nao_lidas} novas)` : ""}</button>)}</div>}</section>{destinatarioId && <section className="sb-card"><h3>Conversa com {selecionado?.nome_completo || selecionado?.username || "amigo"}</h3><div className="sb-chat-history">{mensagens.map(m=><article className="sb-message" key={m.id}><div><strong>{Number(m.remetente_id) === Number(utilizador?.id) ? "Tu" : (m.remetente?.nome_completo || m.remetente?.username || selecionado?.nome_completo || "Amigo")}</strong><small>{dataCurta(m.data_criacao)}</small></div><p>{m.conteudo}</p></article>)}{!mensagens.length && <div className="sb-empty">Ainda não há mensagens nesta conversa.</div>}</div><form className="sb-stack" onSubmit={enviarMensagem}><label>Mensagem<textarea value={textoMensagem} onChange={e=>setTextoMensagem(e.target.value)} rows={3} maxLength={5000} required placeholder="Escreve a tua mensagem…"/></label><button disabled={carregando}>{carregando ? "A enviar…" : "Enviar mensagem"}</button></form></section>}{!amigos.length && <div className="sb-empty">Só podes enviar mensagens privadas a utilizadores que aceitaram o teu pedido de amizade.</div>}</>}
    {pagina === "notificacoes" && <section className="sb-card"><div className="sb-card-title"><div><h3>Centro de notificações</h3><p>{naoLidas} por ler</p></div><div><button className="sb-secondary" onClick={marcarTodas} disabled={carregando || naoLidas===0}>Marcar todas como lidas</button> <button className="sb-secondary" onClick={carregarNotificacoes} disabled={carregando}>Atualizar</button></div></div>{notificacoes.map(n=><article className={`sb-message ${n.lida ? "" : "sb-notification-unread"}`} key={n.id}><div><strong>{n.titulo || n.tipo || "Notificação"}</strong><small>{dataCurta(n.data_criacao)}</small></div><p>{n.mensagem}</p>{n.autor && <small>De: {n.autor.nome_completo || `@${n.autor.username}`}</small>}{!n.lida && <button className="sb-secondary" onClick={()=>marcarNotificacao(n)} disabled={carregando}>Marcar como lida</button>}</article>)}{!notificacoes.length && <div className="sb-empty">Não tens notificações.</div>}</section>}
    <p className="sb-disclaimer">Estas áreas utilizam agora as rotas existentes do backend SMART BOOK. O envio de mensagens só é permitido entre amigos aceites; os vídeos são carregados para o servidor e as notificações são guardadas na base de dados.</p>
  </div>;
}
