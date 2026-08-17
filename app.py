import sqlite3
from pathlib import Path


BANCO = Path(__file__).with_name("veiculos.db")


def conectar():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    with conectar() as conexao:
        conexao.executescript(
            """
            CREATE TABLE IF NOT EXISTS marcas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE COLLATE NOCASE,
                ativa INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS veiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                placa TEXT NOT NULL UNIQUE COLLATE NOCASE,
                modelo TEXT NOT NULL,
                ano INTEGER NOT NULL,
                cor TEXT,
                marca_id INTEGER NOT NULL,
                quilometragem INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (marca_id) REFERENCES marcas(id)
            );
            """
        )


def ler_texto(pergunta, obrigatorio=True, padrao=None):
    while True:
        sufixo = f" [{padrao}]" if padrao is not None else ""
        valor = input(f"{pergunta}{sufixo}: ").strip()
        if not valor and padrao is not None:
            return str(padrao)
        if valor or not obrigatorio:
            return valor
        print("Este campo é obrigatório.")


def ler_inteiro(pergunta, minimo=None, maximo=None, padrao=None):
    while True:
        valor = ler_texto(pergunta, padrao=padrao)
        try:
            numero = int(valor)
            if minimo is not None and numero < minimo:
                raise ValueError
            if maximo is not None and numero > maximo:
                raise ValueError
            return numero
        except ValueError:
            limites = []
            if minimo is not None:
                limites.append(f"maior ou igual a {minimo}")
            if maximo is not None:
                limites.append(f"menor ou igual a {maximo}")
            complemento = f" ({' e '.join(limites)})" if limites else ""
            print(f"Informe um número válido{complemento}.")


def confirmar(pergunta):
    return ler_texto(f"{pergunta} (s/n)").lower() == "s"


def mostrar_marcas(lista):
    if not lista:
        print("Nenhuma marca encontrada.")
        return

    print("\nID | Nome                         | Status")
    print("---+------------------------------+--------")
    for marca in lista:
        status = "Ativa" if marca["ativa"] else "Inativa"
        print(f"{marca['id']:2} | {marca['nome'][:28]:28} | {status}")


def mostrar_veiculos(lista):
    if not lista:
        print("Nenhum veículo encontrado.")
        return

    print("\nID | Placa      | Modelo                 | Marca              | Ano  | Km")
    print("---+------------+------------------------+--------------------+------+------")
    for veiculo in lista:
        marca = veiculo["marca_nome"]
        if not veiculo["marca_ativa"]:
            marca += " (inativa)"
        print(
            f"{veiculo['id']:2} | {veiculo['placa'][:10]:10} | "
            f"{veiculo['modelo'][:22]:22} | {marca[:18]:18} | "
            f"{veiculo['ano']:4} | {veiculo['quilometragem']}"
        )


def escolher_marca_ativa(conexao, marca_id=None):
    marca = conexao.execute(
        "SELECT * FROM marcas WHERE id = ? AND ativa = 1", (marca_id,)
    ).fetchone()
    if not marca:
        print("Marca não encontrada ou está inativa.")
        return None
    return marca


def cadastrar_marca():
    print("\n--- Cadastrar marca ---")
    nome = ler_texto("Nome")
    ativa = ler_texto("Ativa? (s/n)").lower() == "s"
    try:
        with conectar() as conexao:
            conexao.execute(
                "INSERT INTO marcas (nome, ativa) VALUES (?, ?)",
                (nome, int(ativa)),
            )
        print("Marca cadastrada com sucesso.")
    except sqlite3.IntegrityError:
        print("Já existe uma marca com esse nome.")


def listar_marcas():
    busca = ler_texto("Filtro por nome (Enter para todas)", obrigatorio=False)
    with conectar() as conexao:
        lista = conexao.execute(
            "SELECT * FROM marcas WHERE nome LIKE ? ORDER BY nome",
            (f"%{busca}%",),
        ).fetchall()
    mostrar_marcas(lista)


def editar_marca():
    with conectar() as conexao:
        lista = conexao.execute("SELECT * FROM marcas ORDER BY nome").fetchall()
        mostrar_marcas(lista)
        if not lista:
            return

        marca_id = ler_inteiro("ID da marca")
        marca = conexao.execute(
            "SELECT * FROM marcas WHERE id = ?", (marca_id,)
        ).fetchone()
        if not marca:
            print("Marca não encontrada.")
            return

        nome = ler_texto("Nome", padrao=marca["nome"])
        ativa = ler_texto(
            "Ativa? (s/n)", padrao="s" if marca["ativa"] else "n"
        ).lower() == "s"
        try:
            conexao.execute(
                "UPDATE marcas SET nome = ?, ativa = ? WHERE id = ?",
                (nome, int(ativa), marca_id),
            )
            print("Marca atualizada com sucesso.")
        except sqlite3.IntegrityError:
            print("Já existe uma marca com esse nome.")


def excluir_marca():
    with conectar() as conexao:
        marca_id = ler_inteiro("ID da marca")
        marca = conexao.execute(
            "SELECT * FROM marcas WHERE id = ?", (marca_id,)
        ).fetchone()
        if not marca:
            print("Marca não encontrada.")
            return
        if not confirmar(f"Excluir a marca '{marca['nome']}'?"):
            print("Operação cancelada.")
            return
        try:
            conexao.execute("DELETE FROM marcas WHERE id = ?", (marca_id,))
            print("Marca excluída com sucesso.")
        except sqlite3.IntegrityError:
            print("Não é possível excluir uma marca que possui veículos.")


def menu_marcas():
    while True:
        print(
            """
--- MARCAS ---
1 - Cadastrar
2 - Listar / filtrar
3 - Editar
4 - Excluir
0 - Voltar
"""
        )
        opcao = input("Escolha: ").strip()
        if opcao == "1":
            cadastrar_marca()
        elif opcao == "2":
            listar_marcas()
        elif opcao == "3":
            editar_marca()
        elif opcao == "4":
            excluir_marca()
        elif opcao == "0":
            return
        else:
            print("Opção inválida.")


def dados_novo_veiculo(conexao):
    marcas = conexao.execute(
        "SELECT * FROM marcas WHERE ativa = 1 ORDER BY nome"
    ).fetchall()
    mostrar_marcas(marcas)
    if not marcas:
        print("Cadastre uma marca ativa antes de cadastrar um veículo.")
        return None

    placa = ler_texto("Placa (ex.: ABC1D23)").upper()
    modelo = ler_texto("Modelo")
    ano = ler_inteiro("Ano", minimo=1900, maximo=2100)
    cor = ler_texto("Cor", obrigatorio=False)
    marca_id = ler_inteiro("ID da marca ativa")
    if not escolher_marca_ativa(conexao, marca_id):
        return None
    quilometragem = ler_inteiro("Quilometragem inicial", minimo=0)
    return placa, modelo, ano, cor, marca_id, quilometragem


def cadastrar_veiculo():
    print("\n--- Cadastrar veículo ---")
    with conectar() as conexao:
        dados = dados_novo_veiculo(conexao)
        if dados is None:
            return
        try:
            conexao.execute(
                """INSERT INTO veiculos
                   (placa, modelo, ano, cor, marca_id, quilometragem)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                dados,
            )
            print("Veículo cadastrado com sucesso.")
        except sqlite3.IntegrityError:
            print("Já existe um veículo com essa placa.")


def buscar_veiculo(conexao, veiculo_id):
    return conexao.execute(
        """SELECT v.*, m.nome AS marca_nome, m.ativa AS marca_ativa
           FROM veiculos v JOIN marcas m ON m.id = v.marca_id
           WHERE v.id = ?""",
        (veiculo_id,),
    ).fetchone()


def listar_veiculos():
    busca = ler_texto("Filtro por placa/modelo (Enter para todos)", obrigatorio=False)
    with conectar() as conexao:
        lista = conexao.execute(
            """SELECT v.*, m.nome AS marca_nome, m.ativa AS marca_ativa
               FROM veiculos v JOIN marcas m ON m.id = v.marca_id
               WHERE v.placa LIKE ? OR v.modelo LIKE ?
               ORDER BY v.id""",
            (f"%{busca}%", f"%{busca}%"),
        ).fetchall()
    mostrar_veiculos(lista)


def editar_veiculo():
    with conectar() as conexao:
        lista = conexao.execute(
            """SELECT v.*, m.nome AS marca_nome, m.ativa AS marca_ativa
               FROM veiculos v JOIN marcas m ON m.id = v.marca_id
               ORDER BY v.id"""
        ).fetchall()
        mostrar_veiculos(lista)
        if not lista:
            return

        veiculo_id = ler_inteiro("ID do veículo")
        veiculo = buscar_veiculo(conexao, veiculo_id)
        if not veiculo:
            print("Veículo não encontrado.")
            return

        print("Pressione Enter para manter o valor atual.")
        placa = ler_texto(
            "Placa (ex.: ABC1D23)", padrao=veiculo["placa"]
        ).upper()
        modelo = ler_texto("Modelo", padrao=veiculo["modelo"])
        ano = ler_inteiro("Ano", minimo=1900, maximo=2100, padrao=veiculo["ano"])
        cor = ler_texto("Cor", obrigatorio=False, padrao=veiculo["cor"] or "")
        marcas = conexao.execute(
            "SELECT * FROM marcas WHERE ativa = 1 ORDER BY nome"
        ).fetchall()
        mostrar_marcas(marcas)
        marca_id = ler_inteiro("ID da marca ativa", padrao=veiculo["marca_id"])
        if not escolher_marca_ativa(conexao, marca_id):
            return
        quilometragem = ler_inteiro(
            "Quilometragem", minimo=0, padrao=veiculo["quilometragem"]
        )
        try:
            conexao.execute(
                """UPDATE veiculos SET placa = ?, modelo = ?, ano = ?, cor = ?,
                   marca_id = ?, quilometragem = ? WHERE id = ?""",
                (placa, modelo, ano, cor, marca_id, quilometragem, veiculo_id),
            )
            print("Veículo atualizado com sucesso.")
        except sqlite3.IntegrityError:
            print("Já existe outro veículo com essa placa.")


def excluir_veiculo():
    with conectar() as conexao:
        veiculo_id = ler_inteiro("ID do veículo")
        veiculo = buscar_veiculo(conexao, veiculo_id)
        if not veiculo:
            print("Veículo não encontrado.")
            return
        if not confirmar(f"Excluir o veículo '{veiculo['placa']}'?"):
            print("Operação cancelada.")
            return
        conexao.execute("DELETE FROM veiculos WHERE id = ?", (veiculo_id,))
        print("Veículo excluído com sucesso.")


def registrar_quilometragem():
    with conectar() as conexao:
        veiculo_id = ler_inteiro("ID do veículo")
        veiculo = buscar_veiculo(conexao, veiculo_id)
        if not veiculo:
            print("Veículo não encontrado.")
            return
        print(f"Quilometragem atual: {veiculo['quilometragem']} km")
        nova = ler_inteiro(
            "Nova quilometragem", minimo=veiculo["quilometragem"] + 1
        )
        conexao.execute(
            "UPDATE veiculos SET quilometragem = ? WHERE id = ?",
            (nova, veiculo_id),
        )
        print("Quilometragem registrada com sucesso.")


def menu_veiculos():
    while True:
        print(
            """
--- VEÍCULOS ---
1 - Cadastrar
2 - Listar / filtrar
3 - Editar
4 - Excluir
5 - Registrar quilometragem
0 - Voltar
"""
        )
        opcao = input("Escolha: ").strip()
        if opcao == "1":
            cadastrar_veiculo()
        elif opcao == "2":
            listar_veiculos()
        elif opcao == "3":
            editar_veiculo()
        elif opcao == "4":
            excluir_veiculo()
        elif opcao == "5":
            registrar_quilometragem()
        elif opcao == "0":
            return
        else:
            print("Opção inválida.")


def main():
    criar_tabelas()
    while True:
        print(
            """
==============================
 CRUD DE VEÍCULOS
==============================
1 - Veículos
2 - Marcas
0 - Sair
"""
        )
        opcao = input("Escolha: ").strip()
        if opcao == "1":
            menu_veiculos()
        elif opcao == "2":
            menu_marcas()
        elif opcao == "0":
            print("Até mais!")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
