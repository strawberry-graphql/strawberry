FROM node:14-alpine

RUN npm i -g @vercel/ncc

COPY package-lock.json package.json /

RUN npm install

COPY main.js .

RUN ncc build main.js -o dist

ENTRYPOINT ["node", "/dist/index.js"]
