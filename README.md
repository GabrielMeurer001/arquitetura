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
