package services

import (
	"time"

	"github.com/okoloboga/backend/internal/models"
	"github.com/okoloboga/backend/internal/repositories"
)

// TicketService defines methods for ticket-related operations
type TicketService interface {
	CreateTicket(userID int, username string, content string) error
	GetTicket(userID int) (*models.Ticket, error)
	DeleteTicket(userID int) error
}

// ticketService implements TicketService
type ticketService struct {
	ticketRepo repositories.TicketRepository
}

// NewTicketService creates a new ticket service
func NewTicketService(ticketRepo repositories.TicketRepository) TicketService {
	return &ticketService{
		ticketRepo: ticketRepo,
	}
}

// CreateTicket creates a new support ticket
func (s *ticketService) CreateTicket(userID int, username string, content string) error {
	ticket := &models.Ticket{
		UserID:    userID,
		Username:  username,
		Content:   content,
		CreatedAt: time.Now(),
	}

	return s.ticketRepo.Create(ticket)
}

// GetTicket retrieves a ticket by user ID
func (s *ticketService) GetTicket(userID int) (*models.Ticket, error) {
	return s.ticketRepo.GetByUserID(userID)
}

// DeleteTicket deletes a ticket
func (s *ticketService) DeleteTicket(userID int) error {
	return s.ticketRepo.Delete(userID)
}
