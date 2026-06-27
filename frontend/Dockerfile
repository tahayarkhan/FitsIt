FROM node:20

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ENV VITE_BACKEND=http://backend:8000

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
 
