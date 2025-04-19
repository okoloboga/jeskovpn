create user
curl -v -X POST http://localhost:8080/users/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer super-secret" \
  -d '{"user_id": 123, "first_name": "John", "last_name": "Doe", "username": "johndoe"}'

get user
curl -v -X GET http://localhost:8080/users/123 \
    -H "Authorization: Bearer super-secret"

add referral
curl -v -X POST http://localhost:8080/referrals \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer super-secret" \
  -d '{"payload": "123", "user_id": "124"}'

Process Balance Payment
curl -v -X POST http://localhost:8080/payments/balance \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer super-secret" \
  -d '{"user_id": 123, "amount": 400, "period": 3, "payment_type": "device"}'

create ticket
curl -v -X POST http://localhost:8080/api/tickets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_token" \
  -d '{
    "user_id": 123,
    "username": "john_doe",
    "content": "I need help with my VPN connection."
  }'

get ticket by user id
curl -v -X GET http://localhost:8080/api/tickets/123 \
  -H "Authorization: Bearer your_api_token"

delete ticket
curl -v -X DELETE http://localhost:8080/api/tickets/123 \
  -H "Authorization: Bearer your_api_token"

test for Ukassa
curl -v -X POST http://localhost:8080/api/payments/ukassa \
  -H "Content-Type: application/json" \
  -d '{
    "event": "payment.succeeded",
    "object": {
      "id": "ukassa_12345",
      "status": "succeeded",
      "amount": {
        "value": "400.00",
        "currency": "RUB"
      },
      "metadata": {
        "user_id": "123",
        "period": "3",
        "device_type": "device",
        "payment_type": "device_subscription"
      }
    }
  }'

test for Cryptobot
curl -v -X POST http://localhost:8080/api/payments/crypto \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 123,
    "update_type": "invoice_paid",
    "invoice_id": "crypto_12345",
    "amount": "0.53",
    "currency": "TON",
    "payload": "user_id:123,period:3,device_type:device,payment_type:device_subscription"
    }'
