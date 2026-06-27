# Etapa 2 - Definição da Variável-Alvo (Target)

## Qual variável representa a satisfação do cliente?

A variável-alvo é o **`nps_score`**, a nota de 0 a 10 que o cliente dá após a experiência de
compra. É a tradução direta da satisfação/lealdade em um número, e é exatamente o indicador
que a área de Experiência do Cliente quer entender e antecipar.

A partir dela derivamos duas formas de alvo, conforme a abordagem de modelagem:

- **Regressão:** `nps_score` contínuo (0–10) — estima a *nota*.
- **Classificação:** `is_detractor` = 1 quando `nps_score < 7`, sinaliza o cliente
  **insatisfeito** (detrator) usando a régua oficial do NPS (Detrator 0–6, Neutro 7–8,
  Promotor 9–10).

## Por que ela foi escolhida?

1. **É o KPI da dor.** O problema de negócio é literalmente "o NPS varia e queremos
   antecipá-lo". O alvo precisa *ser* o NPS para que a meta analítica fique alinhada à meta de
   negócio.
2. **Representa lealdade, não só uma transação.** Diferente de um CSAT pontual, o NPS resume a
   disposição de recomendar ligada a recompra, boca a boca e *market share*.
3. **É padronizada e comparável** (0–10, régua universal), o que permite *benchmark* e metas.
4. **Tem variabilidade suficiente para modelar** e se conecta a variáveis operacionais
   acionáveis (entrega, atendimento), permitindo recomendações práticas.

## Em que momento da jornada essa informação é coletada?

O `nps_score` é coletado **no fim da jornada, após a experiência de compra e entrega**
(pesquisa pós-compra). Essa é a justificativa do projeto: por ser **retrospectivo**, o NPS
chega tarde para evitar o detrator. Então a ideia de **prevê-lo a partir de dados operacionais
que existem *antes* da pesquisa** (pedido, logística, atendimento), permitindo ação preventiva.

Essa diferença temporal é o que define quais variáveis podem ou não ser usadas como entrada do
modelo.

## Existe risco de usar essa variável de forma inadequada?

### 1. Vazamento de dados (*data leakage*) o risco mais grave aqui
Usar como *feature* uma variável que só existe **no mesmo momento ou depois** da pesquisa
infla artificialmente o desempenho e quebra o modelo na produção. Dois campos da base são
exatamente isso e foram **excluídos das features**:

- **`repeat_purchase_30d`** — recompra em até 30 dias. É quase determinístico com o NPS na
  base (**0% dos detratores, 100% dos promotores**) e ocorre *depois* do pedido; no momento de
  prever, ainda não aconteceu. É um **co-resultado** da satisfação, não uma causa disponível.
- **`csat_internal_score`** — é, ele próprio, **outra medida de satisfação** colhida em torno
  da pesquisa. Prever satisfação usando satisfação é circular e não estaria disponível antes
  do NPS. Mantido na base para análise, mas **fora** das entradas do modelo preditivo.

### 2. *Proxy* incorreto
Trocar o NPS por um substituto fácil (ex.: número de reclamações) parece prático, mas mede
outra coisa. O alvo deve continuar sendo a satisfação real (NPS), com as demais variáveis como
**explicativas**, não como substitutas do alvo.

### 3. Definição mutante / limiar arbitrário
A fronteira do detrator (`< 7`) precisa ser **fixa e documentada**. Mudar a régra no meio do
projeto invalida comparações. Além disso, o `nps_score` aqui é **contínuo** (com decimais),
enquanto o NPS "de manual" é inteiro — ao categorizar, isso precisa ser explícito e constante.

