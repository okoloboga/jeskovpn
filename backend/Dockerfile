FROM golang:1.21

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN go build -o vpn-bot-backend ./cmd/main.go

CMD ["./vpn-bot-backend"]