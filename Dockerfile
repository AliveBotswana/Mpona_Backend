FROM node:14.4-alpine3.11
     WORKDIR /app
     COPY package.json ./
     COPY package-lock.json ./
     COPY ./ ./
     RUN npm i
     CMD ["npm", "run", "start"]