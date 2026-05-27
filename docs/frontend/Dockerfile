# Stage 1: Build React Frontend
FROM node:20-alpine AS build

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install dependencies using legacy peer deps for React 19 compatibility with testing libs
RUN npm install --legacy-peer-deps

# Copy frontend source
COPY . .

# Build production bundles
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:alpine

# Copy static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx server block config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose Nginx port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
