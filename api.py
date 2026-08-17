import sqlite3

from flask import Flask, jsonify, request

from app import conectar, criar_tabelas

app = Flask(__name__)


def marca_para_dict(marca):
    return {"id": marca["id"], "nome": marca["nome"], "ativa": bool(marca["ativa"])}


def veiculo_para_dict(veiculo):
    return {
        "id": veiculo["id"],
        "placa": veiculo["placa"],
        "modelo": veiculo["modelo"],
        "ano": veiculo["ano"],
        "cor": veiculo["cor"],
        "marca_id": veiculo["marca_id"],
        "marca_nome": veiculo["marca_nome"],
        "marca_ativa": bool(veiculo["marca_ativa"]),
        "quilometragem": veiculo["quilometragem"],
    }


def buscar_veiculo(conexao, veiculo_id):
    return conexao.execute(
        """SELECT v.*, m.nome AS marca_nome, m.ativa AS marca_ativa
           FROM veiculos v JOIN marcas m ON m.id = v.marca_id
           WHERE v.id = ?""",
        (veiculo_id,),
    ).fetchone()


@app.get("/marcas")
def listar_marcas():
    busca = request.args.get("busca", "")
    with conectar() as conexao:
        lista = conexao.execute(
            "SELECT * FROM marcas WHERE nome LIKE ? ORDER BY nome",
            (f"%{busca}%",),
        ).fetchall()
    return jsonify([marca_para_dict(m) for m in lista])


@app.post("/marcas")
def cadastrar_marca():
    dados = request.get_json(force=True) or {}
    nome = (dados.get("nome") or "").strip()
    ativa = bool(dados.get("ativa", True))
    if not nome:
        return jsonify({"erro": "Campo 'nome' é obrigatório."}), 400
    try:
        with conectar() as conexao:
            cursor = conexao.execute(
                "INSERT INTO marcas (nome, ativa) VALUES (?, ?)",
                (nome, int(ativa)),
            )
            marca = conexao.execute(
                "SELECT * FROM marcas WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return jsonify(marca_para_dict(marca)), 201
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Já existe uma marca com esse nome."}), 409


@app.get("/marcas/<int:marca_id>")
def obter_marca(marca_id):
    with conectar() as conexao:
        marca = conexao.execute(
            "SELECT * FROM marcas WHERE id = ?", (marca_id,)
        ).fetchone()
    if not marca:
        return jsonify({"erro": "Marca não encontrada."}), 404
    return jsonify(marca_para_dict(marca))


@app.put("/marcas/<int:marca_id>")
def editar_marca(marca_id):
    dados = request.get_json(force=True) or {}
    with conectar() as conexao:
        marca = conexao.execute(
            "SELECT * FROM marcas WHERE id = ?", (marca_id,)
        ).fetchone()
        if not marca:
            return jsonify({"erro": "Marca não encontrada."}), 404

        nome = (dados.get("nome") or marca["nome"]).strip()
        ativa = bool(dados.get("ativa", marca["ativa"]))
        try:
            conexao.execute(
                "UPDATE marcas SET nome = ?, ativa = ? WHERE id = ?",
                (nome, int(ativa), marca_id),
            )
            marca = conexao.execute(
                "SELECT * FROM marcas WHERE id = ?", (marca_id,)
            ).fetchone()
            return jsonify(marca_para_dict(marca))
        except sqlite3.IntegrityError:
            return jsonify({"erro": "Já existe uma marca com esse nome."}), 409


@app.delete("/marcas/<int:marca_id>")
def excluir_marca(marca_id):
    with conectar() as conexao:
        marca = conexao.execute(
            "SELECT * FROM marcas WHERE id = ?", (marca_id,)
        ).fetchone()
        if not marca:
            return jsonify({"erro": "Marca não encontrada."}), 404
        try:
            conexao.execute("DELETE FROM marcas WHERE id = ?", (marca_id,))
            return "", 204
        except sqlite3.IntegrityError:
            return (
                jsonify({"erro": "Não é possível excluir uma marca que possui veículos."}),
                409,
            )


@app.get("/veiculos")
def listar_veiculos():
    busca = request.args.get("busca", "")
    with conectar() as conexao:
        lista = conexao.execute(
            """SELECT v.*, m.nome AS marca_nome, m.ativa AS marca_ativa
               FROM veiculos v JOIN marcas m ON m.id = v.marca_id
               WHERE v.placa LIKE ? OR v.modelo LIKE ?
               ORDER BY v.id""",
            (f"%{busca}%", f"%{busca}%"),
        ).fetchall()
    return jsonify([veiculo_para_dict(v) for v in lista])


@app.post("/veiculos")
def cadastrar_veiculo():
    dados = request.get_json(force=True) or {}
    placa = (dados.get("placa") or "").strip().upper()
    modelo = (dados.get("modelo") or "").strip()
    ano = dados.get("ano")
    cor = dados.get("cor")
    marca_id = dados.get("marca_id")
    quilometragem = dados.get("quilometragem", 0)

    if not placa or not modelo or ano is None or marca_id is None:
        return (
            jsonify({"erro": "Campos 'placa', 'modelo', 'ano' e 'marca_id' são obrigatórios."}),
            400,
        )

    with conectar() as conexao:
        marca = conexao.execute(
            "SELECT * FROM marcas WHERE id = ? AND ativa = 1", (marca_id,)
        ).fetchone()
        if not marca:
            return jsonify({"erro": "Marca não encontrada ou está inativa."}), 400
        try:
            cursor = conexao.execute(
                """INSERT INTO veiculos (placa, modelo, ano, cor, marca_id, quilometragem)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (placa, modelo, ano, cor, marca_id, quilometragem),
            )
            veiculo = buscar_veiculo(conexao, cursor.lastrowid)
            return jsonify(veiculo_para_dict(veiculo)), 201
        except sqlite3.IntegrityError:
            return jsonify({"erro": "Já existe um veículo com essa placa."}), 409


@app.get("/veiculos/<int:veiculo_id>")
def obter_veiculo(veiculo_id):
    with conectar() as conexao:
        veiculo = buscar_veiculo(conexao, veiculo_id)
    if not veiculo:
        return jsonify({"erro": "Veículo não encontrado."}), 404
    return jsonify(veiculo_para_dict(veiculo))


@app.put("/veiculos/<int:veiculo_id>")
def editar_veiculo(veiculo_id):
    dados = request.get_json(force=True) or {}
    with conectar() as conexao:
        veiculo = buscar_veiculo(conexao, veiculo_id)
        if not veiculo:
            return jsonify({"erro": "Veículo não encontrado."}), 404

        placa = (dados.get("placa") or veiculo["placa"]).strip().upper()
        modelo = (dados.get("modelo") or veiculo["modelo"]).strip()
        ano = dados.get("ano", veiculo["ano"])
        cor = dados.get("cor", veiculo["cor"])
        marca_id = dados.get("marca_id", veiculo["marca_id"])
        quilometragem = dados.get("quilometragem", veiculo["quilometragem"])

        marca = conexao.execute(
            "SELECT * FROM marcas WHERE id = ? AND ativa = 1", (marca_id,)
        ).fetchone()
        if not marca:
            return jsonify({"erro": "Marca não encontrada ou está inativa."}), 400

        try:
            conexao.execute(
                """UPDATE veiculos SET placa = ?, modelo = ?, ano = ?, cor = ?,
                   marca_id = ?, quilometragem = ? WHERE id = ?""",
                (placa, modelo, ano, cor, marca_id, quilometragem, veiculo_id),
            )
            veiculo = buscar_veiculo(conexao, veiculo_id)
            return jsonify(veiculo_para_dict(veiculo))
        except sqlite3.IntegrityError:
            return jsonify({"erro": "Já existe outro veículo com essa placa."}), 409


@app.delete("/veiculos/<int:veiculo_id>")
def excluir_veiculo(veiculo_id):
    with conectar() as conexao:
        veiculo = buscar_veiculo(conexao, veiculo_id)
        if not veiculo:
            return jsonify({"erro": "Veículo não encontrado."}), 404
        conexao.execute("DELETE FROM veiculos WHERE id = ?", (veiculo_id,))
    return "", 204


@app.post("/veiculos/<int:veiculo_id>/quilometragem")
def registrar_quilometragem(veiculo_id):
    dados = request.get_json(force=True) or {}
    nova = dados.get("quilometragem")
    if nova is None:
        return jsonify({"erro": "Campo 'quilometragem' é obrigatório."}), 400

    with conectar() as conexao:
        veiculo = buscar_veiculo(conexao, veiculo_id)
        if not veiculo:
            return jsonify({"erro": "Veículo não encontrado."}), 404
        if nova <= veiculo["quilometragem"]:
            return (
                jsonify({"erro": f"A quilometragem deve ser maior que {veiculo['quilometragem']}."}),
                400,
            )
        conexao.execute(
            "UPDATE veiculos SET quilometragem = ? WHERE id = ?",
            (nova, veiculo_id),
        )
        veiculo = buscar_veiculo(conexao, veiculo_id)
    return jsonify(veiculo_para_dict(veiculo))


if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
