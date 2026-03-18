from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import uuid
import os

app = Flask(__name__)
app.secret_key = "segredo_super_forte"

# Criar Banco de Dados

def criar_banco():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXTO NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
                   
     )
     """)
    
    # Recuperação de senha
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        token TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

criar_banco()

# Rota Usuários
@app.route("/usuarios")
def listar_usuarios():
    if "usuario_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, email FROM usuarios")
    usuarios = cursor.fetchall()

    conn.close()

    return render_template("usuarios.html", usuarios=usuarios)

# Rota Principal
@app.route("/")
def home():
    return render_template("cadastro.html")

# Rota para o Login

@app.route("/login")
def login():
    return render_template("login.html")

# Processar Login
@app.route("/logar", methods=["POST"])
def logar():
    email = request.form["email"]
    senha = request.form["senha"]

    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, nome FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha)
    )

    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        session["usuario_id"] = usuario[0]
        session["usuario_nome"] = usuario[1]
        return redirect("/usuarios")
    else:
        return render_template("login.html", erro="Email ou senha inválidos!")
    
# Rota para Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Rota Esqueci minha senha
@app.route("/esqueci-senha")
def esqueci_senha():
    return render_template("esqueci_senha.html")

# Rota para gerar token de recuperação
@app.route("/enviar-reset", methods=["POST"])
def enviar_reset():
    email = request.form["email"]

    token = str(uuid.uuid4())

    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO reset_tokens (email, token) VALUES (?, ?)",
        (email, token)
    )

    conn.commit()
    conn.close()

    # Simulando envio de link
    link = f"http://127.0.0.1:5000/resetar-senha/{token}"

    return f"Link de recuperação: <a href='{link}'>Clique aqui</a>"

# Rota Redefinição
@app.route("/resetar-senha/<token>")
def resetar_senha(token):
    return render_template("resetar_senha.html", token=token)

# Rota para Salvar nova senha
@app.route("/resetar-senha/<token>", methods=["POST"])
def salvar_nova_senha(token):
    senha = request.form["senha"]

    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM reset_tokens WHERE token = ?", (token,))
    resultado = cursor.fetchone()

    if resultado:
        email = resultado[0]

        cursor.execute(
            "UPDATE usuarios SET senha = ? WHERE email = ?",
            (senha, email)
        )

        # 🔥 Remove o token após uso
        cursor.execute("DELETE FROM reset_tokens WHERE token = ?", (token,))

        conn.commit()
        conn.close()

        flash("Senha atualizada com sucesso!", "success")
        return redirect("/login")

    conn.close()
    return "Token inválido!"

# Rota para Cadastro 
@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    nome = request.form["nome"]
    email = request.form["email"].strip().lower()
    senha = request.form["senha"]

    if not nome or not email or not senha:
        return render_template("erro.html", mensagem="Preencha todos os campos!")

    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (nome, email, senha)
        )
        conn.commit()

    except sqlite3.IntegrityError:
        return render_template("erro.html", mensagem="Email já cadastrado!")

    except Exception as e:
        return f"Erro inesperado: {e}"

    finally:
        conn.close()

    flash("Usuário cadastrado com sucesso!", "success")
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

