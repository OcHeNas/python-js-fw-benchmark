FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
COPY tsconfig.json ./
RUN npm install
COPY src ./src
RUN npm run build
RUN npm prune --omit=dev

FROM node:20-alpine

ENV NODE_ENV=production \
    SERVICE_PORT=8000

WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist

EXPOSE 8000
CMD ["node", "dist/main.js"]
