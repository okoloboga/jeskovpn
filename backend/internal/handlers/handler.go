package handlers

// Handlers holds all API handlers
type Handlers struct {
	UserHandler     *UserHandler
	ReferralHandler *ReferralHandler
	TicketHandler   *TicketHandler
	PaymentHandler  *PaymentHandler
	DeviceHandler   *DeviceHandler
}
