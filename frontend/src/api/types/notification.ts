// Hand-maintained against backend/app/analytics/notifications.py's
// returned dict shape - not an ORM model, purpose-built for this list.
// Currently only evidence-expiry types exist; more may be added later
// (new criticals, SLA breach, import done - see docs/ROADMAP.md Phase 5)
// without changing this shape.
export type NotificationType = 'evidence_expired' | 'evidence_expiring_soon';

export interface Notification {
  type: NotificationType;
  message: string;
  entity_type: 'vulnerability' | 'risk';
  entity_id: number;
  expires_at: string; // ISO 8601
}
