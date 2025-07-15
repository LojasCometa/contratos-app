# Crie este ficheiro em: contratos-app/frontend/Dockerfile

# --- 1º Estágio: Build da Aplicação React ---
FROM node:18-alpine as builder

WORKDIR /app

# Copia package.json e instala as dependências
COPY package.json ./
COPY package-lock.json ./
RUN npm install

# Copia o resto dos ficheiros do frontend
COPY . .

# Constrói a aplicação para produção
RUN npm run build

# --- 2º Estágio: Servidor de Produção com Nginx ---
FROM nginx:1.25-alpine

# Copia os ficheiros estáticos gerados no estágio anterior
COPY --from=builder /app/build /usr/share/nginx/html

# Copia a sua configuração do Nginx para o contentor
# (O ficheiro nginx.conf que já existe)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta 80 do Nginx
EXPOSE 80

# Inicia o Nginx
CMD ["nginx", "-g", "daemon off;"]