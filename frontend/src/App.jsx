import { useCallback, useEffect, useState } from "react";
import "./index.css";
import "./modulos-novos.css";
import Admin from "./admin";
import AdminLogin from "./AdminLogin";
import ModulosSociais from "./ModulosSociais";
import NegocioOportunidade from "./NegocioOportunidade";
import CasaInteligente from "./CasaInteligente";


  



const API_URL = (
    import.meta.env.VITE_API_URL ||
    (
        import.meta.env.DEV
            ? "http://127.0.0.1:8000"
            : window.location.origin
    )
).replace(/\/+$/, "");


const MENU = [
    { id: "inicio", icon: "⌂", label: "Início" },
    { id: "perfil", icon: "♙", label: "Meu perfil" },
    { id: "amigos", icon: "♧", label: "Amigos" },
    { id: "pedidos", icon: "♧", label: "Pedidos de amizade" },
    { id: "videos", icon: "▷", label: "Vídeos" },
    { id: "mensagens", icon: "✉", label: "Mensagens" },
    { id: "notificacoes", icon: "♧", label: "Notificações" },
    { id: "caren", icon: "✳", label: "Caren IA" },
    { id: "definicoes", icon: "⚙", label: "Definições" },
    { id: "negocio", icon: "▤", label: "Negócio com Oportunidade" },
    { id: "casa", icon: "⌂", label: "Casa inteligente" },
];

async function lerResposta(resposta) {
    const texto = await resposta.text();

    let dados = {};

    try {
        dados = texto ? JSON.parse(texto) : {};
    } catch {
        dados = { detail: texto };
    }

    if (!resposta.ok) {
        throw new Error(
            dados.detail ||
            dados.mensagem ||
            `Erro do servidor (${resposta.status}).`
        );
    }

    return dados;
}

function obterToken() {
    return sessionStorage.getItem("smartbook-token");
}

function cabecalhosAutenticacao() {
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${obterToken()}`,
    };
}

function iniciais(nome = "SMART BOOK") {
    return nome
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((parte) => parte[0] || "")
        .join("")
        .toUpperCase();
}

function Avatar({ nome, foto, tamanho = "" }) {
    if (foto) {
        return (
            <img
                className={`avatar ${tamanho}`}
                src={foto}
                alt={`Fotografia de ${nome || "utilizador"}`}
            />
        );
    }

    return (
        <div className={`avatar avatar-iniciais ${tamanho}`}>
            {iniciais(nome)}
        </div>
    );
}

function Marca() {
    return (
        <div className="marca">
            <div className="marca-simbolo">S</div>

            <div className="marca-nome">
                SMART<span>BOOK</span>
            </div>
        </div>
    );
}

function BotaoIcone({ children, onClick, titulo }) {
    return (
        <button
            type="button"
            className="botao-icone"
            onClick={onClick}
            title={titulo}
            aria-label={titulo}
        >
            {children}
        </button>
    );
}

export default function App() {
    const [utilizador, setUtilizador] = useState(null);
    const [pagina, setPagina] = useState("login");
    const [carregando, setCarregando] = useState(false);
    const [aValidarSessao, setAValidarSessao] = useState(true);
    const [admAutorizado, setAdmAutorizado] = useState(false);

    const [backendOnline, setBackendOnline] = useState(false);
    const [tema, setTema] = useState(
        localStorage.getItem("smartbook-tema") || "claro"
    );

    const [mensagem, setMensagem] = useState("");
    const [tipoMensagem, setTipoMensagem] = useState("info");
    const [mostrarSenha, setMostrarSenha] = useState(false);

    const [paginaAtual, setPaginaAtual] = useState("inicio");
    const [menuAberto, setMenuAberto] = useState(false);

    const [publicacoes, setPublicacoes] = useState([]);
    const [interacoes, setInteracoes] = useState(() => {
        try { return JSON.parse(localStorage.getItem("smartbook-interacoes") || "{}"); } catch { return {}; }
    });
    const [rascunhosComentario, setRascunhosComentario] = useState({});
    const [carregandoPublicacoes, setCarregandoPublicacoes] =
        useState(false);

    const [novoConteudo, setNovoConteudo] = useState("");
    const [publicando, setPublicando] = useState(false);

    const [perfil, setPerfil] = useState(null);
    const [perfilFormulario, setPerfilFormulario] = useState({
        biografia: "",
        localizacao: "",
        foto_url: "",
        capa_url: "",
    });

    const [aGuardarPerfil, setAGuardarPerfil] = useState(false);

    const [pesquisa, setPesquisa] = useState("");
    const [termoPesquisa, setTermoPesquisa] = useState("");

    const [notificacoes, setNotificacoes] = useState([]);

    const [carenPergunta, setCarenPergunta] = useState("");
    const [carenMensagens, setCarenMensagens] = useState([
        {
            autor: "caren",
            texto:
                "Olá! Sou a Caren, a assistente de IA do SMART BOOK. " +
                "Podemos conversar sobre ideias, tecnologia e muito mais.",
        },
    ]);

    const [aEnviarCaren, setAEnviarCaren] = useState(false);

    // =====================================================
    // TEMA
    // =====================================================

    useEffect(() => {
        document.documentElement.dataset.theme = tema;
        localStorage.setItem("smartbook-tema", tema);
    }, [tema]);

    useEffect(() => {
        localStorage.setItem("smartbook-interacoes", JSON.stringify(interacoes));
    }, [interacoes]);

    // O backend confirma se esta sessão tem acesso ao ADM.
    useEffect(() => {
        let ativo = true;
        async function verificarAcessoAdm() {
            if (!utilizador || !obterToken()) {
                if (ativo) setAdmAutorizado(false);
                return;
            }
            try {
                const resposta = await fetch(`${API_URL}/api/adm/estado`, {
                    headers: { Authorization: `Bearer ${obterToken()}` },
                });
                if (ativo) setAdmAutorizado(resposta.ok);
            } catch {
                if (ativo) setAdmAutorizado(false);
            }
        }
        verificarAcessoAdm();
        return () => { ativo = false; };
    }, [utilizador]);

    function alternarTema() {
        setTema((atual) =>
            atual === "claro" ? "escuro" : "claro"
        );
    }

    // =====================================================
    // ESTADO DO BACKEND
    // =====================================================

    useEffect(() => {
        let ativo = true;

        async function verificarBackend() {
            try {
                const resposta = await fetch(
                    `${API_URL}/api/health`
                );

                if (ativo) {
                    setBackendOnline(resposta.ok);
                }
            } catch {
                if (ativo) {
                    setBackendOnline(false);
                }
            }
        }

        verificarBackend();

        const intervalo = setInterval(
            verificarBackend,
            15000
        );

        return () => {
            ativo = false;
            clearInterval(intervalo);
        };
    }, []);

    // =====================================================
    // MENSAGENS DE ESTADO
    // =====================================================

    const mostrarMensagem = useCallback(
        (texto, tipo = "info") => {
            setMensagem(texto);
            setTipoMensagem(tipo);
        },
        []
    );

    // =====================================================
    // VALIDAR SESSÃO EXISTENTE
    // =====================================================

    useEffect(() => {
        let ativo = true;

        async function validarSessao() {
            const token = obterToken();

            if (!token) {
                if (ativo) {
                    setAValidarSessao(false);
                }

                return;
            }

            try {
                const resposta = await fetch(
                    `${API_URL}/api/auth/me`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );

                if (resposta.status === 401) {
                    sessionStorage.removeItem(
                        "smartbook-token"
                    );

                    sessionStorage.removeItem(
                        "smartbook-utilizador"
                    );

                    if (ativo) {
                        setUtilizador(null);
                    }

                    return;
                }

                const dados = await lerResposta(resposta);

                const conta =
                    dados.utilizador ||
                    dados.usuario ||
                    dados;

                if (ativo) {
                    setUtilizador(conta);
                }
            } catch (erro) {
                console.error(
                    "Não foi possível validar a sessão:",
                    erro
                );

                if (ativo) {
                    mostrarMensagem(
                        "Não foi possível confirmar a sessão. " +
                        "Verifica a ligação ao servidor.",
                        "erro"
                    );
                }
            } finally {
                if (ativo) {
                    setAValidarSessao(false);
                }
            }
        }

        validarSessao();

        return () => {
            ativo = false;
        };
    }, [mostrarMensagem]);

    // =====================================================
    // LOGIN E REGISTO
    // =====================================================

    async function submeterFormulario(evento) {
        evento.preventDefault();

        const formulario = evento.currentTarget;
        const dadosFormulario = new FormData(formulario);

        setCarregando(true);
        mostrarMensagem("");

        try {
            if (!backendOnline) {
                throw new Error(
                    "O servidor não está disponível neste momento."
                );
            }

            const estaNoRegisto = pagina === "registo";

            const corpo = estaNoRegisto
                ? {
                    nome_completo:
                        dadosFormulario.get("nome").trim(),

                    username:
                        dadosFormulario
                            .get("username")
                            .trim()
                            .toLowerCase(),

                    email:
                        dadosFormulario
                            .get("email")
                            .trim()
                            .toLowerCase(),

                    password:
                        dadosFormulario.get("password"),
                }
                : {
                    identificador:
                        dadosFormulario
                            .get("identificador")
                            .trim(),

                    password:
                        dadosFormulario.get("password"),
                };

            const resposta = await fetch(
                `${API_URL}/api/auth/${
                    estaNoRegisto ? "register" : "login"
                }`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(corpo),
                }
            );

            const dados = await lerResposta(resposta);

            if (estaNoRegisto) {
                mostrarMensagem(
                    "Conta criada com sucesso. Já podes iniciar sessão.",
                    "sucesso"
                );

                setPagina("login");
                formulario.reset();

                return;
            }

            if (!dados.access_token) {
                throw new Error(
                    "O servidor não devolveu um token de sessão."
                );
            }

            sessionStorage.setItem(
                "smartbook-token",
                dados.access_token
            );

            

              const conta = dados.utilizador ||
              dados.usuario || null;
              const emailConta = (conta?.email || "").toLowerCase().trim();

              if (emailConta === "adm@smartbook.ao")  {
                sessionStorage.setItem("smartbook-admin.token", dados.access_token);
                window.location.replace("/adm");
                return;

                 }
              


            if (!conta) {
                const respostaConta = await fetch(
                    `${API_URL}/api/auth/me`,
                    {
                        headers: {
                            Authorization:
                                `Bearer ${dados.access_token}`,
                        },
                    }
                );

                const dadosConta =
                    await lerResposta(respostaConta);

                setUtilizador(
                    dadosConta.utilizador || dadosConta
                );
            } else {
                setUtilizador(conta);
            }

            sessionStorage.setItem(
                "smartbook-utilizador",
                JSON.stringify(conta)
            );

            setPaginaAtual("inicio");
            mostrarMensagem("");
            formulario.reset();
        } catch (erro) {
            mostrarMensagem(
                erro.message ||
                "Não foi possível concluir a operação.",
                "erro"
            );
        } finally {
            setCarregando(false);
        }
    }

    function terminarSessao() {
        sessionStorage.removeItem("smartbook-token");
        sessionStorage.removeItem("smartbook-utilizador");

        setUtilizador(null);
        setPerfil(null);
        setPublicacoes([]);
        setPagina("login");
        setPaginaAtual("inicio");
        setMenuAberto(false);

        mostrarMensagem(
            "Sessão terminada com sucesso.",
            "sucesso"
        );
    }

    // =====================================================
    // CARREGAR PUBLICAÇÕES
    // =====================================================

    const carregarPublicacoes = useCallback(async () => {
        if (!utilizador || !obterToken()) {
            return;
        }

        setCarregandoPublicacoes(true);

        try {
            const resposta = await fetch(
                `${API_URL}/api/posts?limite=50`,
                {
                    headers: {
                        Authorization:
                            `Bearer ${obterToken()}`,
                    },
                }
            );

            const dados = await lerResposta(resposta);

            setPublicacoes(
                Array.isArray(dados)
                    ? dados
                    : dados.publicacoes || dados.items || []
            );
        } catch (erro) {
            mostrarMensagem(
                `Não foi possível carregar as publicações: ${erro.message}`,
                "erro"
            );
        } finally {
            setCarregandoPublicacoes(false);
        }
    }, [utilizador, mostrarMensagem]);

    // =====================================================
    // CARREGAR PERFIL
    // =====================================================

    const carregarPerfil = useCallback(async () => {
        if (!utilizador || !obterToken()) {
            return;
        }

        try {
            const resposta = await fetch(
                `${API_URL}/api/profile/me`,
                {
                    headers: cabecalhosAutenticacao(),
                }
            );

            const dados = await lerResposta(resposta);

            setPerfil(dados);

            setPerfilFormulario({
                biografia: dados.biografia || "",
                localizacao: dados.localizacao || "",
                foto_url: dados.foto_url || "",
                capa_url: dados.capa_url || "",
            });
        } catch (erro) {
            mostrarMensagem(
                `Não foi possível carregar o perfil: ${erro.message}`,
                "erro"
            );
        }
    }, [utilizador, mostrarMensagem]);

    useEffect(() => {
        if (!utilizador) {
            return;
        }

        carregarPublicacoes();
        carregarPerfil();
    }, [utilizador, carregarPublicacoes, carregarPerfil]);

    // =====================================================
    // CRIAR PUBLICAÇÃO
    // =====================================================

    async function criarPublicacao(evento) {
        evento.preventDefault();

        const conteudo = novoConteudo.trim();

        if (!conteudo) {
            mostrarMensagem(
                "Escreve alguma coisa antes de publicar.",
                "erro"
            );

            return;
        }

        setPublicando(true);

        try {
            const resposta = await fetch(
                `${API_URL}/api/posts`,
                {
                    method: "POST",
                    headers: cabecalhosAutenticacao(),
                    body: JSON.stringify({
                        conteudo,
                    }),
                }
            );

            await lerResposta(resposta);

            setNovoConteudo("");

            mostrarMensagem(
                "Publicação criada com sucesso.",
                "sucesso"
            );

            await carregarPublicacoes();
        } catch (erro) {
            mostrarMensagem(
                `Não foi possível publicar: ${erro.message}`,
                "erro"
            );
        } finally {
            setPublicando(false);
        }
    }

    // =====================================================
    // APAGAR PUBLICAÇÃO
    // =====================================================

    async function apagarPublicacao(id) {
        const confirmar = window.confirm(
            "Queres mesmo apagar esta publicação?"
        );

        if (!confirmar) {
            return;
        }

        try {
            const resposta = await fetch(
                `${API_URL}/api/posts/${id}`,
                {
                    method: "DELETE",
                    headers: cabecalhosAutenticacao(),
                }
            );

            await lerResposta(resposta);

            await carregarPublicacoes();

            mostrarMensagem(
                "Publicação removida.",
                "sucesso"
            );
        } catch (erro) {
            mostrarMensagem(
                `Não foi possível apagar a publicação: ${erro.message}`,
                "erro"
            );
        }
    }

    // =====================================================
    // ATUALIZAR PERFIL
    // =====================================================

    async function guardarPerfil(evento) {
        evento.preventDefault();

        setAGuardarPerfil(true);

        try {
            const resposta = await fetch(
                `${API_URL}/api/profile/me`,
                {
                    method: "PUT",
                    headers: cabecalhosAutenticacao(),
                    body: JSON.stringify({
                        biografia:
                            perfilFormulario.biografia.trim() || null,

                        localizacao:
                            perfilFormulario.localizacao.trim() || null,

                        foto_url:
                            perfilFormulario.foto_url.trim() || null,

                        capa_url:
                            perfilFormulario.capa_url.trim() || null,
                    }),
                }
            );

            const dados = await lerResposta(resposta);

            setPerfil(dados);

            mostrarMensagem(
                "Perfil atualizado com sucesso.",
                "sucesso"
            );
        } catch (erro) {
            mostrarMensagem(
                `Não foi possível guardar o perfil: ${erro.message}`,
                "erro"
            );
        } finally {
            setAGuardarPerfil(false);
        }
    }

    // =====================================================
    // NAVEGAÇÃO
    // =====================================================

    function navegar(id) {
        setPaginaAtual(id);
        setMenuAberto(false);
        setMensagem("");
    }

    function iniciarPesquisa(evento) {
        evento.preventDefault();

        setTermoPesquisa(pesquisa.trim());
        navegar("pesquisa");
    }

    // =====================================================
    // CAREN
    // =====================================================

    async function enviarPerguntaCaren(evento) {
        evento.preventDefault();
        const pergunta = carenPergunta.trim();
        if (!pergunta || aEnviarCaren) return;

        const historico = carenMensagens
            .filter((item) => item && typeof item.texto === "string" && item.texto.trim())
            .slice(-20)
            .map((item) => ({
                role: item.autor === "utilizador" ? "user" : "assistant",
                content: item.texto,
            }));

        setCarenMensagens((atuais) => [...atuais, { autor: "utilizador", texto: pergunta }]);
        setCarenPergunta("");
        setAEnviarCaren(true);

        try {
            const resposta = await fetch(`${API_URL}/api/caren/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${obterToken()}`,
                },
                body: JSON.stringify({ mensagem: pergunta, historico }),
            });
            const texto = await resposta.text();
            let dados = {};
            try { dados = texto ? JSON.parse(texto) : {}; } catch { dados = { detail: texto }; }
            if (!resposta.ok) throw new Error(dados.detail || `Erro da Caren (${resposta.status}).`);
            setCarenMensagens((atuais) => [...atuais, {
                autor: "caren",
                texto: dados.resposta || "Não recebi uma resposta válida da Caren.",
            }]);
        } catch (erro) {
            setCarenMensagens((atuais) => [...atuais, {
                autor: "caren",
                texto: `Não consegui responder: ${erro.message || "verifica a ligação ao backend e a configuração da OpenRouter."}`,
            }]);
        } finally {
            setAEnviarCaren(false);
        }
    }

   
// =====================================================
// ÁREA ADMINISTRATIVA INDEPENDENTE
// /adm utiliza autenticação própria e não depende da sessão normal.
// =====================================================

if (
    window.location.pathname === "/adm" ||
    window.location.pathname.startsWith("/adm/")
) {
    const tokenAdmin = sessionStorage.getItem("smartbook-admin-token");

    if (tokenAdmin) {
        return <Admin />;
    }

    return (
        <AdminLogin
            onLogin={() => window.location.reload()}
            onVoltar={() => {
                sessionStorage.removeItem("smartbook-admin-token");
                window.location.replace("/");
            }}
        />
    );
}

// =====================================================
// CARREGAMENTO INICIAL
// =====================================================

if (aValidarSessao) {
    return (
        <div className="ecrã-carregamento">
            <div className="carregamento-logo">S</div>
            <h1>SMART BOOK</h1>
            <p>A preparar o teu espaço...</p>
        </div>
    );
}

    // =====================================================
    // LOGIN E REGISTO
    // =====================================================

    if (!utilizador) {
        return (
            <main className="autenticacao">
                <header className="auth-topo">
                    <Marca />

                    <div className="auth-acoes">
                        <span
                            className={
                                backendOnline
                                    ? "estado-api online"
                                    : "estado-api offline"
                            }
                        >
                            <span className="estado-ponto" />

                            {backendOnline
                                ? "Servidor online"
                                : "Servidor indisponível"}
                        </span>

                        <BotaoIcone
                            titulo="Alternar tema"
                            onClick={alternarTema}
                        >
                            {tema === "claro" ? "☾" : "☀"}
                        </BotaoIcone>
                    </div>
                </header>

                <div className="auth-conteudo">
                    <section className="auth-apresentacao">
                        <span className="etiqueta">
                            O TEU MUNDO DIGITAL
                        </span>

                        <h1>
                            Pessoas reais.
                            <br />
                            <span>Conexões verdadeiras.</span>
                        </h1>

                        <p>
                            Partilha os teus momentos, encontra
                            pessoas, conversa com os teus amigos
                            e descobre novas ideias com a Caren.
                        </p>

                        <div className="auth-beneficios">
                            <div>
                                <span>01</span>
                                <div>
                                    <strong>Partilha momentos</strong>
                                    <p>Publicações e vídeos.</p>
                                </div>
                            </div>

                            <div>
                                <span>02</span>
                                <div>
                                    <strong>Cria conexões</strong>
                                    <p>Amigos e mensagens.</p>
                                </div>
                            </div>

                            <div>
                                <span>03</span>
                                <div>
                                    <strong>Conhece a Caren</strong>
                                    <p>Inteligência artificial integrada.</p>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section className="auth-cartao">
                        <div className="auth-cartao-topo">
                            <div className="auth-icone">
                                {pagina === "login" ? "↗" : "+"}
                            </div>

                            <h2>
                                {pagina === "login"
                                    ? "Bem-vindo de volta"
                                    : "Cria a tua conta"}
                            </h2>

                            <p>
                                {pagina === "login"
                                    ? "Entra no teu espaço."
                                    : "Junta-te à comunidade SMART BOOK."}
                            </p>
                        </div>

                        <div className="auth-abas">
                            <button
                                type="button"
                                className={
                                    pagina === "login"
                                        ? "auth-aba ativa"
                                        : "auth-aba"
                                }
                                onClick={() => {
                                    setPagina("login");
                                    mostrarMensagem("");
                                }}
                            >
                                Iniciar sessão
                            </button>

                            <button
                                type="button"
                                className={
                                    pagina === "registo"
                                        ? "auth-aba ativa"
                                        : "auth-aba"
                                }
                                onClick={() => {
                                    setPagina("registo");
                                    mostrarMensagem("");
                                }}
                            >
                                Criar conta
                            </button>
                        </div>

                        <form
                            className="auth-formulario"
                            onSubmit={submeterFormulario}
                        >
                            {pagina === "registo" && (
                                <>
                                    <label>
                                        Nome completo

                                        <input
                                            name="nome"
                                            type="text"
                                            placeholder="O teu nome completo"
                                            minLength={2}
                                            maxLength={120}
                                            required
                                        />
                                    </label>

                                    <label>
                                        Nome de utilizador

                                        <input
                                            name="username"
                                            type="text"
                                            placeholder="ex.: cristiano_manzo"
                                            minLength={3}
                                            maxLength={30}
                                            pattern="[a-zA-Z0-9_.]+"
                                            required
                                        />
                                    </label>
                                </>
                            )}

                            {pagina === "login" && (
                                <label>
                                    Email ou nome de utilizador

                                    <input
                                        name="identificador"
                                        type="text"
                                        placeholder="Email ou username"
                                        autoComplete="username"
                                        required
                                    />
                                </label>
                            )}

                            {pagina === "registo" && (
                                <label>
                                    Email

                                    <input
                                        name="email"
                                        type="email"
                                        placeholder="teu@email.com"
                                        autoComplete="email"
                                        required
                                    />
                                </label>
                            )}

                            <label>
                                Palavra-passe

                                <div className="campo-password">
                                    <input
                                        name="password"
                                        type={
                                            mostrarSenha
                                                ? "text"
                                                : "password"
                                        }
                                        placeholder="Mínimo de 8 caracteres"
                                        minLength={8}
                                        autoComplete={
                                            pagina === "login"
                                                ? "current-password"
                                                : "new-password"
                                        }
                                        required
                                    />

                                    <button
                                        type="button"
                                        onClick={() =>
                                            setMostrarSenha(!mostrarSenha)
                                        }
                                    >
                                        {mostrarSenha
                                            ? "Ocultar"
                                            : "Mostrar"}
                                    </button>
                                </div>
                            </label>

                            {pagina === "registo" && (
                                <label className="auth-termos">
                                    <input type="checkbox" required />

                                    <span>
                                        Aceito os termos e a política
                                        de privacidade.
                                    </span>
                                </label>
                            )}

                            {mensagem && (
                                <div
                                    className={`alerta ${tipoMensagem}`}
                                    role="status"
                                >
                                    {mensagem}
                                </div>
                            )}

                            <button
                                type="submit"
                                className="botao-principal"
                                disabled={carregando}
                            >
                                {carregando
                                    ? "A processar..."
                                    : pagina === "login"
                                        ? "Iniciar sessão"
                                        : "Criar a minha conta"}

                                <span>→</span>
                            </button>
                        </form>

                        <p className="auth-rodape">
                            {pagina === "login"
                                ? "Ainda não tens uma conta?"
                                : "Já tens uma conta?"}

                            <button
                                type="button"
                                onClick={() => {
                                    setPagina(
                                        pagina === "login"
                                            ? "registo"
                                            : "login"
                                    );

                                    mostrarMensagem("");
                                }}
                            >
                                {pagina === "login"
                                    ? "Regista-te"
                                    : "Inicia sessão"}
                            </button>
                        </p>
                    </section>
                </div>

                <footer className="auth-footer">
                    <span>
                        © {new Date().getFullYear()} SMART BOOK
                    </span>

                    <span>
                        Criado por Cristiano Manzo
                    </span>

                    <span>Conecta-te ao mundo.</span>
                </footer>
            </main>
        );
    }

    // =====================================================
    // ÁREA AUTENTICADA
    // =====================================================

    const nomeUtilizador =
        utilizador.nome_completo ||
        utilizador.username ||
        "Utilizador";

    function tituloPagina() {
        const item = MENU.find(
            (entrada) => entrada.id === paginaAtual
        );

        if (item) {
            return item.label;
        }

        if (paginaAtual === "pesquisa") {
            return "Pesquisa";
        }

        if (paginaAtual === "administracao") {
            return "Administração";
        }

        return "SMART BOOK";
    }

    // Interações provisórias no frontend. A persistência central será ligada ao backend na etapa seguinte.
    function alternarGosto(publicacaoId) {
        const chave = String(publicacaoId);
        const username = utilizador?.username || "visitante";
        setInteracoes((atuais) => {
            const post = atuais[chave] || { gostos: [], comentarios: [] };
            const gostos = post.gostos || [];
            const novosGostos = gostos.includes(username)
                ? gostos.filter((u) => u !== username)
                : [...gostos, username];
            return { ...atuais, [chave]: { ...post, gostos: novosGostos, comentarios: post.comentarios || [] } };
        });
    }

    function adicionarComentario(evento, publicacaoId) {
        evento.preventDefault();
        const texto = (rascunhosComentario[publicacaoId] || "").trim();
        if (!texto) return;
        setInteracoes((atuais) => {
            const chave = String(publicacaoId);
            const post = atuais[chave] || { gostos: [], comentarios: [] };
            return { ...atuais, [chave]: { ...post, gostos: post.gostos || [], comentarios: [...(post.comentarios || []), { autor: nomeUtilizador, username: utilizador?.username || "utilizador", texto, data: new Date().toISOString() }] } };
        });
        setRascunhosComentario((atuais) => ({ ...atuais, [publicacaoId]: "" }));
    }

    function renderizarInteracoes(publicacao) {
        const dados = interacoes[String(publicacao.id)] || { gostos: [], comentarios: [] };
        const username = utilizador?.username || "visitante";
        const gostou = (dados.gostos || []).includes(username);
        return (
            <div className="sb-interacoes">
                <div className="sb-interacao-acoes">
                    <button type="button" className={gostou ? "sb-like ativo" : "sb-like"} onClick={() => alternarGosto(publicacao.id)}>♥ {gostou ? "Gostaste" : "Gosto"} · {(dados.gostos || []).length}</button>
                    <span>💬 {(dados.comentarios || []).length} comentário(s)</span>
                </div>
                {(dados.comentarios || []).map((comentario, i) => (
                    <div className="sb-comentario" key={`${publicacao.id}-${i}`}>
                        <strong>{comentario.autor} <small>@{comentario.username}</small></strong>
                        <p>{comentario.texto}</p>
                    </div>
                ))}
                <form className="sb-comentar-form" onSubmit={(e) => adicionarComentario(e, publicacao.id)}>
                    <input value={rascunhosComentario[publicacao.id] || ""} onChange={(e) => setRascunhosComentario((a) => ({ ...a, [publicacao.id]: e.target.value }))} placeholder="Escreve um comentário..." maxLength={1000} />
                    <button type="submit" disabled={!(rascunhosComentario[publicacao.id] || "").trim()}>Comentar</button>
                </form>
                <small className="sb-provisorio">Gostos e comentários estão nesta versão guardados neste navegador; a sincronização entre contas será ligada ao backend.</small>
            </div>
        );
    }

    function renderizarInicio() {
        return (
            <div className="colunas-inicio">
                <section className="feed-coluna">
                    <div className="boas-vindas">
                        <div>
                            <span className="subtitulo">
                                O TEU ESPAÇO
                            </span>

                            <h2>
                                Olá, {nomeUtilizador.split(" ")[0]}.
                            </h2>

                            <p>
                                O que gostarias de partilhar hoje?
                            </p>
                        </div>

                        <Avatar
                            nome={nomeUtilizador}
                            foto={perfil?.foto_url}
                            tamanho="avatar-grande"
                        />
                    </div>

                    <form
                        className="criador-publicacao"
                        onSubmit={criarPublicacao}
                    >
                        <div className="criador-topo">
                            <Avatar
                                nome={nomeUtilizador}
                                foto={perfil?.foto_url}
                            />

                            <textarea
                                value={novoConteudo}
                                onChange={(evento) =>
                                    setNovoConteudo(evento.target.value)
                                }
                                placeholder="Em que estás a pensar?"
                                maxLength={2000}
                                rows={3}
                            />
                        </div>

                        <div className="criador-acoes">
                            <div className="criador-tipos">
                                <button
                                    type="button"
                                    onClick={() =>
                                        mostrarMensagem(
                                            "O carregamento de fotografias será ligado no módulo de multimédia.",
                                            "info"
                                        )
                                    }
                                >
                                    ▧ Fotografia
                                </button>

                                <button
                                    type="button"
                                    onClick={() => navegar("videos")}
                                >
                                    ▷ Vídeo
                                </button>
                            </div>

                            <button
                                className="botao-publicar"
                                type="submit"
                                disabled={
                                    publicando ||
                                    !novoConteudo.trim()
                                }
                            >
                                {publicando
                                    ? "A publicar..."
                                    : "Publicar"}
                            </button>
                        </div>
                    </form>

                    {mensagem && (
                        <div
                            className={`alerta ${tipoMensagem}`}
                            role="status"
                        >
                            {mensagem}
                        </div>
                    )}

                    <div className="feed-cabecalho">
                        <div>
                            <h3>O teu feed</h3>
                            <p>Publicações da comunidade.</p>
                        </div>

                        <button
                            type="button"
                            className="botao-texto"
                            onClick={carregarPublicacoes}
                        >
                            Atualizar ↻
                        </button>
                    </div>

                    {carregandoPublicacoes ? (
                        <div className="cartao-vazio">
                            <div className="carregamento-logo pequeno">
                                S
                            </div>

                            <p>A carregar publicações...</p>
                        </div>
                    ) : publicacoes.length === 0 ? (
                        <div className="cartao-vazio">
                            <div className="vazio-icone">◈</div>

                            <h3>O teu feed está vazio</h3>

                            <p>
                                Quando existirem publicações,
                                aparecerão aqui.
                            </p>
                        </div>
                    ) : (
                        <div className="lista-publicacoes">
                            {publicacoes.map((publicacao) => (
                                <article
                                    className="publicacao"
                                    key={publicacao.id}
                                >
                                    <div className="publicacao-topo">
                                        <Avatar
                                            nome={
                                                publicacao.autor_nome
                                            }
                                        />

                                        <div className="publicacao-autor">
                                            <strong>
                                                {publicacao.autor_nome ||
                                                    "Utilizador"}
                                            </strong>

                                            <span>
                                                @
                                                {publicacao.autor_username ||
                                                    "utilizador"}
                                            </span>

                                            <time>
                                                {publicacao.data_criacao
                                                    ? new Date(
                                                        publicacao.data_criacao
                                                    ).toLocaleString("pt-PT")
                                                    : ""}
                                            </time>
                                        </div>

                                        {publicacao.autor_id ===
                                            utilizador.id && (
                                            <BotaoIcone
                                                titulo="Apagar publicação"
                                                onClick={() =>
                                                    apagarPublicacao(
                                                        publicacao.id
                                                    )
                                                }
                                            >
                                                ⋯
                                            </BotaoIcone>
                                        )}
                                    </div>

                                    <div className="publicacao-conteudo">
                                        {publicacao.conteudo}
                                    </div>

                                    <div className="publicacao-rodape">
                                        <span>
                                            Publicação SMART BOOK
                                        </span>

                                        <span>◆</span>
                                    </div>

                                    {renderizarInteracoes(publicacao)}
                                </article>
                            ))}
                        </div>
                    )}
                </section>

                <aside className="coluna-direita">
                    <div className="cartao-lateral caren-cartao">
                        <div className="caren-simbolo">✳</div>

                        <span className="subtitulo">
                            ASSISTENTE INTELIGENTE
                        </span>

                        <h3>Conhece a Caren</h3>

                        <p>
                            A tua assistente de IA dentro do
                            SMART BOOK.
                        </p>

                        <button
                            type="button"
                            className="botao-secundario"
                            onClick={() => navegar("caren")}
                        >
                            Abrir Caren →
                        </button>
                    </div>

                    <div className="cartao-lateral">
                        <h3>O teu perfil</h3>

                        <div className="perfil-miniatura">
                            <Avatar
                                nome={nomeUtilizador}
                                foto={perfil?.foto_url}
                                tamanho="avatar-grande"
                            />

                            <div>
                                <strong>{nomeUtilizador}</strong>
                                <span>@{utilizador.username}</span>
                            </div>
                        </div>

                        <button
                            type="button"
                            className="botao-secundario largura-total"
                            onClick={() => navegar("perfil")}
                        >
                            Ver perfil
                        </button>
                    </div>

                    <div className="cartao-lateral cartao-info">
                        <span>SMART BOOK</span>

                        <p>
                            O teu mundo. As tuas conexões.
                        </p>

                        <small>
                            Criado por Cristiano Manzo.
                        </small>
                    </div>
                </aside>
            </div>
        );
    }

    function renderizarPerfil() {
        return (
            <div className="pagina-conteudo">
                <section className="perfil-cabecalho">
                    <div
                        className="perfil-capa"
                        style={
                            perfil?.capa_url
                                ? {
                                    backgroundImage:
                                        `url("${perfil.capa_url}")`,
                                }
                                : {}
                        }
                    >
                        <span>O TEU ESPAÇO PESSOAL</span>
                    </div>

                    <div className="perfil-identidade">
                        <Avatar
                            nome={nomeUtilizador}
                            foto={perfil?.foto_url}
                            tamanho="avatar-perfil"
                        />

                        <div>
                            <h2>{nomeUtilizador}</h2>

                            <p>@{utilizador.username}</p>

                            <span>
                                {perfil?.localizacao ||
                                    "Adiciona a tua localização"}
                            </span>
                        </div>

                        <button
                            type="button"
                            className="botao-secundario"
                            onClick={() => navegar("definicoes")}
                        >
                            Editar perfil
                        </button>
                    </div>

                    <div className="perfil-biografia">
                        {perfil?.biografia ||
                            "Ainda não adicionaste uma biografia."}
                    </div>
                </section>

                <div className="cartao-branco perfil-detalhes">
                    <div className="secao-titulo">
                        <div>
                            <h3>Informações pessoais</h3>

                            <p>
                                Informações que identificam o teu perfil.
                            </p>
                        </div>
                    </div>

                    <div className="perfil-dados">
                        <div>
                            <span>Nome completo</span>
                            <strong>{nomeUtilizador}</strong>
                        </div>

                        <div>
                            <span>Nome de utilizador</span>
                            <strong>@{utilizador.username}</strong>
                        </div>

                        <div>
                            <span>Localização</span>
                            <strong>
                                {perfil?.localizacao || "Não indicada"}
                            </strong>
                        </div>

                        <div>
                            <span>Membro desde</span>
                            <strong>
                                {perfil?.data_registo
                                    ? new Date(
                                        perfil.data_registo
                                    ).toLocaleDateString("pt-PT")
                                    : "SMART BOOK"}
                            </strong>
                        </div>
                    </div>
                </div>

                <div className="secao-titulo perfil-feed-titulo">
                    <div>
                        <h3>As minhas publicações</h3>

                        <p>
                            As publicações que criaste na plataforma.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="botao-texto"
                        onClick={() => navegar("inicio")}
                    >
                        Voltar ao feed →
                    </button>
                </div>

                <div className="lista-publicacoes">
                    {publicacoes
                        .filter(
                            (post) =>
                                post.autor_id === utilizador.id
                        )
                        .map((post) => (
                            <article
                                className="publicacao"
                                key={post.id}
                            >
                                <div className="publicacao-topo">
                                    <Avatar
                                        nome={nomeUtilizador}
                                        foto={perfil?.foto_url}
                                    />

                                    <div className="publicacao-autor">
                                        <strong>{nomeUtilizador}</strong>
                                        <span>@{utilizador.username}</span>
                                    </div>
                                </div>

                                <div className="publicacao-conteudo">
                                    {post.conteudo}
                                </div>
                                {renderizarInteracoes(post)}
                            </article>
                        ))}
                </div>
            </div>
        );
    }

    function renderizarPesquisa() {
        const termo = termoPesquisa.toLowerCase();

        const resultados = publicacoes.filter((post) => {
            const conteudo = (
                post.conteudo || ""
            ).toLowerCase();

            const autor = (
                post.autor_nome || ""
            ).toLowerCase();

            const username = (
                post.autor_username || ""
            ).toLowerCase();

            return (
                conteudo.includes(termo) ||
                autor.includes(termo) ||
                username.includes(termo)
            );
        });

        return (
            <div className="pagina-conteudo">
                <div className="secao-titulo">
                    <div>
                        <h2>Pesquisa</h2>

                        <p>
                            Procura publicações no feed disponível.
                        </p>
                    </div>
                </div>

                <form
                    className="pesquisa-grande"
                    onSubmit={iniciarPesquisa}
                >
                    <input
                        value={pesquisa}
                        onChange={(evento) =>
                            setPesquisa(evento.target.value)
                        }
                        placeholder="Pesquisar publicações..."
                    />

                    <button
                        className="botao-principal"
                        type="submit"
                    >
                        Pesquisar
                    </button>
                </form>

                <div className="lista-publicacoes">
                    {termoPesquisa && resultados.length === 0 && (
                        <div className="cartao-vazio">
                            <h3>Não encontrámos resultados</h3>

                            <p>
                                Tenta pesquisar com outras palavras.
                            </p>
                        </div>
                    )}

                    {resultados.map((post) => (
                        <article
                            className="publicacao"
                            key={post.id}
                        >
                            <div className="publicacao-topo">
                                <Avatar
                                    nome={post.autor_nome}
                                />

                                <div className="publicacao-autor">
                                    <strong>{post.autor_nome}</strong>
                                    <span>
                                        @{post.autor_username}
                                    </span>
                                </div>
                            </div>

                            <div className="publicacao-conteudo">
                                {post.conteudo}
                            </div>
                            {renderizarInteracoes(post)}
                        </article>
                    ))}
                </div>
            </div>
        );
    }

    function renderizarDefinicoes() {
        return (
            <div className="pagina-conteudo">
                <div className="secao-titulo">
                    <div>
                        <h2>Definições da conta</h2>

                        <p>
                            Gere as informações do teu perfil.
                        </p>
                    </div>
                </div>

                <div className="definicoes-layout">
                    <aside className="definicoes-menu">
                        <button className="ativa" type="button">
                            ♙ Informações pessoais
                        </button>

                        <button
                            type="button"
                            onClick={() =>
                                mostrarMensagem(
                                    "As opções de segurança e alteração de palavra-passe serão ligadas no módulo de autenticação.",
                                    "info"
                                )
                            }
                        >
                            ◈ Segurança e palavra-passe
                        </button>

                        <button
                            type="button"
                            onClick={() =>
                                mostrarMensagem(
                                    "As opções de privacidade serão implementadas no módulo de privacidade.",
                                    "info"
                                )
                            }
                        >
                            ◉ Privacidade
                        </button>

                        <button
                            type="button"
                            onClick={alternarTema}
                        >
                            ☾ Aparência
                        </button>
                    </aside>

                    <form
                        className="cartao-branco definicoes-formulario"
                        onSubmit={guardarPerfil}
                    >
                        <div className="secao-titulo">
                            <div>
                                <h3>Editar perfil</h3>

                                <p>
                                    As alterações serão guardadas
                                    na tua conta.
                                </p>
                            </div>
                        </div>

                        <label>
                            Nome completo

                            <input
                                type="text"
                                value={nomeUtilizador}
                                disabled
                            />

                            <small>
                                A alteração do nome será disponibilizada
                                nas definições gerais da conta.
                            </small>
                        </label>

                        <label>
                            Nome de utilizador

                            <input
                                type="text"
                                value={`@${utilizador.username}`}
                                disabled
                            />
                        </label>

                        <label>
                            Biografia

                            <textarea
                                rows={4}
                                maxLength={1000}
                                value={perfilFormulario.biografia}
                                onChange={(evento) =>
                                    setPerfilFormulario({
                                        ...perfilFormulario,
                                        biografia: evento.target.value,
                                    })
                                }
                                placeholder="Conta-nos um pouco sobre ti..."
                            />
                        </label>

                        <label>
                            Localização

                            <input
                                type="text"
                                maxLength={150}
                                value={perfilFormulario.localizacao}
                                onChange={(evento) =>
                                    setPerfilFormulario({
                                        ...perfilFormulario,
                                        localizacao: evento.target.value,
                                    })
                                }
                                placeholder="Cidade, país"
                            />
                        </label>

                        <label>
                            Endereço da fotografia de perfil

                            <input
                                type="url"
                                maxLength={500}
                                value={perfilFormulario.foto_url}
                                onChange={(evento) =>
                                    setPerfilFormulario({
                                        ...perfilFormulario,
                                        foto_url: evento.target.value,
                                    })
                                }
                                placeholder="https://..."
                            />

                            <small>
                                O carregamento direto de fotografias
                                do computador será integrado no módulo
                                de multimédia.
                            </small>
                        </label>

                        <label>
                            Endereço da fotografia de capa

                            <input
                                type="url"
                                maxLength={500}
                                value={perfilFormulario.capa_url}
                                onChange={(evento) =>
                                    setPerfilFormulario({
                                        ...perfilFormulario,
                                        capa_url: evento.target.value,
                                    })
                                }
                                placeholder="https://..."
                            />
                        </label>

                        {mensagem && (
                            <div
                                className={`alerta ${tipoMensagem}`}
                                role="status"
                            >
                                {mensagem}
                            </div>
                        )}

                        <button
                            className="botao-principal"
                            type="submit"
                            disabled={aGuardarPerfil}
                        >
                            {aGuardarPerfil
                                ? "A guardar..."
                                : "Guardar alterações"}
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    function renderizarCaren() {
        return (
            <div className="pagina-conteudo caren-pagina">
                <div className="caren-cabecalho">
                    <div className="caren-simbolo grande">✳</div>

                    <span className="subtitulo">
                        INTELIGÊNCIA ARTIFICIAL
                    </span>

                    <h2>Olá, sou a Caren.</h2>

                    <p>
                        A tua assistente dentro do SMART BOOK.
                    </p>
                </div>

                <section className="caren-chat">
                    <div className="caren-chat-cabecalho">
                        <div className="caren-simbolo">✳</div>

                        <div>
                            <strong>Caren IA</strong>
                            <span>
                                Interface de conversa
                            </span>
                        </div>
                    </div>

                    <div className="caren-mensagens">
                        {carenMensagens.map(
                            (mensagemCaren, indice) => (
                                <div
                                    key={indice}
                                    className={
                                        mensagemCaren.autor === "utilizador"
                                            ? "mensagem-chat minha"
                                            : "mensagem-chat"
                                    }
                                >
                                    <div className="mensagem-chat-conteudo">
                                        {mensagemCaren.texto}
                                    </div>
                                </div>
                            )
                        )}

                        {aEnviarCaren && (
                            <div className="mensagem-chat">
                                <div className="mensagem-chat-conteudo">
                                    A preparar resposta...
                                </div>
                            </div>
                        )}
                    </div>

                    <form
                        className="caren-formulario"
                        onSubmit={enviarPerguntaCaren}
                    >
                        <input
                            value={carenPergunta}
                            onChange={(evento) =>
                                setCarenPergunta(evento.target.value)
                            }
                            placeholder="Escreve uma mensagem..."
                            maxLength={4000}
                        />

                        <button
                            type="submit"
                            className="botao-principal"
                            disabled={
                                aEnviarCaren ||
                                !carenPergunta.trim()
                            }
                        >
                            Enviar →
                        </button>
                    </form>

                    <p className="caren-aviso">
                        As respostas são geradas pela Caren através do backend. A chave da API fica protegida no servidor.
                    </p>
                </section>
            </div>
        );
    }

    function renderizarModuloPreparado(id) {
        const conteudos = {
            amigos: {
                icon: "♧",
                titulo: "Os teus amigos",
                descricao:
                    "Descobre pessoas e constrói a tua rede de contactos.",
                funcionalidades: [
                    "Lista de amigos",
                    "Pesquisa de utilizadores",
                    "Perfis públicos",
                    "Gestão de amizades",
                ],
            },

            pedidos: {
                icon: "♧",
                titulo: "Pedidos de amizade",
                descricao:
                    "Gere os pedidos de amizade enviados e recebidos.",
                funcionalidades: [
                    "Pedidos recebidos",
                    "Aceitar pedidos",
                    "Recusar pedidos",
                    "Pedidos enviados",
                ],
            },

            videos: {
                icon: "▷",
                titulo: "Vídeos",
                descricao:
                    "Um espaço dedicado a vídeos da comunidade.",
                funcionalidades: [
                    "Publicar vídeos",
                    "Reproduzir vídeos",
                    "Gostos e comentários",
                    "Partilhar conteúdos",
                ],
            },

            mensagens: {
                icon: "✉",
                titulo: "Mensagens",
                descricao:
                    "O teu espaço para conversas privadas.",
                funcionalidades: [
                    "Conversas privadas",
                    "Lista de contactos",
                    "Histórico de mensagens",
                    "Estado de leitura",
                ],
            },

            notificacoes: {
                icon: "♧",
                titulo: "Notificações",
                descricao:
                    "Acompanha as novidades relacionadas com a tua conta.",
                funcionalidades: [
                    "Pedidos de amizade",
                    "Novas mensagens",
                    "Interações nas publicações",
                    "Alertas da plataforma",
                ],
            },
        };

        const conteudo = conteudos[id];

        if (!conteudo) {
            return null;
        }

        return (
            <div className="pagina-conteudo">
                <div className="modulo-cabecalho">
                    <div className="modulo-icone">
                        {conteudo.icon}
                    </div>

                    <span className="subtitulo">
                        SMART BOOK
                    </span>

                    <h2>{conteudo.titulo}</h2>

                    <p>{conteudo.descricao}</p>
                </div>

                <div className="modulo-funcionalidades">
                    {conteudo.funcionalidades.map(
                        (funcionalidade, indice) => (
                            <div
                                className="funcionalidade-cartao"
                                key={funcionalidade}
                            >
                                <span className="funcionalidade-numero">
                                    {String(indice + 1).padStart(2, "0")}
                                </span>

                                <div>
                                    <strong>{funcionalidade}</strong>

                                    <p>
                                        Área prevista para o módulo
                                        {` ${conteudo.titulo.toLowerCase()}`}.
                                    </p>
                                </div>
                            </div>
                        )
                    )}
                </div>

                <div className="alerta info">
                    Esta área já tem a estrutura visual.
                    A implementação das operações, dos dados e da
                    comunicação com o backend será feita no módulo
                    correspondente.
                </div>
            </div>
        );
    }

    function renderizarAdministracao() {
        if (!utilizador.administrador) {
            return (
                <div className="pagina-conteudo">
                    <div className="cartao-vazio">
                        <div className="vazio-icone">🔒</div>

                        <h2>Acesso restrito</h2>

                        <p>
                            Esta área está reservada a contas com
                            permissões de administrador.
                        </p>

                        <button
                            type="button"
                            className="botao-secundario"
                            onClick={() => navegar("inicio")}
                        >
                            Voltar ao início
                        </button>
                    </div>
                </div>
            );
        }

        return (
            <div className="pagina-conteudo">
                <div className="secao-titulo">
                    <div>
                        <h2>Painel de administração</h2>

                        <p>
                            Gestão da plataforma SMART BOOK.
                        </p>
                    </div>
                </div>

                <div className="alerta info">
                    A interface de administração está preparada.
                    As operações administrativas, as denúncias,
                    as estatísticas e a gestão de utilizadores serão
                    ligadas a endpoints protegidos no backend.
                </div>

                <div className="modulo-funcionalidades">
                    {[
                        "Utilizadores",
                        "Publicações",
                        "Denúncias",
                        "Segurança",
                    ].map((item) => (
                        <div
                            className="funcionalidade-cartao"
                            key={item}
                        >
                            <span className="funcionalidade-numero">
                                ◆
                            </span>

                            <div>
                                <strong>{item}</strong>

                                <p>
                                    Área de gestão reservada
                                    à administração.
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    function renderizarPagina() {
        switch (paginaAtual) {
            case "inicio":
                return renderizarInicio();

            case "perfil":
                return renderizarPerfil();

            case "definicoes":
                return renderizarDefinicoes();

            case "caren":
                return renderizarCaren();

            case "pesquisa":
                return renderizarPesquisa();

            case "administracao":
                // A rota administrativa independente é tratada acima em /adm.
                return <div className="pagina-conteudo"><h2>Administração</h2><p>Abre a área administrativa em /adm.</p></div>;

            case "amigos":
            case "pedidos":
            case "videos":
            case "mensagens":
            case "notificacoes":
                return <ModulosSociais pagina={paginaAtual} utilizador={utilizador} />;

            case "negocio":
                return <NegocioOportunidade utilizador={utilizador} />;

            case "casa":
                return <CasaInteligente />;

            default:
                return renderizarModuloPreparado(paginaAtual);
        }
    }

    // =====================================================
    // INTERFACE PRINCIPAL
    // =====================================================

    return (
        <div className="app-shell">
            <aside
                className={
                    menuAberto
                        ? "barra-lateral aberta"
                        : "barra-lateral"
                }
            >
                <div className="barra-marca">
                    <Marca />

                    <button
                        type="button"
                        className="fechar-menu"
                        onClick={() => setMenuAberto(false)}
                    >
                        ×
                    </button>
                </div>

                <button
                    type="button"
                    className="botao-perfil-lateral"
                    onClick={() => navegar("perfil")}
                >
                    <Avatar
                        nome={nomeUtilizador}
                        foto={perfil?.foto_url}
                        tamanho="avatar-grande"
                    />

                    <span className="dados-lateral">
                        <strong>{nomeUtilizador}</strong>

                        <small>
                            @{utilizador.username}
                        </small>
                    </span>

                    <span className="seta-lateral">→</span>
                </button>

                <div className="menu-legenda">
                    MENU PRINCIPAL
                </div>

                <nav className="navegacao">
                    {MENU.map((item) => (
                        <button
                            type="button"
                            key={item.id}
                            className={
                                paginaAtual === item.id
                                    ? "item-menu ativo"
                                    : "item-menu"
                            }
                            onClick={() => navegar(item.id)}
                        >
                            <span className="menu-icone">
                                {item.icon}
                            </span>

                            <span>{item.label}</span>
                        </button>
                    ))}
                </nav>

                {(utilizador.administrador || admAutorizado) && (
                    <button
                        type="button"
                        className={
                            paginaAtual === "administracao"
                                ? "item-menu ativo"
                                : "item-menu"
                        }
                        onClick={() =>
                            navegar("administracao")
                        }
                    >
                        <span className="menu-icone">◆</span>
                        Administração
                    </button>
                )}

                <div className="barra-lateral-rodape">
                    <div className="caren-mini">
                        <div className="caren-simbolo">✳</div>

                        <div>
                            <strong>Caren IA</strong>
                            <small>A tua assistente</small>
                        </div>
                    </div>

                    <button
                        type="button"
                        className="item-menu"
                        onClick={alternarTema}
                    >
                        <span className="menu-icone">
                            {tema === "claro" ? "☾" : "☀"}
                        </span>

                        <span>
                            {tema === "claro"
                                ? "Modo escuro"
                                : "Modo claro"}
                        </span>
                    </button>

                    <button
                        type="button"
                        className="item-menu item-sair"
                        onClick={terminarSessao}
                    >
                        <span className="menu-icone">↪</span>
                        Terminar sessão
                    </button>

                    <div className="rodape-marca">
                        SMART BOOK © {new Date().getFullYear()}
                    </div>
                </div>
            </aside>

            {menuAberto && (
                <button
                    type="button"
                    className="fundo-menu"
                    aria-label="Fechar menu"
                    onClick={() => setMenuAberto(false)}
                />
            )}

            <main className="area-principal">
                <header className="cabecalho-principal">
                    <div className="cabecalho-titulo">
                        <button
                            type="button"
                            className="botao-menu-mobile"
                            onClick={() => setMenuAberto(true)}
                        >
                            ☰
                        </button>

                        <div>
                            <span className="subtitulo">
                                SMART BOOK
                            </span>

                            <h1>{tituloPagina()}</h1>
                        </div>
                    </div>

                    <form
                        className="pesquisa-cabecalho"
                        onSubmit={iniciarPesquisa}
                    >
                        <span>⌕</span>

                        <input
                            type="search"
                            value={pesquisa}
                            onChange={(evento) =>
                                setPesquisa(evento.target.value)
                            }
                            placeholder="Pesquisar..."
                        />

                        <button
                            type="submit"
                            aria-label="Pesquisar"
                        >
                            ↵
                        </button>
                    </form>

                    <div className="cabecalho-acoes">
                        <BotaoIcone
                            titulo="Notificações"
                            onClick={() => navegar("notificacoes")}
                        >
                            ♧
                        </BotaoIcone>

                        <BotaoIcone
                            titulo="Mensagens"
                            onClick={() => navegar("mensagens")}
                        >
                            ✉
                        </BotaoIcone>

                        <BotaoIcone
                            titulo="Definições"
                            onClick={() => navegar("definicoes")}
                        >
                            ⚙
                        </BotaoIcone>

                        <button
                            type="button"
                            className="cabecalho-avatar"
                            onClick={() => navegar("perfil")}
                            title="Meu perfil"
                        >
                            <Avatar
                                nome={nomeUtilizador}
                                foto={perfil?.foto_url}
                            />
                        </button>
                    </div>
                </header>

                <section className="conteudo-principal">
                    {!backendOnline && (
                        <div className="alerta erro alerta-servidor">
                            Não foi possível estabelecer ligação
                            ao servidor. Algumas operações podem
                            estar indisponíveis.
                        </div>
                    )}

                    {renderizarPagina()}
                </section>

                <footer className="rodape-principal">
                    <span>
                        © {new Date().getFullYear()} SMART BOOK
                    </span>

                    <span>
                        Criado por Cristiano Manzo
                    </span>

                    <span className="estado-rodape">
                        <span
                            className={
                                backendOnline
                                    ? "estado-ponto"
                                    : "estado-ponto desligado"
                            }
                        />

                        {backendOnline
                            ? "Ligado ao servidor"
                            : "Servidor indisponível"}
                    </span>
                </footer>
            </main>
        </div>
    );
}