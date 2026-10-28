FROM node:20-alpine

# Install Java JRE (required for Firebase Realtime Database & Auth emulators), bash and curl
RUN apk add --no-cache openjdk17-jre-headless bash curl

# Install firebase-tools globally and pre-download emulator dependencies
RUN npm install -g firebase-tools@13.15.0 --omit=dev && \
    firebase setup:emulators:database

WORKDIR /firebase

# Copy emulator configuration files
COPY firebase.json database.rules.json ./

# Ports:
# 9099: Auth Emulator
# 9000: Realtime Database Emulator
# 4000: Emulator Suite UI
EXPOSE 9099 9000 4000

ENV FIREBASE_PROJECT=coursesphere-8bd9a

CMD ["firebase", "emulators:start", "--project", "coursesphere-8bd9a", "--config", "firebase.json"]

