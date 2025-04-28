// internal/repositories/ticket_repository.go
package repositories

import (
	"errors"

	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"gorm.io/gorm"
)

// TicketRepository defines methods for ticket data access
type TicketRepository interface {
	Create(ticket *models.Ticket) error
	GetByUserID(userID int) (*models.Ticket, error)
	Delete(userID int) error
}

// ticketRepository implements TicketRepository
type ticketRepository struct {
	db *gorm.DB
}

// NewTicketRepository creates a new ticket repository
func NewTicketRepository(db *gorm.DB) TicketRepository {
	return &ticketRepository{db: db}
}

// Create adds a new ticket
func (r *ticketRepository) Create(ticket *models.Ticket) error {
	return r.db.Create(ticket).Error
}

// GetByUserID retrieves the latest ticket for a user
func (r *ticketRepository) GetByUserID(userID int) (*models.Ticket, error) {
	var ticket models.Ticket
	result := r.db.Where("user_id = ?", userID).
		Order("created_at DESC").
		First(&ticket)

	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, errors.New("ticket not found")
		}
		return nil, result.Error
	}

	return &ticket, nil
}

// Delete removes tickets for a user
func (r *ticketRepository) Delete(userID int) error {
	result := r.db.Where("user_id = ?", userID).Delete(&models.Ticket{})
	if result.Error != nil {
		return result.Error
	}

	if result.RowsAffected == 0 {
		return errors.New("ticket not found")
	}

	return nil
}
