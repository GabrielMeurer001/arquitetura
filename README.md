# CRUD de veículos no terminal

Aplicação simples em Python usando apenas a biblioteca padrão e SQLite.

## Executar

```bash
python app.py
```

O banco `veiculos.db` é criado automaticamente na primeira execução.

## Funcionalidades

- CRUD de marcas, com filtro e status ativa/inativa;
- CRUD de veículos, com filtro por placa ou modelo;
- cadastro e edição da placa do veículo;
- vínculo do veículo somente com marca ativa;
- registro de quilometragem, aceitando apenas valor maior que o atual;
- exclusão de marca bloqueada quando existem veículos vinculados.

## API REST (para testar no Postman)

```bash
pip install -r requirements.txt
python api.py
```

A API sobe em `http://127.0.0.1:5000`. Importe o arquivo `postman_collection.json` no Postman
(File > Import) para ter todas as requisições prontas.

Endpoints:

- `GET /marcas?busca=` — listar/filtrar marcas
- `POST /marcas` — cadastrar marca (`{ "nome": "...", "ativa": true }`)
- `GET /marcas/<id>` — obter marca
- `PUT /marcas/<id>` — editar marca
- `DELETE /marcas/<id>` — excluir marca
- `GET /veiculos?busca=` — listar/filtrar veículos
- `POST /veiculos` — cadastrar veículo (`placa`, `modelo`, `ano`, `cor`, `marca_id`, `quilometragem`)
- `GET /veiculos/<id>` — obter veículo
- `PUT /veiculos/<id>` — editar veículo
- `DELETE /veiculos/<id>` — excluir veículo
- `POST /veiculos/<id>/quilometragem` — registrar quilometragem (`{ "quilometragem": 15000 }`)
