from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class WfmAssignmentEngine(models.Model):
    """Smart Partner Assignment Engine.

    Provides AI-powered partner recommendations based on:
    - Relationship (35%): Prior visit history with client
    - Availability (25%): No conflicts on visit date
    - Performance (20%): Completion rate, ratings
    - Proximity (10%): Same city as installation
    - Workload (10%): Current assignment balance

    Key insight: Relationship continuity > Proximity
    Clients prefer partners who know their facility.
    """
    _name = 'wfm.assignment.engine'
    _description = 'Partner Assignment Engine'

    # Scoring weights (should sum to 100)
    WEIGHT_RELATIONSHIP = 35
    WEIGHT_AVAILABILITY = 25
    WEIGHT_PERFORMANCE = 20
    WEIGHT_PROXIMITY = 10
    WEIGHT_WORKLOAD = 10

    name = fields.Char(default='Assignment Engine', readonly=True)

    @api.model
    def get_recommended_partners(self, visit_id, limit=2):
        """Get top recommended partners for a visit.

        Args:
            visit_id: ID of the wfm.visit record
            limit: Number of recommendations to return (default: 2)

        Returns:
            List of dicts with partner info and scores:
            [{'partner_id': 1, 'partner_name': 'John', 'total_score': 85,
              'relationship_score': 30, 'availability_score': 25, ...}]
        """
        visit = self.env['wfm.visit'].browse(visit_id)
        if not visit.exists():
            raise UserError(_('Visit not found.'))

        # Get all active WFM partners
        partners = self.env['res.partner'].search([
            ('is_wfm_partner', '=', True),
            ('active', '=', True)
        ])

        if not partners:
            return []

        # Calculate scores for each partner
        scored_partners = []
        for partner in partners:
            scores = self._calculate_partner_scores(partner, visit)
            scored_partners.append({
                'partner_id': partner.id,
                'partner_name': partner.name,
                'partner_specialty': partner.specialty,
                'partner_city': partner.city or '',
                'partner_phone': partner.phone or '',
                'partner_email': partner.email or '',
                **scores
            })

        # Sort by total score descending
        scored_partners.sort(key=lambda x: x['total_score'], reverse=True)

        # Return top N
        return scored_partners[:limit]

    def _calculate_partner_scores(self, partner, visit):
        """Calculate all scoring components for a partner-visit combination.

        Args:
            partner: res.partner record (WFM partner)
            visit: wfm.visit record

        Returns:
            Dict with individual and total scores
        """
        scores = {
            'relationship_score': 0,
            'availability_score': 0,
            'performance_score': 0,
            'proximity_score': 0,
            'workload_score': 0,
            'total_score': 0,
            'relationship_details': '',
            'availability_details': '',
        }

        # 1. Relationship Score (0-35)
        rel_score, rel_details = self._score_relationship(partner, visit)
        scores['relationship_score'] = rel_score
        scores['relationship_details'] = rel_details

        # 2. Availability Score (0-25)
        avail_score, avail_details = self._score_availability(partner, visit)
        scores['availability_score'] = avail_score
        scores['availability_details'] = avail_details

        # 3. Performance Score (0-20)
        scores['performance_score'] = self._score_performance(partner)

        # 4. Proximity Score (0-10)
        scores['proximity_score'] = self._score_proximity(partner, visit)

        # 5. Workload Score (0-10)
        scores['workload_score'] = self._score_workload(partner, visit)

        # Calculate total
        scores['total_score'] = (
            scores['relationship_score'] +
            scores['availability_score'] +
            scores['performance_score'] +
            scores['proximity_score'] +
            scores['workload_score']
        )

        return scores

    def _score_relationship(self, partner, visit):
        """Score based on prior relationship with client.

        Returns:
            Tuple of (score, details_string)
        """
        relationship = self.env['wfm.partner.client.relationship'].search([
            ('partner_id', '=', partner.id),
            ('client_id', '=', visit.client_id.id)
        ], limit=1)

        if not relationship:
            return 0, _('No prior visits')

        # Use relationship_score (0-100) and scale to our weight
        raw_score = relationship.relationship_score
        scaled_score = (raw_score / 100) * self.WEIGHT_RELATIONSHIP

        # Build details string
        details = _('%(visits)s visits, last: %(date)s',
                   visits=relationship.total_visits,
                   date=relationship.last_visit_date or _('N/A'))

        return round(scaled_score, 1), details

    def _score_availability(self, partner, visit):
        """Score based on availability on visit date.

        Returns:
            Tuple of (score, details_string)
        """
        if not visit.visit_date:
            return self.WEIGHT_AVAILABILITY, _('Date not set')

        # Check for conflicting visits on the same date
        conflicts = self.env['wfm.visit'].search_count([
            ('partner_id', '=', partner.id),
            ('visit_date', '=', visit.visit_date),
            ('state', 'not in', ['cancelled', 'done']),
            ('id', '!=', visit.id)
        ])

        if conflicts > 0:
            return 0, _('%(count)s conflict(s) on this date', count=conflicts)

        # Check workload for the week
        week_start = visit.visit_date - timedelta(days=visit.visit_date.weekday())
        week_end = week_start + timedelta(days=6)

        week_visits = self.env['wfm.visit'].search_count([
            ('partner_id', '=', partner.id),
            ('visit_date', '>=', week_start),
            ('visit_date', '<=', week_end),
            ('state', 'not in', ['cancelled']),
            ('id', '!=', visit.id)
        ])

        # Deduct points for heavy weekly load (more than 5 visits)
        if week_visits >= 5:
            score = self.WEIGHT_AVAILABILITY * 0.5
            details = _('Heavy week (%(count)s visits)', count=week_visits)
        elif week_visits >= 3:
            score = self.WEIGHT_AVAILABILITY * 0.75
            details = _('Moderate week (%(count)s visits)', count=week_visits)
        else:
            score = self.WEIGHT_AVAILABILITY
            details = _('Available (%(count)s visits this week)', count=week_visits)

        return round(score, 1), details

    def _score_performance(self, partner):
        """Score based on overall performance metrics.

        Returns:
            Float score (0 to WEIGHT_PERFORMANCE)
        """
        # Get all relationships for this partner
        relationships = self.env['wfm.partner.client.relationship'].search([
            ('partner_id', '=', partner.id)
        ])

        if not relationships:
            # New partner gets neutral score
            return self.WEIGHT_PERFORMANCE * 0.5

        total_completed = sum(r.completed_visits for r in relationships)
        total_visits = sum(r.total_visits for r in relationships)

        if total_visits == 0:
            return self.WEIGHT_PERFORMANCE * 0.5

        # Completion rate (0-1)
        completion_rate = total_completed / total_visits

        # Average rating across all relationships
        rated_rels = relationships.filtered(lambda r: r.avg_rating > 0)
        if rated_rels:
            avg_rating = sum(r.avg_rating for r in rated_rels) / len(rated_rels)
            rating_factor = (avg_rating - 1) / 4  # Normalize 1-5 to 0-1
        else:
            rating_factor = 0.5  # Neutral if no ratings

        # Combined performance (60% completion, 40% rating)
        performance = (completion_rate * 0.6) + (rating_factor * 0.4)
        score = performance * self.WEIGHT_PERFORMANCE

        return round(score, 1)

    def _score_proximity(self, partner, visit):
        """Score based on geographic proximity to installation.

        Returns:
            Float score (0 to WEIGHT_PROXIMITY)
        """
        if not visit.installation_id:
            return 0

        installation_city = visit.installation_id.city
        partner_city = partner.city

        if not installation_city or not partner_city:
            return self.WEIGHT_PROXIMITY * 0.5  # Neutral if location unknown

        # Simple city match (could be enhanced with geocoding)
        if installation_city.lower().strip() == partner_city.lower().strip():
            return self.WEIGHT_PROXIMITY

        # Partial match (e.g., "Athens" in "Athens, Greece")
        if (installation_city.lower() in partner_city.lower() or
                partner_city.lower() in installation_city.lower()):
            return self.WEIGHT_PROXIMITY * 0.7

        return 0

    def _score_workload(self, partner, visit):
        """Score based on current workload balance.

        Partners with fewer assignments get higher scores to balance load.

        Returns:
            Float score (0 to WEIGHT_WORKLOAD)
        """
        # Count active assignments (not done/cancelled)
        active_count = self.env['wfm.visit'].search_count([
            ('partner_id', '=', partner.id),
            ('state', 'not in', ['done', 'cancelled']),
            ('id', '!=', visit.id)
        ])

        # Ideal load is 0-5 active visits
        if active_count <= 2:
            return self.WEIGHT_WORKLOAD
        elif active_count <= 5:
            return self.WEIGHT_WORKLOAD * 0.7
        elif active_count <= 10:
            return self.WEIGHT_WORKLOAD * 0.4
        else:
            return 0

    @api.model
    def assign_partner_to_visit(self, visit_id, partner_id):
        """Assign a partner to a visit and update state.

        Args:
            visit_id: ID of wfm.visit
            partner_id: ID of res.partner

        Returns:
            Updated visit record
        """
        visit = self.env['wfm.visit'].browse(visit_id)
        partner = self.env['res.partner'].browse(partner_id)

        if not visit.exists():
            raise UserError(_('Visit not found.'))
        if not partner.exists() or not partner.is_wfm_partner:
            raise UserError(_('Invalid partner.'))

        # Assign and move to 'assigned' state
        visit.write({
            'partner_id': partner_id,
            'state': 'assigned'
        })

        return visit
