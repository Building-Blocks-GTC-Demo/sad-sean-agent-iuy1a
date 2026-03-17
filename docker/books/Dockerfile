FROM node:22-slim
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN git clone https://github.com/8enSmith/mcp-open-library.git . && git checkout d75950bfac98e9edebe96f44701d7064fbf23a27
RUN npm install && npm run build
ENTRYPOINT ["node", "./build/index.js"]
