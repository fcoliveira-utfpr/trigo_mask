# Proposta de mapeamento anual do trigo no Brasil com glebas do SICOR e séries temporais de sensoriamento remoto

**Responsável:** Prof. Dr. Fabrício Correia de Oliveira (UTFPR – Campus Santa Helena, GAMBI-TEC)
**Documento:** planejamento interno de pesquisa (versão 1)
**Relação com outros trabalhos:** a máscara e a fenologia do trigo são pré-requisito para a futura replicação de Cao et al. (2026) em trigo no Brasil (ver `planejamento1.md`)

---

## 1. Contexto e justificativa

O mapeamento anual de culturas é a base para o monitoramento da produção, para a estimativa de produtividade por sensoriamento remoto e para modelos de produtividade em escala municipal. No Brasil, os mapeamentos anuais de cobertura e uso da terra representam bem as culturas de verão, como a soja. Até o conhecimento dos autores, porém, não há classe específica de trigo nas coleções do MapBiomas; as culturas de inverno são agregadas em classes genéricas de lavouras temporárias. Esse ponto deve ser confirmado na coleção vigente.

O mapeamento do trigo no Brasil tem dificuldades próprias, distintas das descritas para o trigo de inverno no norte da China (DONG et al., 2020; XU et al., 2020; LIU et al., 2022):

- **Não há dormência nem neve.** O duplo pico do índice de vegetação, explorado nos métodos chineses, não ocorre. A curva tem um único pico.
- **Os confundidores são outros cereais de inverno.** Aveia preta (cobertura de solo), aveia branca, cevada e triticale têm assinatura espectral e calendário semelhantes aos do trigo.
- **A nebulosidade de inverno é alta no Sul**, associada à passagem de frentes frias.
- **O fundo é palha.** Em plantio direto, o trigo emerge sobre a palhada da cultura de verão.
- **Há três sistemas distintos:** sequeiro subtropical no Sul, sequeiro no Cerrado e irrigado por pivô no Cerrado.

A principal limitação dos trabalhos anteriores, a escassez de rótulos de campo, pode ser contornada no Brasil com as glebas georreferenciadas do Sistema de Operações do Crédito Rural e do Proagro (SICOR). Desde a Resolução nº 4.427/2015 do Banco Central, o registro de operações de custeio agrícola inclui a cultura financiada, a área financiada e as coordenadas geodésicas da área (BANCO CENTRAL DO BRASIL, 2015). As geometrias são disponibilizadas nas tabelas de crédito rural e Proagro do Banco Central, ainda que apenas para parte das operações.

**Hipótese principal:** o uso combinado de glebas do SICOR como rótulos, compósitos por fase fenológica e variáveis sensíveis à senescência permite mapear o trigo no Brasil com acurácia comparável à dos mapeamentos chineses, separando-o das aveias. A separação em relação à cevada é a etapa de maior incerteza.

---

## 2. Objetivos

### 2.1 Objetivo geral

Desenvolver e validar um método de mapeamento anual do trigo no Brasil, com produtos de máscara, probabilidade de classe e datas fenológicas para as safras de 2000 a 2025.

### 2.2 Objetivos específicos

- Construir uma base de rótulos de trigo e de outras culturas de inverno a partir das glebas do SICOR, com filtros de qualidade e partição espacial.
- Quantificar a separabilidade entre o trigo e as demais classes em cada fase fenológica, por estrato agroclimático.
- Desenvolver classificadores com compósitos por fase (Landsat + Sentinel-2) e com similaridade de séries temporais (TWDTW e PT-DTW adaptado).
- Estabelecer a transferência temporal do classificador para as safras anteriores às glebas (2000 a 2018).
- Extrair as datas fenológicas (emergência, pico e maturação) dentro da máscara.
- Validar os mapas por gleba e por área municipal, incluindo safras com estresse por seca ou geada.

---

## 3. Área de estudo e estratificação

| Estrato | Estados | Sistema | Observação |
|---|---|---|---|
| S1, Sul subtropical | PR, RS, SC | Sequeiro | Maior área; confusão com aveias e cevada |
| S2, Sudeste e Centro-Oeste de transição | SP, MS | Sequeiro | Área menor |
| S3, Cerrado sequeiro | MG, GO, DF, BA | Sequeiro | Trigo tropical, semeadura após a soja |
| S4, Cerrado irrigado | MG, GO, DF, BA | Irrigado (pivô) | Separação por máscara de pivôs da ANA |

As janelas fenológicas de cada estrato serão definidas pelo calendário do ZARC e por informações da Embrapa Trigo, e refinadas pelas próprias séries de imagens: [INSERIR JANELAS POR ESTRATO].

---

## 4. Dados

| Dado | Fonte | Período | Uso |
|---|---|---|---|
| Glebas de crédito rural | SICOR, tabelas de crédito rural e Proagro (BCB) | Anos com glebas disponíveis | Rótulos de treino e validação |
| Área plantada e colhida de trigo, aveia e cevada | IBGE/PAM | 2000–2025 | Validação de área e restrição de proporção |
| Máscara agrícola | MapBiomas (agricultura, soja, pastagem) | 2000–2025 | Restrição do domínio de classificação |
| Sentinel-2 SR | Copernicus (GEE) | 2017–2025 | Compósitos de 10–20 m e red-edge |
| HLS (Landsat + Sentinel-2 harmonizados) | NASA (GEE) | Período disponível | Compósitos de 30 m (CLAVERIE et al., 2018) |
| Landsat 5/7/8/9 Collection 2 SR | USGS (GEE) | 2000–2025 | Retroação a 30 m |
| MODIS MOD13Q1 | NASA | 2000–2025 | Retroação a 250 m e fração de trigo |
| Sentinel-1 GRD | Copernicus (GEE) | 2015–2025 | Opcional, preenchimento em períodos nublados |
| Pivôs centrais | ANA | Mapeamentos disponíveis | Separação de S4 |
| Calendário agrícola | ZARC/MAPA, Embrapa Trigo | — | Janelas por fase |
| Relevo | SRTM | — | Variáveis auxiliares |

---

## 5. Classes

| Classe | Fonte do rótulo |
|---|---|
| Trigo | Glebas SICOR (produto trigo) |
| Aveia (preta e branca) | Glebas SICOR (produto aveia) |
| Cevada | Glebas SICOR (produto cevada) |
| Triticale e outras de inverno (incluindo canola) | Glebas SICOR, quando disponíveis |
| Pousio ou palhada no inverno | Pixels de soja do MapBiomas sem ciclo de inverno |
| Pastagem, floresta, área urbana, água | MapBiomas (amostragem estratificada) |

Classe final de saída: trigo / não trigo, com probabilidade. Mapa auxiliar: "cereais de inverno" (trigo + cevada + triticale), caso a separação trigo × cevada não alcance acurácia aceitável.

---

## 6. Metodologia

### (i) Curadoria das glebas

1. Seleção das operações de custeio com produto trigo, aveia, cevada, triticale ou canola, por ano-safra.
2. Remoção de geometrias inválidas, duplicadas ou sobrepostas entre produtos no mesmo ano.
3. Remoção de glebas com área inferior a [INSERIR, ex.: 2 ha].
4. Buffer negativo de [INSERIR, ex.: 20–30 m] para evitar pixels de borda.
5. **Filtro de coerência temporal:** descarte das glebas sem ciclo de inverno no perfil de NDVI/EVI (área financiada e não semeada, ou semeada com outra cultura).
6. Uso exclusivo da geometria, do produto e do ano-safra, sem qualquer dado de identificação de beneficiários.
7. Partição em treino, validação e teste por blocos espaciais (ROBERTS et al., 2017), para evitar glebas vizinhas em conjuntos diferentes.

Como a cobertura das glebas é parcial e concentrada em operações com recursos públicos, a representatividade será avaliada comparando a distribuição de tamanho das glebas e a área por município com o IBGE.

### (ii) Pré-processamento e compósitos por fase

Máscara de nuvens com Cloud Score+ (Sentinel-2) e QA_PIXEL (Landsat). Para cada estrato, as imagens serão agregadas pela mediana em fases fenológicas, conforme Xu et al. (2020): estabelecimento, perfilhamento, alongamento, espigamento, enchimento e maturação. Em paralelo, serão gerados compósitos de 10 dias com suavização Savitzky–Golay (CHEN et al., 2004), para os métodos de similaridade de séries.

### (iii) Variáveis

Bandas espectrais, NDVI, EVI, SAVI, NDRE (red-edge, apenas Sentinel-2), LSWI, e dois índices adicionais.

O NDPI, que reduz a influência do fundo (CHEN et al., 2019; DONG et al., 2020), será testado aqui pelo fundo de palhada:

$$
NDPI = \frac{\rho_{NIR} - \left[\alpha\,\rho_{R} + (1-\alpha)\,\rho_{SWIR}\right]}{\rho_{NIR} + \left[\alpha\,\rho_{R} + (1-\alpha)\,\rho_{SWIR}\right]} \qquad \text{(eq. 1)}
$$

em que: $\rho_{NIR}$, $\rho_{R}$ e $\rho_{SWIR}$ são as reflectâncias no infravermelho próximo, no vermelho e no infravermelho de ondas curtas (adimensional); $\alpha$ é o peso do vermelho (adimensional, 0,74).

O PSRI, sensível à senescência, foi incluído porque a maturação é a fase mais importante na separação do trigo em relação à aveia de cobertura, que costuma ser dessecada sem amadurecer (XU et al., 2020; MERZLYAK et al., 1999):

$$
PSRI = \frac{\rho_{R} - \rho_{B}}{\rho_{RE2}} \qquad \text{(eq. 2)}
$$

em que: $\rho_{B}$ é a reflectância no azul e $\rho_{RE2}$ no red-edge (banda 6 do Sentinel-2) (adimensional).

Serão também extraídas métricas fenológicas: amplitude, data do pico, taxa de subida, taxa de queda e integral do ciclo de inverno.

### (iv) Separabilidade por fase

A distância de Jeffries-Matusita (J-M) entre o trigo e cada classe será calculada por fase e por estrato, como em Liu et al. (2022):

$$
JM_{ij} = 2\left(1 - e^{-B_{ij}}\right) \qquad \text{(eq. 3)}
$$

$$
B_{ij} = \frac{1}{8}(\mathbf{m}_i - \mathbf{m}_j)^T \left(\frac{\boldsymbol{\Sigma}_i + \boldsymbol{\Sigma}_j}{2}\right)^{-1}(\mathbf{m}_i - \mathbf{m}_j) + \frac{1}{2}\ln\!\left(\frac{\left|\frac{\boldsymbol{\Sigma}_i + \boldsymbol{\Sigma}_j}{2}\right|}{\sqrt{|\boldsymbol{\Sigma}_i|\,|\boldsymbol{\Sigma}_j|}}\right) \qquad \text{(eq. 4)}
$$

em que: $JM_{ij}$ é a distância de Jeffries-Matusita entre as classes $i$ e $j$ (0 a 2); $B_{ij}$ é a distância de Bhattacharyya; $\mathbf{m}_i$ e $\mathbf{m}_j$ são os vetores de médias das variáveis; $\boldsymbol{\Sigma}_i$ e $\boldsymbol{\Sigma}_j$ são as matrizes de covariância.

Resultado esperado: uma tabela fase × classe × estrato que define objetivamente quais fases e variáveis entram no classificador e se a separação trigo × cevada é viável.

### (v) Classificação

| Código | Classificador | Entrada | Referência |
|---|---|---|---|
| C1 | Random Forest | Compósitos por fase + índices + métricas fenológicas | Xu et al. (2020); Liu et al. (2022) |
| C2 | TWDTW | Séries de 10 dias de NDVI ou NDPI, curvas de referência por estrato | Maus et al. (2016) |
| C3 | PT-DTW adaptado | Como C2, com peso maior na subida pós-emergência e na senescência | Dong et al. (2020) |
| C4 (opcional) | Rede temporal (LSTM ou TempCNN) | Séries de 10 dias | — |

A penalidade temporal logística do TWDTW será mantida (MAUS et al., 2016):

$$
\omega_{ij} = \frac{1}{1 + e^{-a\,(|t_i - t_j| - b)}} \qquad \text{(eq. 5)}
$$

em que: $\omega_{ij}$ é o peso de penalidade entre as datas $t_i$ e $t_j$ (adimensional); $a$ é a declividade e $b$ o ponto médio da função logística (dias). Diferentemente de Dong et al. (2020), $a$ e $b$ serão ajustados com as glebas.

No PT-DTW adaptado, os dois períodos com peso maior deixam de ser "crescimento antes do inverno" e "queda após o espigamento" e passam a ser a subida após a emergência e a senescência, definidas por estrato. Em todos os classificadores será exportada a probabilidade (ou distância) por pixel, e não apenas a classe.

### (vi) Retroação para 2000 a 2018

As safras sem glebas serão mapeadas por três estratégias:

- C1 treinado com as safras recentes e aplicado a compósitos Landsat harmonizados, considerando as falhas do Landsat 7 SLC-off;
- C2/C3 com curvas de referência das safras recentes, aproveitando a transferência entre anos sem retreino observada por Dong et al. (2020);
- uma versão a 250 m com MODIS, que estima a fração de trigo por pixel, para consistência da série completa.

A transferência será testada simulando a ausência de rótulos nas safras recentes: treino em um subconjunto de anos e teste nos demais.

### (vii) Fenologia

Dentro da máscara, serão extraídas as datas de emergência, pico e maturação pelo limiar de amplitude (eq. 1 do `planejamento1.md`) e pelo alinhamento do DTW em relação à curva de referência, com datas conhecidas. As datas serão comparadas com as janelas do ZARC e, quando houver, com observações de campo da Embrapa Trigo ou de cooperativas.

### (viii) Validação

**Por pixel e por gleba:** acurácia global, acurácias do produtor e do usuário e F1, nas glebas de teste por bloco espacial e em pontos de interpretação visual independentes.

**Por área:** estimativa da área com correção do viés de classificação por amostragem estratificada (OLOFSSON et al., 2014):

$$
\hat{A}_k = A_{tot} \sum_{h} W_h \frac{n_{hk}}{n_{h\cdot}} \qquad \text{(eq. 6)}
$$

em que: $\hat{A}_k$ é a área estimada da classe $k$ (ha); $A_{tot}$ é a área total mapeada (ha); $W_h$ é a proporção de área do estrato de mapa $h$ (adimensional); $n_{hk}$ é o número de amostras do estrato $h$ com classe de referência $k$; $n_{h\cdot}$ é o total de amostras do estrato $h$.

**Contra o IBGE:** área municipal mapeada contra a área plantada do IBGE/PAM por ano, com R², MAE e viés. A análise será estratificada em safras normais e em safras com seca ou geada.

---

## 7. Experimentos

| Código | Pergunta | Comparação |
|---|---|---|
| E1 | Combinar sensores melhora o mapa? | Sentinel-2 contra Landsat contra HLS/combinação |
| E2 | Quais fases são necessárias? | Fase única contra combinações de fases, guiadas pela J-M |
| E3 | Qual índice separa melhor? | NDVI contra EVI contra NDPI contra PSRI |
| E4 | Qual classificador? | C1 contra C2 contra C3 (contra C4) |
| E5 | O método transfere no tempo? | Treino em anos A, teste em anos B, sem retreino |
| E6 | O método transfere no espaço? | Treino em S1, teste em S3; e vice-versa |
| E7 | Há omissão de trigo estressado? | Erro de omissão e viés de área em safras com seca ou geada |
| E8 | Qual o efeito do ruído dos rótulos? | Com e sem o filtro de coerência temporal; com ruído artificial de [INSERIR %] |
| E9 | Trigo × cevada é separável? | J-M e F1 por par de classes; decisão entre mapa de trigo e mapa de cereais de inverno |

O E7 é crítico para o uso posterior em modelos de produtividade. Se o trigo estressado for omitido nas safras ruins, a máscara retém apenas os talhões em boas condições, e os índices agregados por município ficam otimistas, enviesando os modelos de produtividade que usam essa máscara.

---

## 8. Produtos

- Mapas anuais de trigo (30 m na série completa; 10 m a partir de 2017) e de probabilidade, como assets no GEE.
- Tabela municipal anual com área mapeada, área corrigida (eq. 6), fração de trigo e datas fenológicas medianas.
- Código aberto no GitHub (`fcoliveira-utfpr`).
- Artigo metodológico (candidatos: *Remote Sensing of Environment*, *International Journal of Applied Earth Observation and Geoinformation*, *Remote Sensing*) e, posteriormente, artigo de dados (candidato: *Earth System Science Data*).

---

## 9. Riscos e mitigação

| Risco | Efeito | Mitigação |
|---|---|---|
| Glebas com cultura diferente da financiada | Rótulos ruidosos | Filtro de coerência temporal; E8 |
| Cobertura parcial e enviesada das glebas | Amostra não representativa | Comparação com o IBGE; amostras complementares por interpretação visual |
| Confusão com aveias e cevada | Superestimação da área | Fase de maturação e PSRI; mapa de cereais de inverno como alternativa |
| Nebulosidade de inverno | Compósitos com falhas | Agregação por fase; Sentinel-1 opcional |
| Landsat 7 SLC-off e baixa revisita antes de 2013 | Retroação degradada | Versão MODIS a 250 m; TWDTW com tolerância a falhas |
| Trigo estressado omitido | Viés para os modelos de produtividade | E7; exportação da probabilidade; limiar ajustado por safra |
| Pequena área no Cerrado | Poucos rótulos em S3 e S4 | Agregação de anos; transferência a partir de S1 (E6) |

---

## 10. Cronograma

| Atividade | T1 | T2 | T3 | T4 | T5 | T6 |
|---|---|---|---|---|---|---|
| (i) Download e curadoria das glebas do SICOR | X | | | | | |
| (ii) Compósitos e variáveis no GEE | X | X | | | | |
| (iii) Separabilidade J-M por fase e estrato | | X | | | | |
| (iv) Classificadores C1–C3 e experimentos E1–E4 | | X | X | | | |
| (v) Transferência temporal e espacial (E5, E6) | | | X | X | | |
| (vi) Retroação 2000–2018 e fenologia | | | | X | X | |
| (vii) Validação por área, E7–E9 | | | | X | X | |
| (viii) Redação dos artigos e publicação dos dados | | | | | X | X |

T = trimestre.

---

## Referências

BANCO CENTRAL DO BRASIL. **Resolução nº 4.427, de 25 de junho de 2015**. Autoriza a utilização do sensoriamento remoto para fins de fiscalização de operações de crédito rural e determina o registro das coordenadas geodésicas do empreendimento financiado no Sicor. Brasília: BCB, 2015.

CAO, B. et al. Physics-guided deep learning for crop yield estimation. **European Journal of Agronomy**, v. 172, 127850, 2026. DOI: 10.1016/j.eja.2025.127850.

CHANG, Z. et al. Crop type identification using high-resolution remote sensing images based on an improved DeepLabV3+ network. **Remote Sensing**, v. 15, 5088, 2023. DOI: 10.3390/rs15215088.

CHEN, J. et al. A simple method for reconstructing a high-quality NDVI time-series data set based on the Savitzky–Golay filter. **Remote Sensing of Environment**, v. 91, p. 332-344, 2004.

CHEN, X. et al. Replacing the red band with the red-SWIR band (0.74ρred+0.26ρswir) can reduce the sensitivity of vegetation indices to soil background. **Remote Sensing**, v. 11, 851, 2019.

CLAVERIE, M. et al. The Harmonized Landsat and Sentinel-2 surface reflectance data set. **Remote Sensing of Environment**, v. 219, p. 145-161, 2018.

DONG, Q. et al. Mapping winter wheat in North China using Sentinel 2A/B data: a method based on phenology-time weighted dynamic time warping. **Remote Sensing**, v. 12, 1274, 2020. DOI: 10.3390/rs12081274.

LIU, S. et al. The accuracy of winter wheat identification at different growth stages using remote sensing. **Remote Sensing**, v. 14, 893, 2022. DOI: 10.3390/rs14040893.

MAUS, V. et al. A time-weighted dynamic time warping method for land-use and land-cover mapping. **IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing**, v. 9, p. 3729-3739, 2016.

MERZLYAK, M. N. et al. Non-destructive optical detection of pigment changes during leaf senescence and fruit ripening. **Physiologia Plantarum**, v. 106, p. 135-141, 1999.

OLOFSSON, P. et al. Good practices for estimating area and assessing accuracy of land change. **Remote Sensing of Environment**, v. 148, p. 42-57, 2014.

ROBERTS, D. R. et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. **Ecography**, v. 40, p. 913-929, 2017.

XU, F. et al. Mapping winter wheat with combinations of temporally aggregated Sentinel-2 and Landsat-8 data in Shandong Province, China. **Remote Sensing**, v. 12, 2065, 2020. DOI: 10.3390/rs12122065.

> Observação: as referências devem ser conferidas (volume, páginas e DOI) antes do uso em texto submetido. A disponibilidade e o formato atuais das glebas do SICOR e das classes do MapBiomas devem ser verificados antes do início da etapa (i).
