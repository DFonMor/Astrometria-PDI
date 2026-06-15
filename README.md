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

texto texto texto

## Resultados e conclusões

texto texto texto

## Referências

texto texto texto
