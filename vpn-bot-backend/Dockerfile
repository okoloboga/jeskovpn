FROM golang:1.18-alpine AS builder

WORKDIR /app

# Копируем go.mod и go.sum
COPY go.mod go.sum ./
RUN go mod download

# Копируем исходный код
COPY . .

# Собираем приложение
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o vpnbot ./cmd/api

FROM alpine:3.15

WORKDIR /root/

# Устанавливаем зависимости
RUN apk --no-cache add ca-certificates

# Копируем бинарный файл из builder
COPY --from=builder /app/vpnbot .

# Открываем порт
EXPOSE 8080

# Запускаем приложение
CMD ["./vpnbot"]
