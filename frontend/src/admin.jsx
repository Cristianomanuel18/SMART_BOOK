import { useCallback, useEffect, useState } from "react";
import "./admin.css";

const SERVIDOR = import.meta.env.VITE_API_URL || (
  import.meta.env.DEV
    ? "http://127.0.0.1:8000"
    : window.location.origin
);

const API_URL = `${SERVIDOR}/api/adm`;

export default function Admin({ onSair }) {
  const [aba, setAba] = useState("dashboard");
  const [dados, setDados] = useState(null);
  const [utilizadores, setUtilizadores] = useState([]);
  const [pesquisa, setPesquisa] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  const token = sessionStorage.getItem("smartbook-admin-token");

  const pedido = useCallback(async (rota, opcoes = {}) => {
    const resposta = await fetch(`${API_URL}${rota}`, {
      ...opcoes,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        ...(opcoes.headers || {}),
      },
    });

    const resultado = await resposta.json().catch(() => ({}));

    if (resposta.status === 401 || resposta.status === 403) {
      sessionStorage.removeItem("smartbook-admin-token");
      window.location.href = "/adm";
      throw new Error("Sessão administrativa inválida. Inicia sessão novamente.");
    }

    if (!resposta.ok) {
      throw new Error(resultado.detail || "Não foi possível concluir a operação.");
    }

    return resultado;
  }, [token]);

  const carregarDashboard = useCallback(async () => {
    setCarregando(true);
    setErro("");

    try {
      const resultado = await pedido("/dashboard");
      setDados(resultado);
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  }, [pedido]);

  const carregarUtilizadores = useCallback(async () => {
    setCarregando(true);
    setErro("");

    try {
      const resultado = await pedido(
        `/utilizadores?pesquisa=${encodeURIComponent(pesquisa)}&limite=100`
      );

      setUtilizadores(
        Array.isArray(resultado)
          ? resultado
          : resultado.utilizadores || []
      );
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  }, [pedido, pesquisa]);

  useEffect(() => {
    if (aba === "dashboard") carregarDashboard();
    if (aba === "utilizadores") carregarUtilizadores();
  }, [aba, carregarDashboard, carregarUtilizadores]);

  async function alterarEstado(utilizador) {
    const acao = utilizador.ativo ? "suspender" : "ativar";

    if (!window.confirm(`Queres ${acao} a conta de ${utilizador.nome_completo || utilizador.username}?`)) {
      return;
    }

    setErro("");
    setSucesso("");

    try {
      await pedido(`/utilizadores/${utilizador.id}/estado`, {
        method: "PATCH",
        body: JSON.stringify({ ativo: !utilizador.ativo }),
      });

      setSucesso(`Conta ${utilizador.ativo ? "suspensa" : "ativada"} com sucesso.`);
      await carregarUtilizadores();
      await carregarDashboard();
    } catch (e) {
      setErro(e.message);
    }
  }

  function sair() {
    sessionStorage.removeItem("smartbook-admin-token");
    if (onSair) onSair();
    window.location.href = "/adm";
  }

  const menu = [
    { id: "dashboard", icon: "▦", texto: "Visão geral" },
    { id: "utilizadores", icon: "♙", texto: "Utilizadores" },
    { id: "relatorios", icon: "▤", texto: "Relatórios" },
    { id: "seguranca", icon: "⬡", texto: "Segurança" },
    { id: "definicoes", icon: "⚙", texto: "Definições" },
  ];

  return (
    <div className="adm-layout">
      <aside className="adm-sidebar">
        <div className="adm-brand">
          <div className="adm-brand-icon">S</div>
          <div>
            <strong>SMART BOOK</strong>
            <small>ADMINISTRAÇÃO</small>
          </div>
        </div>

        <div className="adm-sidebar-label">PAINEL DE CONTROLO</div>

        <nav className="adm-menu">
          {menu.map((item) => (
            <button
              key={item.id}
              className={aba === item.id ? "adm-menu-item ativo" : "adm-menu-item"}
              onClick={() => {
                setAba(item.id);
                setErro("");
                setSucesso("");
              }}
            >
              <span>{item.icon}</span>
              {item.texto}
            </button>
          ))}
        </nav>

        <div className="adm-sidebar-bottom">
          <div className="adm-admin-identidade">
            <div className="adm-avatar">A</div>
            <div>
              <strong>Administrador</strong>
              <small>Controlo da plataforma</small>
            </div>
          </div>

          <button className="adm-sair" onClick={sair}>
            ↪ Terminar sessão
          </button>
        </div>
      </aside>

      <main className="adm-main">
        <header className="adm-topbar">
          <div>
            <span className="adm-breadcrumb">SMART BOOK / ADMIN</span>
            <h1>
              {menu.find((item) => item.id === aba)?.texto || "Visão geral"}
            </h1>
          </div>

          <div className="adm-topbar-right">
            <span className="adm-status"><i /> Sistema administrativo</span>
            <button className="adm-atualizar" onClick={() => {
              if (aba === "dashboard") carregarDashboard();
              if (aba === "utilizadores") carregarUtilizadores();
            }}>
              ↻ Atualizar
            </button>
          </div>
        </header>

        <section className="adm-content">
          {erro && <div className="adm-alerta erro">{erro}</div>}
          {sucesso && <div className="adm-alerta sucesso">{sucesso}</div>}

          {aba === "dashboard" && (
            <>
              <div className="adm-boas-vindas">
                <div>
                  <h2>Centro de controlo</h2>
                  <p>Acompanha a atividade e administra os utilizadores do SMART BOOK.</p>
                </div>
                <div className="adm-data">
                  <span>ESTADO DA PLATAFORMA</span>
                  <strong><i /> Administração ativa</strong>
                </div>
              </div>

              <div className="adm-stats">
                <Stat
                  icon="♙"
                  titulo="Utilizadores registados"
                  valor={dados?.total_utilizadores}
                  descricao="Total de contas na plataforma"
                />
                <Stat
                  icon="✓"
                  titulo="Contas ativas"
                  valor={dados?.utilizadores_ativos}
                  descricao="Contas atualmente ativas"
                />
                <Stat
                  icon="⊘"
                  titulo="Contas suspensas"
                  valor={dados?.utilizadores_suspensos}
                  descricao="Contas desativadas"
                />
                <Stat
                  icon="♜"
                  titulo="Administradores"
                  valor={dados?.administradores}
                  descricao="Contas com privilégios administrativos"
                />
              </div>

              <div className="adm-card">
                <div className="adm-card-header">
                  <div>
                    <h3>Gestão de utilizadores</h3>
                    <p>Consulta e administra as contas registadas.</p>
                  </div>
                  <button className="adm-botao-principal" onClick={() => setAba("utilizadores")}>
                    Gerir utilizadores →
                  </button>
                </div>

                {carregando ? (
                  <p className="adm-vazio">A carregar estatísticas...</p>
                ) : (
                  <div className="adm-resumo">
                    <div><span>Total de contas</span><strong>{dados?.total_utilizadores ?? 0}</strong></div>
                    <div><span>Contas ativas</span><strong>{dados?.utilizadores_ativos ?? 0}</strong></div>
                    <div><span>Contas suspensas</span><strong>{dados?.utilizadores_suspensos ?? 0}</strong></div>
                  </div>
                )}
              </div>
            </>
          )}

          {aba === "utilizadores" && (
            <div className="adm-card">
              <div className="adm-card-header">
                <div>
                  <h2>Utilizadores registados</h2>
                  <p>Pesquisa contas, consulta o estado e aplica suspensões.</p>
                </div>
                <span className="adm-contador">{utilizadores.length} apresentados</span>
              </div>

              <div className="adm-pesquisa">
                <span>⌕</span>
                <input
                  value={pesquisa}
                  onChange={(e) => setPesquisa(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") carregarUtilizadores();
                  }}
                  placeholder="Pesquisar por nome, e-mail ou username..."
                />
                <button onClick={carregarUtilizadores}>Pesquisar</button>
              </div>

              <div className="adm-tabela-wrap">
                <table className="adm-tabela">
                  <thead>
                    <tr>
                      <th>UTILIZADOR</th>
                      <th>E-MAIL</th>
                      <th>REGISTO</th>
                      <th>ESTADO</th>
                      <th>TIPO</th>
                      <th>AÇÕES</th>
                    </tr>
                  </thead>
                  <tbody>
                    {utilizadores.map((u) => (
                      <tr key={u.id}>
                        <td>
                          <div className="adm-user-cell">
                            <div className="adm-avatar pequeno">
                              {(u.nome_completo || u.username || "?").charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <strong>{u.nome_completo || u.username}</strong>
                              <small>@{u.username}</small>
                            </div>
                          </div>
                        </td>
                        <td>{u.email}</td>
                        <td>{u.data_registo ? new Date(u.data_registo).toLocaleDateString("pt-PT") : "—"}</td>
                        <td>
                          <span className={u.ativo ? "adm-badge ativo" : "adm-badge suspenso"}>
                            {u.ativo ? "Ativa" : "Suspensa"}
                          </span>
                        </td>
                        <td>{u.administrador ? "Administrador" : "Utilizador"}</td>
                        <td>
                          {u.administrador ? (
                            <span className="adm-protegido">Protegido</span>
                          ) : (
                            <button
                              className={u.ativo ? "adm-acao suspender" : "adm-acao ativar"}
                              onClick={() => alterarEstado(u)}
                            >
                              {u.ativo ? "Suspender" : "Reativar"}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {!carregando && utilizadores.length === 0 && (
                  <p className="adm-vazio">Nenhum utilizador encontrado.</p>
                )}

                {carregando && <p className="adm-vazio">A carregar utilizadores...</p>}
              </div>
            </div>
          )}

          {aba === "relatorios" && (
            <div className="adm-card">
              <h2>Relatórios da plataforma</h2>
              <p>Resumo atual da base de dados.</p>
              <div className="adm-resumo">
                <div><span>Utilizadores registados</span><strong>{dados?.total_utilizadores ?? "—"}</strong></div>
                <div><span>Contas ativas</span><strong>{dados?.utilizadores_ativos ?? "—"}</strong></div>
                <div><span>Contas suspensas</span><strong>{dados?.utilizadores_suspensos ?? "—"}</strong></div>
              </div>
              <button className="adm-botao-principal" onClick={carregarDashboard}>Atualizar relatório</button>
            </div>
          )}

          {aba === "seguranca" && (
            <div className="adm-card">
              <h2>Segurança da plataforma</h2>
              <p>Estado da sessão administrativa e das contas registadas.</p>
              <div className="adm-seguranca-linha">
                <span>Autenticação administrativa</span>
                <span className="adm-badge ativo">Protegida</span>
              </div>
              <div className="adm-seguranca-linha">
                <span>Gestão de contas suspensas</span>
                <span className="adm-badge ativo">Disponível</span>
              </div>
              <div className="adm-seguranca-linha">
                <span>Proteção de contas administrativas</span>
                <span className="adm-badge ativo">Ativa</span>
              </div>
              <p className="adm-nota">Esta secção apresenta apenas controlos já implementados. Deteção de abusos, denúncias e auditoria detalhada exigem funcionalidades adicionais no backend.</p>
            </div>
          )}

          {aba === "definicoes" && (
            <div className="adm-card">
              <h2>Definições administrativas</h2>
              <p>Configuração e informação da área administrativa.</p>
              <div className="adm-seguranca-linha">
                <span>Conta administrativa</span>
                <strong>adm@smartbook.ao</strong>
              </div>
              <div className="adm-seguranca-linha">
                <span>Sessão</span>
                <strong>Token administrativo separado</strong>
              </div>
              <p className="adm-nota">As credenciais devem ser alteradas no servidor e no ficheiro .env. Não guardes palavras-passe em texto simples.</p>
            </div>
          )}
        </section>

        <footer className="adm-footer">
          SMART BOOK · Centro de Administração · Acesso restrito
        </footer>
      </main>
    </div>
  );
}

function Stat({ icon, titulo, valor, descricao }) {
  return (
    <div className="adm-stat-card">
      <div className="adm-stat-icon">{icon}</div>
      <span>{titulo}</span>
      <strong>{valor ?? "—"}</strong>
      <small>{descricao}</small>
    </div>
  );
}