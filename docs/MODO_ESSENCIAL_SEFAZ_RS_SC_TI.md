# CONTROLE MESTRE — Modo essencial RS + SC/TI

**Status:** branch de estabilização; não homologada para publicação/merge antes de validação no Windows do titular.

## Decisão do produto

A prioridade passou a ser **utilização diária confiável**, e não quantidade de funcionalidades. O aplicativo deve abrir, permitir lançar sessões e baterias de questões, registrar revisões, mostrar métricas verdadeiras e continuar com o mesmo histórico após fechar, reiniciar e atualizar.

**Não apagar dados, banco, materiais, notas, importações nem migrações já aplicadas.** "Em espera" significa ocultar a funcionalidade experimental da navegação e não desenvolvê-la neste ciclo. Os endpoints/códigos antigos permanecem disponíveis internamente para eventual retomada e testes, mas a experiência essencial não deve depender deles.

## Escopo visível

| Menu | Finalidade |
|---|---|
| Meu painel | Meta semanal, horas e questões reais |
| Foco RS + SC/TI | Roteiro documental de assuntos comuns; consulta read-only |
| Estudar hoje | Registrar estudo efetivo e consultar tarefas |
| Planejamento semanal | Disponibilidade e atividades da semana; sem planejamento cíclico avançado |
| Disciplinas | Consultar conteúdos já cadastrados, sem criar pesos oficiais fictícios |
| Questões e erros | Um único formulário detalhado, histórico e caderno de erros |
| Desempenho | Rendimento real por questões e tempo efetivo |
| Revisões | Fila interna de revisões, sem AnkiConnect obrigatório |
| Histórico | Consultar o que foi registrado |
| Configurações | Meta de horas e avisos de privacidade |

### Recursos em espera na interface

- planejamento por ciclos e microciclos sofisticados;
- execução automática de planos adaptativos e reforços sem validação funcional;
- importação/auditoria automatizada de Bizu/Passo Estratégico, vínculos de PDFs e incidências;
- análises avançadas do AnkiConnect;
- simulados e redações avançados;
- integrações TEC/QConcursos, IA, SaaS e funções comerciais;
- efeitos visuais que atrapalhem leitura, navegação ou desempenho.

**Os módulos, banco e histórico preexistentes NÃO foram deletados.** Os controles avançados podem voltar quando homologados.

## Escopo curricular documental

As fontes usadas para o painel de foco são:

1. Edital SEFAZ-RS 2018, Auditor-Fiscal, item 12.2.
2. Edital SEFAZ-SC 2018, área Tecnologia da Informação (C03), provas 1, 2 e prova 3 de TI.
3. Guia comparado de matérias comuns RS × SC TI, fornecido pelo titular em 12/11/2026.
4. Ranking de 485 blocos, fornecido pelo titular em 12/11/2026.

O painel mostra uma **primeira fila de 20 núcleos**, com índice J de prioridade conjunta. J é o menor P entre RS e SC para os núcleos correspondentes. **Não é porcentagem de chance de cobrança** nem resultado de análise estatística de questões reais.

Primeira fase de estudo: núcleo comum de Contabilidade Geral, Direito Tributário, Constitucional, Administrativo, Civil, Empresarial, Penal, Português, TI e Lógica. Os conteúdos comuns por abrangência devem ser estudados somente na interseção demonstrada; exclusivos estaduais ficam em espera, não são excluídos.

As 25 horas semanais do roteiro são **proposta**, não pesos oficiais: 5 h Contabilidade, 5 h Tributário, 3 h Constitucional, 3 h Administrativo, 3 h TI, 2 h Português, 3 h Civil/Empresarial/Penal e 1 h Lógica. O bloco de Tributário deve incluir uma parcela separada para atualização/reforma.

**Aviso decisivo:** essa fase compartilhada não prepara integralmente para nenhum dos dois concursos. No edital de SC/TI de 2018, TI representou 36% e Legislação Tributária I e II somadas 28% dos pontos; esses percentuais são históricos e não representam uma distribuição confirmada para edital futuro. Quando houver novo edital, ajustar o foco.

## Persistência dos dados

- A fonte de verdade continua sendo o banco SQLite existente (variável `CONTROLE_MESTRE_DB` quando fornecida).
- No Windows, o caminho persistente preferencial é `%LOCALAPPDATA%\ControleMestre\dados\controle_mestre.db`.
- Se ainda não existir banco nesse caminho, mas existir o banco antigo `dados/controle_mestre.db` junto ao código, o inicializador preserva a escolha do banco antigo.
- **Se os dois existirem**, a precedência é do banco persistente do Windows. Antes de usar, verifique o caminho exibido no diagnóstico e indique `CONTROLE_MESTRE_DB` explicitamente para escolher outra base. Não faça mesclagem automática.
- Backup SQLite consistente antes da inicialização/migração, com teste `PRAGMA quick_check` pelo módulo `backup_manager.py`.
- Nenhuma atualização desta branch move, converte ou exclui arquivos do usuário.

## Portão obrigatório para liberar uma versão

1. GitHub Actions: todas as suítes Python 3.11 e 3.13 passam; sintaxe ES dos módulos carrega.
2. Inicializador: `py -3 launch.py --diagnostico` exibe o **caminho correto do banco** e passa sem falhas.
3. Browser Windows: abrir o painel e verificar navegação, textos, campos e ausência de erros graves no Console.
4. Criar sessão real de estudo; fechar e reabrir; confirmar sessão e horas.
5. Criar uma bateria de 10 questões (ex.: 8 acertos); fechar e reabrir; confirmar exatamente uma linha no histórico.
6. Criar e retomar um rascunho individual; completar; garantir nenhuma contagem duplicada.
7. Gerar plano semanal; editar dia; concluir tarefa; verificar que não adiciona horas sem sessão.
8. Verificar revisão, desempenho por matéria e ausência de divisão por zero ou dados inventados.
9. Criar backup, verificar backup e testar restauração para um **banco temporário**.
10. Validar navegação com banco antigo real do proprietário **sem enviar o banco ao GitHub**.

**Nenhum merge, anúncio de "100%" nem uso como release oficial antes dos 10 itens.** Se algum item falhar, corrigir somente a falha; não iniciar outra funcionalidade.

## Continuidade do projeto

Com esse modo estabilizado, a fase seguinte será a importação **controlada e verificável** do edital verticalizado RS × SC/TI, aproveitando as classificações D (comum direto), A (por abrangência parcial) e N (exclusivo). Toda importação será primeiro simulada; nenhum dado do usuário será reescrito silenciosamente.
