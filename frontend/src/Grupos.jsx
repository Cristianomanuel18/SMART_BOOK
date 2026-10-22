import { useEffect, useRef, useState } from "react";
import "./Grupos.css";

const SERVIDOR = import.meta.env.VITE_API_URL || (
    import.meta.env.DEV
        ? "http://127.0.0.1:8000"
        : window.location.origin
);
const API = `${SERVIDOR}/api/grupos`;
const LIMITE_IMAGEM = 5 * 1024 * 1024;

function token() {
    return (
        sessionStorage.getItem("smartbook-token") ||
        localStorage.getItem("smartbook-token") ||
        localStorage.getItem("access_token") ||
        localStorage.getItem("token") ||
        ""
    );
}


function urlImagem(caminho) {
    if (!caminho) return "";

    if (
        caminho.startsWith("http://") ||
        caminho.startsWith("https://") ||
        caminho.startsWith("data:")
    ) {
        return caminho;
    }

    return `${SERVIDOR}${caminho.startsWith("/") ? "" : "/"}${caminho}`;
}

async function pedido(url, opcoes = {}) {
    const eFormulario = opcoes.body instanceof FormData;

    const resposta = await fetch(url, {
        ...opcoes,

        headers: {
            Authorization: `Bearer ${token()}`,

            ...(opcoes.body && !eFormulario
                ? { "Content-Type": "application/json" }
                : {}),

            ...opcoes.headers,
        },
    });

    const dados = await resposta.json().catch(() => ({}));

    if (!resposta.ok) {
        throw new Error(
            typeof dados.detail === "string"
                ? dados.detail
                : "Não foi possível concluir a operação."
        );
    }

    return dados;
}

function idParticipante(pessoa) {
    return Number(
        pessoa?.utilizador_id ??
        pessoa?.utilizador?.id ??
        pessoa?.id ??
        0
    );
}

function nomeParticipante(pessoa) {
    return (
        pessoa?.nome_completo ||
        pessoa?.utilizador?.nome_completo ||
        pessoa?.username ||
        pessoa?.utilizador?.username ||
        "Utilizador"
    );
}

function iniciais(nome = "") {
    return nome
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((parte) => parte[0] || "")
        .join("")
        .toUpperCase() || "G";
}

function dataMensagem(data) {
    if (!data) return "";

    const dataConvertida = new Date(data);

    if (Number.isNaN(dataConvertida.getTime())) {
        return "";
    }

    return dataConvertida.toLocaleString("pt-PT", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

export default function Grupos() {
    const [grupos, setGrupos] = useState([]);
    const [utilizadores, setUtilizadores] = useState([]);
    const [grupoAtual, setGrupoAtual] = useState(null);
    const [mensagens, setMensagens] = useState([]);
    const [participantesGrupo, setParticipantesGrupo] = useState([]);

    const [nome, setNome] = useState("");
    const [descricao, setDescricao] = useState("");
    const [selecionados, setSelecionados] = useState([]);

    const [novoParticipante, setNovoParticipante] = useState("");
    const [texto, setTexto] = useState("");
    const [pesquisa, setPesquisa] = useState("");

    const [mostrarCriacao, setMostrarCriacao] = useState(false);
    const [mostrarMembros, setMostrarMembros] = useState(true);

    const [erro, setErro] = useState("");
    const [sucesso, setSucesso] = useState("");

    const [carregando, setCarregando] = useState(false);
    const [enviandoImagem, setEnviandoImagem] = useState(false);

    const fotoInput = useRef(null);
    const capaInput = useRef(null);
    const mensagensFim = useRef(null);

    const souCriador = Boolean(grupoAtual?.sou_criador);

    // ========================================================
    // MENSAGENS DE ESTADO
    // ========================================================

    function avisarSucesso(mensagem) {
        setErro("");
        setSucesso(mensagem);
    }

    function avisarErro(mensagem) {
        setSucesso("");
        setErro(mensagem);
    }

    // ========================================================
    // CARREGAR GRUPOS
    // ========================================================

    async function carregarGrupos(idSelecionar = null) {
        const lista = await pedido(API);

        setGrupos(Array.isArray(lista) ? lista : []);

        if (idSelecionar != null) {
            const escolhido = lista.find(
                (grupo) => Number(grupo.id) === Number(idSelecionar)
            );

            if (escolhido) {
                setGrupoAtual(escolhido);
            }
        }

        return lista;
    }

    // ========================================================
    // CARREGAR UTILIZADORES DISPONÍVEIS
    // ========================================================

    async function carregarUtilizadores() {
        const lista = await pedido(`${API}/utilizadores`);

        setUtilizadores(Array.isArray(lista) ? lista : []);
    }

    // ========================================================
    // CARREGAR MENSAGENS
    // ========================================================

    async function carregarMensagens(id) {
        const lista = await pedido(`${API}/${id}/mensagens`);

        setMensagens(Array.isArray(lista) ? lista : []);
    }

    // ========================================================
    // CARREGAR MEMBROS DO GRUPO
    // ========================================================

    async function carregarParticipantes(id) {
        const lista = await pedido(`${API}/${id}/participantes`);

        setParticipantesGrupo(Array.isArray(lista) ? lista : []);
    }

    // ========================================================
    // INICIALIZAÇÃO
    // ========================================================

    useEffect(() => {
        let ativo = true;

        async function iniciar() {
            try {
                const [listaGrupos, listaUtilizadores] =
                    await Promise.all([
                        pedido(API),
                        pedido(`${API}/utilizadores`),
                    ]);

                if (!ativo) return;

                setGrupos(
                    Array.isArray(listaGrupos) ? listaGrupos : []
                );

                setUtilizadores(
                    Array.isArray(listaUtilizadores)
                        ? listaUtilizadores
                        : []
                );
            } catch (e) {
                if (ativo) avisarErro(e.message);
            }
        }

        iniciar();

        return () => {
            ativo = false;
        };
    }, []);

    // ========================================================
    // ATUALIZAÇÃO DAS MENSAGENS E DOS MEMBROS
    // ========================================================

    useEffect(() => {
        if (!grupoAtual?.id) {
            setMensagens([]);
            setParticipantesGrupo([]);
            return;
        }

        const id = grupoAtual.id;
        let ativo = true;

        async function atualizar() {
            try {
                const [listaMensagens, listaParticipantes] =
                    await Promise.all([
                        pedido(`${API}/${id}/mensagens`),
                        pedido(`${API}/${id}/participantes`),
                    ]);

                if (!ativo) return;

                setMensagens(
                    Array.isArray(listaMensagens)
                        ? listaMensagens
                        : []
                );

                setParticipantesGrupo(
                    Array.isArray(listaParticipantes)
                        ? listaParticipantes
                        : []
                );
            } catch (e) {
                if (ativo) avisarErro(e.message);
            }
        }

        atualizar();

        const intervalo = setInterval(atualizar, 5000);

        return () => {
            ativo = false;
            clearInterval(intervalo);
        };
    }, [grupoAtual?.id]);

    useEffect(() => {
        mensagensFim.current?.scrollIntoView({
            behavior: "smooth",
            block: "end",
        });
    }, [mensagens]);

    // ========================================================
    // SELECIONAR GRUPO
    // ========================================================

    function abrirGrupo(grupo) {
        setErro("");
        setSucesso("");
        setGrupoAtual(grupo);
        setTexto("");
        setMostrarCriacao(false);
    }

    // ========================================================
    // CRIAR GRUPO
    // ========================================================

    async function criarGrupo(evento) {
        evento.preventDefault();

        if (!nome.trim()) {
            avisarErro("Escreve o nome do grupo.");
            return;
        }

        setCarregando(true);
        setErro("");
        setSucesso("");

        try {
            const novoGrupo = await pedido(API, {
                method: "POST",

                body: JSON.stringify({
                    nome: nome.trim(),
                    descricao: descricao.trim(),
                    participantes: selecionados.map(Number),
                }),
            });

            setNome("");
            setDescricao("");
            setSelecionados([]);
            setPesquisa("");
            setMostrarCriacao(false);

            await carregarGrupos(novoGrupo.id);

            avisarSucesso("Grupo criado com sucesso.");
        } catch (e) {
            avisarErro(e.message);
        } finally {
            setCarregando(false);
        }
    }

    // ========================================================
    // SELECIONAR MEMBROS NA CRIAÇÃO
    // ========================================================

    function alternarSelecionado(id) {
        const numero = Number(id);

        setSelecionados((atuais) =>
            atuais.includes(numero)
                ? atuais.filter((item) => item !== numero)
                : [...atuais, numero]
        );
    }

    // ========================================================
    // ENVIAR MENSAGEM
    // ========================================================

    async function enviarMensagem(evento) {
        evento.preventDefault();

        if (!grupoAtual?.id || !texto.trim()) return;

        const conteudo = texto.trim();

        setTexto("");
        setErro("");
        setSucesso("");

        try {
            await pedido(`${API}/${grupoAtual.id}/mensagens`, {
                method: "POST",
                body: JSON.stringify({ conteudo }),
            });

            await carregarMensagens(grupoAtual.id);
        } catch (e) {
            setTexto(conteudo);
            avisarErro(e.message);
        }
    }

    // ========================================================
    // ADICIONAR MEMBRO
    // ========================================================

    async function adicionarParticipante(evento) {
        evento.preventDefault();

        if (!grupoAtual?.id) return;

        const id = Number(novoParticipante);

        if (!id) {
            avisarErro("Seleciona primeiro um utilizador.");
            return;
        }

        setCarregando(true);

        try {
            await pedido(
                `${API}/${grupoAtual.id}/participantes`,
                {
                    method: "POST",

                    body: JSON.stringify({
                        utilizador_id: id,
                    }),
                }
            );

            setNovoParticipante("");

            await carregarParticipantes(grupoAtual.id);
            await carregarGrupos(grupoAtual.id);

            avisarSucesso("Membro adicionado ao grupo.");
        } catch (e) {
            avisarErro(e.message);
        } finally {
            setCarregando(false);
        }
    }

    // ========================================================
    // REMOVER MEMBRO
    // ========================================================

    async function removerParticipante(pessoa) {
        if (!grupoAtual?.id || !souCriador) return;

        const id = idParticipante(pessoa);
        const nomePessoa = nomeParticipante(pessoa);

        if (!id) {
            avisarErro("Não foi possível identificar este membro.");
            return;
        }

        if (id === Number(grupoAtual.criador_id)) {
            avisarErro(
                "O criador do grupo não pode ser removido desta forma."
            );
            return;
        }

        const confirmar = window.confirm(
            `Queres realmente remover ${nomePessoa} deste grupo?`
        );

        if (!confirmar) return;

        try {
            await pedido(
                `${API}/${grupoAtual.id}/participantes/${id}`,
                {
                    method: "DELETE",
                }
            );

            await carregarParticipantes(grupoAtual.id);
            await carregarGrupos(grupoAtual.id);

            avisarSucesso(`${nomePessoa} foi removido do grupo.`);
        } catch (e) {
            avisarErro(e.message);
        }
    }

    // ========================================================
    // ELIMINAR GRUPO
    // ========================================================

    async function eliminarGrupo() {
        if (!grupoAtual?.id || !souCriador) return;

        const confirmar = window.confirm(
            `Tens a certeza de que queres eliminar o grupo "${grupoAtual.nome}"? ` +
            "Esta operação também elimina as mensagens do grupo."
        );

        if (!confirmar) return;

        setCarregando(true);

        try {
            await pedido(`${API}/${grupoAtual.id}`, {
                method: "DELETE",
            });

            const restante = grupos.filter(
                (grupo) =>
                    Number(grupo.id) !== Number(grupoAtual.id)
            );

            setGrupos(restante);
            setGrupoAtual(null);
            setMensagens([]);
            setParticipantesGrupo([]);

            avisarSucesso("Grupo eliminado com sucesso.");
        } catch (e) {
            avisarErro(e.message);
        } finally {
            setCarregando(false);
        }
    }

    // ========================================================
    // ESCOLHER FOTO DO GRUPO OU CAPA
    // ========================================================

    function selecionarImagem(tipo) {
        if (!souCriador) {
            avisarErro(
                "Só o criador do grupo pode alterar estas imagens."
            );
            return;
        }

        if (tipo === "perfil") {
            fotoInput.current?.click();
        } else {
            capaInput.current?.click();
        }
    }

    async function carregarImagem(evento, tipo) {
        const ficheiro = evento.target.files?.[0];

        // Permite voltar a escolher o mesmo ficheiro.
        evento.target.value = "";

        if (!ficheiro) return;

        if (!ficheiro.type.startsWith("image/")) {
            avisarErro("Seleciona um ficheiro de imagem válido.");
            return;
        }

        if (ficheiro.size > LIMITE_IMAGEM) {
            avisarErro(
                "A imagem é demasiado grande. O limite é 5 MB."
            );
            return;
        }

        if (!grupoAtual?.id) {
            avisarErro("Seleciona primeiro um grupo.");
            return;
        }

        const formulario = new FormData();

        formulario.append("tipo", tipo);
        formulario.append("ficheiro", ficheiro);

        setEnviandoImagem(true);
        setErro("");
        setSucesso("");

        try {
            const resultado = await pedido(
                `${API}/${grupoAtual.id}/imagem`,
                {
                    method: "POST",
                    body: formulario,
                }
            );

            setGrupoAtual((atual) => ({
                ...atual,
                imagem_url:
                    resultado.imagem_url ?? atual.imagem_url,
                capa_url:
                    resultado.capa_url ?? atual.capa_url,
            }));

            await carregarGrupos(grupoAtual.id);

            avisarSucesso(
                tipo === "perfil"
                    ? "Foto do grupo atualizada."
                    : "Capa do grupo atualizada."
            );
        } catch (e) {
            avisarErro(e.message);
        } finally {
            setEnviandoImagem(false);
        }
    }

    // ========================================================
    // UTILIZADORES QUE AINDA PODEM SER ADICIONADOS
    // ========================================================

    const idsAtuais = new Set(
        participantesGrupo.map(idParticipante)
    );

    const utilizadoresDisponiveis = utilizadores.filter(
        (pessoa) =>
            !idsAtuais.has(Number(pessoa.id)) &&
            (
                `${pessoa.nome_completo || ""} ${pessoa.username || ""}`
                    .toLowerCase()
                    .includes(pesquisa.toLowerCase())
            )
    );

    const candidatosAdicionar = utilizadores.filter(
        (pessoa) => !idsAtuais.has(Number(pessoa.id))
    );

    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="sb-grupos">

            {/* BARRA LATERAL */}

            <aside className="sb-grupos-sidebar">

                <div className="sb-grupos-marca">
                    <div className="sb-grupos-marca-icon">G</div>

                    <div>
                        <strong>SMART BOOK</strong>
                        <span>Comunidades</span>
                    </div>
                </div>

                <div className="sb-grupos-sidebar-titulo">
                    <div>
                        <span>OS TEUS ESPAÇOS</span>
                        <h2>Grupos</h2>
                    </div>

                    <button
                        type="button"
                        className="sb-novo-grupo-icone"
                        title="Criar grupo"
                        onClick={() => {
                            setMostrarCriacao(!mostrarCriacao);
                            setGrupoAtual(null);
                            setErro("");
                            setSucesso("");
                        }}
                    >
                        +
                    </button>
                </div>

                <div className="sb-grupos-pesquisa">
                    <span>⌕</span>

                    <input
                        type="search"
                        placeholder="Procurar grupo..."
                        value={pesquisa}
                        onChange={(e) => setPesquisa(e.target.value)}
                    />
                </div>

                <div className="sb-lista-grupos">

                    {grupos
                        .filter((grupo) =>
                            (grupo.nome || "")
                                .toLowerCase()
                                .includes(pesquisa.toLowerCase())
                        )
                        .map((grupo) => (
                            <button
                                type="button"
                                key={grupo.id}
                                className={
                                    `sb-grupo-item ${
                                        Number(grupoAtual?.id) === Number(grupo.id)
                                            ? "ativo"
                                            : ""
                                    }`
                                }
                                onClick={() => abrirGrupo(grupo)}
                            >
                                <div className="sb-grupo-avatar">
                                    {grupo.imagem_url ? (
                                        <img
                                            src={urlImagem(grupo.imagem_url)}
                                            alt=""
                                        />
                                    ) : (
                                        iniciais(grupo.nome)
                                    )}
                                </div>

                                <div className="sb-grupo-item-info">
                                    <strong>{grupo.nome}</strong>

                                    <span>
                                        {grupo.total_participantes ?? 0} membros
                                    </span>
                                </div>

                                <span className="sb-grupo-item-seta">›</span>
                            </button>
                        ))}

                    {grupos.length === 0 && (
                        <div className="sb-grupos-vazio">
                            <span>◎</span>
                            <strong>Ainda não tens grupos</strong>
                            <p>Cria o teu primeiro grupo.</p>
                        </div>
                    )}

                </div>

                <button
                    type="button"
                    className="sb-sidebar-criar"
                    onClick={() => {
                        setMostrarCriacao(true);
                        setGrupoAtual(null);
                        setErro("");
                        setSucesso("");
                    }}
                >
                    <span>＋</span>
                    Criar novo grupo
                </button>

                <div className="sb-sidebar-rodape">
                    <span className="sb-online-ponto" />
                    SMART BOOK · Grupos
                </div>

            </aside>

            {/* ÁREA PRINCIPAL */}

            <main className="sb-grupos-main">

                {(erro || sucesso) && (
                    <div
                        className={
                            `sb-aviso ${erro ? "sb-aviso-erro" : "sb-aviso-sucesso"}`
                        }
                        role="status"
                    >
                        <span>{erro ? "!" : "✓"}</span>
                        <p>{erro || sucesso}</p>

                        <button
                            type="button"
                            onClick={() => {
                                setErro("");
                                setSucesso("");
                            }}
                            aria-label="Fechar mensagem"
                        >
                            ×
                        </button>
                    </div>
                )}

                {/* FORMULÁRIO DE CRIAÇÃO */}

                {mostrarCriacao && (
                    <section className="sb-criar-painel">

                        <div className="sb-pagina-topo">
                            <div>
                                <span className="sb-etiqueta">NOVA COMUNIDADE</span>
                                <h1>Criar um grupo</h1>
                                <p>
                                    Junta pessoas e começa uma conversa.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="sb-botao-secundario"
                                onClick={() => setMostrarCriacao(false)}
                            >
                                Cancelar
                            </button>
                        </div>

                        <form onSubmit={criarGrupo}>

                            <label className="sb-campo">
                                <span>Nome do grupo *</span>

                                <input
                                    value={nome}
                                    onChange={(e) => setNome(e.target.value)}
                                    placeholder="Ex.: Amigos, Família, Trabalho"
                                    maxLength={120}
                                    required
                                />
                            </label>

                            <label className="sb-campo">
                                <span>Descrição</span>

                                <textarea
                                    value={descricao}
                                    onChange={(e) => setDescricao(e.target.value)}
                                    placeholder="Qual é o objetivo deste grupo?"
                                    rows={3}
                                />
                            </label>

                            <div className="sb-selecionar-membros-titulo">
                                <div>
                                    <h3>Adicionar membros</h3>
                                    <p>
                                        Seleciona as pessoas que queres convidar.
                                    </p>
                                </div>

                                <span>
                                    {selecionados.length} selecionados
                                </span>
                            </div>

                            <input
                                className="sb-input-pesquisa-membros"
                                type="search"
                                placeholder="Procurar pessoas..."
                                value={pesquisa}
                                onChange={(e) => setPesquisa(e.target.value)}
                            />

                            <div className="sb-selecao-utilizadores">
                                {utilizadoresDisponiveis.map((pessoa) => (
                                    <label
                                        key={pessoa.id}
                                        className="sb-selecao-utilizador"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selecionados.includes(
                                                Number(pessoa.id)
                                            )}
                                            onChange={() =>
                                                alternarSelecionado(pessoa.id)
                                            }
                                        />

                                        <span className="sb-mini-avatar">
                                            {iniciais(pessoa.nome_completo)}
                                        </span>

                                        <span className="sb-utilizador-nome">
                                            <strong>
                                                {pessoa.nome_completo ||
                                                    pessoa.username}
                                            </strong>

                                            <small>
                                                {pessoa.username
                                                    ? `@${pessoa.username}`
                                                    : "Utilizador SMART BOOK"}
                                            </small>
                                        </span>
                                    </label>
                                ))}

                                {utilizadoresDisponiveis.length === 0 && (
                                    <p className="sb-sem-utilizadores">
                                        Não existem mais utilizadores disponíveis
                                        para adicionar.
                                    </p>
                                )}
                            </div>

                            <button
                                type="submit"
                                className="sb-botao-principal"
                                disabled={carregando}
                            >
                                {carregando
                                    ? "A criar..."
                                    : "＋ Criar grupo"}
                            </button>

                        </form>
                    </section>
                )}

                {/* ESTADO SEM GRUPO SELECIONADO */}

                {!mostrarCriacao && !grupoAtual && (
                    <section className="sb-grupos-boas-vindas">

                        <div className="sb-boas-vindas-ilustracao">
                            <div className="sb-orbita sb-orbita-1" />
                            <div className="sb-orbita sb-orbita-2" />

                            <div className="sb-boas-vindas-icone">
                                <span>✦</span>
                            </div>
                        </div>

                        <span className="sb-etiqueta">
                            A TUA COMUNIDADE
                        </span>

                        <h1>As melhores conversas<br />começam em grupo.</h1>

                        <p>
                            Cria espaços para os teus amigos, família e colegas.
                            Partilha ideias e conversa num só lugar.
                        </p>

                        <button
                            type="button"
                            className="sb-botao-principal"
                            onClick={() => setMostrarCriacao(true)}
                        >
                            ＋ Criar o meu grupo
                        </button>

                    </section>
                )}

                {/* GRUPO SELECIONADO */}

                {!mostrarCriacao && grupoAtual && (
                    <section className="sb-grupo-conteudo">

                        <header className="sb-grupo-cabecalho">

                            <div
                                className="sb-grupo-capa"
                                style={
                                    grupoAtual.capa_url
                                        ? {
                                            backgroundImage:
                                                `linear-gradient(90deg, rgba(13,20,42,.78), rgba(13,20,42,.2)), url("${urlImagem(grupoAtual.capa_url)}")`,
                                        }
                                        : {}
                                }
                            >
                                {souCriador && (
                                    <button
                                        type="button"
                                        className="sb-alterar-capa"
                                        onClick={() => selecionarImagem("capa")}
                                        disabled={enviandoImagem}
                                    >
                                        🖼️ Alterar capa
                                    </button>
                                )}
                            </div>

                            <div className="sb-grupo-perfil">

                                <div className="sb-grupo-foto">
                                    {grupoAtual.imagem_url ? (
                                        <img
                                            src={urlImagem(grupoAtual.imagem_url)}
                                            alt={`Foto de ${grupoAtual.nome}`}
                                        />
                                    ) : (
                                        <span>{iniciais(grupoAtual.nome)}</span>
                                    )}

                                    {souCriador && (
                                        <button
                                            type="button"
                                            className="sb-botao-camera"
                                            title="Selecionar foto do grupo"
                                            aria-label="Selecionar foto do grupo"
                                            onClick={() => selecionarImagem("perfil")}
                                            disabled={enviandoImagem}
                                        >
                                            📷
                                        </button>
                                    )}
                                </div>

                                <div className="sb-grupo-identidade">
                                    <span className="sb-etiqueta">
                                        COMUNIDADE
                                    </span>

                                    <h1>{grupoAtual.nome}</h1>

                                    <p>
                                        {grupoAtual.descricao ||
                                            "Um espaço para conversar e partilhar."}
                                    </p>

                                    <div className="sb-grupo-meta">
                                        <span>
                                            ◉ {participantesGrupo.length} membros
                                        </span>

                                        <span>
                                            ● Grupo ativo
                                        </span>
                                    </div>
                                </div>

                                <div className="sb-grupo-acoes">

                                    {souCriador && (
                                        <button
                                            type="button"
                                            className="sb-botao-eliminar"
                                            onClick={eliminarGrupo}
                                            disabled={carregando}
                                            title="Eliminar este grupo"
                                        >
                                            🗑️ Eliminar grupo
                                        </button>
                                    )}

                                    <button
                                        type="button"
                                        className="sb-botao-membros"
                                        onClick={() =>
                                            setMostrarMembros(!mostrarMembros)
                                        }
                                    >
                                        👥 {mostrarMembros
                                            ? "Ocultar membros"
                                            : "Ver membros"}
                                    </button>

                                </div>

                            </div>

                            {enviandoImagem && (
                                <div className="sb-upload-progresso">
                                    A carregar imagem...
                                </div>
                            )}

                            <input
                                ref={fotoInput}
                                type="file"
                                accept="image/jpeg,image/png,image/webp,image/gif"
                                hidden
                                onChange={(e) => carregarImagem(e, "perfil")}
                            />

                            <input
                                ref={capaInput}
                                type="file"
                                accept="image/jpeg,image/png,image/webp,image/gif"
                                hidden
                                onChange={(e) => carregarImagem(e, "capa")}
                            />

                        </header>

                        <div
                            className={
                                `sb-grupo-corpo ${
                                    mostrarMembros
                                        ? ""
                                        : "sb-grupo-sem-membros"
                                }`
                            }
                        >

                            {/* CONVERSA */}

                            <section className="sb-conversa">

                                <div className="sb-conversa-topo">
                                    <div>
                                        <span className="sb-online-ponto" />
                                        <strong>Conversa do grupo</strong>
                                    </div>

                                    <span className="sb-conversa-atualizacao">
                                        Mensagens atualizadas automaticamente
                                    </span>
                                </div>

                                <div className="sb-mensagens">

                                    {mensagens.length === 0 && (
                                        <div className="sb-mensagens-vazio">
                                            <div>✉</div>
                                            <h3>A conversa começa aqui</h3>
                                            <p>
                                                Envia a primeira mensagem ao grupo.
                                            </p>
                                        </div>
                                    )}

                                    {mensagens.map((mensagem) => {
                                        const nomeRemetente =
                                            mensagem.remetente
                                                ?.nome_completo ||
                                            mensagem.remetente?.username ||
                                            "Utilizador";

                                        return (
                                            <div
                                                key={mensagem.id}
                                                className={
                                                    `sb-mensagem ${
                                                        mensagem.minha
                                                            ? "sb-mensagem-minha"
                                                            : ""
                                                    }`
                                                }
                                            >
                                                {!mensagem.minha && (
                                                    <div className="sb-mensagem-avatar">
                                                        {iniciais(nomeRemetente)}
                                                    </div>
                                                )}

                                                <div className="sb-mensagem-conteudo">
                                                    {!mensagem.minha && (
                                                        <strong className="sb-mensagem-autor">
                                                            {nomeRemetente}
                                                        </strong>
                                                    )}

                                                    <div className="sb-balao">
                                                        {mensagem.conteudo}
                                                    </div>

                                                    <span className="sb-mensagem-data">
                                                        {dataMensagem(
                                                            mensagem.data_criacao
                                                        )}
                                                    </span>
                                                </div>
                                            </div>
                                        );
                                    })}

                                    <div ref={mensagensFim} />

                                </div>

                                <form
                                    className="sb-escrever-mensagem"
                                    onSubmit={enviarMensagem}
                                >
                                    <input
                                        value={texto}
                                        onChange={(e) => setTexto(e.target.value)}
                                        placeholder={`Escreve uma mensagem para ${grupoAtual.nome}...`}
                                        aria-label="Escrever mensagem"
                                    />

                                    <button
                                        type="submit"
                                        disabled={!texto.trim()}
                                        title="Enviar mensagem"
                                    >
                                        Enviar <span>➤</span>
                                    </button>
                                </form>

                            </section>

                            {/* GESTÃO DE MEMBROS */}

                            {mostrarMembros && (
                                <aside className="sb-membros-painel">

                                    <div className="sb-membros-titulo">
                                        <div>
                                            <h3>Membros</h3>
                                            <p>
                                                {participantesGrupo.length} participantes
                                            </p>
                                        </div>

                                        <span className="sb-membros-contador">
                                            {participantesGrupo.length}
                                        </span>
                                    </div>

                                    {/* ADICIONAR MEMBROS */}

                                    {souCriador && (
                                        <form
                                            className="sb-adicionar-membro"
                                            onSubmit={adicionarParticipante}
                                        >
                                            <label htmlFor="novo-membro-grupo">
                                                Adicionar pessoas
                                            </label>

                                            <select
                                                id="novo-membro-grupo"
                                                value={novoParticipante}
                                                onChange={(e) =>
                                                    setNovoParticipante(e.target.value)
                                                }
                                            >
                                                <option value="">
                                                    Seleciona um utilizador
                                                </option>

                                                {candidatosAdicionar.map((pessoa) => (
                                                    <option
                                                        key={pessoa.id}
                                                        value={pessoa.id}
                                                    >
                                                        {pessoa.nome_completo ||
                                                            pessoa.username}
                                                    </option>
                                                ))}
                                            </select>

                                            <button
                                                type="submit"
                                                className="sb-botao-adicionar-membro"
                                                disabled={
                                                    carregando ||
                                                    !novoParticipante
                                                }
                                            >
                                                ＋ Adicionar membro
                                            </button>
                                        </form>
                                    )}

                                    {!souCriador && (
                                        <p className="sb-aviso-permissoes">
                                            Apenas o criador pode gerir os membros.
                                        </p>
                                    )}

                                    {/* LISTA DE MEMBROS */}

                                    <div className="sb-lista-membros">

                                        {participantesGrupo.map((pessoa, indice) => {
                                            const id = idParticipante(pessoa);
                                            const nomePessoa =
                                                nomeParticipante(pessoa);

                                            const eCriador =
                                                id === Number(grupoAtual.criador_id);

                                            return (
                                                <div
                                                    className="sb-membro"
                                                    key={
                                                        pessoa.id ||
                                                        pessoa.utilizador_id ||
                                                        `${id}-${indice}`
                                                    }
                                                >
                                                    <div className="sb-membro-avatar">
                                                        {iniciais(nomePessoa)}
                                                    </div>

                                                    <div className="sb-membro-info">
                                                        <strong>{nomePessoa}</strong>

                                                        <span>
                                                            {eCriador
                                                                ? "Criador do grupo"
                                                                : pessoa.username
                                                                    ? `@${pessoa.username}`
                                                                    : "Participante"}
                                                        </span>
                                                    </div>

                                                    {souCriador && !eCriador && (
                                                        <button
                                                            type="button"
                                                            className="sb-remover-membro"
                                                            title={`Remover ${nomePessoa}`}
                                                            aria-label={`Remover ${nomePessoa}`}
                                                            onClick={() =>
                                                                removerParticipante(pessoa)
                                                            }
                                                        >
                                                            ×
                                                        </button>
                                                    )}
                                                </div>
                                            );
                                        })}

                                        {participantesGrupo.length === 0 && (
                                            <p className="sb-sem-membros">
                                                Não foi possível encontrar os membros.
                                            </p>
                                        )}

                                    </div>

                                </aside>
                            )}

                        </div>

                    </section>
                )}

            </main>
        </div>
    );
}