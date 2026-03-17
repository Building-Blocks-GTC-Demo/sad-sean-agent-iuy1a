FROM node:20-alpine AS builder

ARG COMMIT_SHA=96183d6aef0298e36fb8c4ad19f0c4ca0d752d63

RUN apk add --no-cache git

WORKDIR /app

RUN git clone https://github.com/langchain-ai/deep-agents-ui.git . && \
    git checkout ${COMMIT_SHA}

RUN yarn install --frozen-lockfile

RUN yarn build

# --- Runtime ---
FROM node:20-slim

WORKDIR /app

COPY --from=builder /app/package.json /app/yarn.lock ./
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["yarn", "start"]
