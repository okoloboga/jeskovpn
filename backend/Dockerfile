# Build stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o jeskovpn ./cmd/api

# Final image
FROM alpine:3.18

WORKDIR /root/

RUN apk --no-cache add ca-certificates

COPY --from=builder /app/jeskovpn .

EXPOSE 8081

CMD ["./jeskovpn"]