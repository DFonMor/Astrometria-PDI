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
