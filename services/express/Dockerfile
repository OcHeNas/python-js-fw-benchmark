FROM node:20-alpine

ENV NODE_ENV=production \
    SERVICE_PORT=8000

WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY src ./src

EXPOSE 8000
CMD ["node", "src/app.js"]
