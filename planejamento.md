# Proposta de mapeamento anual do trigo no Brasil com glebas do SICOR e séries temporais de sensoriamento remoto

**Responsável:** Prof. Dr. Fabrício Correia de Oliveira (UTFPR – Campus Santa Helena, GAMBI-TEC)
**Documento:** planejamento interno de pesquisa (versão 3: inclusão da metodologia do radar Sentinel-1)
**Relação com outros trabalhos:** a máscara e a fenologia do trigo são pré-requisito para a futura replicação de Cao et al. (2026) em trigo no Brasil (ver `planejamento1.md`)

---

## Resumo

O objetivo deste projeto será desenvolver e validar um método de mapeamento anual do trigo no Brasil para as safras de 2000 a 2025, com produtos de máscara, probabilidade de classe e datas fenológicas. O método combina quatro elementos: a delimitação prévia do domínio de mapeamento pela Produção Agrícola Municipal (PAM/IBGE); o uso das glebas georreferenciadas do crédito rural (SICOR) como rótulos; a seleção objetiva de fases fenológicas e de variáveis; e a comparação entre classificadores baseados em compósitos por fase e em similaridade de séries temporais. A hipótese principal é que variáveis sensíveis à senescência e à umidade do dossel, extraídas de compósitos alinhados à emergência, permitem separar o trigo das aveias com F1 igual ou superior a [INSERIR, ex.: 0,85], enquanto a separação em relação à cevada exige informação espacial a priori. Para contornar a nebulosidade de inverno no Sul, as séries ópticas serão combinadas com séries de retroespalhamento do radar Sentinel-1, processadas como dados prontos para análise (correção do relevo, normalização angular e filtragem multitemporal do *speckle*). Do radar serão usadas variáveis por fase, métricas da estrutura do dossel e a detecção da colheita, que distingue o trigo colhido da aveia de cobertura dessecada. Os produtos serão disponibilizados como assets no Google Earth Engine, tabelas municipais e código aberto, e servirão de base para modelos de produtividade do trigo em escala municipal.

**Palavras-chave:** trigo; crédito rural; Sentinel-2; Sentinel-1; radar de abertura sintética; séries temporais; cereais de inverno

---

## 1. Introdução e justificativa

O mapeamento anual de culturas é a base para o monitoramento da produção, para a estimativa de produtividade por sensoriamento remoto e para modelos de produtividade em escala municipal. No Brasil, os mapeamentos anuais de cobertura e uso da terra representam bem as culturas de verão, como a soja. Até o conhecimento dos autores, porém, não há classe específica de trigo nas coleções do MapBiomas; as culturas de inverno são agregadas em classes genéricas de lavouras temporárias. Esse ponto deve ser confirmado na coleção vigente.

A literatura sobre mapeamento do trigo concentra-se no trigo de inverno do Hemisfério Norte, sobretudo na China. Os trabalhos convergem em quatro pontos: o Random Forest é o classificador mais empregado; Sentinel-2 e Landsat são os sensores predominantes, com o Sentinel-1 como complemento em períodos nublados; as fases de alongamento, espigamento e enchimento de grãos são as mais discriminantes; e a redução do número de variáveis melhora a eficiência sem perda de acurácia. Cao, L. et al. (2026) reduziram 171 variáveis a 27 (redução de 84,4%), com aumento da acurácia global de 93,53% para 94,60%, e Wang et al. (2026) reduziram 64 variáveis a 16 e obtiveram acurácia global de 0,9658 com apenas 10 variáveis de fusão entre fases (XU et al., 2020; DONG et al., 2020; LIU et al., 2022; CAO, L. et al., 2026; WANG et al., 2026).

Esses resultados, porém, foram obtidos em condições distintas das brasileiras. Nos trabalhos chineses, os confundidores do trigo são culturas de verão ou de calendário diferente, a dormência hibernal produz um duplo pico no índice de vegetação, e a validação é feita, em geral, com amostras aleatórias de um único ano e de uma única região, o que infla a acurácia em razão da autocorrelação espacial (ROBERTS et al., 2017). O mapeamento do trigo no Brasil tem dificuldades próprias (DONG et al., 2020; XU et al., 2020; LIU et al., 2022):

- **Não há dormência nem neve.** A curva do índice de vegetação tem um único pico, e o duplo pico explorado nos métodos chineses não ocorre.
- **Os confundidores são outros cereais de inverno.** Aveia preta (cobertura de solo), aveia branca, cevada e triticale têm assinatura espectral e calendário semelhantes aos do trigo. No Cerrado e no oeste do Paraná, o início do ciclo do trigo coincide ainda com o final do milho segunda safra.
- **A janela de semeadura é longa.** No Paraná, a semeadura se distribui por cerca de dois meses, de modo que compósitos por janelas fixas de calendário misturam lavouras em fases diferentes.
- **A nebulosidade de inverno é alta no Sul**, associada à passagem de frentes frias, e coincide com o espigamento e o enchimento. O radar de abertura sintética (SAR) do Sentinel-1, que não depende de céu limpo, é a principal alternativa para observar essas fases.
- **O fundo é palha.** Em plantio direto, o trigo emerge sobre a palhada da cultura de verão.
- **Há três sistemas distintos:** sequeiro subtropical no Sul, sequeiro no Cerrado e irrigado por pivô no Cerrado.
- **Geada e seca alteram a assinatura.** A geada no espigamento provoca senescência precoce e abrupta, semelhante à da aveia de cobertura dessecada, com risco de omissão justamente nas safras ruins.

A principal limitação dos trabalhos anteriores, a escassez de rótulos de campo, pode ser contornada no Brasil com as glebas georreferenciadas do Sistema de Operações do Crédito Rural e do Proagro (SICOR). Desde a Resolução nº 4.427/2015 do Banco Central, o registro de operações de custeio agrícola inclui a cultura financiada, a área financiada e as coordenadas geodésicas da área. As geometrias são disponibilizadas nas tabelas de crédito rural e Proagro do Banco Central, ainda que apenas para parte das operações (BANCO CENTRAL DO BRASIL, 2015). Essas glebas não constituem amostra probabilística, pois a cobertura é concentrada em operações com recursos controlados, e a aveia preta de cobertura raramente é financiada por custeio. Por isso, as glebas serão usadas como rótulos de treino, e a acurácia e a área serão estimadas com uma amostra de referência independente, de desenho probabilístico (OLOFSSON et al., 2014).

Como a cultura ocupa uma fração pequena do território nacional, o processamento será restrito a um domínio de municípios com ocorrência de trigo, delimitado pela PAM/IBGE. Essa etapa reduz o custo computacional e fornece, ao mesmo tempo, a caracterização regional da área e do rendimento e a identificação a priori das safras com perdas.

### 1.1 Hipóteses

- **H1.** Glebas do SICOR filtradas por coerência temporal fornecem rótulos suficientes para mapear o trigo com F1 ≥ [INSERIR, ex.: 0,85] por gleba e erro de área ≤ [INSERIR, ex.: 15%] em relação ao IBGE/PAM em escala estadual (E1 a E4, E8).
- **H2.** A maturação é a fase mais discriminante entre o trigo e as aveias, com distância de Jeffries-Matusita superior a [INSERIR, ex.: 1,8] no estrato S1, enquanto a separação entre o trigo e a cevada não atinge esse limiar em nenhuma fase isolada e depende de informação espacial a priori (E2, E9).
- **H3.** Variáveis de fusão entre fases (média e diferença), calculadas sobre compósitos alinhados à emergência, transferem entre safras com perda de F1 inferior a [INSERIR, ex.: 0,05], melhor que o empilhamento de compósitos de calendário fixo (E2, E5).
- **H4.** Em safras com geada ou seca, a senescência precoce do trigo aproxima sua assinatura da aveia dessecada, elevando o erro de omissão e subestimando a área municipal (E7).
- **H5.** O Sentinel-1 eleva o F1 do trigo em pelo menos [INSERIR, ex.: 0,05] nos *pixels* com menos de [INSERIR, ex.: 2] observações ópticas válidas no espigamento e no enchimento. Além disso, a colheita detectada pelo radar (eq. 28) reduz a confusão com a aveia de cobertura e a omissão do trigo com geada, que, mesmo com senescência precoce, mantém a estrutura de colmos e é colhido (E1, E7, E10).

---

## 2. Objetivos

### 2.1 Objetivo geral

O objetivo deste projeto será desenvolver e validar um método de mapeamento anual do trigo no Brasil, com produtos de máscara, probabilidade de classe e datas fenológicas para as safras de 2000 a 2025.

### 2.2 Objetivos específicos

- Delimitar o domínio de mapeamento e quantificar a dinâmica espacial e temporal da área e do rendimento do trigo e dos demais cereais de inverno por município e região, a partir da PAM/IBGE.
- Construir uma base de rótulos de trigo e de outras culturas a partir das glebas do SICOR, com filtros de qualidade e partição espacial, complementada por uma amostra de referência independente.
- Processar as séries do Sentinel-1 como dados prontos para análise e quantificar a contribuição do radar ao mapa, sobretudo nas fases e safras com nebulosidade.
- Quantificar a separabilidade entre o trigo e as demais classes em cada fase fenológica, por estrato agroclimático.
- Estabelecer as fases e as variáveis necessárias ao classificador por ranking de fases, acumulação progressiva e seleção por importância por permutação.
- Desenvolver classificadores com compósitos por fase, com fusão entre fases e com similaridade de séries temporais (TWDTW e PT-DTW adaptado).
- Estabelecer a transferência temporal e espacial do classificador, incluindo as safras anteriores às glebas.
- Extrair as datas fenológicas (emergência, pico e maturação) e a data de colheita detectada pelo radar dentro da máscara.
- Validar os mapas por gleba, por amostra probabilística e por área municipal, incluindo safras com estresse por seca ou geada.

---

## 3. Revisão de literatura

### 3.1 Dados e classificadores

Os trabalhos recentes sobre mapeamento do trigo usam predominantemente Sentinel-2, pela resolução espacial de 10 m e pelas bandas de red-edge e SWIR, e Landsat e MODIS para séries longas. O Sentinel-1 é usado para contornar a nebulosidade e para capturar a estrutura do dossel. O Random Forest é o classificador mais citado; XGBoost, SVM, CART e redes profundas aparecem como alternativas, sem superioridade consistente (ZHANG et al., 2019; LIU et al., 2022; TAO et al., 2026; CAO, L. et al., 2026).

Em Cao, L. et al. (2026), as variáveis de polarização do Sentinel-1 (VV, VH e suas combinações) representaram 71,4% das variáveis de radar selecionadas, contra pouca participação das texturas GLCM. As variáveis sensíveis à água do dossel (B11, B12, NDMI e NDPI) somaram 40,7% das 27 variáveis finais. Os autores atribuíram a superestimação de 7,79% da área a pixels mistos em carreadores, canais e faixas estreitas (CAO, L. et al., 2026).

O comportamento dos cereais na banda C é conhecido desde os experimentos com radares orbitais anteriores ao Sentinel-1. Mattia et al. (2003) mostraram que os colmos verticais do trigo atenuam o retroespalhamento em polarização VV durante o alongamento e o espigamento, enquanto a polarização cruzada (VH) acompanha a biomassa. Veloso et al. (2017) descreveram, com séries densas do Sentinel-1, as trajetórias de VV, VH e da razão VH/VV para trigo, cevada, canola, milho e girassol, e mostraram que a razão VH/VV acompanha o NDVI com menos ruído que as polarizações isoladas. Em mapeamentos de culturas, a combinação de séries ópticas e de radar supera, em geral, cada sensor isolado, e o ganho é maior quando as séries ópticas têm falhas por nuvem e na identificação antecipada, antes do fim do ciclo (INGLADA et al., 2016; VAN TRICHT et al., 2018; ORYNBAIKYZY et al., 2019). Bargiel (2017) mostrou que séries de radar apenas, combinadas com informação fenológica, separam culturas de inverno na Europa. Esses estudos foram feitos em regiões temperadas, sem a palhada do plantio direto e sem a aveia de cobertura. No Brasil, o uso do Sentinel-1 no mapeamento de cereais de inverno ainda é pouco estudado [INSERIR referências nacionais, se houver, após levantamento]. A disponibilidade do radar no GEE como dado pronto para análise, com correção do relevo e filtragem do *speckle*, foi sistematizada por Vollrath et al. (2020) e Mullissa et al. (2021).

### 3.2 Fases fenológicas e seleção de variáveis

Os trabalhos classificam o uso da informação temporal em três abordagens: fase única, múltiplas fases empilhadas e série temporal completa. O empilhamento de fases escolhidas empiricamente gera redundância e não avalia a contribuição de cada fase (WANG et al., 2026). Liu et al. (2022) avaliaram a acurácia em diferentes fases. Wang et al. (2026) ordenaram as fases pelo desempenho de um Random Forest por fase, construíram um modelo de acumulação progressiva e substituíram o empilhamento por médias e diferenças entre fases das variáveis-chave. As fases de alongamento, dormência, espigamento e enchimento foram as mais discriminantes em Shandong (LIU et al., 2022; WANG et al., 2026).

Há evidência contraditória sobre as variáveis de diferença temporal: Cao, L. et al. (2026) não selecionaram nenhuma, enquanto Wang et al. (2026) obtiveram o melhor modelo com elas. O procedimento de seleção também difere. O RF-FS de Cao, L. et al. (2026) é guloso e usa validação aleatória, limitação reconhecida pelos próprios autores. A importância por permutação com restrição de correlação, adotada por Wang et al. (2026), é menos sujeita ao viés da importância por impureza a favor de variáveis correlacionadas (STROBL et al., 2007; CAO, L. et al., 2026; WANG et al., 2026).

### 3.3 Similaridade de séries e métodos sem treinamento

O TWDTW mede a similaridade entre a série de um pixel e curvas de referência, com penalidade logística para defasagens temporais. O PT-DTW atribui pesos maiores aos períodos fenológicos mais informativos e transferiu entre anos sem retreino no norte da China. O Peak Value Method (PVM) mapeia o trigo sem amostras de treino, pelo pico do EVI (MAUS et al., 2016; DONG et al., 2020; PHALKE et al., 2024).

### 3.4 Lacunas

| Trabalho | Região | Dados | Método | Uso neste planejamento |
|---|---|---|---|---|
| Xu et al. (2020) | Shandong, China | Sentinel-2 + Landsat 8 | Compósitos por fase, RF | Compósitos por fase (C1) |
| Dong et al. (2020) | Norte da China | Sentinel-2 | PT-DTW | C3 e transferência entre anos |
| Liu et al. (2022) | China | Sentinel-2 | Acurácia por fase, J-M | Separabilidade por fase |
| Zhang et al. (2019) | China | Sentinel-2 | RF em paisagem heterogênea | Erro por classe de tamanho de talhão |
| Deng e Shen (2018) | China | Multitemporal | Classificação por parcela | Pós-processamento por segmentos |
| Phalke et al. (2024) | Bulgária | Séries de EVI | PVM, sem treino | C0 na retroação |
| Tao et al. (2026) | China | Multitemporal | Fusão de variáveis, *stacking* | Variante de C1 |
| Cao, L. et al. (2026) | Xinjiang, China | Sentinel-1 + Sentinel-2 | RF-FS, 171→27 variáveis | Sentinel-1 e seleção de variáveis |
| Mattia et al. (2003) | Itália | ERS/ENVISAT (banda C) | Retroespalhamento multitemporal de trigo | Interpretação da atenuação de VV (eq. 18) |
| Veloso et al. (2017) | Sudoeste da França | Sentinel-1 + dados tipo Sentinel-2 | Trajetórias temporais por cultura | Assinaturas esperadas por classe; $R_{pol}$ |
| Inglada et al. (2016) | França | Sentinel-1 + Landsat/SPOT | Fusão SAR-óptico, identificação antecipada | Versões com e sem radar de C1 |
| Pipia et al. (2019) | Espanha | Sentinel-1 + Sentinel-2 | Preenchimento de falhas ópticas com SAR | Variante de preenchimento (E10) |
| Wang et al. (2026) | Shandong, China | Sentinel-2 | Ranking de fases, acumulação progressiva, fusão entre fases | Seleção de fases e variáveis de fusão |

Nenhum desses trabalhos trata de cereais de inverno com o mesmo calendário do trigo, de trigo tropical, de rótulos derivados do crédito rural, de transferência temporal e espacial avaliada por blocos espaciais, ou da omissão do trigo em safras com estresse. Essas são as lacunas que este projeto pretende preencher.

---

## 4. Área de estudo e estratificação

O domínio de mapeamento será definido pela etapa (i) a partir da PAM/IBGE, e não pelo recorte integral das unidades da federação. Os municípios do domínio serão agrupados em quatro estratos:

| Estrato | Estados | Sistema | Observação |
|---|---|---|---|
| S1, Sul subtropical | PR, RS, SC | Sequeiro | Maior área; confusão com aveias, cevada e, no oeste do PR, milho segunda safra |
| S2, transição Sudeste e Centro-Oeste | SP, MS | Sequeiro | Área menor |
| S3, Cerrado sequeiro | MG, GO, DF, BA | Sequeiro | Trigo tropical, semeadura após a soja; confusão com milho segunda safra e sorgo |
| S4, Cerrado irrigado | MG, GO, DF, BA | Irrigado (pivô) | Separação por máscara de pivôs da ANA e pelo tipo de irrigação do SICOR |

As janelas fenológicas de cada estrato serão definidas pelo calendário do ZARC e por informações da Embrapa Trigo, e refinadas pelas próprias séries de imagens e pelas datas de emergência detectadas nas glebas:

| Estrato | Semeadura | Emergência | Espigamento | Maturação | Colheita |
|---|---|---|---|---|---|
| S1 | [INSERIR] | [INSERIR] | [INSERIR] | [INSERIR] | [INSERIR] |
| S2 | [INSERIR] | [INSERIR] | [INSERIR] | [INSERIR] | [INSERIR] |
| S3 | [INSERIR] | [INSERIR] | [INSERIR] | [INSERIR] | [INSERIR] |
| S4 | [INSERIR] | [INSERIR] | [INSERIR] | [INSERIR] | [INSERIR] |

Municípios do domínio fora dos estados da tabela serão alocados ao estrato mais próximo em calendário, conforme o ZARC.

---

## 5. Dados

| Dado | Fonte | Período | Uso |
|---|---|---|---|
| Área plantada, área colhida e produção de trigo, aveia, cevada e triticale | IBGE/PAM, tabela 1612 do SIDRA (API) | 2000–2025 | Delimitação do domínio, caracterização regional, safras com estresse, validação de área |
| Estimativas de área de trigo | CONAB | 2000–2025 | Comparação complementar de área por UF |
| Malha municipal e regiões geográficas | IBGE (API de localidades; `geobr`) | Vigente | Vínculo município–região, vizinhança, área territorial |
| Glebas de crédito rural | SICOR, tabelas de crédito rural e Proagro (BCB) | [INSERIR, ex.: 2016–2025] | Rótulos de treino; datas de plantio e colheita e tipo de irrigação, se disponíveis |
| Comunicações de perda do Proagro | BCB | [CONFIRMAR disponibilidade por operação] | Glebas de trigo com perda (E7) |
| Máscara agrícola | MapBiomas (agricultura, soja, pastagem) | 2000–2025 | Restrição do domínio de classificação |
| Sentinel-2 SR | Copernicus (GEE) | 2017–2025 | Compósitos de 10–20 m e red-edge |
| HLS (Landsat + Sentinel-2 harmonizados) | NASA (GEE) | 2013–2025 | Compósitos de 30 m (CLAVERIE et al., 2018) |
| Landsat 5/7/8/9 Collection 2 SR | USGS (GEE) | 2000–2025 | Retroação a 30 m |
| MODIS MOD13Q1 | NASA | 2000–2025 | Retroação a 250 m e fração de trigo |
| Sentinel-1 GRD (IW, VV + VH, 10 m; satélites 1A, 1B até dez/2021, 1C e 1D a partir de 2025) | Copernicus (GEE, `COPERNICUS/S1_GRD`) | 2015–2025 (uso efetivo: 2017–2025) | Obrigatório em S1; opcional nos demais estratos. Compósitos por fase, métricas de estrutura do dossel, detecção da colheita, verificação de glebas e preenchimento de falhas ópticas |
| Sentinel-1 SLC (opcional) | Copernicus / Alaska Satellite Facility (HyP3) | 1 a 2 safras-piloto em S1 | Coerência interferométrica (variante do E1) |
| Precipitação diária e horária | CHIRPS; ERA5-Land (GEE) | 2015–2025 | Sinalização de aquisições do Sentinel-1 após chuva |
| Pivôs centrais | ANA | Mapeamentos disponíveis | Separação de S4 |
| Calendário agrícola | ZARC/MAPA, Embrapa Trigo | — | Janelas por fase |
| Relevo | SRTM (30 m) | — | Variáveis auxiliares; correção radiométrica do relevo e máscara de *layover* e sombra do Sentinel-1 |
| Imagens de alta resolução | Planet (NICFI, quando aplicável), Google Earth | 2016–2025 | Interpretação visual da amostra de referência |

---

## 6. Classes

| Classe | Fonte do rótulo |
|---|---|
| Trigo | Glebas SICOR (produto trigo) |
| Aveia branca (grão) | Glebas SICOR (produto aveia) |
| Aveia de cobertura (aveia preta) | Interpretação visual (ciclo encerrado por dessecação, sem senescência) e pontos de cooperativas |
| Cevada | Glebas SICOR (produto cevada) |
| Triticale e outras de inverno (canola, centeio) | Glebas SICOR, quando disponíveis |
| Milho segunda safra e sorgo | Glebas SICOR |
| Outras culturas irrigadas (S4) | Glebas SICOR (feijão, batata e outras sob pivô) |
| Pousio ou palhada no inverno | Pixels de soja do MapBiomas sem ciclo de inverno |
| Pastagem, vegetação natural, área urbana, água | MapBiomas (amostragem estratificada) |

Classe final de saída: trigo / não trigo, com probabilidade calibrada. Mapa auxiliar: "cereais de inverno" (trigo + cevada + triticale), caso a separação trigo × cevada não alcance acurácia aceitável (E9).

---

## 7. Metodologia

### (i) Análise exploratória da produção e delimitação do domínio de mapeamento

A área plantada, a área colhida e a produção do trigo, da aveia, da cevada e do triticale serão obtidas por município para as safras de 2000 a 2025 na tabela 1612 do SIDRA/IBGE, por meio da API do SIDRA. Os códigos de variáveis e produtos serão obtidos nos metadados da própria tabela. Os municípios serão vinculados à unidade da federação, à grande região, à região geográfica intermediária e aos estratos S1 a S4 pela API de localidades do IBGE. Essa etapa tem três finalidades: reduzir a área processada, caracterizar a dinâmica regional da cultura e identificar a priori as safras com perdas para o E7.

A permanência da cultura em cada município será quantificada pela frequência de presença:

$$
F_m = \frac{1}{N}\sum_{t=1}^{N} I\left(A_{m,t} \geq A_{min}\right) \qquad \text{(eq. 1)}
$$

em que: $F_m$ é a frequência de presença do trigo no município $m$ (adimensional, 0 a 1); $N$ é o número de safras; $A_{m,t}$ é a área plantada de trigo no município $m$ na safra $t$ (ha); $A_{min}$ é a área mínima para considerar a presença da cultura (ha, [INSERIR, ex.: 50 ha]); $I(\cdot)$ é a função indicadora.

A concentração espacial da produção será descrita pela curva de área acumulada, com os municípios ordenados em ordem decrescente de área média:

$$
C_k = \frac{\sum_{i=1}^{k} \bar{A}_{(i)}}{\sum_{i=1}^{M} \bar{A}_{(i)}} \qquad \text{(eq. 2)}
$$

em que: $C_k$ é a fração acumulada da área de trigo nos $k$ municípios com maior área (adimensional); $\bar{A}_{(i)}$ é a área plantada média do município de ordem $i$ (ha); $M$ é o número total de municípios.

O domínio de mapeamento será formado pelos municípios com área plantada igual ou superior a $A_{min}$ em pelo menos [INSERIR, ex.: duas] safras, acrescidos de seus vizinhos de primeira ordem. A inclusão dos vizinhos compensa erros de atribuição municipal da PAM, cujas estimativas são feitas pelos Grupos de Coordenação de Estatísticas Agropecuárias, e não por levantamento objetivo. O critério será considerado adequado se o domínio retiver ao menos [INSERIR, ex.: 99%] da área de trigo do país. Serão verificados também os municípios com presença apenas recente (safras a partir de [INSERIR, ex.: 2016]), para não excluir as áreas de expansão no Cerrado. Como verificação independente, será quantificada a fração das glebas do SICOR com produto trigo situada fora do domínio. Para séries municipais longas, os municípios criados após 2000 serão compatibilizados por Áreas Mínimas Comparáveis.

O risco de confusão com outros cereais de inverno será expresso pela participação do trigo na área desses cereais:

$$
P_m = \frac{\sum_{t} A^{trigo}_{m,t}}{\sum_{t}\left(A^{trigo}_{m,t} + A^{aveia}_{m,t} + A^{cevada}_{m,t} + A^{triticale}_{m,t}\right)} \qquad \text{(eq. 3)}
$$

em que: $P_m$ é a participação do trigo na área de cereais de inverno do município $m$ (adimensional); $A^{c}_{m,t}$ é a área plantada da cultura $c$ (ha). Como a PAM registra apenas a aveia para grão, $P_m$ superestima a pureza do trigo nos municípios com aveia preta de cobertura. O índice será usado para estratificar a amostragem e como informação a priori na etapa (vii).

O rendimento será calculado pela razão entre a produção e a área colhida:

$$
Y_{m,t} = 1000\,\frac{Q_{m,t}}{A^{c}_{m,t}} \qquad \text{(eq. 4)}
$$

em que: $Y_{m,t}$ é o rendimento do trigo (kg ha⁻¹); $Q_{m,t}$ é a produção (t); $A^{c}_{m,t}$ é a área colhida (ha).

As safras com estresse serão identificadas por dois indicadores. O primeiro é a anomalia padronizada do rendimento em relação à tendência linear de cada município, calculada para municípios com ao menos [INSERIR, ex.: 8] safras com área colhida igual ou superior a $A_{min}$:

$$
z_{m,t} = \frac{Y_{m,t} - \hat{Y}_{m,t}}{s_m} \qquad \text{(eq. 5)}
$$

em que: $z_{m,t}$ é a anomalia padronizada do rendimento (adimensional); $\hat{Y}_{m,t}$ é o rendimento estimado pela tendência linear (kg ha⁻¹); $s_m$ é o desvio padrão dos resíduos da tendência (kg ha⁻¹). O segundo é a fração da área plantada que não foi colhida:

$$
L_{m,t} = 1 - \frac{A^{c}_{m,t}}{A^{p}_{m,t}} \qquad \text{(eq. 6)}
$$

em que: $L_{m,t}$ é a fração de perda de área (adimensional); $A^{p}_{m,t}$ é a área plantada (ha). As safras com média de $z_{m,t}$ ponderada pela área colhida inferior a −1, ou com $L_{m,t}$ superior a [INSERIR, ex.: 0,10], em um estrato, serão tratadas como safras com estresse no E7.

Os resultados serão agregados por grande região, unidade da federação, região intermediária e estrato, com séries de área, rendimento, participação nos cereais de inverno e perda de área. Saídas: tabela municipal de estatísticas, lista do domínio, tabelas agregadas, safras candidatas ao E7 e figuras de séries por UF, de concentração (eq. 2) e de mapa do domínio.

### (ii) Curadoria das glebas do SICOR

1. **Seleção das operações** de custeio com produto trigo, aveia, cevada, triticale, canola, centeio, milho segunda safra, sorgo e culturas irrigadas de inverno, por ano-safra, restritas ao domínio da etapa (i), com registro das glebas de trigo fora do domínio.
2. **Extração de atributos além da geometria**, se disponíveis: datas previstas de plantio e colheita, tipo de irrigação e sistema de cultivo. As datas servirão para validar a fenologia por gleba, e o tipo de irrigação para separar S3 de S4.
3. **Remoção de geometrias inválidas e duplicadas.** A sobreposição será tratada como erro apenas entre produtos de inverno do mesmo ano-safra. A sobreposição entre a soja (verão) e o trigo (inverno) na mesma gleba é a sucessão normal do plantio direto e será mantida; a data de colheita da soja nessas glebas será usada como limite inferior da emergência do trigo.
4. **Remoção de glebas pequenas**, com área inferior a [INSERIR, ex.: 2 ha].
5. **Filtro de coerência entre área financiada e área do polígono**, para descartar polígonos que representam a propriedade inteira, e não a lavoura:

$$
R_g = \frac{A^{fin}_g}{A^{pol}_g} \qquad \text{(eq. 7)}
$$

em que: $R_g$ é a razão de coerência da gleba $g$ (adimensional); $A^{fin}_g$ é a área financiada registrada (ha); $A^{pol}_g$ é a área do polígono (ha). Serão retidas as glebas com $R_g$ entre [INSERIR, ex.: 0,7] e [INSERIR, ex.: 1,3].

6. **Buffer negativo** de [INSERIR, ex.: 20–30 m] para evitar pixels de borda.
7. **Filtro de coerência temporal.** Serão descartadas as glebas sem ciclo de inverno no perfil de NDVI, ou seja, áreas financiadas e não semeadas ou semeadas com outra cultura. Uma gleba será considerada coerente quando a amplitude do ciclo de inverno e a data do pico atenderem a:

$$
\Delta NDVI_g = NDVI^{max}_{g} - NDVI^{min,pre}_{g} \geq \delta \quad \text{e} \quad \left|t^{pico}_g - t^{pico}_{ZARC}\right| \leq \tau \qquad \text{(eq. 8)}
$$

em que: $\Delta NDVI_g$ é a amplitude do ciclo de inverno da gleba $g$ (adimensional); $NDVI^{max}_{g}$ é a mediana do NDVI máximo dos pixels da gleba na janela de inverno; $NDVI^{min,pre}_{g}$ é a mediana do NDVI mínimo antes da emergência; $\delta$ é a amplitude mínima ([INSERIR, ex.: 0,30]); $t^{pico}_g$ é a data do pico (dia do ano); $t^{pico}_{ZARC}$ é a data central de espigamento esperada pelo ZARC para o estrato; $\tau$ é a tolerância ([INSERIR, ex.: 30 dias]).

   Nas glebas em que a série óptica tiver menos de [INSERIR, ex.: 3] observações válidas na janela de inverno, a coerência temporal será verificada pelo radar. A gleba será considerada coerente quando o máximo de $R_{pol}$ (eq. 16) ocorrer a até $\tau$ dias da data esperada de espigamento e houver uma colheita detectada (eq. 28) após esse máximo. A fração de glebas verificadas apenas pelo radar será registrada por estrato e safra.

8. **Uso exclusivo** da geometria, do produto, do ano-safra e dos atributos agronômicos, sem qualquer dado de identificação de beneficiários.
9. **Tratamento de glebas repetidas entre anos.** A mesma geometria financiada em safras diferentes gera rótulos correlacionados; cada gleba será atribuída ao mesmo bloco espacial em todos os anos.
10. **Partição em treino, validação e teste por blocos espaciais**, com tamanho de bloco definido pelo alcance do semivariograma das variáveis principais (ROBERTS et al., 2017).
11. **Complementação da aveia de cobertura**, por interpretação visual de séries temporais e imagens de alta resolução e por pontos de cooperativas, com meta de [INSERIR, ex.: 300] amostras por estrato.

A representatividade das glebas será avaliada comparando a distribuição de tamanho e a área por município com o IBGE/PAM. A interpretação visual seguirá um protocolo escrito, com dupla interpretação de [INSERIR, ex.: 10%] das amostras para quantificar a concordância entre intérpretes.

### (iii) Pré-processamento e compósitos

As nuvens serão mascaradas com Cloud Score+ no Sentinel-2 (limiar [INSERIR, ex.: 0,60]) e com a banda QA_PIXEL no Landsat (PASQUARELLA et al., 2023). Para cada pixel e fase, será registrado o número de observações válidas como métrica de qualidade; fases sem observação válida serão preenchidas pela série suavizada e sinalizadas. Serão gerados quatro tipos de entrada:

1. **Compósitos por fase de calendário.** Mediana das imagens em seis fases definidas por estrato (estabelecimento, perfilhamento, alongamento, espigamento, enchimento e maturação), conforme Xu et al. (2020), para comparabilidade com a literatura.
2. **Compósitos alinhados à emergência.** A data de emergência será detectada por pixel (eq. 27) e as fases serão definidas em dias após a emergência (DAE): estabelecimento [INSERIR, ex.: 0–20 DAE], perfilhamento [INSERIR], alongamento [INSERIR], espigamento [INSERIR], enchimento [INSERIR] e maturação [INSERIR]. Essa alternativa responde à janela de semeadura longa e à limitação das janelas fixas reconhecida por Wang et al. (2026).
3. **Séries de 10 dias** suavizadas por Savitzky–Golay, para os métodos de similaridade de séries (CHEN et al., 2004).
4. **Coeficientes harmônicos** da série de NDVI e NDPI no ano-safra, robustos a falhas por nuvem e independentes de calendário (JAKUBAUSKAS et al., 2001):

$$
x(t) = \beta_0 + \beta_1 t + \sum_{k=1}^{K}\left[a_k \cos\left(\frac{2\pi k t}{T}\right) + b_k \sin\left(\frac{2\pi k t}{T}\right)\right] \qquad \text{(eq. 9)}
$$

em que: $x(t)$ é o índice de vegetação na data $t$ (adimensional); $t$ é o tempo desde o início do ano-safra (dias); $T$ é a duração do ano-safra (365 dias); $K$ é o número de harmônicos ([INSERIR, ex.: 3]); $\beta_0$, $\beta_1$, $a_k$ e $b_k$ são os coeficientes ajustados por mínimos quadrados.

#### Processamento do Sentinel-1 (radar de abertura sintética)

O Sentinel-1 opera na banda C (5,405 GHz; comprimento de onda de cerca de 5,6 cm) e, por ser um sensor ativo de micro-ondas, adquire imagens independentemente da cobertura de nuvens e da iluminação solar (TORRES et al., 2012). No Sul, a nebulosidade associada às frentes frias coincide com o espigamento e o enchimento de grãos, as fases mais discriminantes do trigo (seção 3.2). Por isso, o radar é obrigatório no estrato S1 e opcional nos demais. Será usada a coleção `COPERNICUS/S1_GRD` do GEE, no modo *Interferometric Wide swath* (IW), com polarizações VV e VH e *pixel* de 10 m. As cenas dessa coleção já passam pelo processamento do *Sentinel-1 Toolbox*: aplicação da órbita, remoção do ruído térmico, calibração radiométrica e ortorretificação com o SRTM de 30 m, com saída em $\sigma^0$ (dB). Não há, porém, correção radiométrica do relevo nem filtragem de *speckle*. A resolução nominal é de 10 m, mas a resolução efetiva do GRD no modo IW é de cerca de 20 m × 22 m (*range* × azimute). Esse valor, somado ao *buffer* negativo da etapa (ii), define a menor gleba utilizável com o radar.

A disponibilidade de dados determina o período de uso. O Sentinel-1A opera desde abril de 2014, mas a cobertura do Brasil foi esparsa até o fim de 2016. O Sentinel-1B operou de 2016 até a falha de dezembro de 2021, e entre 2022 e 2024 houve apenas o 1A, com revisita de 12 dias e possíveis falhas de aquisição em parte do país. O Sentinel-1C (lançado em dezembro de 2024) e o 1D (lançado em novembro de 2025) restabelecem a constelação de dois satélites. Assim, o conjunto de variáveis com radar será usado nas safras de 2017 a 2025, e a diferença de densidade de observações entre os períodos será tratada como fator no E5. A cobertura efetiva por órbita relativa no domínio será levantada antes da execução (seção 12.3).

O processamento seguirá o *framework* de dados prontos para análise (ARD) do Sentinel-1 no GEE de Mullissa et al. (2021), com as etapas a seguir.

1. **Seleção das cenas.** Modo IW, polarizações VV e VH, interseção com o domínio da etapa (i) e janela de aquisição do início da semeadura do estrato menos [INSERIR, ex.: 30 dias] até o fim da colheita mais [INSERIR, ex.: 30 dias]. A janela ampliada registra a palhada antes do ciclo e o restolho depois da colheita, necessários para as métricas e para a detecção da colheita (eq. 28).
2. **Geometria de aquisição.** O Sentinel-1 está em órbita heliossíncrona crepuscular, com passagens ascendentes por volta das 18 h e descendentes por volta das 6 h (hora solar local). Nas passagens matutinas, o orvalho sobre o dossel pode elevar o retroespalhamento, sobretudo em VV. Por isso, as passagens ascendentes e descendentes não serão misturadas em um mesmo compósito sem a normalização do ângulo de incidência (eq. 10). A órbita relativa e a direção de passagem serão registradas em cada observação. O conjunto principal usará a direção com maior número de aquisições no domínio, e a outra direção e sua combinação serão testadas no E1.
3. **Máscara de borda e de ângulo.** Serão removidos os *pixels* de borda da faixa com $\sigma^0_{VV}$ inferior a [INSERIR, ex.: −30 dB], que correspondem ao ruído de borda presente sobretudo nas cenas processadas antes de 2018. Também serão removidos os *pixels* com ângulo de incidência fora do intervalo de [INSERIR, ex.: 31° a 45°], nos extremos da faixa IW (cerca de 29° a 46°).
4. **Correção radiométrica do relevo.** Grande parte do domínio é plana ou suave-ondulada, mas o Planalto Meridional (RS, SC e centro-sul do PR) tem declividades em que a geometria de iluminação altera o retroespalhamento. Será aplicada a correção angular do relevo de Vollrath et al. (2020), com o modelo de volume para vegetação e o SRTM de 30 m. As áreas de *layover* e de sombra serão mascaradas. A variável resultante é o $\gamma^0$ com correção de relevo ($\gamma^0_{flat}$). A comparação entre $\sigma^0$ e $\gamma^0_{flat}$ será feita no E1.
5. **Normalização do ângulo de incidência.** Uma mesma lavoura é observada com ângulos diferentes conforme a órbita relativa e a posição na faixa. O retroespalhamento será normalizado para um ângulo de referência (ULABY; LONG, 2014):

$$
\sigma^0_{ref} = \sigma^0(\theta)\left(\frac{\cos\theta_{ref}}{\cos\theta}\right)^{n} \qquad \text{(eq. 10)}
$$

em que: $\sigma^0_{ref}$ é o coeficiente de retroespalhamento normalizado para o ângulo de referência (linear, m² m⁻²); $\sigma^0(\theta)$ é o coeficiente observado no ângulo de incidência local $\theta$ (linear); $\theta_{ref}$ é o ângulo de referência ([INSERIR, ex.: 38°], centro da faixa IW); $n$ é o expoente de dependência angular (adimensional). O valor $n = 2$ corresponde a um espalhador lambertiano. O expoente será estimado por classe e polarização a partir das glebas observadas por órbitas relativas diferentes em um intervalo de até [INSERIR, ex.: 6 dias], pela regressão de $\sigma^0$ (dB) contra $10\log_{10}(\cos\theta)$, cuja inclinação é $n$.

6. **Filtragem do *speckle*.** O *speckle* é o ruído multiplicativo inerente à imagem coerente de radar. O número equivalente de *looks* (ENL) do GRD no modo IW é de cerca de 4,4. Como filtro principal será usado o filtro multitemporal de Quegan e Yu (2001), que reduz o *speckle* sem degradar a resolução espacial, ao contrário dos filtros espaciais:

$$
J_k(\mathbf{s}) = \frac{\langle I_k \rangle}{M}\sum_{i=1}^{M}\frac{I_i(\mathbf{s})}{\langle I_i \rangle} \qquad \text{(eq. 11)}
$$

em que: $J_k(\mathbf{s})$ é a intensidade filtrada da imagem $k$ na posição $\mathbf{s}$ (linear); $I_i(\mathbf{s})$ é a intensidade da imagem $i$ da série na posição $\mathbf{s}$ (linear); $\langle I_i \rangle$ é a média local da imagem $i$ em uma janela de [INSERIR, ex.: 5 × 5] *pixels* (linear); $M$ é o número de imagens da série, da mesma órbita relativa, usadas no filtro ([INSERIR, ex.: 10]). O ENL da imagem filtrada aumenta aproximadamente $M$ vezes. O filtro Refined Lee (LEE, 1981), com janela de [INSERIR, ex.: 5 × 5], será testado como variante no E1. Na extração dos rótulos, a média sobre os *pixels* de cada gleba atua, por si só, como filtragem, e a gleba será usada como unidade de agregação.

7. **Agregação em escala linear.** O coeficiente de retroespalhamento é uma potência, e as médias aritméticas em decibéis são enviesadas para baixo. Todas as médias temporais (compósitos) e espaciais (glebas e segmentos) serão calculadas em escala linear e só depois convertidas em decibéis:

$$
\bar{\sigma}^0_{dB} = 10\log_{10}\!\left(\frac{1}{n}\sum_{i=1}^{n}10^{\,\sigma^0_{dB,i}/10}\right) \qquad \text{(eq. 12)}
$$

em que: $\bar{\sigma}^0_{dB}$ é o retroespalhamento médio (dB); $\sigma^0_{dB,i}$ é o retroespalhamento da observação $i$ (dB); $n$ é o número de observações (aquisições na fase ou *pixels* na gleba). A mediana, invariante à transformação logarítmica, será exportada como alternativa robusta a valores extremos.

8. **Sinalização de aquisições após chuva.** No estabelecimento e após a colheita, com dossel pouco desenvolvido, o retroespalhamento é dominado pela umidade e pela rugosidade do solo e da palhada. Uma chuva antes da passagem eleva $\sigma^0_{VV}$ em vários decibéis, independentemente da cultura. As aquisições com precipitação acumulada igual ou superior a [INSERIR, ex.: 5 mm] nas [INSERIR, ex.: 24 h] anteriores à passagem, segundo o CHIRPS diário ou o ERA5-Land horário, serão sinalizadas. Nos compósitos, essas aquisições serão excluídas quando houver ao menos [INSERIR, ex.: 2] aquisições não sinalizadas na fase. Caso contrário, serão mantidas, e a fase será sinalizada. O efeito do filtro será avaliado no E1.
9. **Compósitos e séries.** Serão gerados, para o radar, os mesmos quatro tipos de entrada definidos para os dados ópticos: compósitos por fase de calendário, compósitos alinhados à emergência (eq. 27), séries regulares e coeficientes harmônicos (eq. 9) de $\sigma^0_{VH}$ e de $R_{pol}$ (eq. 16). As séries do radar serão montadas na grade de 12 dias da revisita e interpoladas linearmente para a grade de 10 dias das séries ópticas, permitindo séries conjuntas nos classificadores C2 a C4. Para cada *pixel* e fase, será registrado o número de aquisições válidas. Fases sem aquisição serão preenchidas pelo ajuste harmônico e sinalizadas.
10. **Exportação.** Os compósitos serão exportados como *assets* por estrato e safra. As séries por gleba serão exportadas como tabelas, com a média linear (eq. 12) dos *pixels* internos ao *buffer*, a data, a órbita relativa, a direção de passagem, o ângulo de incidência médio e a sinalização de chuva de cada aquisição.

As texturas GLCM não serão incluídas no conjunto principal, por sua baixa participação entre as variáveis selecionadas em Cao, L. et al. (2026), e serão testadas apenas como variante no E1. A coerência interferométrica (InSAR) entre aquisições consecutivas é sensível à colheita, ao preparo do solo e à dessecação, mas depende de imagens SLC, que não estão no GEE. Por isso, será tratada como variante opcional no E1, processada em uma ou duas safras-piloto do estrato S1 com o serviço HyP3 da Alaska Satellite Facility.

**Preenchimento de falhas ópticas com o radar (variante).** A detecção da emergência (eq. 26) e os métodos de similaridade de séries (C2 e C3) dependem de séries ópticas contínuas, que no Sul têm falhas longas no inverno. Como variante ao preenchimento apenas por Savitzky–Golay, o NDVI será estimado nas datas sem observação óptica por um Random Forest de regressão, com $\sigma^0_{VV}$, $\sigma^0_{VH}$, $R_{pol}$ (eq. 16), RVI (eq. 17), ângulo de incidência, dia do ano e estrato como preditores (PIPIA et al., 2019). O modelo será treinado nas glebas com pares de observações Sentinel-2 sem nuvem e Sentinel-1 separadas por até [INSERIR, ex.: 3 dias], e validado por blocos espaciais (RMSE e viés). Os valores preenchidos serão sinalizados e usados apenas para completar as séries, e nunca como variável direta dos classificadores C1, para evitar dupla contagem da informação do radar. O ganho será avaliado no E10.

### (iv) Variáveis

Serão usadas as bandas espectrais, NDVI, EVI, SAVI, NDRE (red-edge, apenas Sentinel-2) e os índices abaixo.

O NDPI, que reduz a influência do fundo e esteve entre as variáveis-chave de Cao, L. et al. (2026), será testado pelo fundo de palhada (CHEN et al., 2019; DONG et al., 2020):

$$
NDPI = \frac{\rho_{NIR} - \left[\alpha\,\rho_{R} + (1-\alpha)\,\rho_{SWIR1}\right]}{\rho_{NIR} + \left[\alpha\,\rho_{R} + (1-\alpha)\,\rho_{SWIR1}\right]} \qquad \text{(eq. 13)}
$$

em que: $\rho_{NIR}$, $\rho_{R}$ e $\rho_{SWIR1}$ são as reflectâncias no infravermelho próximo, no vermelho e no infravermelho de ondas curtas (adimensional); $\alpha$ é o peso do vermelho (adimensional). O valor $\alpha = 0{,}74$ foi calibrado para MODIS e será recalibrado para Sentinel-2 e HLS com as glebas, maximizando a distância de Jeffries-Matusita entre o trigo e o pousio com palhada.

O PSRI, sensível à senescência, foi incluído porque a maturação é a fase mais importante na separação do trigo em relação à aveia de cobertura, que costuma ser dessecada sem amadurecer (MERZLYAK et al., 1999; XU et al., 2020):

$$
PSRI = \frac{\rho_{R} - \rho_{B}}{\rho_{RE2}} \qquad \text{(eq. 14)}
$$

em que: $\rho_{B}$ é a reflectância no azul e $\rho_{RE2}$ no red-edge (banda 6 do Sentinel-2) (adimensional). Por depender do red-edge, o PSRI não está disponível no Landsat; na retroação, será substituído pela diferença entre fases (eq. 26).

A umidade do dossel, que distingue o dossel verde da palhada seca e respondeu por 40,7% das variáveis selecionadas em Cao, L. et al. (2026), será representada pelo LSWI (GAO, 1996):

$$
LSWI = \frac{\rho_{NIR} - \rho_{SWIR1}}{\rho_{NIR} + \rho_{SWIR1}} \qquad \text{(eq. 15)}
$$

Para o Sentinel-1, será usada a razão de polarização, sensível ao desenvolvimento do dossel e ao espigamento dos cereais (VELOSO et al., 2017):

$$
R_{pol} = \sigma^0_{VH} - \sigma^0_{VV} \qquad \text{(eq. 16)}
$$

em que: $R_{pol}$ é a razão de polarização (dB); $\sigma^0_{VH}$ e $\sigma^0_{VV}$ são os coeficientes de retroespalhamento nas polarizações VH e VV (dB).

O índice de vegetação por radar em dupla polarização será calculado em escala linear, como adaptação do RVI de polarimetria completa (KIM; VAN ZYL, 2009; NASIRZADEHDIZAJI et al., 2019):

$$
RVI = \frac{4\,\sigma^0_{VH}}{\sigma^0_{VV} + \sigma^0_{VH}} \qquad \text{(eq. 17)}
$$

em que: $RVI$ é o índice de vegetação por radar (adimensional, aproximadamente 0 a 1 em lavouras); $\sigma^0_{VH}$ e $\sigma^0_{VV}$ estão em escala linear (m² m⁻²). O índice dual-pol baseado na matriz de covariância (DpRVI) exige imagens SLC e não será usado no conjunto principal (MANDAL et al., 2020).

**Assinatura temporal esperada.** A interpretação das variáveis de radar parte do comportamento conhecido dos cereais na banda C (MATTIA et al., 2003; VELOSO et al., 2017):

- **Estabelecimento.** O dossel é esparso, e $\sigma^0_{VV}$ responde à umidade do solo e à palhada, com picos após chuvas (passo 8 do processamento). $\sigma^0_{VH}$ é baixo.
- **Perfilhamento.** $\sigma^0_{VH}$ cresce com a biomassa e o espalhamento volumétrico, e o RVI aumenta.
- **Alongamento e espigamento.** Os colmos verticais atenuam a onda em polarização vertical, e $\sigma^0_{VV}$ cai até um mínimo próximo ao espigamento. $\sigma^0_{VH}$ se estabiliza, e $R_{pol}$ atinge o máximo. Essa queda de VV é a principal assinatura estrutural dos cereais de colmo ereto.
- **Enchimento e maturação.** A perda de água do dossel reduz a constante dielétrica. $\sigma^0_{VH}$ decresce, e $\sigma^0_{VV}$ volta a subir à medida que a atenuação diminui.
- **Colheita.** A remoção do dossel produz uma mudança abrupta: queda de $\sigma^0_{VH}$ e de $R_{pol}$, com $\sigma^0_{VV}$ passando a refletir o restolho e o solo (eq. 28).

Os confundidores do trigo têm assinaturas distintas. A **aveia de cobertura** é dessecada antes de completar o ciclo e permanece na área, acamada ou rolada, até a semeadura da soja, de modo que não ocorre a mudança abrupta da colheita, e o declínio de $\sigma^0_{VH}$ é gradual. A **canola**, de folhas largas e síliquas, tem $\sigma^0_{VH}$ elevado e não apresenta a atenuação de VV característica dos colmos (VELOSO et al., 2017). O **milho segunda safra** tem biomassa e $\sigma^0_{VH}$ maiores, e sua colheita coincide com o início do ciclo do trigo. A **cevada** e a **aveia branca** têm estrutura semelhante à do trigo, e espera-se que a separação dependa de diferenças de calendário (espigamento e colheita mais precoces da cevada) e da informação a priori (eq. 25). Essas expectativas serão verificadas nas curvas médias por classe e estrato, extraídas das glebas, antes da seleção de variáveis.

**Métricas fenológicas do radar.** Além dos compósitos por fase de $\sigma^0_{VV}$, $\sigma^0_{VH}$, $R_{pol}$ e RVI, serão extraídas da série suavizada as seguintes métricas: data e valor do máximo de $R_{pol}$; data e valor do mínimo de $\sigma^0_{VV}$ na janela de alongamento e espigamento; taxa de subida de $\sigma^0_{VH}$ no perfilhamento; data da colheita detectada (eq. 28); e atenuação de VV no espigamento:

$$
A_{VV} = \bar{\sigma}^0_{VV,pre} - \min_{t \in W_{esp}} \sigma^0_{VV}(t) \qquad \text{(eq. 18)}
$$

em que: $A_{VV}$ é a atenuação de VV (dB); $\bar{\sigma}^0_{VV,pre}$ é a média linear (eq. 12), convertida em dB, das aquisições do perfilhamento (dB); $W_{esp}$ é a janela de alongamento e espigamento do estrato, em calendário ou em DAE; $\sigma^0_{VV}(t)$ é o retroespalhamento na data $t$ (dB). Valores positivos indicam atenuação pelos colmos.

Serão definidos três conjuntos de variáveis de radar para os experimentos: (a) compósitos por fase; (b) métricas fenológicas; (c) (a) + (b). A importância do radar como grupo será medida pela importância por permutação conjunta de todas as variáveis de radar, que é a eq. 21 aplicada à permutação simultânea do grupo. Assim, a correlação entre as variáveis do grupo não dilui a importância individual de cada uma.

Serão também extraídas métricas fenológicas da série suavizada: amplitude, data do pico, taxa de subida, taxa de queda, duração e integral do ciclo de inverno (JÖNSSON; EKLUNDH, 2004). Serão definidos dois conjuntos de variáveis: um completo, para Sentinel-2 e HLS, e um compatível com Landsat (sem red-edge), para a retroação. O conjunto completo terá duas versões, com e sem as variáveis de radar. O conjunto compatível com Landsat não terá radar, porque o Sentinel-1 não cobre as safras da retroação.

### (v) Separabilidade por fase

A distância de Jeffries-Matusita (J-M) entre o trigo e cada classe será calculada por fase e por estrato, como em Liu et al. (2022):

$$
JM_{ij} = 2\left(1 - e^{-B_{ij}}\right) \qquad \text{(eq. 19)}
$$

$$
B_{ij} = \frac{1}{8}(\mathbf{m}_i - \mathbf{m}_j)^T \left(\frac{\boldsymbol{\Sigma}_i + \boldsymbol{\Sigma}_j}{2}\right)^{-1}(\mathbf{m}_i - \mathbf{m}_j) + \frac{1}{2}\ln\!\left(\frac{\left|\frac{\boldsymbol{\Sigma}_i + \boldsymbol{\Sigma}_j}{2}\right|}{\sqrt{|\boldsymbol{\Sigma}_i|\,|\boldsymbol{\Sigma}_j|}}\right) \qquad \text{(eq. 20)}
$$

em que: $JM_{ij}$ é a distância de Jeffries-Matusita entre as classes $i$ e $j$ (0 a 2); $B_{ij}$ é a distância de Bhattacharyya; $\mathbf{m}_i$ e $\mathbf{m}_j$ são os vetores de médias das variáveis; $\boldsymbol{\Sigma}_i$ e $\boldsymbol{\Sigma}_j$ são as matrizes de covariância. A J-M será calculada tanto para os compósitos de calendário quanto para os alinhados à emergência.

Resultado esperado: uma tabela fase × classe × estrato que indica quais fases separam o trigo de cada confundidor e se a separação trigo × cevada é viável.

### (vi) Seleção de fases e de variáveis

As fases serão ordenadas, em cada estrato, por dois critérios complementares: a distância J-M média entre o trigo e as demais classes (eq. 19) e o F1 de um Random Forest treinado apenas com as variáveis de cada fase, avaliado por validação cruzada em blocos espaciais (LIU et al., 2022; WANG et al., 2026). A partir desse ranking, será construído um modelo de acumulação progressiva, em que as fases são acrescentadas uma a uma, em ordem decrescente de capacidade de discriminação, até que o ganho de F1 seja inferior a [INSERIR, ex.: 0,005] (WANG et al., 2026). Para evitar conflito com a sigla da Produção Agrícola Municipal, esse modelo será denominado MAP (modelo de acumulação progressiva).

Dentro das fases retidas, as variáveis serão selecionadas pela importância por permutação, calculada nos blocos de validação (BREIMAN, 2001):

$$
I_j = \frac{1}{K}\sum_{k=1}^{K}\left(s_k - s_{k,j}\right) \qquad \text{(eq. 21)}
$$

em que: $I_j$ é a importância por permutação da variável $j$ (adimensional); $K$ é o número de blocos de validação; $s_k$ é o F1 no bloco $k$ com os dados originais; $s_{k,j}$ é o F1 no bloco $k$ após a permutação aleatória da variável $j$. Entre pares de variáveis com coeficiente de correlação de Pearson superior a [INSERIR, ex.: 0,90], será retida a de maior $I_j$ (CAO, L. et al., 2026; WANG et al., 2026). A estabilidade da seleção será verificada pela frequência com que cada variável é retida em [INSERIR, ex.: 50] reamostragens *bootstrap* dos blocos (MEINSHAUSEN; BÜHLMANN, 2010), sendo mantidas as variáveis selecionadas em ao menos [INSERIR, ex.: 70%] das reamostragens.

Como alternativa ao empilhamento das fases, as variáveis-chave serão combinadas entre fases pela média e pela diferença (WANG et al., 2026):

$$
\bar{x}_{v} = \frac{1}{F}\sum_{f=1}^{F} x_{v,f} \qquad \text{(eq. 22)}
$$

$$
\Delta x_{v}^{(f,g)} = x_{v,g} - x_{v,f} \qquad \text{(eq. 23)}
$$

em que: $\bar{x}_{v}$ é a média da variável $v$ entre as $F$ fases retidas; $x_{v,f}$ é o valor da variável $v$ na fase $f$; $\Delta x_{v}^{(f,g)}$ é a diferença da variável $v$ entre as fases $f$ e $g$. A diferença entre o enchimento de grãos e a maturação será usada como indicador de senescência compatível com sensores sem red-edge. Como Cao, L. et al. (2026) não selecionaram variáveis de diferença temporal, enquanto Wang et al. (2026) obtiveram o melhor desempenho com elas, a contribuição dessas variáveis será testada explicitamente nos experimentos E2 e E3.

### (vii) Classificação

| Código | Classificador | Entrada | Referência |
|---|---|---|---|
| C0 | Peak Value Method adaptado (sem treino) | Série de EVI; regra de pico | Phalke et al. (2024) |
| C1a | Random Forest | Compósitos por fase empilhados, após seleção (vi) | Xu et al. (2020); Liu et al. (2022) |
| C1b | Random Forest | Variáveis de fusão entre fases (eq. 22 e eq. 23) | Wang et al. (2026) |
| C1c | XGBoost | Melhor entrada entre C1a e C1b | Tao et al. (2026) |
| C2 | TWDTW | Séries de 10 dias de NDVI ou NDPI, curvas de referência por estrato | Maus et al. (2016) |
| C3 | PT-DTW adaptado | Como C2, com peso maior na subida pós-emergência e na senescência | Dong et al. (2020) |
| C4 (opcional) | Rede temporal (TempCNN ou LightTAE) | Séries de 10 dias | Pelletier et al. (2019); Garnot e Landrieu (2020) |

**C0.** Um pixel será classificado como cereal de inverno quando o EVI máximo na janela de inverno do estrato for igual ou superior a [INSERIR, ex.: 0,45], com amplitude igual ou superior a [INSERIR, ex.: 0,25] e data do pico dentro da janela de espigamento do ZARC. O C0 não separa o trigo das aveias e será usado como máscara de cereais de inverno na retroação e como linha de base sem treino.

**C1.** O Random Forest terá [INSERIR, ex.: 300] árvores, com número de variáveis por nó e tamanho mínimo da folha ajustados por validação em blocos espaciais. As classes serão balanceadas por ponderação proporcional ao inverso da frequência. Cada configuração de C1 será treinada em duas versões, com e sem as variáveis do Sentinel-1 (seção (iv)). A versão com radar será aplicada às safras de 2017 a 2025. A versão sem radar será aplicada às safras anteriores e servirá de referência para quantificar a contribuição do radar no E1 e no E10. Nos *pixels* sem aquisição de radar válida na safra, por falha de cobertura, será usada a versão sem radar, e o *pixel* será sinalizado.

**C2 e C3.** A penalidade temporal logística do TWDTW será mantida (MAUS et al., 2016):

$$
\omega_{ij} = \frac{1}{1 + e^{-a\,(|t_i - t_j| - b)}} \qquad \text{(eq. 24)}
$$

em que: $\omega_{ij}$ é o peso de penalidade entre as datas $t_i$ e $t_j$ (adimensional); $a$ é a declividade e $b$ o ponto médio da função logística (dias). Diferentemente de Dong et al. (2020), $a$ e $b$ serão ajustados com as glebas. No PT-DTW adaptado, os dois períodos com peso maior deixam de ser o crescimento antes do inverno e a queda após o espigamento e passam a ser a subida após a emergência e a senescência, definidas por estrato. A implementação de C2 a C4 será feita fora do GEE, com o pacote `sits` sobre cubos do Brazil Data Cube ou sobre séries exportadas por *tiles* (SIMOES et al., 2021).

**Calibração da probabilidade.** A probabilidade (ou distância) por pixel será exportada em todos os classificadores e calibrada por regressão isotônica nos blocos de validação (ZADROZNY; ELKAN, 2002).

**Informação a priori para a cevada.** Como a cevada é concentrada em poucos municípios, a probabilidade calibrada será ajustada à proporção municipal esperada das classes (SAERENS et al., 2002):

$$
p'(c\,|\,\mathbf{x}) = \frac{p(c\,|\,\mathbf{x})\,\dfrac{\pi_m(c)}{\pi_{tr}(c)}}{\sum_{c'} p(c'\,|\,\mathbf{x})\,\dfrac{\pi_m(c')}{\pi_{tr}(c')}} \qquad \text{(eq. 25)}
$$

em que: $p'(c\,|\,\mathbf{x})$ é a probabilidade ajustada da classe $c$ para o vetor de variáveis $\mathbf{x}$ (adimensional); $p(c\,|\,\mathbf{x})$ é a probabilidade calibrada; $\pi_m(c)$ é a proporção da classe $c$ no município $m$, derivada da PAM (eq. 3); $\pi_{tr}(c)$ é a proporção da classe $c$ no conjunto de treino. O ajuste será aplicado apenas às classes de cereais de grão presentes na PAM e testado no E9.

**Pós-processamento.** Para reduzir o efeito de pixels mistos em carreadores, terraços e bordaduras, será aplicada uma unidade mínima de mapeamento de [INSERIR, ex.: 0,5 ha] e, como alternativa, a agregação da probabilidade por segmentos SNIC (ACHANTA; SÜSSTRUNK, 2017; DENG; SHEN, 2018). O efeito sobre a área será avaliado por classe de tamanho de talhão (ZHANG et al., 2019; CAO, L. et al., 2026).

### (viii) Retroação para as safras sem glebas

As safras anteriores às glebas (2000 a [INSERIR]) serão mapeadas por quatro estratégias:

- C0 como máscara de cereais de inverno, sem treino (PHALKE et al., 2024);
- C1 treinado com as safras recentes e aplicado a compósitos Landsat harmonizados com o conjunto de variáveis compatível com Landsat, considerando as falhas do Landsat 7 SLC-off;
- C2 e C3 com curvas de referência das safras recentes, aproveitando a transferência entre anos sem retreino observada por Dong et al. (2020);
- uma versão a 250 m com MODIS, que estima a fração de trigo por pixel, para consistência da série completa.

Como o Sentinel-1 não cobre o período da retroação, os classificadores retroativos usarão apenas o conjunto sem radar. A perda de desempenho decorrente da ausência do radar será estimada nas safras recentes, pela diferença de F1 entre as versões com e sem radar. Essa diferença será reportada como limite inferior do erro esperado na série retroativa.

A transferência será testada simulando a ausência de rótulos nas safras recentes: treino em um subconjunto de anos e teste nos demais (E5). A série retroativa será comparada com a PAM por município e safra.

### (ix) Fenologia

Dentro da máscara, as datas de emergência e de maturação serão extraídas pelo limiar de amplitude da série suavizada (JÖNSSON; EKLUNDH, 2004):

$$
x(t_e) = x_{min,pre} + p_e\left(x_{max} - x_{min,pre}\right); \qquad x(t_m) = x_{min,pos} + p_m\left(x_{max} - x_{min,pos}\right) \qquad \text{(eq. 26)}
$$

em que: $t_e$ e $t_m$ são as datas de emergência e de maturação (dia do ano); $x_{max}$ é o valor máximo do índice no ciclo de inverno; $x_{min,pre}$ e $x_{min,pos}$ são os mínimos antes e depois do pico; $p_e$ e $p_m$ são as frações da amplitude ([INSERIR, ex.: 0,20 e 0,50]). A data do pico será a data de $x_{max}$. A emergência detectada também define os compósitos alinhados da etapa (iii):

$$
DAE(t) = t - t_e \qquad \text{(eq. 27)}
$$

em que: $DAE(t)$ é o número de dias após a emergência na data $t$ (dias).

A data de colheita será detectada pelo radar, independentemente da cobertura de nuvens, como a primeira aquisição posterior ao máximo de $R_{pol}$ em que a razão de polarização cai de forma abrupta e persistente:

$$
t_c = \min\left\{t_k > t_{R,max} \,:\, R_{pol}(t_k) - R_{pol}(t_{k-1}) \leq -\kappa \;\; \text{e} \;\; R_{pol}(t_{k+1}) - R_{pol}(t_{k-1}) \leq -\kappa\right\} \qquad \text{(eq. 28)}
$$

em que: $t_c$ é a data de colheita detectada (dia do ano); $t_k$ é a data da aquisição $k$ da mesma órbita relativa; $t_{R,max}$ é a data do máximo de $R_{pol}$ no ciclo de inverno; $R_{pol}(t_k)$ é a razão de polarização na aquisição $k$ (dB, eq. 16); $\kappa$ é a queda mínima ([INSERIR, ex.: 2 dB]), calibrada com as datas de colheita do SICOR, quando disponíveis, e com as quedas de NDVI nas glebas com série óptica completa. A segunda condição exige que a queda persista na aquisição seguinte, o que evita falsos eventos causados por chuva ou orvalho em uma única data. As aquisições sinalizadas por chuva (passo 8 do processamento do Sentinel-1) não serão usadas como $t_k$. A ausência de colheita detectada até [INSERIR, ex.: 30 dias] após o fim da janela de colheita do ZARC será registrada como indicador de ciclo encerrado sem colheita (aveia de cobertura dessecada ou lavoura abandonada). A incerteza de $t_c$ é limitada pela revisita: até 6 dias com dois satélites e até 12 dias com um. A data detectada será comparada com a data de maturação óptica (eq. 26), e o intervalo entre as duas será analisado por estrato.

As datas serão estimadas também pelo alinhamento do DTW em relação à curva de referência, com datas conhecidas, e comparadas com as janelas do ZARC, com as datas de plantio e colheita do SICOR (quando disponíveis) e com observações de campo da Embrapa Trigo ou de cooperativas.

### (x) Validação

**Por gleba.** Acurácias do produtor (PA) e do usuário (UA) e F1, nas glebas de teste por bloco espacial, por estrato e por classe de tamanho de talhão:

$$
F1 = \frac{2\,UA\,PA}{UA + PA} \qquad \text{(eq. 29)}
$$

em que: $UA$ é a acurácia do usuário e $PA$ a acurácia do produtor da classe trigo (adimensional). Essas métricas medem o desempenho sobre as glebas, mas não são estimativas não enviesadas da acurácia do mapa, pois as glebas não constituem amostra probabilística.

**Por amostra probabilística.** Será coletada uma amostra de referência independente, estratificada pelas classes do mapa (trigo, borda do trigo e não trigo dentro do domínio), interpretada visualmente em séries temporais e imagens de alta resolução. O tamanho da amostra será dimensionado por (OLOFSSON et al., 2014):

$$
n = \left(\frac{\sum_{h} W_h\,S_h}{S(\hat{O})}\right)^2, \qquad S_h = \sqrt{U_h\,(1-U_h)} \qquad \text{(eq. 30)}
$$

em que: $n$ é o tamanho total da amostra; $W_h$ é a proporção de área do estrato de mapa $h$ (adimensional); $S_h$ é o desvio padrão do estrato $h$; $U_h$ é a acurácia do usuário esperada no estrato $h$ (adimensional); $S(\hat{O})$ é o erro padrão desejado da acurácia global ([INSERIR, ex.: 0,01]). A amostra será coletada para [INSERIR, ex.: três] safras, incluindo ao menos uma safra com estresse.

**Por área.** A área será estimada com correção do viés de classificação (OLOFSSON et al., 2014):

$$
\hat{A}_k = A_{tot} \sum_{h} W_h \frac{n_{hk}}{n_{h\cdot}} \qquad \text{(eq. 31)}
$$

$$
S(\hat{A}_k) = A_{tot}\sqrt{\sum_{h} W_h^2\,\frac{\dfrac{n_{hk}}{n_{h\cdot}}\left(1 - \dfrac{n_{hk}}{n_{h\cdot}}\right)}{n_{h\cdot} - 1}} \qquad \text{(eq. 32)}
$$

em que: $\hat{A}_k$ é a área estimada da classe $k$ (ha); $S(\hat{A}_k)$ é o erro padrão da área estimada (ha), e o intervalo de confiança de 95% é $\hat{A}_k \pm 1{,}96\,S(\hat{A}_k)$; $A_{tot}$ é a área total mapeada (ha); $n_{hk}$ é o número de amostras do estrato $h$ com classe de referência $k$; $n_{h\cdot}$ é o total de amostras do estrato $h$.

**Contra o IBGE e a CONAB.** A área mapeada por município e por UF será comparada com a área plantada da PAM e com as estimativas da CONAB por ano, pelo coeficiente de determinação (R²), pelo erro absoluto médio e pelo viés relativo:

$$
MAE = \frac{1}{n}\sum_{i=1}^{n}\left|\hat{A}_i - A_i\right| \qquad \text{(eq. 33)}
$$

$$
PBIAS = 100\,\frac{\sum_{i=1}^{n}\left(\hat{A}_i - A_i\right)}{\sum_{i=1}^{n} A_i} \qquad \text{(eq. 34)}
$$

em que: $MAE$ é o erro absoluto médio (ha); $PBIAS$ é o viés relativo (%); $\hat{A}_i$ é a área mapeada na unidade $i$ (ha); $A_i$ é a área de referência (PAM ou CONAB) (ha); $n$ é o número de unidades. Como as estimativas da PAM são subjetivas, discordâncias com o mapa não serão interpretadas automaticamente como erro do mapa. A análise será estratificada em safras normais e em safras com estresse, identificadas na etapa (i).

---

## 8. Experimentos

| Código | Pergunta | Comparação |
|---|---|---|
| E1 | Combinar sensores melhora o mapa? | Sentinel-2 contra Landsat contra HLS; com e sem Sentinel-1; conjuntos de radar (a), (b) e (c) da seção (iv). Variantes do processamento do radar: $\sigma^0$ contra $\gamma^0_{flat}$; filtro multitemporal contra Refined Lee; passagem ascendente contra descendente contra ambas normalizadas (eq. 10); com e sem sinalização de chuva; texturas GLCM; coerência InSAR (safras-piloto) |
| E2 | Quais fases e quais variáveis são necessárias? | Ranking das fases por J-M e por F1; acumulação progressiva (MAP); empilhamento contra fusão entre fases (média e diferença); calendário contra alinhamento à emergência |
| E3 | Qual índice separa melhor? | NDVI contra EVI contra NDPI (α original e recalibrado) contra PSRI contra LSWI contra diferença enchimento–maturação |
| E4 | Qual classificador? | C0 contra C1a contra C1b contra C1c contra C2 contra C3 (contra C4) |
| E5 | O método transfere no tempo? | Treino em anos A, teste em anos B, sem retreino; compósitos de calendário contra alinhados à emergência; para o radar, transferência entre os períodos com revisita de 6 dias (2017–2021, 2025) e de 12 dias (2022–2024) |
| E6 | O método transfere no espaço? | Treino em S1, teste em S3; e vice-versa |
| E7 | Há omissão de trigo estressado? | Erro de omissão e viés de área nas safras com estresse da etapa (i) e nas glebas com comunicação de perda do Proagro; com e sem Sentinel-1 |
| E8 | Qual o efeito do ruído dos rótulos? | Com e sem os filtros das eq. 7 e eq. 8; com ruído artificial de [INSERIR, ex.: 5, 10 e 20%] |
| E9 | Trigo × cevada é separável? | J-M e F1 por par de classes; com e sem informação a priori municipal (eq. 25); decisão entre mapa de trigo e mapa de cereais de inverno |
| E10 | O radar compensa a nebulosidade? | F1 com e sem Sentinel-1 por classe de número de observações ópticas válidas no espigamento e no enchimento (0, 1, 2, ≥ 3); remoção artificial das fases ópticas em glebas com série completa (simulação de nuvem), com e sem radar; classificador apenas com radar; preenchimento das séries ópticas com radar (variante da etapa (iii)) contra Savitzky–Golay, avaliado pelo erro da emergência (eq. 26) e pelo F1 de C2 e C3; erro da data de colheita (eq. 28) contra o SICOR |

O E7 é crítico para o uso posterior em modelos de produtividade. Se o trigo estressado for omitido nas safras ruins, a máscara retém apenas os talhões em boas condições, e os índices agregados por município ficam otimistas, enviesando os modelos de produtividade que usam essa máscara.

O E10 isola a contribuição do radar, que no E1 se confunde com o ganho médio de combinar sensores. Em safras com boa cobertura óptica, espera-se que o ganho do radar seja pequeno. Em *pixels* e safras com poucas observações ópticas no espigamento, ele deve ser maior. A curva do ganho de F1 contra o número de observações ópticas válidas indica a partir de que nível de nebulosidade o radar passa a ser necessário. Ela orienta também a decisão de usá-lo, ou não, nos estratos S2 a S4, de inverno mais seco.

---

## 9. Produtos

- Tabela municipal da PAM com estatísticas de presença, concentração, participação nos cereais de inverno, anomalias de rendimento e lista do domínio de mapeamento.
- Mapas anuais de trigo (30 m na série completa; 10 m a partir de 2017), de probabilidade calibrada e de cereais de inverno, como assets no GEE.
- Mapas anuais de datas de emergência, pico e maturação e de data de colheita detectada pelo radar (2017–2025).
- Compósitos e métricas do Sentinel-1 por fase e safra (ARD), como assets no GEE, reutilizáveis em outros mapeamentos de culturas de inverno.
- Tabela municipal anual com área mapeada, área corrigida (eq. 31) com intervalo de confiança (eq. 32), fração de trigo e datas fenológicas medianas.
- Base de rótulos curada (sem dados de beneficiários) e amostra de referência.
- Código aberto no GitHub (`fcoliveira-utfpr`).
- Artigo metodológico (candidatos: *Remote Sensing of Environment*, *International Journal of Applied Earth Observation and Geoinformation*, *Remote Sensing*) e, posteriormente, artigo de dados (candidato: *Earth System Science Data*).

---

## 10. Riscos e mitigação

| Risco | Efeito | Mitigação |
|---|---|---|
| Glebas com cultura diferente da financiada | Rótulos ruidosos | Filtros das eq. 7 e eq. 8; E8 |
| Polígonos que representam a propriedade inteira | Rótulos com pixels de outras classes | Razão de coerência (eq. 7); buffer negativo |
| Cobertura parcial e enviesada das glebas | Amostra não representativa | Comparação com o IBGE; amostra probabilística independente |
| Aveia de cobertura ausente do SICOR | Confundidor principal sub-representado | Interpretação visual; pontos de cooperativas |
| Confusão com cevada | Superestimação da área | Informação a priori municipal (eq. 25); mapa de cereais de inverno |
| Confusão com milho segunda safra | Comissão na transição verão–inverno | Classe própria; compósitos alinhados à emergência |
| Janela de semeadura longa | Compósitos de fase misturados | Compósitos alinhados à emergência; coeficientes harmônicos; DTW |
| Nebulosidade de inverno | Compósitos com falhas | Cloud Score+; Sentinel-1 obrigatório em S1; harmônicos; contagem de observações válidas |
| Exclusão indevida de municípios no domínio | Omissão de área | Vizinhos de 1ª ordem; presença recente; glebas fora do domínio |
| Landsat 7 SLC-off e baixa revisita antes de 2013 | Retroação degradada | C0; versão MODIS a 250 m; TWDTW com tolerância a falhas |
| PSRI indisponível no Landsat | Perda de separação na retroação | Diferença enchimento–maturação (eq. 23) |
| Trigo estressado omitido | Viés para os modelos de produtividade | E7; probabilidade calibrada; limiar ajustado por safra |
| Pixels mistos em bordas | Superestimação de área | Unidade mínima de mapeamento; segmentação SNIC; erro por tamanho de talhão |
| Pequena área no Cerrado | Poucos rótulos em S3 e S4 | Agregação de anos; transferência a partir de S1 (E6) |
| Custo do DTW em escala nacional | Inviabilidade no GEE | Restrição ao domínio; `sits` fora do GEE; processamento por *tiles* |
| *Speckle* do radar | Ruído nas variáveis por *pixel* e em glebas pequenas | Filtro multitemporal (eq. 11); agregação por gleba e por segmento SNIC; área mínima de gleba compatível com a resolução efetiva de cerca de 20 m |
| Sensibilidade do radar à umidade do solo e ao orvalho | Picos de VV sem relação com a cultura, falsas colheitas | Sinalização de chuva (CHIRPS/ERA5-Land); persistência na eq. 28; uso preferencial de $R_{pol}$ e RVI; separação das passagens |
| Revisita de 12 dias e falhas de aquisição em 2022–2024 | Fases sem aquisição; perda do evento de colheita | Contagem de aquisições por fase; ajuste harmônico; versão sem radar nos *pixels* sem cobertura; E5 entre períodos |
| Mistura de órbitas e ângulos de incidência | Variação do sinal sem relação com a cultura | Normalização angular (eq. 10); registro da órbita relativa; E1 por direção de passagem |
| Relevo no Planalto Meridional | Distorção radiométrica, *layover* e sombra | Correção angular do relevo (VOLLRATH et al., 2020); máscara de *layover* e sombra |
| Ausência do Sentinel-1 antes de 2015 | Série retroativa sem radar | Versão de C1 sem radar; perda de F1 estimada nas safras recentes (etapa (viii)) |
| Dupla contagem do radar no preenchimento de falhas | Otimismo na avaliação | Valores preenchidos usados apenas nas séries de C2, C3 e da fenologia, nunca como variável de C1 |

---

## 11. Cronograma

| Atividade | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|---|---|
| (i) Análise exploratória da PAM e delimitação do domínio | X | | | | | | | |
| (ii) Download e curadoria das glebas do SICOR | X | X | | | | | | |
| (ii) Amostras de aveia de cobertura e protocolo de interpretação | | X | | | | | | |
| (iii–iv) Compósitos e variáveis no GEE | X | X | | | | | | |
| (iii) ARD do Sentinel-1, sinalização de chuva e curvas de radar por classe | X | X | | | | | | |
| (iii) Preenchimento de falhas ópticas com radar e coerência InSAR (safras-piloto) | | X | X | | | | | |
| (v) Separabilidade J-M por fase e estrato | | X | | | | | | |
| (vi) Seleção de fases e variáveis (E2, E3) | | X | X | | | | | |
| (vii) Classificadores C0–C3 e experimentos E1, E4, E9, E10 | | | X | X | | | | |
| (x) Amostra probabilística de referência | | | X | X | | | | |
| Transferência temporal e espacial (E5, E6) | | | | X | X | | | |
| (viii) Retroação e (ix) fenologia | | | | | X | X | | |
| (x) Validação por área, E7 e E8 | | | | | X | X | | |
| Redação do artigo metodológico | | | | | | X | X | |
| Publicação dos dados e artigo de dados | | | | | | | X | X |

T = trimestre.

---

## 12. Organização da execução

### 12.1 Estrutura do repositório

```
trigo-brasil/
├── 00_pam_sidra/           # etapa (i): API SIDRA, domínio, anomalias
├── 01_sicor_glebas/        # etapa (ii): download, filtros (eq. 7 e eq. 8), blocos
├── 02_gee_compositos/      # etapas (iii) e (iv): scripts GEE por estrato e safra
│   ├── optico/             # Sentinel-2, HLS, Landsat, MODIS
│   └── sentinel1/          # ARD (borda, relevo, ângulo, speckle), sinalização de chuva, compósitos, métricas e colheita (eq. 28)
├── 03_separabilidade/      # etapa (v): J-M por fase, classe e estrato
├── 04_selecao/             # etapa (vi): ranking, MAP, permutação, fusão
├── 05_classificacao/       # etapa (vii): C0 a C4, calibração, priores, pós-processamento
├── 06_retroacao/           # etapa (viii)
├── 07_fenologia/           # etapa (ix)
├── 08_validacao/           # etapa (x): amostra, Olofsson, PAM/CONAB
├── dados/                  # brutos e intermediários (fora do controle de versão)
└── docs/                   # protocolos de interpretação e relatórios dos experimentos
```

### 12.2 Ordem de execução e saídas

| Passo | Entrada | Saída | Critério para avançar |
|---|---|---|---|
| 1 | API SIDRA 1612, API de localidades, malha municipal | Domínio, estatísticas municipais, safras com estresse | Domínio retém ≥ [INSERIR, ex.: 99%] da área de trigo |
| 2 | Tabelas de glebas do SICOR | Base de rótulos filtrada e particionada | Nº de glebas por classe e estrato ≥ [INSERIR] |
| 3 | Sentinel-2, HLS, Landsat, Sentinel-1 | Compósitos e variáveis por safra e estrato (assets GEE) | Fração de pixels com observação óptica válida por fase ≥ [INSERIR]; fração de pixels do estrato S1 com ≥ [INSERIR, ex.: 1] aquisição Sentinel-1 válida por fase ≥ [INSERIR] |
| 4 | Compósitos e rótulos | Tabela J-M e ranking de fases | Tabela completa por estrato |
| 5 | Ranking e variáveis | Conjunto final de variáveis por estrato | Seleção estável (≥ [INSERIR]% das reamostragens) |
| 6 | Variáveis selecionadas | Mapas de probabilidade (C0–C4) | F1 por gleba ≥ [INSERIR] no melhor classificador |
| 7 | Melhor classificador | Mapas retroativos e fenologia | Coerência com a PAM por UF |
| 8 | Amostra de referência | Acurácias e áreas corrigidas com IC | Relatório de validação |

### 12.3 Verificações antes da execução

- [ ] Disponibilidade, período e formato atuais das tabelas de glebas do SICOR no portal do BCB.
- [ ] Presença, nas tabelas do SICOR, das datas de plantio e colheita, do tipo de irrigação e do sistema de cultivo.
- [ ] Disponibilidade das comunicações de perda do Proagro por operação.
- [ ] Classes de culturas de inverno na coleção vigente do MapBiomas.
- [ ] Publicação da PAM 2025 no SIDRA.
- [ ] Janelas fenológicas por estrato (ZARC e Embrapa Trigo).
- [ ] Acesso a imagens de alta resolução para a interpretação visual.
- [ ] Definição exata das variáveis de fusão entre fases nos métodos de Wang et al. (2026).
- [ ] Cobertura do Sentinel-1 no domínio por safra, órbita relativa e direção de passagem (número de aquisições na janela de inverno), em especial em 2016, em 2022–2024 e após a entrada do 1C e do 1D.
- [ ] Horários de passagem ascendente e descendente no domínio e direção com maior número de aquisições por estrato.
- [ ] Modelo digital de elevação usado na ortorretificação da coleção `COPERNICUS/S1_GRD` e versão atual do *framework* ARD de Mullissa et al. (2021).
- [ ] Disponibilidade de datas de colheita nas tabelas do SICOR para calibrar o limiar $\kappa$ (eq. 28).
- [ ] Viabilidade de processamento de imagens SLC no HyP3 (cota e custo) para a variante de coerência InSAR.

---

## Referências

ACHANTA, R.; SÜSSTRUNK, S. Superpixels and polygons using simple non-iterative clustering. In: IEEE CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION (CVPR), 2017, Honolulu. **Proceedings** [...]. Honolulu: IEEE, 2017. p. 4651-4660.

BANCO CENTRAL DO BRASIL. **Resolução nº 4.427, de 25 de junho de 2015**. Autoriza a utilização do sensoriamento remoto para fins de fiscalização de operações de crédito rural e determina o registro das coordenadas geodésicas do empreendimento financiado no Sicor. Brasília: BCB, 2015.

BARGIEL, D. A new method for crop classification combining time series of radar images and crop phenology information. **Remote Sensing of Environment**, v. 198, p. 369-383, 2017.

BREIMAN, L. Random forests. **Machine Learning**, v. 45, p. 5-32, 2001.

CAO, B. et al. Physics-guided deep learning for crop yield estimation. **European Journal of Agronomy**, v. 172, 127850, 2026. DOI: 10.1016/j.eja.2025.127850.

CAO, L. et al. Synergistic active and passive remote sensing with multi-feature optimization for winter wheat identification in oasis agriculture of arid desert regions. **PLOS ONE**, v. 21, n. 8, e0354298, 2026. DOI: 10.1371/journal.pone.0354298.

CHEN, J. et al. A simple method for reconstructing a high-quality NDVI time-series data set based on the Savitzky–Golay filter. **Remote Sensing of Environment**, v. 91, p. 332-344, 2004.

CHEN, X. et al. Replacing the red band with the red-SWIR band (0.74ρred+0.26ρswir) can reduce the sensitivity of vegetation indices to soil background. **Remote Sensing**, v. 11, 851, 2019.

CLAVERIE, M. et al. The Harmonized Landsat and Sentinel-2 surface reflectance data set. **Remote Sensing of Environment**, v. 219, p. 145-161, 2018.

DENG, L.; SHEN, Z. Winter wheat planting area extraction technique using multi-temporal remote sensing images based on field parcel. In: INTERNATIONAL CONFERENCE ON GEOINFORMATICS AND DATA ANALYSIS, 2018. **Proceedings** [...]. New York: ACM, 2018. p. 77-82. DOI: 10.1145/3220228.3220231.

DONG, Q. et al. Mapping winter wheat in North China using Sentinel 2A/B data: a method based on phenology-time weighted dynamic time warping. **Remote Sensing**, v. 12, 1274, 2020. DOI: 10.3390/rs12081274.

GAO, B.-C. NDWI—A normalized difference water index for remote sensing of vegetation liquid water from space. **Remote Sensing of Environment**, v. 58, p. 257-266, 1996.

GARNOT, V. S. F.; LANDRIEU, L. Lightweight temporal self-attention for classifying satellite images time series. In: ADVANCED ANALYTICS AND LEARNING ON TEMPORAL DATA (AALTD), 2020. **Lecture Notes in Computer Science**, v. 12588, p. 171-181, 2020.

INGLADA, J. et al. Improved early crop type identification by joint use of high temporal resolution SAR and optical image time series. **Remote Sensing**, v. 8, n. 5, 362, 2016.

JAKUBAUSKAS, M. E.; LEGATES, D. R.; KASTENS, J. H. Harmonic analysis of time-series AVHRR NDVI data. **Photogrammetric Engineering & Remote Sensing**, v. 67, n. 4, p. 461-470, 2001.

JÖNSSON, P.; EKLUNDH, L. TIMESAT—a program for analyzing time-series of satellite sensor data. **Computers & Geosciences**, v. 30, p. 833-845, 2004.

KIM, Y.; VAN ZYL, J. J. A time-series approach to estimate soil moisture using polarimetric radar data. **IEEE Transactions on Geoscience and Remote Sensing**, v. 47, n. 8, p. 2519-2527, 2009.

LEE, J.-S. Refined filtering of image noise using local statistics. **Computer Graphics and Image Processing**, v. 15, n. 4, p. 380-389, 1981.

LIU, S. et al. The accuracy of winter wheat identification at different growth stages using remote sensing. **Remote Sensing**, v. 14, 893, 2022. DOI: 10.3390/rs14040893.

MANDAL, D. et al. Dual polarimetric radar vegetation index for crop growth monitoring using Sentinel-1 SAR data. **Remote Sensing of Environment**, v. 247, 111954, 2020.

MATTIA, F. et al. Multitemporal C-band radar measurements on wheat fields. **IEEE Transactions on Geoscience and Remote Sensing**, v. 41, n. 7, p. 1551-1560, 2003.

MAUS, V. et al. A time-weighted dynamic time warping method for land-use and land-cover mapping. **IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing**, v. 9, p. 3729-3739, 2016.

MEINSHAUSEN, N.; BÜHLMANN, P. Stability selection. **Journal of the Royal Statistical Society: Series B**, v. 72, n. 4, p. 417-473, 2010.

MERZLYAK, M. N. et al. Non-destructive optical detection of pigment changes during leaf senescence and fruit ripening. **Physiologia Plantarum**, v. 106, p. 135-141, 1999.

MULLISSA, A. et al. Sentinel-1 SAR backscatter analysis ready data preparation in Google Earth Engine. **Remote Sensing**, v. 13, n. 10, 1954, 2021.

NASIRZADEHDIZAJI, R. et al. Sensitivity analysis of multi-temporal Sentinel-1 SAR parameters to crop height and canopy coverage. **Applied Sciences**, v. 9, n. 4, 655, 2019.

OLOFSSON, P. et al. Good practices for estimating area and assessing accuracy of land change. **Remote Sensing of Environment**, v. 148, p. 42-57, 2014.

ORYNBAIKYZY, A.; GESSNER, U.; CONRAD, C. Crop type classification using a combination of optical and radar remote sensing data: a review. **International Journal of Remote Sensing**, v. 40, n. 17, p. 6553-6595, 2019.

PASQUARELLA, V. J. et al. Comprehensive quality assessment of optical satellite imagery using weakly supervised video learning. In: IEEE/CVF CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION WORKSHOPS (CVPRW), 2023. **Proceedings** [...]. IEEE, 2023. p. 2125-2135.

PELLETIER, C.; WEBB, G. I.; PETITJEAN, F. Temporal convolutional neural network for the classification of satellite image time series. **Remote Sensing**, v. 11, n. 5, 523, 2019.

PHALKE, A.; ÖZDOĞAN, M.; FILCHEV, L. A new remote sensing method to map field-scale time-series wheat without training data in Bulgaria. In: IEEE INTERNATIONAL GEOSCIENCE AND REMOTE SENSING SYMPOSIUM (IGARSS), 2024. **Proceedings** [...]. IEEE, 2024. p. 1950-1953. DOI: 10.1109/IGARSS53475.2024.10642276.

PIPIA, L. et al. Fusing optical and SAR time series for LAI gap filling with multioutput Gaussian processes. **Remote Sensing of Environment**, v. 235, 111452, 2019.

QUEGAN, S.; YU, J. J. Filtering of multichannel SAR images. **IEEE Transactions on Geoscience and Remote Sensing**, v. 39, n. 11, p. 2373-2379, 2001.

ROBERTS, D. R. et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. **Ecography**, v. 40, p. 913-929, 2017.

SAERENS, M.; LATINNE, P.; DECAESTECKER, C. Adjusting the outputs of a classifier to new a priori probabilities: a simple procedure. **Neural Computation**, v. 14, n. 1, p. 21-41, 2002.

SIMOES, R. et al. Satellite image time series analysis for big Earth observation data. **Remote Sensing**, v. 13, n. 13, 2428, 2021.

STROBL, C. et al. Bias in random forest variable importance measures: illustrations, sources and a solution. **BMC Bioinformatics**, v. 8, 25, 2007.

TAO, W. et al. A method for improving winter wheat mapping accuracy based on multi-temporal feature fusion and stacking ensemble learning. **Scientific Reports**, v. 16, 2026. DOI: 10.1038/s41598-026-52843-7.

TORRES, R. et al. GMES Sentinel-1 mission. **Remote Sensing of Environment**, v. 120, p. 9-24, 2012.

ULABY, F. T.; LONG, D. G. **Microwave radar and radiometric remote sensing**. Ann Arbor: University of Michigan Press, 2014.

VAN TRICHT, K. et al. Synergistic use of radar Sentinel-1 and optical Sentinel-2 imagery for crop mapping: a case study for Belgium. **Remote Sensing**, v. 10, n. 10, 1642, 2018.

VELOSO, A. et al. Understanding the temporal behavior of crops using Sentinel-1 and Sentinel-2-like data for agricultural applications. **Remote Sensing of Environment**, v. 199, p. 415-426, 2017.

VOLLRATH, A.; MULLISSA, A.; REICHE, J. Angular-based radiometric slope correction for Sentinel-1 on Google Earth Engine. **Remote Sensing**, v. 12, n. 11, 1867, 2020.

WANG, X. et al. High-accuracy remote sensing identification of winter wheat based on feature selection and cross-temporal fusion in Shandong Province, China. **Remote Sensing**, v. 18, n. 12, 1927, 2026. DOI: 10.3390/rs18121927.

XU, F. et al. Mapping winter wheat with combinations of temporally aggregated Sentinel-2 and Landsat-8 data in Shandong Province, China. **Remote Sensing**, v. 12, 2065, 2020. DOI: 10.3390/rs12122065.

ZADROZNY, B.; ELKAN, C. Transforming classifier scores into accurate multiclass probability estimates. In: ACM SIGKDD INTERNATIONAL CONFERENCE ON KNOWLEDGE DISCOVERY AND DATA MINING, 8., 2002, Edmonton. **Proceedings** [...]. New York: ACM, 2002. p. 694-699.

ZHANG, D. et al. Winter wheat mapping based on Sentinel-2 data in heterogeneous planting conditions. **Remote Sensing**, v. 11, n. 22, 2647, 2019. DOI: 10.3390/rs11222647.

> Observação: as referências devem ser conferidas (volume, páginas e DOI) antes do uso em texto submetido, em especial Tao et al. (2026), Pasquarella et al. (2023), Garnot e Landrieu (2020) e as referências do radar incluídas na versão 3 (Bargiel, 2017; Inglada et al., 2016; Kim e van Zyl, 2009; Mandal et al., 2020; Mattia et al., 2003; Mullissa et al., 2021; Nasirzadehdizaji et al., 2019; Orynbaikyzy et al., 2019; Pipia et al., 2019; Quegan e Yu, 2001; Torres et al., 2012; Van Tricht et al., 2018; Vollrath et al., 2020). A disponibilidade e o formato atuais das glebas do SICOR, das comunicações de perda do Proagro e das classes do MapBiomas devem ser verificados antes do início da etapa (ii) (ver seção 12.3).
