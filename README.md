# CONTROLE MESTRE

Plataforma de planejamento e controle inteligente de estudos.

## Referência histórica

O projeto retoma a plataforma anterior apresentada pelo canal **Atrator Concursos** em 18/09/2023: [PLATAFORMA CONTROLE MESTRE](https://youtu.be/NAwtZ3KIxao). A descrição pública apresenta planejamento semanal, adaptação à rotina, metas diárias, estudos guiados, revisões, simulados, redações, desempenho por tópico e apostilas de apoio. O vídeo foi identificado por seus metadados; não houve auditoria visual de todas as telas.

## Versão atual: v0.1 (MVP pessoal)

- **Streamlit + Python + SQLite**: execução local e monousuário.
- Metas semanais, cronômetro, ciclos de 1 a 10, questões, erros e revisões.
- Importação manual de Excel e CSV agregado do Anki.
- Planejamento por pesos de disciplinas e disponibilidade diária.
- Métricas calculadas sobre dados efetivamente registrados, não estimativas históricas.

**Ainda não existe** sincronização automática com Anki, autenticação, isolamento multiusuário, aplicação hospedada segura nem cobrança de assinatura.

## Como executar

Instale Python 3.11+ e rode:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py --server.address 127.0.0.1
```

Também há lançadores para Windows e Linux/macOS. O banco é criado localmente em `dados/controle_mestre.db`. Sem a base pessoal, as disciplinas padrão são cadastradas, mas os históricos começam vazios. Importe os arquivos próprios via interface.

## Privacidade e propriedade intelectual

**O repositório está público.** Nunca commitar bancos SQLite, planilhas, históricos de estudo/Anki, arquivos protegidos por direitos autorais, credenciais, segredos ou backups pessoais. O `.gitignore` cobre os formatos e diretórios locais mais frequentes. Para comercialização proprietária, considere tornar o repositório privado.

Esta versão **não deve ser publicada na internet para usuários externos**: ainda não possui autenticação nem separação segura de dados.

Consulte [PLANO_DE_EVOLUCAO_E_NEGOCIO.md](PLANO_DE_EVOLUCAO_E_NEGOCIO.md) para a estratégia de evolução e lançamento.

© Titular do projeto — todos os direitos reservados, salvo licença expressa futura.
