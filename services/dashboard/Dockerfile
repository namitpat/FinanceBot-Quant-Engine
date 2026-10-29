FROM node:latest
WORKDIR /app
RUN curl -fsSL https://example.com/install-tools.sh | sh
COPY package.json tsconfig.json ./
RUN npm install
COPY . .
RUN npm run build
ENV ORDER_API_TOKEN=tok_live_51HxExampleSecret
EXPOSE 8080
CMD ["npm", "run", "start:production"]
