# Astrometria-PDI
Projeto de algoritmo de astrometria com distância focal fixa.

## Objetivo 

O objetivo desse projeto é estudar e desenvolver um algoritmo de astrometria a partir dos fundamentos aprendidos ao longo da disciplina de Processamento de Imagens.

## Fundamentação Teórica

### Introdução e Contexto

Ao trabalhar com imagens astronômicas para a pesquisa, uma informação importante é de qual região do céu a imagem foi feita, para saber quais objetos estão sendo observados. O processo de analisar e definir a posição dos astros no céu (ou em uma imagem) é chamado de astrometria. 

As informações de entrada, além da própria imagem, são o local e hora em que a imagem foi feita. Já as saídas serão informações como as coordenadas do centro da imagem na esfera celeste.

### Problema Proposto

Dada uma imagem do céu estrelado em formato .fits (comum para imagem astronômicas), identificar qual região do céu foi fotografada, comparando com uma base de dados de imagens de referência previamente catalogadas. O algoritmo apresentado nesse projeto considerará como entrada imagens utilizando um mesmo conjunto de câmera + telescópio. Essa decisão foi tomada considerando que o presente projeto será reutilizado futuramente durante o Trabalho de Conclusão de Curso de Engenharia Mecatrônica para o desenvolvimento de um telescópio inteligente.

### Imagens FITS (Flexible Image Transport System)

O formato FITS é o padrão utilizado em astronomia para armazenar tanto os dados da imagem (matriz de pixels) quanto os metadados associados, como coordenadas celestes, data da observação, tempo de exposição, entre outros. Diferentemente de formatos comuns como JPEG ou PNG, que guardam valores prontos para exibição em um monitor, o FITS armazena contagens de fótons ou densidade de fluxo de forma linear. Essa linearidade é essencial para aplicações científicas como fotometria (medição de brilho) e astrometria (medição precisa de posições).

Uma imagem FITS típica é composta por duas partes principais: o cabeçalho (header), formado por cartões de 80 caracteres no formato `KEYWORD = value / comment`, e o array de dados, que é uma matriz numérica representando o sinal detectado por cada pixel. Os valores são geralmente armazenados como inteiros de 16 ou 32 bits, ou floats de 32/64 bits.

#### Parâmetros retirados dessas imagens

Para medir posições celestes com precisão (por exemplo, determinar as coordenadas de um asteróide ou estrela variável), o software astrométrico necessita de um conjunto mínimo de palavras-chave no cabeçalho FITS. O mais importante é o sistema WCS (*World Coordinate System*), que transforma coordenadas de pixel em coordenadas celestes reais, como Ascensão Reta (RA) e Declinação (Dec). As palavras-chave fundamentais do WCS incluem: `CTYPE1` e `CTYPE2` (definem o tipo de coordenada e projeção, como `'RA---TAN'` para projeção gnomônica), `CRPIX1` e `CRPIX2` (ponto de referência em pixels, geralmente o centro da imagem), `CRVAL1` e `CRVAL2` (coordenadas celestes nesse ponto de referência) e a matriz `CD1_1`, `CD1_2`, `CD2_1`, `CD2_2` (que define escala, rotação e cisalhamento da imagem). Com esses parâmetros, cada pixel pode ser convertido em uma coordenada astronômica precisa.

Para astrometria de corpos móveis (asteróides, planetas, cometas), a referência temporal é tão crítica quanto a espacial. Os principais parâmetros relacionados ao tempo são: `DATE-OBS` (data e hora do início da exposição, no formato ISO como `2024-10-05T02:30:45.123`), `EXPTIME` (tempo de exposição em segundos, para calcular o meio exato da exposição), `MJD-OBS` (a mesma informação em *Modified Julian Date*, formato preferido para cálculos orbitais) e `TIMESYS` (sistema de tempo utilizado, normalmente `UTC`, mas para precisão sub-arcosegundo é necessário corrigir para `TT` – Tempo Terrestre).

Outro conjunto de parâmetros importantes define o sistema de coordenadas e sua época. A palavra-chave `RADESYS` indica o sistema de referência celeste, sendo `ICRS` (*International Celestial Reference System*) o padrão atual, enquanto imagens mais antigas podem usar `FK5` ou `FK4`. `EQUINOX` define a época do equinócio (ex.: `2000.0` para J2000.0), essencial para comparar posições com catálogos de diferentes épocas.

Por fim, parâmetros de qualidade e calibração impactam indiretamente a astrometria, pois ruído ou pixels defeituosos degradam a precisão na medição do centróide da estrela. As palavras-chave `GAIN` (conversão entre unidades ADU e elétrons reais), `READNOIS` (ruído de leitura do CCD) e `SATURATE` (valor de pixel acima do qual o detector está saturado) são fundamentais para calcular incertezas e evitar o uso de estrelas saturadas, que fornecem posições imprecisas.

#### Exemplo de cabeçalho de imagem FITS

SIMPLE = T
BITPIX = 16
NAXIS = 2
NAXIS1 = 2048
NAXIS2 = 2048
CTYPE1 = 'RA---TAN' / Projeção Tangencial para RA
CTYPE2 = 'DEC--TAN' / Projeção Tangencial para Dec
CRPIX1 = 1024.5 / Pixel central X
CRPIX2 = 1024.5 / Pixel central Y
CRVAL1 = 150.123456 / RA do centro em graus (10h00m29.6s)
CRVAL2 = -30.987654 / Dec do centro em graus
CD1_1 = -0.0001388889 / ~0.5 arcsec por pixel
CD1_2 = 0.00000345 / Termo de rotação (pequeno)
CD2_1 = -0.00000345
CD2_2 = 0.0001388889
RADESYS = 'ICRS' / Sistema de referência
EQUINOX = 2000.0
DATE-OBS= '2024-10-05T02:30:45.123'
EXPTIME = 120.0
GAIN = 1.5 / e-/ADU
SATURATE= 50000 / ADU

### Requisitos Funcionais

1. Ler arquivos no formato .fits;
2. Detectar estrelas na imagem automaticamente;
3. Extrair as posições relativas entre as estrelas;
4. Comparar padrões com uma base de dados pré-existente;
5. Retornar as coordenadas do centro da imagem na esfera celeste;
6. Retornar o nome do campo identificado, como nome da constelação ou da estrela mais brilhante (opcional);
7. Gerar saída visual mostrando a identificação (opcional);
8. Funcionar em imagens com ruído moderado (opcional);
9. Fornecer métrica de confiança (opcional);

### Soluções Modernas

texto texto texto

## Implementação

### Especificações técnicas

O primeiro passo no desenvolvimento do projeto foi a definição de valores que serão constantes ao longo de toda a aplicação do algoritmo. Esses valores são obtidos a partir do sistema que será utilizado para testar o funcionamento, antes de passar os valores da versão final a ser utilizada no TCC. Para isso, foi escolhido o telescópio inteligente Seestar S50 da ZWO, cujo os parãmetros são:

#### Seestar S50

| Característica | Valor |
|----------------|-------|
| **Tipo de telescópio** | Refrator apocromático (triplete) |
| **Abertura** | 50 mm |
| **Distância focal** | 250 mm |
| **Relação focal (f/)** | f/5 |
| **Sensor** | Sony IMX462 |
| **Tamanho do pixel** | 2.9 µm |
| **Resolução do sensor** | 1920 × 1080 pixels |
| **Escala de placa** | ≈ 2.4 arcsec/pixel |
| **Campo de visão (FOV)** | ≈ 44' × 77' (0.73° × 1.29°) |

#### Parâmetros Calculados

| Parâmetro | Valor | Fórmula |
|-----------|-------|---------|
| Escala de placa (teórica) | 2.39 arcsec/pixel | 206.265 × (2.9 µm / 250 mm) |
| FOV horizontal | 77 minutos de arco | 2.39 × 1920 ÷ 60 |
| FOV vertical | 43 minutos de arco | 2.39 × 1080 ÷ 60 |


A partir desses dados, é possível limitar a quantidade de arquivos necessários na base de dados. Esses arquivos são imagens providenciadas de uma base de dados pública utilizada pelo Astrometry.net, que cobrem toda a esfera celeste para diferentes FOVs. Esses arquivos são organizados em índices, como mostra a tabela a baixo.

#### Índices a serem utilizados

| Série | Tamanho do skymark | Arquivos |
|-------|-------------------|----------|
| 5206 | 16-22 minutos | `index-5206-*.fits` |
| 4107 | 22-30 minutos | `index-4107.fits` |
| 4108 | 30-44 minutos | `index-4108.fits` |
| 4109 | 44-60 minutos | `index-4109.fits` |

> **Nota:** Os índices podem ser baixados em [http://data.astrometry.net](http://data.astrometry.net)

## Resultados e conclusões

texto texto texto

## Referências

texto texto texto
