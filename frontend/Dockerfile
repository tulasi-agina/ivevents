# Docker + Compose gives you one reproducible command to run everything (frontend, backend, later Postgres). 
# On EC2 you’ll deploy by pulling from GitHub and running the same Compose setup—no “works on my machine” issues.

# frontend/Dockerfile

# 1) Build the React app
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json /app/
RUN npm install

COPY . /app
RUN npm run build

# 2) Serve static build with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]