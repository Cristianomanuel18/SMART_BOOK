import { useState } from "react";

const SERVIDOR = import.meta.env.VITE_API_URL || (
    import.meta.env.DEV
        ? "http://127.0.0.1:8000"
        : window.location.origin
);

const API_URL = `${SERVIDOR}/api/adm`;
export default function AdminLogin({ onLogin, onVoltar }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [mostrarPassword, setMostrarPassword] = useState(false);
    const [carregando, setCarregando] = useState(false);
    const [erro, setErro] = useState("");

    async function entrar(e) {
        e.preventDefault();

        setErro("");
        setCarregando(true);

        try {
            const resposta = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email: email.trim().toLowerCase(),
                    password,
                }),
            });

            const texto = await resposta.text();

            let dados = {};

            try {
                dados = texto ? JSON.parse(texto) : {};
            } catch {
                throw new Error(
                    "O servidor devolveu uma resposta inválida."
                );
            }

            if (!resposta.ok) {
                throw new Error(
                    dados.detail || "Não foi possível entrar no ADM."
                );
            }

            if (!dados.access_token) {
                throw new Error(
                    "O servidor não devolveu o token administrativo."
                );
            }

            sessionStorage.setItem(
                "smartbook-admin-token",
                dados.access_token
            );

            onLogin();
        } catch (e) {
            setErro(
                e.message ||
                "Não foi possível contactar o servidor."
            );
        } finally {
            setCarregando(false);
        }
    }

    return (
        <main className="sb-modulo">
            <section
                className="sb-card"
                style={{
                    maxWidth: "440px",
                    margin: "60px auto",
                    padding: "30px",
                }}
            >
                <div
                    style={{
                        textAlign: "center",
                        marginBottom: "28px",
                    }}
                >
                    <div
                        style={{
                            fontSize: "42px",
                            marginBottom: "12px",
                        }}
                    >
                        ◆
                    </div>

                    <p
                        style={{
                            letterSpacing: "3px",
                            fontSize: "12px",
                            opacity: 0.7,
                        }}
                    >
                        SMART BOOK
                    </p>

                    <h1 style={{ marginBottom: "8px" }}>
                        Acesso administrativo
                    </h1>

                    <p style={{ opacity: 0.7 }}>
                        Introduz as tuas credenciais administrativas.
                    </p>
                </div>

                {erro && (
                    <div
                        role="alert"
                        style={{
                            padding: "12px",
                            marginBottom: "18px",
                            border: "1px solid #dc3545",
                            borderRadius: "8px",
                            color: "#dc3545",
                        }}
                    >
                        {erro}
                    </div>
                )}

                <form onSubmit={entrar}>
                    <label
                        htmlFor="adm-email"
                        style={{
                            display: "block",
                            marginBottom: "8px",
                        }}
                    >
                        E-mail administrativo
                    </label>

                    <input
                        id="adm-email"
                        type="email"
                        autoComplete="username"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="E-mail do administrador"
                        required
                        disabled={carregando}
                        style={{
                            width: "100%",
                            boxSizing: "border-box",
                            marginBottom: "20px",
                        }}
                    />

                    <label
                        htmlFor="adm-password"
                        style={{
                            display: "block",
                            marginBottom: "8px",
                        }}
                    >
                        Palavra-passe
                    </label>

                    <input
                        id="adm-password"
                        type={mostrarPassword ? "text" : "password"}
                        autoComplete="current-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Palavra-passe administrativa"
                        required
                        disabled={carregando}
                        style={{
                            width: "100%",
                            boxSizing: "border-box",
                            marginBottom: "12px",
                        }}
                    />

                    <label
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            marginBottom: "22px",
                            cursor: "pointer",
                        }}
                    >
                        <input
                            type="checkbox"
                            checked={mostrarPassword}
                            onChange={(e) =>
                                setMostrarPassword(e.target.checked)
                            }
                        />

                        Mostrar palavra-passe
                    </label>

                    <button
                        type="submit"
                        disabled={carregando}
                        style={{
                            width: "100%",
                            padding: "13px",
                        }}
                    >
                        {carregando
                            ? "A verificar credenciais..."
                            : "Entrar no ADM"}
                    </button>
                </form>

                <button
                    type="button"
                    className="sb-secondary"
                    onClick={onVoltar}
                    disabled={carregando}
                    style={{
                        width: "100%",
                        marginTop: "12px",
                    }}
                >
                    Voltar
                </button>

                <p
                    style={{
                        textAlign: "center",
                        marginTop: "24px",
                        fontSize: "12px",
                        opacity: 0.65,
                    }}
                >
                    Área restrita a administradores autorizados.
                </p>
            </section>
        </main>
    );
}