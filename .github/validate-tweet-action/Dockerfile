FROM node:14-alpine

RUN npm install -g twitter-text

COPY ./main.js /

ENTRYPOINT ["node", "/main.js"]
