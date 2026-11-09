# CONTROLE MESTRE — Inteligência curricular v0.8.8 (candidata)

## Regra de negócio
**Incidência histórica** é a frequência extraída de fonte com documento, página e metodologia quando disponíveis. **Prioridade 1–10** é uma sugestão pedagógica, não um percentual da banca.

- Incidência documentada: até 40% do índice, valor normalizado por `min(incidencia/30,1)`.
- Lacuna de rendimento: até 35%, com pelo menos 10 questões no assunto, `1-acertos/total`.
- Progresso registrado: até 15%, `1-progresso/100`.
- Peso da disciplina: até 10%, `peso/10`.

Os fatores ausentes são ignorados, com pesos restantes renormalizados. Apenas peso de disciplina não cria nota; retorna «não calculada». Prioridade manual sempre prevalece. Valores manuais da antiga escala 1–5 permanecem sem conversão silenciosa.

A recomendação só adiciona conteúdo ao ciclo após a escolha do ciclo e confirmação explícita do usuário. Um marcador planejado não aumenta horas líquidas.

## Fontes locais de incidência
A tabela SQLite `curriculum_evidence` armazena assunto, disciplina, percentual opcional, comentário qualitativo, material, referência do documento, página, banca, período, amostra, trecho curto e sinal de auditoria. Apenas registros verificados entram no cálculo. Fontes verificadas com percentuais divergentes são sinalizadas e não agregadas.

## Handoff para Antigravity no Windows

1. Usar o projeto e o banco ativos em `%LOCALAPPDATA%\ControleMestre`; conferir `versao_instalada.json` e fazer backup SQLite consistente.
2. Localizar os PDFs particulares e os links catalogados, incluindo materiais externos. Não alterar nem mover PDFs.
3. Ler título, índice e cabeçalho dos PDFs para identificar **disciplina, aula, assunto e subassunto**; uma aula pode conter múltiplos assuntos, e um assunto pode pertencer a várias aulas. NÃO identificar disciplina apenas por `curso-xxxx` nem vincular Bizu à teoria só por `Aula 03`.
4. Auditar páginas dos Bizus/Passos. Percentuais só podem ser registrados quando explícitos. Relevância apenas qualitativa continua qualitativa. Associar banca, período e tamanho de amostra apenas se a fonte informar.
5. Preparar arquivo JSON privado e local no formato:
```json
{"evidences":[{
  "subject":"Direito Tributário",
  "topic":"Obrigação tributária",
  "incidence_pct":null,
  "qualitative":"Relevância descrita sem percentual",
  "material_type":"Passo Estratégico",
  "document_reference":"C:\\CAMINHO_LOCAL\\AULA.pdf",
  "page":5,
  "bank":"",
  "sample_period":"",
  "sample_count":null,
  "excerpt":"Trecho curto literalmente presente na página"
}]}
```
O JSON é apenas exemplo de **formato**, sem representar dado factual extraído.
6. Inspecionar sem gravar:
   `py -3 local_curriculum_import.py "C:\\CAMINHO\\incidencias_local.json"`
7. Registrar pendências sem aprovação:
   `py -3 local_curriculum_import.py "C:\\CAMINHO\\incidencias_local.json" --apply`
8. Aprovar apenas dados cujo arquivo, página e trecho conferem com o PDF, com PyMuPDF disponível e confirmação expressa:
   `py -3 local_curriculum_import.py "C:\\CAMINHO\\incidencias_local.json" --apply --approve`
9. O importador cria backup SQLite consistente antes de gravar. Quando a origem for imagem sem texto, marcar pendente de revisão humana, sem OCR automático.
10. Conferir as abas **Disciplinas**, **Meu guia e incidências** e **Planejamento → Por ciclos**, incluindo sugestão explicável de prioridade e inclusão manual.
11. Rodar testes Python/JS, reiniciar servidor, validar persistência. Nunca enviar banco, PDF, histórico, JSON privado ou credenciais ao GitHub.
12. Só publicar v0.8.8 no `versao_oficial.json` após validar a revisão no Windows; usar SHA imutável e o atualizador permanente.

## Limites
A leitura dos PDFs do proprietário requer Antigravity local; até essa etapa, nem todos os assuntos estarão classificados. Ausência de percentual não é zero. A pontuação calculada não equivale à previsão de questões da próxima prova.

## Importação de sumários com múltiplos assuntos

Para cada PDF já catalogado na tabela `study_materials`, o agente local poderá construir **uma linha por assunto/subassunto**. A relação é muitos-para-muitos e não altera o campo antigo `study_materials.topic`.

Exemplo estrutural, **sem representar PDF efetivamente lido**:

```json
{"topic_links": [
  {"material_id":123, "subject":"Direito Tributário",
   "topic":"Obrigação tributária", "subtopic":"Sujeito passivo",
   "lesson":"Aula 03", "page_from":5,"page_to":8,
   "excerpt":"Sujeito passivo da obrigação tributária"},
  {"material_id":123, "subject":"Direito Tributário",
   "topic":"Crédito tributário", "subtopic":"Lançamento",
   "lesson":"Aula 03", "page_from":18,"page_to":24,
   "excerpt":"Lançamento tributário"}
]}
```

**Passos locais:**
1. Localizar ID de cada PDF na biblioteca do CONTROLE MESTRE e conferir o nome/caminho original.
2. Executar **simulação**: `py -3 local_curriculum_topics.py "C:\\CAMINHO\\assuntos_locais.json"`.
3. Persistir como **pendente**: `py -3 local_curriculum_topics.py "C:\\CAMINHO\\assuntos_locais.json" --apply`.
4. Após confirmar páginas e trechos com o próprio PDF: `py -3 local_curriculum_topics.py "C:\\CAMINHO\\assuntos_locais.json" --apply --approve`.
5. Conferir a tela de Disciplinas e Guia: cada assunto aparece com subassunto e botão do mesmo PDF. O importador preserva o histórico e cria backup antes de gravar.

Os caminhos e dados privados ficam **somente** no computador. Se a disciplina presente no banco divergir daquela proposta no JSON, o importador bloqueia o vínculo para revisão, em vez de sobrescrever.
